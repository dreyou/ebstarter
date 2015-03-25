#!/bin/sh

pushd `dirname $0` > /dev/null
CPATH=`pwd -P`
popd > /dev/null

COPER=$1
CAPP=$2
CSRC=$3

COPER=${COPER:=create}

CAPP=${CAPP:=samplepdf}

CSRC=${CSRC:=none}

$CPATH/sender.py -a $CAPP -o $COPER -s $CSRC

exit 0