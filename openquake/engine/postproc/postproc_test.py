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
import unittest
import pytest
import numpy
import pandas
from openquake.baselib import general, hdf5
from openquake.hazardlib.contexts import ContextMaker
from openquake.commonlib import logs, datastore
from openquake.engine.postproc.rupture_histogram import compute_histogram
from openquake.engine.postproc import compute_mrd, disagg_by_rel_sources
from openquake.calculators import base
from openquake.qa_tests_data import mosaic

DATA = os.path.join(os.path.dirname(__file__), 'data')
MOSAIC = os.path.dirname(mosaic.__file__)
rupdata = '''\
sids,mag,rrup
0,5.5,100.
0,6.6,110.
0,7.3,120.
0,7.3,130.
0,7.3,140.
0,7.3,150.
0,7.5,160.
0,7.8,120.
0,7.8,120.
0,7.8,120.
'''


def test_compute_histogram():
    ctx = hdf5.read_csv(
        general.gettemp(rupdata),
        {'sids': numpy.uint32, 'mag': float, 'rrup': float}
    ).array.view(numpy.recarray)
    params = {'mag': numpy.unique(ctx.mag), 'imtls': {'PGA': [.1, .2]}}
    cmaker = ContextMaker('*', [], params)
    
    magbins = numpy.linspace(2, 10.2, 20)
    dstbins = numpy.linspace(0, 1000., 50)
    dic = compute_histogram(ctx, cmaker, magbins, dstbins)
    assert dic == {(0, 9, 5): 1,
                   (0, 11, 6): 1,
                   (0, 13, 6): 1,
                   (0, 13, 7): 2,
                   (0, 13, 8): 2,
                   (0, 14, 6): 3}


def test_compute_mrd():
    if os.environ.get('JENKINS_URL'):
        raise unittest.SkipTest('Hanging on Jenkins')
    parent = os.path.join(DATA, 'calc_001.hdf5')
    config = os.path.join(DATA, 'mrd.toml')
    mrd = compute_mrd.main(parent, config)
    assert abs(mrd.mean() - 1.04e-05) < 1e-6


@pytest.mark.parametrize('model', ['CCA', 'EUR'])
def test_mosaic(model):
    fname = os.path.join(MOSAIC, 'test_sites.csv')
    df = pandas.read_csv(fname).set_index('model')
    sitedict = df.loc[model].to_dict()
    job_ini = os.path.join(MOSAIC, model, 'in', 'job_vs30.ini')
    with logs.init("job", job_ini) as log:
        log.params['disagg_by_src'] = 'true'
        log.params['ps_grid_spacing'] = '0.'
        log.params['pointsource_distance'] = '40.'
        log.params['sites'] = '%(lon)s %(lat)s' % sitedict
        log.params['cachedir'] = datastore.get_datadir()
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run()
        calc.datastore.close()
    disagg_by_rel_sources.main(calc.datastore.calc_id)
