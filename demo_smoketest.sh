#!/bin/sh

DATA_DIR=./tests/data/smoketest

echo "Running smoketest..."
python bin/opengem --config_file $DATA_DIR/config.gem $@