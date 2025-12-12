# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import os
import logging
from unittest import mock

from openquake.baselib import performance
from openquake.commonlib import logs
from openquake.calculators import base
from openquake.hazardlib import nrml
from openquake.risklib import read_nrml  # noqa
from openquake.risklib.asset import Exposure
from openquake.engine import engine

def check_input(ini, monitor=performance.Monitor()):
    with logs.init(ini) as log:
        cmode = log.params['calculation_mode']
        if 'risk' in cmode or 'damage' in cmode:
            log.params['hazard_calculation_id'] = '<fake>.ini'
        oq = log.get_oqparam()
        logging.info('Running oq check_input %s', oq.inputs['job_ini'])
        calc = base.calculators(oq, log.calc_id)
        with mock.patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
            calc.read_inputs()
        logging.info('%s is correct', oq.inputs['job_ini'])


def main(fnames):
    """
    Check the validity of job.ini files, job.zip files and .xml files.
    """
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    for fname in fnames:
        if fname.endswith('.xml'):
            node = nrml.to_python(fname)
            if node.tag.endswith('exposureModel'):
                err = Exposure.check(fname)
                if err:
                    logging.warning(err)
            else:
                logging.info('Checked %s', fname)
        elif fname.endswith(('.ini', '.zip')):
            check_input(fname)
        elif fname.endswith('.toml'):
            for workflow in engine.read_many([fname]):
                for params in workflow.inis:
                    check_input(params)

main.fnames = dict(help='File names to check', nargs='+')
