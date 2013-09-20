#!/bin/bash -ex

for test in *test.py
do
    ./"$test"
done

rm -f '.tmp'
./cppclean 'test' > '.tmp'
diff --unified 'test/expected.txt' '.tmp' && rm -f '.tmp'
