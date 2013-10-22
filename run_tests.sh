#!/bin/bash

# We attempt to determine the path to the higu directory automatically. For
# safety or for alternate installation configurations, you may hardcode the
# path here.
HIGUHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $HIGUHOME

PYTHONPATH=./lib:./test

echo 'Testing HIGU core library and database functions'
echo '============================================================'
python test/higu_cases.py
