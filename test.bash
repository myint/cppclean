#!/bin/bash -ex

for test in *test.py
do
    ./$test
done

cd 'test'
rm -f '.tmp'
../cppclean . > '.tmp'
diff --unified '.tmp' 'expected.txt' && rm -f '.tmp'
