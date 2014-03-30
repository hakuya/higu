#!/bin/bash

HIGU_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
DATA_DIR="$HIGU_DIR/test/data"
WORK_DIR="$( mktemp -d )"

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
    cp black_sq.png black_sq2.png || return $?
}

run() {
    echo "Making database for v$1"
    echo "==============================="

    echo "[main]" > build_dbs.cfg
    echo "library = $MKDB_LIB_PATH" >> build_dbs.cfg

    echo "Loading files..."

    load $2 || return $?

    if [[ $1 = '1.0' ]]; then
        echo "Patching source..."
        patch -p1 < "$HIGU_DIR/test/fix_1.0.patch" > /dev/null || return $?
    fi

    echo "Generating DB..."
    python "$HIGU_DIR/test/make_test_db.py" $1 > /dev/null || return $?

    echo "Saving DB..."
    cp $MKDB_LIB_PATH/hfdb.dat $DATA_DIR/hfdb_$1.dat

    echo ""
    clean
}

git clone $HIGU_DIR $WORK_DIR

cd $WORK_DIR
clean
run 1.0 d87edb56bb3f1cc81181fe1a8d78456a7246cd93
run 1.1 64786758ed87200e2c296c839b7ed4b2e104fa6d
run 2.0 9d6d91e34353b70eb6e86da069e88ff2116884a5
run 3.0 2c94321e777e130d1df40c916f30beeb65543dda
run 4.0 5408d42b1ad501c4b69ffb548d9714214123d4f4
run 5.0 6342ce3b0c2862d8353c65f92086987acf1f0593
run 6.0 cd56151a1ff3fc9f54eabda571a8ccb11b7838e6
run 7.0 master

cd
rm -rf $WORK_DIR
