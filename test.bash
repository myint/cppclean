#!/bin/bash -ex

for test in *test.py
do
    ./$test
done

rm -f .tmp
./cppclean test/ | grep -v Processing | grep -v Unable > .tmp
diff --unified .tmp test/expected.txt && rm -f .tmp
