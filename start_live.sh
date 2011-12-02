#!/bin/bash

export HIGU_BINDADDR="0.0.0.0"
export HIGU_BINDPORT="8080"

LIBRARY="/home/hakuya/.live"

python lib/server.py $LIBRARY
