#!/bin/bash -ex

for test in *test.py
do
    ./$test
done

rm -f '.tmp'
./cppclean 'test' > '.tmp'
diff --unified '.tmp' 'test/expected.txt' && rm -f '.tmp'
