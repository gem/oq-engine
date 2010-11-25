#!/bin/sh

DATA_DIR=./tests/data
SRC_DIR=$DATA_DIR/usgs-nshm
TARGET_DIR=$DATA_DIR/output

# Download the git repo with NSHMP data if necessary
if [ -d $SRC_DIR ]; then
    echo "Already got the data..."
    pushd $SRC_DIR
    git pull
    popd
else
    git clone https://github.com/gem/usgs-nshm.git $SRC_DIR
fi

mkdir -p $TARGET_DIR

echo "Running converter demo..."
python bin/gemconvert \
    --debug=debug \
    --convert_input=$SRC_DIR \
    --convert_type="openquake.parser.nshmp" \
    --convert_output=$TARGET_DIR \
    --target_type="openquake.parser.nrml" \
    $@
 
