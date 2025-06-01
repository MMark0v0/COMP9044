#!/usr/bin/dash
# test07.sh: Multiple commands combined, all following the a command are treated as text

input=$(seq 1 5)
expected=$(printf '%s\n' "$input" | 2041 pied '2d;4a X;s/5/50/')
actual=$(printf '%s\n' "$input" | python3 pied.py '2d;4a X;s/5/50/')
if [ "$actual" = "$expected" ]; then
    echo "test07.sh: PASS"
    exit 0
else
    echo "test07.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi

