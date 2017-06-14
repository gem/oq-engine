#!/bin/bash
set -e
# run some fast risk demos
for demo_dir in $(find $1 -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       python -m openquake.commands engine --run $demo_dir/job_hazard.ini
       python -m openquake.commands engine --run $demo_dir/job_risk.ini --hc -1
   fi
done
# run the other demos (slow)
#for ini in $(find $1 -name job.ini | sort); do
#    python -m openquake.commands engine --run $ini
#done

# do something with the generated data
python -m openquake.commands export hcurves-rlzs 18 --exports hdf5 -d /tmp
python -m openquake.commands engine --lhc
MPLBACKEND=Agg python -m openquake.commands plot 18
MPLBACKEND=Agg python -m openquake.commands plot_uhs 18
