#!/bin/sh

PGM=$1
shift

export PYTHONPATH=/home/$USER/work/headers

$PYTHONPATH/cpp/$PGM.py $*
