#!/bin/bash
set -e
# run some risk demos
for demo_dir in $(find $TRAVIS_BUILD_DIR -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       cd $demo_dir
       python -m openquake.commands engine --run job_hazard.ini
       python -m openquake.commands engine --run job_risk.ini --hc -1
       cd -
   fi
done
# run the other demos
for ini in $(find $TRAVIS_BUILD_DIR -name job.ini | sort); do
    oq engine --run $ini
done
oq export hcurves-rlzs --exports hdf5
python -m openquake.commands engine --lhc
MPLBACKEND=Agg python -m openquake.commands plot -1
MPLBACKEND=Agg python -m openquake.commands plot_uhs -1
