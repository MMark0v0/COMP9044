#!/usr/bin/dash
# test04.sh: Delete from line 3 to the end (3,$d)

input=$(seq 1 5)
expected=$(printf '%s\n' "$input" | 2041 pied '3,$d')
actual=$(printf '%s\n' "$input" | python3 pied.py '3,$d')
if [ "$actual" = "$expected" ]; then
    echo "test04.sh: PASS"
    exit 0
else
    echo "test04.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi