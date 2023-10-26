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
try:
    import rtgmpy
except ImportError:
    rtgmpy = None
from openquake.qa_tests_data import mosaic
from openquake.commonlib import logs
from openquake.calculators import base, views
from openquake.calculators.export import export
from openquake.engine.aelo import get_params_from

MOSAIC_DIR = os.path.dirname(mosaic.__file__)
aac = numpy.testing.assert_allclose


SITES = ['far -90.071 16.60'.split(), 'close -85.071 10.606'.split()]
EXPECTED = [[0.320349, 0.667217, 0.761118], [0.76334, 1.84954, 1.28972]]
ASCE7 = ['0.78388', '0.50000', '0.50000', '1.84954', '0.95911', '1.50000',
         '1.50000', 'Very High', '1.28972', '0.95670', '0.60000', '0.60000',
         'Very High']
ASCE41 = [1.5, 1.45971, 1.45971, 0.83825, 0.83825, 1., 0.6,
          1.00814, 0.6 , 0.4, 0.57332, 0.4]


def test_CCA():
    # RTGM under and over the deterministic limit for the CCA model
    job_ini = os.path.join(MOSAIC_DIR, 'CCA/in/job_vs30.ini')
    for (site, lon, lat), expected in zip(SITES, EXPECTED):
        dic = dict(lon=lon, lat=lat, site=site, vs30='760')
        with logs.init('job', job_ini) as log:
            log.params.update(get_params_from(dic, MOSAIC_DIR))
            calc = base.calculators(log.get_oqparam(), log.calc_id)
            calc.run()
        if rtgmpy:
            [fname] = export(('rtgm', 'csv'), calc.datastore)
            df = pandas.read_csv(fname, skiprows=1)
            aac(df.RTGM, expected, atol=1E-6)

    if rtgmpy:
        # check asce7 exporter
        [fname] = export(('asce7', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        numpy.testing.assert_equal(df.value.to_numpy(), ASCE7)

        # check asce41 exporter
        [fname] = export(('asce41', 'csv'), calc.datastore)
        df = pandas.read_csv(fname, skiprows=1)
        aac(df.value, ASCE41)

        # run mag_dst_eps_sig exporter
        [fname] = export(('mag_dst_eps_sig', 'csv'), calc.datastore)
        pandas.read_csv(fname, skiprows=1)


def test_JPN():
    # test with mutex sources    
    job_ini = os.path.join(MOSAIC_DIR, 'JPN/in/job_vs30.ini')
    dic = dict(lon=139, lat=36, site='JPN-site', vs30='760')
    with logs.init('job', job_ini) as log:
        log.params.update(get_params_from(dic, MOSAIC_DIR))
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
    df = views.view('compare_disagg_rates', calc.datastore)
    assert str(df) == '''\
       imt                    src  disagg_rate  interp_rate
0      PGA  IF-NPSS-Nankai_Trough     0.020527     0.020202
1  SA(0.2)  IF-NPSS-Nankai_Trough     0.026339     0.026202
2  SA(1.0)  IF-NPSS-Nankai_Trough     0.026264     0.026018'''
