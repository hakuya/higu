#!/bin/bash

HIGUHOME="/home/hakuya/higu"
LIBRARY="/home/hakuya/.live"

if [[ $1 = '' ]]; then
    echo 'Usage: addto.sh [-r] [-a album] [-t taglist] [-n|-N] [-o|-O] file...'
    exit
fi

python $HIGUHOME/lib/insertfile.py -d $LIBRARY "$@"
