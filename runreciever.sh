#!/bin/sh

pushd `dirname $0` > /dev/null
CPATH=`pwd -P`
popd > /dev/null

RUN=$1

if [ -z "$AWSENV" ]
then
    AWSENV=$CPATH/.aws/aws_env
fi

if [ ! -f "$AWSENV" ]
then
    echo "$AWSENV not found"
    exit 1
fi

if [[ $RUN == 'run' ]]
then
    RUN="-r yes"
else
    RUN=""
fi

. $AWSENV &>/dev/null

$CPATH/reciever.py $RUN

exit 0