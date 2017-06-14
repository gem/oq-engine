#!/bin/bash
set -e
# run some risk demos
for demo_dir in $(find $TRAVIS_BUILD_DIR/demos -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       cd $demo_dir
       python -m openquake.commands engine --run job_hazard.ini
       python -m openquake.commands engine --run job_risk.ini --hc -1
   fi
done
# run the other demos
for ini in $(find $TRAVIS_BUILD_DIR/demos -name job.ini | sort); do
    oq engine --run $ini
done

# do something with the generated data
python -m openquake.commands export hcurves-rlzs 18 --exports hdf5 -d /tmp
python -m openquake.commands engine --lhc
MPLBACKEND=Agg python -m openquake.commands plot 18
MPLBACKEND=Agg python -m openquake.commands plot_uhs 18
