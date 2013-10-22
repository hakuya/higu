#!/bin/bash

# We attempt to determine the path to the higu directory automatically. For
# safety or for alternate installation configurations, you may hardcode the
# path here.
HIGUHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NAME=`basename $0`
NAME=${NAME%.*}
NAME=${NAME#*.}

# Set the path to the main config file here
HIGUCFG="$HIGUHOME/$NAME.cfg"

if [[ $1 = '' ]]; then
    echo "Usage: $(basename $0) [-a album] [-t taglist] [-n|-N] [-o|-O] file..."
    exit
fi

python $HIGUHOME/lib/insertfile.py -c $HIGUCFG "$@"