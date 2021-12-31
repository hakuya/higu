#!/bin/bash

# We attempt to determine the path to the higu directory automatically. For
# safety or for alternate installation configurations, you may hardcode the
# path here.
HIGUHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $HIGUHOME

PYTHON=python3

export PYTHONPATH=./lib:./test

if [ -z $1 ] || [ $1 == "req" ]; then
    echo 'Testing system requirements to run HIGU'
    echo '============================================================'
    $PYTHON test/req_cases.py $2 || exit $?
fi

if [ -z $1 ] || [ $1 == "imgdb" ]; then
    echo 'Testing image database functions'
    echo '============================================================'
    $PYTHON test/imgdb_cases.py $2 || exit $?
fi

if [ -z $1 ] || [ $1 == "hdbfs" ] || [ $1 == "hdbfs_core" ]; then
    echo 'Testing HDBFS core library and database functions'
    echo '============================================================'
    $PYTHON test/higu_cases.py $2 || exit $?
fi

if [ -z $1 ] || [ $1 == "hdbfs" ] || [ $1 == "hdbfs_query" ]; then
    echo 'Testing HDBFS core library query functions'
    echo '============================================================'
    $PYTHON test/query_cases.py $2 || exit $?
fi

if [ -z $1 ] || [ $1 == "hdbfs" ] || [ $1 == "hdbfs_thumb" ]; then
    echo 'Testing HDBFS thumbnail functions'
    echo '============================================================'
    $PYTHON test/thumb_cases.py $2 || exit $?
fi

if [ -z $1 ] || [ $1 == "insert" ]; then
    echo 'Testing insertfile script'
    echo '============================================================'
    $PYTHON test/insert_cases.py $2 || exit $?
fi

if [ -z $1 ] || [ $1 == "web" ]; then
    echo 'Testing web session'
    echo '============================================================'
    $PYTHON test/websession_cases.py $2 || exit $?
fi

if [ -z $1 ] || [ $1 == "legacy" ]; then
    echo 'Creating databases for next tests'
    echo '============================================================'
    test/build_legacy_dbs.sh $2 || exit $?

    echo 'Testing legacy support'
    echo '============================================================'
    $PYTHON test/legacy_cases.py $2 || exit $?
fi
