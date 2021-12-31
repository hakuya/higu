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
    git checkout $1 2> /dev/null || return $?
    cp $DATA_DIR/*.png . || return $?
    cp grey_sq.png grey_sq2.png || return $?
}

run() {
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

    load $COMMIT || return $?

    if [[ $VERSION = '1.0' ]]; then
        echo "Patching source..."
        patch -p1 < "$HIGU_DIR/test/fix_1.0.patch" > /dev/null || return $?
    fi

    echo "Generating DB..."
    $PYTHON "$HIGU_DIR/test/make_test_db.py" $VERSION > /dev/null || return $?

    echo "Saving DB..."
    rm -rf $DATA_DIR/ver_$VERSION.db
    mv -b $MKDB_LIB_PATH $DATA_DIR/ver_$VERSION.db

    echo ""
    clean
}

git clone $HIGU_DIR $WORK_DIR

cd $WORK_DIR
clean

run python2 1.0 d87edb56bb3f1cc81181fe1a8d78456a7246cd93
run python2 1.1 64786758ed87200e2c296c839b7ed4b2e104fa6d
run python2 2.0 9d6d91e34353b70eb6e86da069e88ff2116884a5
run python2 3.0 2c94321e777e130d1df40c916f30beeb65543dda
run python2 4.0 5408d42b1ad501c4b69ffb548d9714214123d4f4
run python2 5.0 6342ce3b0c2862d8353c65f92086987acf1f0593
run python2 6.0 cd56151a1ff3fc9f54eabda571a8ccb11b7838e6
run python2 7.0 dadd6da530a2ef4fbe9ffcb24b813c6368cb5f77
run python2 8.0 e134d661b70f7395341325c805be5c7b9aa31986
run python2 8.1 88e291f5b6b823513741fc846fc2f94d55122e31
run python2 9.0 70816940bd0c22b3c54c1da44b05dac62e712ec4
run python2 10.0 0ef7a25f1bf979bc84529c1dd4efc2893ac510b8
run python2 11.0 c4e225a0835784ffe24a68012347203183fce750
run python3 12.0 54bcea2a6df66be0c2d6f7c7d24587d9b66ce616
run python3 13.0 origin/HEAD

cd
rm -rf $WORK_DIR
