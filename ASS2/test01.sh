#!/usr/bin/dash
# test01.sh: Out-of-range append — should have no effect when the address exceeds the total number of lines

input=$(seq 1 3)
expected=$(printf '%s\n' "$input" | 2041 pied '10a hello')
actual=$(printf '%s\n' "$input" | python3 pied.py '10a hello')
if [ "$actual" = "$expected" ]; then
    echo "test01.sh: PASS"
    exit 0
else
    echo "test01.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi