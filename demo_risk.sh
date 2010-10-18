#!/bin/sh

DATA_DIR=./tests/data

# echo "Generating demo data files..."
# python tests/generate_demo_files.py

echo "Running demo..."
python bin/opengem \
  --exposure $DATA_DIR/FakeExposurePortfolio.xml \
  --vulnerability $DATA_DIR/VulnerabilityModelFile-jobber-test.xml \
  --hazard_curves $DATA_DIR/HazardOneSite.xml \
  --filter_region $DATA_DIR/rect.region $@
 

#--shakemap $DATA_DIR/shakemap.fake \
