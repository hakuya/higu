#!/bin/bash

export HIGU_BINDADDR="0.0.0.0"
export HIGU_BINDPORT="30080"

HIGUHOME="/home/hakuya/higu"
LIBRARY="/home/hakuya/.live"

cd $HIGUHOME
python lib/server.py $LIBRARY