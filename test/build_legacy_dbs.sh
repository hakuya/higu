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

map_images() {
    for img in $(find "$1" -iname '*.png'); do
        img_hash=$(md5sum "$img" | cut -d" " -f1 )
        match=
        for orig in $(find "$2" -maxdepth 1 -iname '*.png'); do
            orig_hash=$(md5sum "$orig" | cut -d" " -f1 )
            if [ "$img_hash" = "$orig_hash" ]; then
                match="$orig"
                break
            fi
        done
        if [ -z "$match" ]; then
            echo "Failed matching $img"
            exit 1
        fi
        rel_match=$(realpath -s --relative-to="$(dirname "$img")" "$match")
        rm "$img"
        ln -s "$rel_match" "$img"
    done
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

    if [[ $VERSION = '1.0' ]]; then
        echo "Patching source..."
        patch -p1 < "$HIGU_DIR/test/fix_1.0.patch" > /dev/null || return $?
    fi

    echo "Generating DB..."
    $PYTHON "$HIGU_DIR/test/make_test_db.py" $VERSION > /dev/null || return $?

    echo "Saving DB..."

    rm -rf $DATA_DIR/ver_$VERSION.db
    mv -b $MKDB_LIB_PATH $DATA_DIR/ver_$VERSION.db
    sql_dump $DATA_DIR/ver_$VERSION.db/hfdb.dat $DATA_DIR/ver_$VERSION.db/hfdb.sql
    map_images $DATA_DIR/ver_$VERSION.db $DATA_DIR

    echo ""
    clean
}

DB_1_0_COMMIT=d87edb56bb3f1cc81181fe1a8d78456a7246cd93
DB_1_0_PYTHON=python2
ALL_VERSIONS="1.0"

DB_1_1_COMMIT=64786758ed87200e2c296c839b7ed4b2e104fa6d
DB_1_1_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 1.1"

DB_2_0_COMMIT=9d6d91e34353b70eb6e86da069e88ff2116884a5
DB_2_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 2.0"

DB_3_0_COMMIT=2c94321e777e130d1df40c916f30beeb65543dda
DB_3_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 3.0"

DB_4_0_COMMIT=5408d42b1ad501c4b69ffb548d9714214123d4f4
DB_4_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 4.0"

DB_5_0_COMMIT=6342ce3b0c2862d8353c65f92086987acf1f0593
DB_5_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 5.0"

DB_6_0_COMMIT=cd56151a1ff3fc9f54eabda571a8ccb11b7838e6
DB_6_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 6.0"

DB_7_0_COMMIT=dadd6da530a2ef4fbe9ffcb24b813c6368cb5f77
DB_7_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 7.0"

DB_8_0_COMMIT=e134d661b70f7395341325c805be5c7b9aa31986
DB_8_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 8.0"

DB_8_1_COMMIT=88e291f5b6b823513741fc846fc2f94d55122e31
DB_8_1_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 8.1"

DB_9_0_COMMIT=70816940bd0c22b3c54c1da44b05dac62e712ec4
DB_9_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 9.0"

DB_10_0_COMMIT=0ef7a25f1bf979bc84529c1dd4efc2893ac510b8
DB_10_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 10.0"

DB_11_0_COMMIT=f46f708691666979c0444b4eaa483c8a339e8838
DB_11_0_PYTHON=python2
ALL_VERSIONS="$ALL_VERSIONS 11.0"

DB_12_0_COMMIT=54bcea2a6df66be0c2d6f7c7d24587d9b66ce616
DB_12_0_PYTHON=python3
ALL_VERSIONS="$ALL_VERSIONS 12.0"

DB_13_0_COMMIT=origin/HEAD
DB_13_0_PYTHON=python3
ALL_VERSIONS="$ALL_VERSIONS 13.0"

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
else
    run $VERSION $ORIGIN
fi

if [ $ORIGIN = "build" ]; then
    cd
    rm -rf $WORK_DIR
fi
