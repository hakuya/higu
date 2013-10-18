#!/bin/bash

# We attempt to determine the path to the higu directory automatically. For
# safety or for alternate installation configurations, you may hardcore the
# path here.
HIGUHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NAME=`basename $0`
NAME=${NAME%.*}
NAME=${NAME#*.}

# Set the path to the main config file here
HIGUCFG="$HIGUHOME/$NAME.cfg"

cd $HIGUHOME
python lib/server.py $HIGUCFG
