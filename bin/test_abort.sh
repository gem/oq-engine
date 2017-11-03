#!/bin/bash
# test the abort functionality
cd $1  # demos directory
python -m openquake.commands engine --run hazard/AreaSourceClassicalPSHA/job.ini &
python -m openquake.commands engine --run hazard/EventBasedPSHA/job.ini &
python -m openquake.commands engine --run hazard/Disaggregation/job.ini &
python -m openquake.commands engine --run hazard/ScenarioCase1/job.ini &
sleep 2  # give time to start
python -m openquake.commands abort -2
