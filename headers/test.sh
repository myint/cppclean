#!/bin/bash

# Run all the unittests.

export PYTHONPATH=${0%/*}

for f in $PYTHONPATH/cpp/*_test.py ; do
  $f
done
