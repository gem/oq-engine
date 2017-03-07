#!/bin/bash
python -m openquake.commands engine --run oq-engine/demos/hazard/AreaSourceClassicalPSHA/job.ini
MPLBACKEND=Template python -m openquake.commands plot_uhs -1
# MPLBACKEND=Template python -m openquake.commands plot -1
