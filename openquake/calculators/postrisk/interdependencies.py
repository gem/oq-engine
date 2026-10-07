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
import logging

from openquake.baselib import sap
from openquake.commonlib import datastore, logs, readinput
from openquake.calculators.base import run_calc


def main(dstore, child_exposure_xml, interdependencies_csv):
    """
    Run a connectivity analysis on child_exposure_xml by taking
    into account the damages caused by a scenario_damage parent
    calculation via the interdependencies file connecting child assets
    with parent assets. For an example, see the test
    infrastructure_risk/interdependencies/job.ini
    """
    if isinstance(dstore, str):  # calc_id or path
        dstore = datastore.read(int(dstore) if dstore.isdigit() else dstore)
    oq = dstore['oqparam']
    oq.inputs['exposure'] = os.path.join(oq.base_path, child_exposure_xml)
    oq.inputs['interdependencies'] = os.path.join(oq.base_path, interdependencies_csv)
    oq.infrastructure_connectivity_analysis = True
    # Delete postrisk_func and postrisk_args from the oqparam to avoid
    # passing them to the child calculation
    oq.__dict__.pop('postrisk_func', None)
    oq.__dict__.pop('postrisk_args', None)
    # Run the child calculation in-memory, passing a job_dict derived
    # from the oqparam instead of writing a child.ini file on disk
    job_ini = readinput.to_dict(oq)
    calc = run_calc(job_ini, hazard_calculation_id=dstore.calc_id)
    outs = '\n'.join(logs.dbcmd('list_outputs', calc.datastore.calc_id, False))
    logging.info(outs)
    return calc.datastore.calc_id  # child ID


if __name__ == '__main__':
    sap.run(main)
