#!/usr/bin/dash
# test08.sh: Default printing + p — Without using -n, '/2/p' should print line 2 twice

input=$(printf '1\n2\n3\n')
expected=$(printf '%s\n' "$input" | 2041 pied '/2/p')
actual=$(printf '%s\n' "$input" | python3 pied.py '/2/p')
if [ "$actual" = "$expected" ]; then
    echo "test08.sh: PASS"
    exit 0
else
    echo "test08.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi