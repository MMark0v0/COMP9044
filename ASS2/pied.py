#!/usr/bin/env python3
'''
A lightweight sed-like stream editor supporting print, delete, substitute, insert, append, and change commands with regex or line address ranges, processing text from stdin or files, optionally suppressing automatic printing.
'''


import sys
import re
import argparse
from io import StringIO


def parse_args():
    """
    Parse command-line arguments and prepare input sources.
    """
    parser = argparse.ArgumentParser(
        description="Pied: simplified sed-like stream editor",
        usage="pied.py [-n] [-i] [-f SCRIPT] [COMMAND] [FILES...]"
    )
    parser.add_argument('-n', action='store_true', dest='no_auto',)
    parser.add_argument('-i', action='store_true', dest='place',)
    parser.add_argument('-f', '--script-file',)
    parser.add_argument('target_file', nargs='*',)
    args = parser.parse_args()

    # Determine where commands come from and which files to process
    if args.script_file:
        args.commands_raw = None
        args.files = args.target_file
    elif args.target_file:
        # First target is the inline commands, rest are files
        args.commands_raw = args.target_file[0]
        args.files = args.target_file[1:]
    else:
        args.commands_raw = None
        args.files = []
    return args


def load_script(args):
    """
    Load and normalize the script commands
    """
    raw_lines = []
    if args.script_file:
        with open(args.script_file) as f:
            raw_lines = f.read().splitlines()
    elif args.commands_raw:
        raw_lines = args.commands_raw.splitlines()
    else:
        return ''

    cleaned = []
    for line in raw_lines:
        # Remove comments and trim
        code = line.split('#', 1)[0].strip()
        if code:
            # Normalize spaces around commas
            code = re.sub(r'\s*,\s*', ',', code)
            cleaned.append(code)
    # Combine commands into a single script string
    return ';'.join(cleaned)


def split_commands(script: str) -> list[str]:
    """
    Split a script string into individual commands, handling
    """
    cmds: list[str] = []
    i = 0
    n = len(script)

    def skip_regex(idx: int) -> int:
        """
        Advance past a `/.../` regex, handling escaped slashes.
        Return the position just after the closing slash.
        """
        idx += 1  # skip opening '/'
        while idx < n:
            if script[idx] == "\\":      # escaped character
                idx += 2
                continue
            if script[idx] == "/":
                return idx + 1  # after closing '/'
            idx += 1
        raise ValueError("Unterminated regex address")

    while i < n:
        # Skip whitespace or extra semicolons
        while i < n and (script[i].isspace() or script[i] == ';'):
            i += 1
        if i >= n:
            break

        cmd_start = i

        # Parse up to two optional addresses
        for addr_index in range(2):
            if i < n and script[i] == '/':
                i = skip_regex(i)
            elif i < n and (script[i].isdigit() or script[i] == '$'):
                # Numeric line or end-of-file symbol
                while i < n and script[i].isdigit():
                    i += 1
                if i < n and script[i] == '$':
                    i += 1
            else:
                break
            # If first address, allow a comma then continue second address
            if addr_index == 0 and i < n and script[i] == ',':
                i += 1
                while i < n and script[i].isspace():
                    i += 1
            else:
                break

        # Skip whitespace before the command letter
        while i < n and script[i].isspace():
            i += 1
        if i >= n:
            cmds.append(script[cmd_start:].strip())
            break

        cmd_letter = script[i]

        # Substitute command 's' — read until next unescaped semicolon
        if cmd_letter == 's':
            i += 1
            if i >= n:
                raise ValueError("Invalid substitute syntax — missing delimiter")
            delim = script[i]
            i += 1
            # Skip pattern
            while i < n:
                if script[i] == "\\":
                    i += 2
                    continue
                if script[i] == delim:
                    i += 1
                    break
                i += 1
            else:
                raise ValueError("Invalid substitute syntax — unterminated pattern")
            # Skip replacement
            while i < n:
                if script[i] == "\\":
                    i += 2
                    continue
                if script[i] == delim:
                    i += 1
                    break
                i += 1
            else:
                raise ValueError("Invalid substitute syntax — unterminated replacement")
            # Skip flags until semicolon
            while i < n and script[i] != ';':
                i += 1
            cmds.append(script[cmd_start:i].strip())
            if i < n and script[i] == ';':
                i += 1
            continue

        # Insert, append, or change — consume rest of script as literal text
        if cmd_letter in ('i', 'a', 'c'):
            cmds.append(script[cmd_start:].rstrip())
            break

        # Other commands — read until next unescaped semicolon
        i += 1
        while i < n:
            if script[i] == '/':
                try:
                    i = skip_regex(i)
                    continue
                except ValueError:
                    pass
            if script[i] == "\\":
                i += 2
                continue
            if script[i] == ';':
                break
            i += 1
        cmds.append(script[cmd_start:i].strip())
        if i < n and script[i] == ';':
            i += 1

    # Filter out any empty commands
    return [c for c in cmds if c]


def parse_single_address(addr):
    """Convert an address string to a usable form: int, '$', or regex."""
    if not addr:
        return None
    token = addr.strip()
    if token == '$':
        return '$'
    if re.fullmatch(r'\d+', token):
        return int(token)
    # Regex address: strip slashes
    return re.compile(token.strip('/'))


def parse_command(cmd_str):
    """
    Parse a single command string into its components
    """
    addr_pattern = r'(?:\d+|\$|/(?:\\/|[^/])*/)'  # number, $, or /regex/
    commands = 'pdqsai c'.replace(' ', '')  # allowed command letters
    regex = re.compile(
        rf'^\s*({addr_pattern})?'         # optional address1
        rf'(?:\s*,\s*({addr_pattern}))?'  # optional address2
        rf'\s*([{commands}])'             # command letter
        r'\s*(.*)$'                       # rest of the command
    )
    m = regex.match(cmd_str)
    if not m:
        raise ValueError(f"Invalid command: '{cmd_str}'")
    addr1_str, addr2_str, cmd, rest = m.groups()
    address1 = parse_single_address(addr1_str) if addr1_str else None
    address2 = parse_single_address(addr2_str) if addr2_str else None
    argv = []


    if cmd == 's':
        rest_str = rest
        # 1) delimitor is the very first char
        delim = rest_str[0]
        i = 1

        # 2) extract pattern
        pat_chars = []
        while i < len(rest_str):
            c = rest_str[i]
            # a) escaping the delim ⇒ literal delim
            if c == '\\' and i+1 < len(rest_str) and rest_str[i+1] == delim:
                pat_chars.append(delim)
                i += 2
                continue
            # b) general escape ⇒ keep both
            if c == '\\' and i+1 < len(rest_str):
                pat_chars.append(c)
                pat_chars.append(rest_str[i+1])
                i += 2
                continue
            # c) unescaped delim ⇒ end of pattern
            if c == delim:
                i += 1
                break
            # d) normal char
            pat_chars.append(c)
            i += 1
        pattern = ''.join(pat_chars)

        # 3) extract replacement
        rep_chars = []
        while i < len(rest_str):
            c = rest_str[i]
            # a) escaping the delim ⇒ literal delim
            if c == '\\' and i+1 < len(rest_str) and rest_str[i+1] == delim:
                rep_chars.append(delim)
                i += 2
                continue
            # b) general escape ⇒ keep both
            if c == '\\' and i+1 < len(rest_str):
                rep_chars.append(c)
                rep_chars.append(rest_str[i+1])
                i += 2
                continue
            # c) unescaped delim ⇒ end of replacement
            if c == delim:
                i += 1
                break
            # d) normal char
            rep_chars.append(c)
            i += 1
        replacement = ''.join(rep_chars)

        # 4) whatever remains are flags
        flags = rest_str[i:]
        argv = [pattern, replacement, flags]
    elif cmd in ('a', 'i', 'c'):
        argv = [rest]

    return {
        'address1': address1,
        'address2': address2,
        'command': cmd,
        'argv': argv,
        'in_range': False,
        'range_output': False,
    }


def match_address_single(addr, line, ln, last):
    """
    Check a single address against the current line
    """
    if addr is None:
        return True
    if isinstance(addr, int):
        return ln == addr
    if addr == '$':
        return last
    return bool(addr.search(line))


def match_address(cmd, line, ln, last=False):
    """
    Determine whether the given command applies to the current line,
    handling single-address and two-address range logic.
    """
    a1, a2 = cmd['address1'], cmd['address2']
    # Two-address range commands
    if a2 is not None:
        if cmd['command'] in ('p', 'c'):
            # Range for print or change: single pass through range
            if not cmd['in_range'] and not cmd.get('range_done', False):
                if match_address_single(a1, line, ln, last):
                    cmd['in_range'] = True
                    return True
                return False
            if cmd['in_range']:
                if match_address_single(a2, line, ln, last):
                    cmd['in_range'] = False
                    cmd['range_done'] = True
                return True
            # After finishing once, only match address1 again
            return match_address_single(a1, line, ln, last)
        else:
            # Standard sed range behavior (multiple ranges allowed)
            if not cmd['in_range']:
                if match_address_single(a1, line, ln, last):
                    cmd['in_range'] = True
                    return True
                return False
            if match_address_single(a2, line, ln, last):
                cmd['in_range'] = False
            return True
    # Single-address commands
    return match_address_single(a1, line, ln, last)


def process_stream_stream(commands, args):
    """
    Process stdin line by line, handling live streaming
    """
    stream = sys.stdin
    first = stream.readline()
    if not first:
        return
    ln = 1
    cur = first.rstrip('\n')

    while True:
        nxt = stream.readline()
        last = (nxt == '')
        to_print = []
        deleted = False
        quit_now = False

        # 1) insert before (i)
        for cmd in commands:
            if cmd['command'] == 'i' and match_address(cmd, cur, ln, last):
                to_print.append(cmd['argv'][0])

        # 2) change (c) — handle first, single or ranged
        for cmd in commands:
            if cmd['command'] != 'c':
                continue
            a1, a2 = cmd['address1'], cmd['address2']
            # Single-address change
            if a2 is None:
                if match_address_single(a1, cur, ln, last):
                    to_print.append(cmd['argv'][0])
                    deleted = True
                break
            # Ranged change
            if not cmd['in_range'] and match_address_single(a1, cur, ln, last):
                cmd['in_range'] = True
                cmd['range_output'] = False
            if cmd['in_range']:
                if not cmd['range_output']:
                    to_print.append(cmd['argv'][0])
                    cmd['range_output'] = True
                if match_address_single(a2, cur, ln, last) or last:
                    cmd['in_range'] = False
                deleted = True
                break

        # 3) other commands: q, d, s, p
        if not deleted:
            for cmd in commands:
                if not match_address(cmd, cur, ln, last):
                    continue
                c = cmd['command']
                if c == 'q':
                    quit_now = True
                    break
                if c == 'd':
                    deleted = True
                    break
                if c == 's':
                    pat, repl, flags = cmd['argv']
                    # global vs single replacement
                    if 'g' in flags:
                        cur = re.sub(pat, repl, cur)
                    else:
                        cur = re.sub(pat, repl, cur, count=1)
                if c == 'p':
                    to_print.append(cur)

        # 4) default printing
        if not args.no_auto and not deleted:
            to_print.append(cur)

        # 5) append after (a)
        for cmd in commands:
            if cmd['command'] == 'a' and match_address(cmd, cur, ln, last):
                to_print.append(cmd['argv'][0])

        # 6) output collected lines
        for line in to_print:
            print(line)

        # 7) quit if requested
        if quit_now:
            sys.exit(0)

        if last:
            break

        ln += 1
        cur = nxt.rstrip('\n')


def process_stream(commands, args, raw_lines):
    """
    Process a list of lines (e.g., from files) similarly to streaming.
    """
    total = len(raw_lines)
    ln = 1
    for idx, raw in enumerate(raw_lines):
        cur = raw.rstrip('\n')
        last = (idx == total - 1)
        to_print = []
        deleted = False
        quit_now = False

        # Repeat same command logic as streaming...
        # Insert before
        for cmd in commands:
            if cmd['command'] == 'i' and match_address(cmd, cur, ln, last):
                to_print.append(cmd['argv'][0])
        # Change
        for cmd in commands:
            if cmd['command'] != 'c':
                continue
            a1, a2 = cmd['address1'], cmd['address2']
            if a2 is None:
                if match_address_single(a1, cur, ln, last):
                    to_print.append(cmd['argv'][0])
                    deleted = True
                break
            if not cmd['in_range'] and match_address_single(a1, cur, ln, last):
                cmd['in_range'] = True
                cmd['range_output'] = False
            if cmd['in_range']:
                if not cmd['range_output']:
                    to_print.append(cmd['argv'][0])
                    cmd['range_output'] = True
                if match_address_single(a2, cur, ln, last) or last:
                    cmd['in_range'] = False
                    cmd['range_output'] = False
                deleted = True
                break
        # Other commands: q/d/s/p
        if not deleted:
            for cmd in commands:
                if not match_address(cmd, cur, ln, last):
                    continue
                c = cmd['command']
                if c == 'q':
                    quit_now = True
                    break
                if c == 'd':
                    deleted = True
                    break
                if c == 's':
                    pat, repl, flags = cmd['argv']
                    cur = re.sub(pat, repl, cur, 0 if 'g' in flags else 1)
                if c == 'p':
                    to_print.append(cur)
        # Default print
        if not args.no_auto and not deleted:
            to_print.append(cur)
        # Append after
        for cmd in commands:
            if cmd['command'] == 'a' and match_address(cmd, cur, ln, last):
                to_print.append(cmd['argv'][0])
        # Output
        for line in to_print:
            print(line)
        # Quit
        if quit_now:
            sys.exit(0)
        ln += 1


def main():
    args = parse_args()
    script = load_script(args)
    commands = [parse_command(c) for c in split_commands(script)]

    if args.files:
        if args.place:
            # In-place edit: read and overwrite each file
            for fname in args.files:
                with open(fname) as f:
                    lines = f.readlines()
                buf = StringIO()
                orig_stdout = sys.stdout
                sys.stdout = buf
                process_stream(commands, args, lines)
                sys.stdout = orig_stdout
                with open(fname, 'w') as f:
                    f.write(buf.getvalue())
        else:
            # Read files and write to stdout
            raw_lines = []
            for fname in args.files:
                raw_lines.extend(open(fname).readlines())
            process_stream(commands, args, raw_lines)
    else:
        # No files: read from stdin
        process_stream_stream(commands, args)


if __name__ == '__main__':
    main()
