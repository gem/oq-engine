#!/bin/bash
# test the abort functionality
if [ ! -d "$1" ]; then
    echo "Please specify the location of the folder containing the demos" >&2
    exit 1
fi
cd $1  # demos directory
python3 -m openquake.commands engine --run hazard/AreaSourceClassicalPSHA/job.ini &
sleep .25
python3 -m openquake.commands engine --run hazard/EventBasedPSHA/job.ini &
sleep .25
python3 -m openquake.commands engine --run hazard/Disaggregation/job.ini &
sleep .25
python3 -m openquake.commands engine --run hazard/ScenarioCase1/job.ini &
sleep 2  # give time to start
python3 -m openquake.commands abort -2  # the disaggregation
