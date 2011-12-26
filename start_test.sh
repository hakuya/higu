#!/bin/bash

export HIGU_BINDADDR="0.0.0.0"
export HIGU_BINDPORT="8880"

HIGUHOME="/home/hakuya/higu"
LIBRARY="/home/hakuya/.test"

cd $HIGUHOME
python lib/server.py $LIBRARY
