# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os

from openquake.baselib import sap
from openquake.commonlib import datastore
from openquake.calculators.base import run_calc

# The infrastructure connectivity analysis is performed by the damage
# calculators (see `connectivity` in openquake/risklib) when the job.ini
# contains `infrastructure_connectivity_analysis = true`. It stores the
# average losses in `infra-avg_loss`, with one column per metric and a single
# row, and the per-event losses in `infra-event_<metric>`, with the loss in
# the column given here.
#
# To get a calculation to summarize, run the test case below and then pass
# its ID (the job printed by the engine) to this module:
#
#   oq engine --run \
#       openquake/qa_tests_data/infrastructure_risk/demand_supply/job.ini
#   python -m openquake.calculators.postrisk.connectivity <calc_id>
#
# The same case is run by the test
# openquake/calculators/tests/infrastructure_risk_test.py
# (test_demand_supply), which checks the `infra-*` outputs.


def main(dstore, road_exposure_xml, interdependencies_csv):
    """
    Summarize the infrastructure connectivity analysis of a finished damage
    calculation, i.e. one run with
    `infrastructure_connectivity_analysis = true`. `dstore` is the
    calculation holding that analysis: a calculation ID (as an int, or as
    the string of digits the command line produces), the name of an HDF5
    file, or an open datastore. The summary, a dataframe with one row per
    connectivity metric, is stored in a new calculation with its own
    datastore, whose `parent` attribute points to the given one, which is
    therefore left untouched.
    """
    if isinstance(dstore, str):  # calc_id or path
        dstore = datastore.read(int(dstore) if dstore.isdigit() else dstore)
    oq = dstore['oqparam']
    oq.inputs['exposure'] = os.path.join(oq.base_path, road_exposure_xml)
    oq.inputs['interdependencies'] = os.path.join(oq.base_path, interdependencies_csv)
    ini = oq.to_ini()
    child_ini = os.path.join(oq.base_path, 'child.ini')
    with open(child_ini, 'w') as f:
        f.write(ini)
    run_calc(child_ini)


if __name__ == '__main__':
    sap.run(main)
