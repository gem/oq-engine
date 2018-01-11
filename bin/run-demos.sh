#!/bin/bash
set -e
# run demos with job_hazard.ini and job_risk.ini
for demo_dir in $(find "$1" -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       oq engine --run $demo_dir/job_hazard.ini
       oq engine --run $demo_dir/job_risk.ini --hc -1
   fi
done
# run the other demos
if [ ! -d "$1" ]; then
    echo "Please specify the location of the folder containing the demos. Aborting." >&2
    exit 1
fi

for ini in $(find $1 -name job.ini | sort); do
    oq engine --run $ini
done

# test generation of statistical hazard curves from previous calculation;
# -6 is LogicTreeCase3ClassicalPSHA
oq engine --run $1/hazard/LogicTreeCase3ClassicalPSHA/job.ini --hc -6

# do something with the generated data
oq extract -1 hazard/rlzs
oq engine --lhc
MPLBACKEND=Agg oq plot -1
MPLBACKEND=Agg oq plot_uhs -1
MPLBACKEND=Agg oq plot_sites -1

# fake a wrong calculation still in executing status (AreaSource)
oq db set_status 26 executing
# repeat the failed/executing calculation, which is useful for QGIS
oq engine --run $1/hazard/AreaSourceClassicalPSHA/job.ini

# display the calculations
oq db find %

# build an HTML report
oq engine --make-html-report today
