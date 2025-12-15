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
ae = numpy.testing.assert_equal

last_job = None

def path(job_ini):
    return os.path.join(MOSAIC_DIR, job_ini)


def count_rups(dstore, model):
    arr = dstore['ruptures'][:]
    return (arr['model'] == model.encode('ascii')).sum()


def check(dstore, calcs):
    with hdf5.File(RUP_HDF5) as ds, \
         read(calcs[0]) as ds_EUR, \
         read(calcs[1]) as ds_MIE:

        # count the ruptures outside the models
        mie_unknown = count_rups(ds_MIE, '???')
        assert mie_unknown == 0
        eur_unknown = count_rups(ds_EUR, '???')
        assert eur_unknown == 0
        
        nrup_EUR = count_rups(ds_EUR, 'EUR')
        nrup_MIE = count_rups(ds_MIE, 'MIE')
        rups = ds['ruptures'][:]
        nrup = len(rups)
        assert nrup == nrup_EUR + nrup_MIE  # no double counting
        assert dstore['avg_gmf'].shape == (2, 4328, 1)


def setup_module():
    worflow_id = global_ses.main(
        MOSAIC_DIR, 'rups.hdf5', 'EUR,MIE',
        number_of_logic_tree_samples=200)
    wdf = read(worflow_id).read_df('workflow')
    dstore = base.run_calc(
        path('job.ini'), hazard_calculation_id='rups.hdf5'
    ).datastore
    check(dstore, list(wdf.calc_id))
    ae(dstore['source_info/EUR']['source_id'],
       [b'IF-CFS-0', b'IF-CFS-1', b'IF-CFS-2', b'IF-CFS-3'])
    ae(dstore['source_info/MIE']['source_id'],
       [b'DS-AS-AZEAS300', b'DS-AS-AZEAS301', b'DS-AS-IRNAS300',
        b'DS-AS-IRNAS301', b'DS-AS-IRNAS302', b'DS-AS-PAKAS300',
        b'IF-CFS-3', b'IF-CFS-CYSD05', b'IF-CFS-GRID03', b'IF-CFS-TRID04',
        b'SL-AS-GRIDAS08', b'SL-AS-PAKAS202', b'SL-AS-TRIDAS09',
        b'SSC-mps-0', b'SSC-mps-1', b'SSC-mps-2', b'SSC-mps-3',
        b'SSC-mps-4'])


def test_sites():  # 6 sites
    global last_job
    dstore = base.run_calc(
        path('job_sites.ini'), hazard_calculation_id='rups.hdf5'
    ).datastore
    last_job = dstore.calc_id
    gmvs = dstore['avg_gmf'][0, :, 0]
    assert (gmvs > 0).sum() == 6


def test_site_model():  # 6 sites
    global last_job
    dstore = base.run_calc(
        path('job_sm.ini'), hazard_calculation_id='rups.hdf5'
    ).datastore
    last_job = dstore.calc_id
    gmvs = dstore['avg_gmf'][0, :, 0]
    assert (gmvs > 0).sum() == 6


def teardown_module():
    if os.path.exists(RUP_HDF5):
        os.remove(RUP_HDF5)
    if last_job:
        # make sure `read` works after rups.hdf5 has been removed
        read(last_job)
