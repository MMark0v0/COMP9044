#!/usr/bin/dash
# test02.sh: change command did not match any lines — should leave the original unchanged

input=$(seq 1 3)
expected=$(printf '%s\n' "$input" | 2041 pied '/xyz/c replaced')
actual=$(printf '%s\n' "$input" | python3 pied.py '/xyz/c replaced')
if [ "$actual" = "$expected" ]; then
    echo "test02.sh: PASS"
    exit 0
else
    echo "test02.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi