#!/usr/bin/dash
# test09.sh: No matching for p or s under -n option — should remain completely silent

input=$(printf 'foo\nbar\nbaz\n')
expected=$(printf '%s\n' "$input" | 2041 pied '/2/p')
actual=$(printf '%s\n' "$input" | python3 pied.py '/2/p')
if [ "$actual" = "$expected" ]; then
  echo "test09.sh: PASS"
  exit 0
else
    echo "test09.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi