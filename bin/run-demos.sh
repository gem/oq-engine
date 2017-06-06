#!/bin/bash
set -e
python -m openquake.commands engine --run $TRAVIS_BUILD_DIR/demos/hazard/AreaSourceClassicalPSHA/job.ini
oq export hcurves-rlzs --exports hdf5
python -m openquake.commands engine --lhc
MPLBACKEND=Agg python -m openquake.commands plot -1
MPLBACKEND=Agg python -m openquake.commands plot_uhs -1
