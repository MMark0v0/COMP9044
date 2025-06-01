#!/usr/bin/dash
# test06.sh: -n + range p — only print lines 2 to 4

input=$(seq 1 5)
expected=$(printf '%s\n' "$input" | 2041 pied -n '2,4p')
actual=$(printf '%s\n' "$input" | python3 pied.py -n '2,4p')
if [ "$actual" = "$expected" ]; then
    echo "test06.sh: PASS"
    exit 0
else
    echo "test06.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi