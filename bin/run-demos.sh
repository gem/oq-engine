#!/bin/bash
set -e
if [ ! -d "$1" ]; then
    echo "Please specify the location of the folder containing the demos. Aborting." >&2
    exit 1
fi

oq info venv
oq info cfg

# create .tmp.ini files with oqparam.to_ini()
python -c"import os
from openquake.calculators.checkers import check_ini
for cwd, dirs, files in os.walk('$1'):
     for f in files:
         if f.endswith('.ini') and not f.endswith('.tmp.ini'):
             path = os.path.join(cwd, f)
             check_ini(path, hc='risk' in f)"
# run the demos with the generated file
for demo_dir in $(find "$1" -type d | sort); do
   if [ -f $demo_dir/job_hazard.ini ]; then
       oq engine --run $demo_dir/job_hazard.tmp.ini --exports csv,hdf5
       oq engine --run $demo_dir/job_risk.tmp.ini --hc -1
   fi
done

# run the other demos
for ini in $(find $1 -name job.tmp.ini | sort); do
    oq engine --run $ini --exports csv,hdf5
done

oq export hcurves 16  # export with GMPETables

# test the --eos option
oq engine --eos -1 /tmp

# extract disaggregation data
oq extract "disagg_layer?" 14

# do something with the generated data, 9 is the AreaSource demo
oq engine --lhc
oq plot examples
MPLBACKEND=Agg oq plot 'hcurves?kind=stats&imt=PGA' 9
MPLBACKEND=Agg oq plot 'hmaps?kind=mean&imt=PGA' 9
MPLBACKEND=Agg oq plot 'uhs?kind=stats' 9
MPLBACKEND=Agg oq plot 'disagg?kind=Mag&imt=PGA&poe_id=1&spec=rlzs' 14
MPLBACKEND=Agg oq plot 'task_info?kind=classical' 9
MPLBACKEND=Agg oq plot_assets -1
MPLBACKEND=Agg oq plot memory? -1

# run multi_risk test
oq engine --run $1/../openquake/qa_tests_data/multi_risk/case_1/job_2.ini

echo "Testing ShakeMap calculator"
oq run $1/../openquake/qa_tests_data/scenario_risk/case_shakemap/pre-job.ini $1/../openquake/qa_tests_data/scenario_risk/case_shakemap/job.ini

# run ebrisk
oq engine --run $1/risk/EventBasedRisk/job_eb.ini -e csv,hdf5
# oq plot avg_gmf?imt=PGA  # hangs on the macOS Action
oq show aggrisk
MPLBACKEND=Agg oq plot rupture_info?min_mag=6
echo "Displaying the exposed values in the ebrisk demo"
oq show agg_values

# recompute losses
oq reaggregate -1 NAME_1
oq engine --list-outputs -1

# sensitivity to the strike angle
oq shell $1/risk/ScenarioRisk/sensitivity.py

echo "Testing csm2rup"
OQ_DISTRIBUTE=processpool utils/csm2rup $1/risk/ClassicalRisk/job_hazard.ini

echo "Testing oq info usgs_rupture"
oq info usgs_rupture:us70006sj8

# display the calculations
oq db find %

# build an HTML report
oq engine --make-html-report today
