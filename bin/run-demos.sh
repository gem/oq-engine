#!/bin/bash
set -x
if [ ! -d "$1" ]; then
    echo "Please specify the location of the folder containing the demos. Aborting." >&2
    exit 1
fi

# run demos with job_hazard.ini and job_risk.ini
for demo_dir in $(find "$1" -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       oq engine --run $demo_dir/job_hazard.ini --exports npz -p pointsource_distance=0
       oq engine --run $demo_dir/job_risk.ini --hc -1
   fi
done

# run the other demos
for ini in $(find $1 -name job.ini | sort); do
    oq engine --run $ini --exports xml,hdf5 -p pointsource_distance=0 -r
done

oq export hcurves 16  # export with GMPETables

# test the --eos option
oq engine --eos -1 /tmp

# extract disaggregation data
oq extract "disagg_layer?" 14

# do something with the generated data, 9 is the AreaSource demo
oq engine --lhc
MPLBACKEND=Agg oq plot 'hcurves?kind=stats&imt=PGA' 9
MPLBACKEND=Agg oq plot 'hmaps?kind=mean&imt=PGA' 9
MPLBACKEND=Agg oq plot 'uhs?kind=stats' 9
MPLBACKEND=Agg oq plot 'disagg?kind=Mag&imt=PGA&poe_id=1&rlz=0' 14
MPLBACKEND=Agg oq plot 'task_info?kind=classical_split_filter' 9
MPLBACKEND=Agg oq plot_sites -1
MPLBACKEND=Agg oq plot memory? -1
MPLBACKEND=Agg oq plot sources? 9

# fake a failed/executing calculation to check that it is not exported
oq engine --run $1/hazard/AreaSourceClassicalPSHA/job.ini --config-file openquake/engine/openquake.cfg
oq db set_status -1 executing

# run multi_risk test
oq engine --run $1/../openquake/qa_tests_data/multi_risk/case_1/job_2.ini

echo "Testing ShakeMap calculator"
oq run $1/../openquake/qa_tests_data/scenario_risk/case_shakemap/pre-job.ini $1/../openquake/qa_tests_data/scenario_risk/case_shakemap/job.ini

# run ebrisk
oq engine --run $1/risk/EventBasedRisk/job_eb.ini -e csv
MPLBACKEND=Agg oq plot rupture_info?min_mag=6
echo "Displaying the exposed values in the ebrisk demo"
oq show exposed_values/agg_NAME_1_taxonomy
oq show exposed_values/agg_NAME_1
oq show exposed_values/agg_taxonomy
oq show exposed_values/agg

# recompute losses
oq recompute_losses -1 NAME_1
oq engine --list-outputs -1

# display the calculations
oq db find %

# build an HTML report
oq engine --make-html-report today
