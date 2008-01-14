#!/bin/sh

# Run all the unittests.

export PYTHONPATH=/home/$USER/work/headers

for f in $PYTHONPATH/cpp/*_test.py ; do
  $f
done
