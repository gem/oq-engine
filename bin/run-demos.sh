#!/bin/bash
set -e
# run demos with job_hazard.ini and job_risk.ini
for demo_dir in $(find "$1" -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       python -m openquake.commands engine --run $demo_dir/job_hazard.ini
       python -m openquake.commands engine --run $demo_dir/job_risk.ini --hc -1
   fi
done
# run the other demos
if [ ! -d "$1" ]; then
    echo "Please specify the location of the folder containing the demos. Aborting." >&2
    exit 1
fi

for ini in $(find $1 -name job.ini | sort); do
    python -m openquake.commands engine --run $ini
done

# do something with the generated data; -2 is LogicTreeCase3ClassicalPSHA
python -m openquake.commands export hcurves-rlzs -2 --exports hdf5 -d /tmp
python -m openquake.commands engine --lhc
MPLBACKEND=Agg python -m openquake.commands plot -2
MPLBACKEND=Agg python -m openquake.commands plot_uhs -2

# fake a wrong calculation still in executing status
python -m openquake.commands db set_status 1 executing
# repeat the failed/executing calculation, which is useful for QGIS
python -m openquake.commands engine --run $1/hazard/AreaSourceClassicalPSHA/job.ini
