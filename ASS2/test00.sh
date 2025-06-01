#!/usr/bin/dash
# test00.sh: d command without address — delete all lines

input=$(seq 1 3)
expected=$(printf '%s\n' "$input" | 2041 pied 'd')
actual=$(printf '%s\n' "$input" | python3 pied.py 'd')
if [ "$actual" = "$expected" ]; then
    echo "test00.sh: PASS"
    exit 0
else
    echo "test00.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi