#!/bin/bash

# We attempt to determine the path to the higu directory automatically. For
# safety or for alternate installation configurations, you may hardcode the
# path here.
HIGUHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $HIGUHOME

export PYTHONPATH=./lib:./test

if [ -z $1 ] || [ $1 == "req" ]; then
    echo 'Testing system requirements to run HIGU'
    echo '============================================================'
    python test/req_cases.py || exit $?
fi

if [ -z $1 ] || [ $1 == "imgdb" ]; then
    echo 'Testing image database functions'
    echo '============================================================'
    python test/imgdb_cases.py || exit $?
fi

if [ -z $1 ] || [ $1 == "hdbfs" ] || [ $1 == "hdbfs_core" ]; then
    echo 'Testing HDBFS core library and database functions'
    echo '============================================================'
    python test/higu_cases.py || exit $?
fi

if [ -z $1 ] || [ $1 == "hdbfs" ] || [ $1 == "hdbfs_query" ]; then
    echo 'Testing HDBFS core library query functions'
    echo '============================================================'
    python test/query_cases.py || exit $?
fi

if [ -z $1 ] || [ $1 == "hdbfs" ] || [ $1 == "hdbfs_thumb" ]; then
    echo 'Testing HDBFS thumbnail functions'
    echo '============================================================'
    python test/thumb_cases.py || exit $?
fi

if [ -z $1 ] || [ $1 == "insert" ]; then
    echo 'Testing insertfile script'
    echo '============================================================'
    python test/insert_cases.py || exit $?
fi

if [ -z $1 ] || [ $1 == "web" ]; then
    echo 'Testing web session'
    echo '============================================================'
    python test/websession_cases.py || exit $?
fi

if [ -z $1 ] || [ $1 == "legacy" ]; then
    echo 'Creating databases for next tests'
    echo '============================================================'
    test/build_legacy_dbs.sh || exit $?

    echo 'Testing legacy support'
    echo '============================================================'
    python test/legacy_cases.py || exit $?
fi
