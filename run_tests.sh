#!/bin/bash

# We attempt to determine the path to the higu directory automatically. For
# safety or for alternate installation configurations, you may hardcode the
# path here.
HIGUHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $HIGUHOME

export PYTHONPATH=./lib:./test

echo 'Testing system requirements to run HIGU'
echo '============================================================'
python test/req_cases.py || exit $?

echo 'Testing HIGU core library and database functions'
echo '============================================================'
python test/higu_cases.py || exit $?

echo 'Testing insertfile script'
echo '============================================================'
python test/insert_cases.py || exit $?
