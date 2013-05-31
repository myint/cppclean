#!/bin/bash

PGM=$1
shift

export PYTHONPATH=${0%/*}

$PYTHONPATH/cpp/$PGM $*
