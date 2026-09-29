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

import logging
import numpy
import pandas

from openquake.baselib import sap
from openquake.commonlib import datastore
from openquake.calculators.base import expose_outputs

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
EVENT_COLS = {'ccl': 'CCL', 'pcl': 'PCL', 'wcl': 'WCL', 'efl': 'EL'}
AVG_LOSS = 'infra-avg_loss'
NODE_EL = 'infra-node_el'  # efficiency loss of each node


def _summary(parent):
    """
    Dataframe with one row per connectivity metric, comparing the average
    loss stored by the calculation with the per-event distribution, or None
    if there is no connectivity analysis. Lookups go through the parent of
    the datastore, if any (see DataStore.__contains__), so this works on a
    postprocessing calculation too, reading from its own parent.
    """
    avg = parent.read_df(AVG_LOSS) if AVG_LOSS in parent else None
    rows = []
    for metric, col in EVENT_COLS.items():
        key = 'infra-event_' + metric
        if key not in parent:
            continue
        df = parent.read_df(key)
        values = df[col].to_numpy()
        imax = int(numpy.argmax(values))
        rows.append(dict(
            metric=metric,
            avg_loss=(avg[metric].iloc[0] if avg is not None and
                      metric in avg else numpy.nan),
            num_events=len(values), mean=values.mean(), max=values[imax],
            worst=int(df.event_id.to_numpy()[imax])))
    return pandas.DataFrame(rows) if rows else None


def main(dstore, name='connectivity_summary'):
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
    if isinstance(dstore, (str, int)):  # calc_id or path
        dstore = datastore.read(
            int(dstore) if str(dstore).isdigit() else dstore)
    summary = _summary(dstore)
    if summary is None:
        logging.warning('No connectivity outputs in the calculation %d. '
                        'Was it run with '
                        'infrastructure_connectivity_analysis = true?',
                        dstore.calc_id)
        return
    oqp = dstore['oqparam']
    ini = dict(description='%s [%s]' % (oqp.description, name),
               calculation_mode='post_risk',
               hazard_calculation_id=dstore.calc_id)
    log, child = datastore.create_job_dstore(ini=ini, parent=dstore)
    with child, log:
        child.create_df(name, summary, display_name='Connectivity Summary')
        logging.info('Connectivity summary of the calculation %d\n%s',
                     dstore.calc_id, summary.to_string(index=False))
        expose_outputs(child)
    return child


if __name__ == '__main__':
    sap.run(main)
