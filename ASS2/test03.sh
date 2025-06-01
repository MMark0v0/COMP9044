#!/usr/bin/dash
# test03.sh: Only execute the i command, everything after it is treated as text

input='a\nb\nc\nd\n'
expected=$(echo "$input" | 2041 pied '3i Y;3a X')
actual=$(echo "$input" | python3 pied.py '3i Y;3a X')
if [ "$actual" = "$expected" ]; then
    echo "test03.sh: PASS"
    exit 0
else
    echo "test03.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi