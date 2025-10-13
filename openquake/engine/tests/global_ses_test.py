# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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
from openquake.baselib import hdf5
from openquake.qa_tests_data import mosaic_for_ses
from openquake.commonlib.datastore import read
from openquake.calculators import base
from openquake.engine import global_ses

MOSAIC_DIR = os.path.dirname(mosaic_for_ses.__file__)
RUP_HDF5 = os.path.join(MOSAIC_DIR, 'rups.hdf5')
aac = numpy.testing.assert_allclose
def path(job_ini):
    return os.path.join(MOSAIC_DIR, job_ini)


def check(dstore, fnames):
    with hdf5.File(RUP_HDF5) as ds, \
         read(fnames[0]) as ds_EUR, \
         read(fnames[1]) as ds_MIE:
        nrup_EUR = len(ds_EUR['ruptures'])
        nrup_MIE = len(ds_MIE['ruptures'])
        rups = ds['ruptures'][:]
        nrup = len(rups)
        assert nrup == nrup_EUR + nrup_MIE
        assert dstore['avg_gmf'].shape == (2, 167, 1)


def setup_module():
    global_ses.MODELS = ['EUR', 'MIE']
    fnames = global_ses.main(MOSAIC_DIR, RUP_HDF5)
    dstore = base.run_calc(path('job.ini')).datastore
    check(dstore, fnames)


def test_sites():  # 6 sites
    dstore = base.run_calc(path('job_sites.ini')).datastore
    gmvs = dstore['avg_gmf'][0, :, 0]
    aac(gmvs, [0.0201735, 0.0202367, 0.0203708,
               0.0202335, 0.0202477, 0.0202308], atol=1E-6)


def test_site_model():  # 5 sites
    dstore = base.run_calc(path('job_sm.ini')).datastore
    gmvs = dstore['avg_gmf'][0, :, 0]
    aac(gmvs, [0.020281, 0.020274, 0.020219,
               0.020302, 0.020263], atol=1E-6)


def teardown_module():
    if os.path.exists(RUP_HDF5):
        os.remove(RUP_HDF5)
