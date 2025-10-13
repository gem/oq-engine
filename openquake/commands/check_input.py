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
import sys
import logging
from unittest import mock
from openquake.risklib.asset import Exposure
from openquake.commonlib import logs, readinput
from openquake.calculators import base
from openquake.hazardlib import nrml
from openquake.risklib import read_nrml  # noqa


def main(job_ini_or_zip_or_nrmls):
    """
    Check the validity of job.ini files, job.zip files and .xml files.
    NB: `oq check_input job_haz.ini job_risk.ini` is special-cased so
    that the risk files are checked before the hazard files.
    """
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    all_inis = all(f.endswith('.ini') for f in job_ini_or_zip_or_nrmls)
    if all_inis:  # the typical case is job_haz.ini + job_risk.ini
        dic = {}
        for ini in job_ini_or_zip_or_nrmls:
            for key, val in readinput.get_params(ini).items():
                if key == 'inputs' and key in dic:
                    dic[key].update(val)
                else:  # the last wins
                    dic[key] = val
        with logs.init('job', dic) as log:
            logging.info('Running oq check_input %s',
                         ' '.join(job_ini_or_zip_or_nrmls))
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            base.BaseCalculator.gzip_inputs = lambda self: None  # disable
            with mock.patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
                calc.read_inputs()
        return

    for job_ini_or_zip_or_nrml in job_ini_or_zip_or_nrmls:
        if job_ini_or_zip_or_nrml.endswith('.xml'):
            try:
                node = nrml.to_python(job_ini_or_zip_or_nrml)
                if node.tag.endswith('exposureModel'):
                    err = Exposure.check(job_ini_or_zip_or_nrml)
                    if err:
                        logging.warning(err)
                else:
                    logging.info('Checked %s', job_ini_or_zip_or_nrml)
            except Exception as exc:
                sys.exit(exc)
        else:  # .zip
            with logs.init('job', job_ini_or_zip_or_nrml) as log:
                path = os.path.abspath(job_ini_or_zip_or_nrml)
                logging.info('Running oq check_input %s', path)
                calc = base.calculators(log.get_oqparam(), log.calc_id)
                base.BaseCalculator.gzip_inputs = lambda self: None  # disable
                with mock.patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
                    calc.read_inputs()


main.job_ini_or_zip_or_nrmls = dict(help='File names to check', nargs='+')
