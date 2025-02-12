#!/bin/bash

HIGU_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
DATA_DIR="$HIGU_DIR/test/data"
WORK_DIR="$( mktemp -d )"

REQUESTED=$1

export PYTHONPATH="$WORK_DIR/lib"
export MKDB_LIB_PATH="$WORK_DIR/lib.db"

clean() {
    rm -f *.png
    rm -f lib/*.pyc
    rm -rf $MKDB_LIB_PATH
    git checkout .
}

load() {
    git checkout $1 > /dev/null || return $?
    cp $DATA_DIR/*.png . || return $?
    cp grey_sq.png grey_sq2.png || return $?
}

sql_dump() {
    sqlite3 "$1" << EOF
.output "$2"
.dump
.exit
EOF
}

build_db() {
    PYTHON="$1"
    VERSION="$2"
    COMMIT="$3"

    if ! [ -z $REQUESTED ] && [ $VERSION != $REQUESTED ]; then
        return
    fi

    echo "Making database for v$VERSION"
    echo "==============================="

    echo "[main]" > build_dbs.cfg
    echo "library = $MKDB_LIB_PATH" >> build_dbs.cfg

    echo "Loading files..."

    load $COMMIT || exit $?

    echo "Generating DB..."
    $PYTHON "$HIGU_DIR/test/make_test_db.py" $VERSION > /dev/null || return $?

    echo "Saving DB..."

    rm -rf $DATA_DIR/ver_$VERSION.db
    cp -r $MKDB_LIB_PATH $DATA_DIR/ver_$VERSION.db
    sql_dump $DATA_DIR/ver_$VERSION.db/hfdb.dat $DATA_DIR/ver_$VERSION.db/hfdb.sql

    echo ""
    clean
}

PYTHON2_VER=$(python2 --version 2>&1)
if [ $? -eq 0 ] && [[ "$PYTHON2_VER" == "Python"* ]]; then
    # Only produce python2 versions if we have python2

    DB_1_0_COMMIT=schema-1.0p1
    DB_1_0_PYTHON=python2
    ALL_VERSIONS="1.0"

    DB_1_1_COMMIT=schema-1.1
    DB_1_1_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 1.1"

    DB_2_0_COMMIT=schema-2.0
    DB_2_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 2.0"

    DB_3_0_COMMIT=schema-3.0
    DB_3_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 3.0"

    DB_4_0_COMMIT=schema-4.0
    DB_4_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 4.0"

    DB_5_0_COMMIT=schema-5.0
    DB_5_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 5.0"

    DB_6_0_COMMIT=schema-6.0
    DB_6_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 6.0"

    DB_7_0_COMMIT=schema-7.0
    DB_7_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 7.0"

    DB_8_0_COMMIT=schema-8.0
    DB_8_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 8.0"

    DB_8_1_COMMIT=schema-8.1
    DB_8_1_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 8.1"

    DB_9_0_COMMIT=schema-9.0
    DB_9_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 9.0"

    DB_10_0_COMMIT=schema-10.0
    DB_10_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 10.0"

    DB_11_0_COMMIT=schema-11.0
    DB_11_0_PYTHON=python2
    ALL_VERSIONS="$ALL_VERSIONS 11.0"
fi

DB_12_0_COMMIT=schema-12.0p1
DB_12_0_PYTHON=python3
ALL_VERSIONS="$ALL_VERSIONS 12.0"

DB_13_0_COMMIT=schema-13.0p1
DB_13_0_PYTHON=python3
ALL_VERSIONS="$ALL_VERSIONS 13.0"

DB_13_1_COMMIT=schema-13.1p1
DB_13_1_PYTHON=python3
ALL_VERSIONS="$ALL_VERSIONS 13.1"

DB_14_0_COMMIT=schema-14.0p1
DB_14_0_PYTHON=python3
ALL_VERSIONS="$ALL_VERSIONS 14.0"

DB_14_1_COMMIT=$(git -C $HIGU_DIR rev-parse HEAD)
DB_14_1_PYTHON=python3
ALL_VERSIONS="$ALL_VERSIONS 14.1"

db_var()
{
    verstr=$(echo $1 | sed 's/\./_/g')
    echo $(eval echo \$DB_${verstr}_${2})
}

run()
{
    local VERSION=$1
    local ORIGIN=$2

    if [ $ORIGIN = "build" ]; then
        build_db $(db_var $VERSION PYTHON) $VERSION $(db_var $VERSION COMMIT)
    fi
}

VERSION=${1:-all}
ORIGIN=${2:-build}

if [ $ORIGIN = "build" ]; then
    git clone $HIGU_DIR $WORK_DIR

    cd $WORK_DIR
    clean
fi

if [ $VERSION = "all" ]; then
    for ver in $ALL_VERSIONS; do
        run $ver $ORIGIN
    done
    echo $ALL_VERSIONS > $DATA_DIR/versions.txt
else
    run $VERSION $ORIGIN
    echo $VERSION > $DATA_DIR/versions.txt
fi

if [ $ORIGIN = "build" ]; then
    cd
    rm -rf $WORK_DIR
fi
