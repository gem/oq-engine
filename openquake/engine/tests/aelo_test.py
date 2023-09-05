# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2023, GEM Foundation
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
import numpy
import pandas
from openquake.qa_tests_data import mosaic
from openquake.commonlib import logs
from openquake.calculators import base
from openquake.calculators.export import export
from openquake.engine.aelo import get_params_from

MOSAIC_DIR = os.path.dirname(mosaic.__file__)
aae = numpy.testing.assert_allclose


def test_CCA_strong():
    # RTGM over the deterministic limit
    job_ini = os.path.join(MOSAIC_DIR, 'CCA/in/job_vs30.ini')
    dic = dict(lon='-85.071', lat='10.606', site='site_close', vs30='760')
    with logs.init('calc', job_ini) as log:
        log.params.update(get_params_from(dic, MOSAIC_DIR))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
    [fname] = export(('rtgm', 'csv'), calc.datastore)
    df = pandas.read_csv(fname, skiprows=1)
    aae(df.RTGM, [0.763373, 1.68145, 0.992067], atol=1E-6)


def test_CCA_small():
    # RTGM below the deterministic limit
    job_ini = os.path.join(MOSAIC_DIR, 'CCA/in/job_vs30.ini')
    dic = dict(lon='-90.071', lat='16.606', site='site_far', vs30='760')
    with logs.init('calc', job_ini) as log:
        log.params.update(get_params_from(dic, MOSAIC_DIR))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
    [fname] = export(('rtgm', 'csv'), calc.datastore)
    df = pandas.read_csv(fname, skiprows=1)
    aae(df.RTGM, [0.317864, 0.600875, 0.583109], atol=1E-6)
