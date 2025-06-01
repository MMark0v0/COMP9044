#!/usr/bin/dash
# test05.sh: Under -n, no matching p or s — should remain completely silent

input=$(printf 'foo\nbar\nbaz\n')
expected=$(echo "$input" | 2041 pied -n 's/xyz/XYZ/')
actual=$(echo "$input" | python3 pied.py -n 's/xyz/XYZ/')
if [ -z "$actual" ]; then
    echo "test05.sh: PASS"
    exit 0
else
    echo "test05.sh: FAIL"
    echo "Got: \n$actual"
    echo "Answer is:\n$expected"
    exit 1
fi