#!/bin/bash -ex

rm -f .tmp
./cppclean test/ | grep -v Processing | grep -v Unable > .tmp
diff --unified .tmp test/expected.txt && rm -f .tmp
