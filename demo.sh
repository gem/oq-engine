#!/bin/sh

DATA_DIR=./tests/data

echo "Generating demo data files..."
python tests/generate_demo_files.py

echo "Running demo..."
python bin/gem-risk-deterministic \
  --shakemap $DATA_DIR/shakemap.fake \
  --exposure $DATA_DIR/exposure.fake \
  --vulnerability $DATA_DIR/vulnerability.fake \
  --region $DATA_DIR/rect.region $@
