#!/bin/bash -ex

trap "echo -e '\x1b[01;31mFailed\x1b[0m'" ERR

for test in test_*.py
do
    $PYTHON ./"$test"
done

$PYTHON ./cppclean test/c++11.h

rm -f '.tmp'
$PYTHON ./cppclean \
    --include-path='test/external' \
    --exclude='ignore.cc' \
    'test' > '.tmp' || true
diff --unified 'test/expected.txt' '.tmp'
rm -f '.tmp'

echo -e '\x1b[01;32mOkay\x1b[0m'
