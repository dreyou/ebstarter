#!/bin/sh

pushd `dirname $0` > /dev/null
CPATH=`pwd -P`
popd > /dev/null

COPER=$1
CAPP=$2

COPER=${COPER:=create}

CAPP=${CAPP:=samplepdf}

if [ -z "$AWSENV" ]
then
    AWSENV=$CPATH/.aws/aws_env
fi

if [ ! -f "$AWSENV" ]
then
    echo "$AWSENV not found"
    exit 1
fi

. $AWSENV &>/dev/null

$CPATH/sender.py -a $CAPP -o $COPER

exit 0