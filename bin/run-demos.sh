#!/bin/bash
set -e
if [ ! -d "$1" ]; then
    echo "Please specify the location of the folder containing the demos. Aborting." >&2
    exit 1
fi

# run demos with job_hazard.ini and job_risk.ini
for demo_dir in $(find "$1" -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       oq engine --run $demo_dir/job_hazard.ini --exports npz
       oq engine --run $demo_dir/job_risk.ini --hc -1
   fi
done

# run the other demos
for ini in $(find $1 -name job.ini | sort); do
    oq engine --run $ini --exports xml,hdf5
done

# test the --eos option
oq engine --eos -1 /tmp

# test generation of statistical hazard curves from previous calculation
oq engine --run $1/hazard/LogicTreeCase3ClassicalPSHA/job.ini --reuse-hazard

# do something with the generated data
oq engine --lhc
MPLBACKEND=Agg oq plot 'hcurves?kind=stats&imt=PGA' -1
MPLBACKEND=Agg oq plot 'hmaps?kind=mean&imt=PGA' -1
MPLBACKEND=Agg oq plot 'uhs?kind=stats' -1
MPLBACKEND=Agg oq plot_sites -1
MPLBACKEND=Agg oq plot_memory

# fake a failed/executing calculation to check that it is not exported
oq engine --run $1/hazard/AreaSourceClassicalPSHA/job.ini --config-file openquake/engine/openquake.cfg
oq db set_status -1 executing

# display the calculations
oq db find %

# build an HTML report
oq engine --make-html-report today
