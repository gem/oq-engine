#!/bin/bash
set -e
python -m openquake.commands engine --run $HOME/demos/hazard/AreaSourceClassicalPSHA/job.ini
MPLBACKEND=Template python -m openquake.commands plot_uhs -1
# MPLBACKEND=Template python -m openquake.commands plot -1
