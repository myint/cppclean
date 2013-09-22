#!/bin/bash -ex

for test in test_*.py
do
    ./"$test"
done

rm -f '.tmp'
./cppclean \
    --include-path='test/external' \
    --exclude='ignore.cc' \
    'test' > '.tmp'
diff --unified 'test/expected.txt' '.tmp' && rm -f '.tmp'
