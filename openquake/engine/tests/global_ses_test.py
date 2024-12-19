# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024, GEM Foundation
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
from unittest.mock import patch
from openquake.baselib import general, hdf5
from openquake.qa_tests_data import mosaic_for_ses
from openquake.commonlib.datastore import read
from openquake.commonlib.readinput import read_geometries
from openquake.calculators import base, event_based
from openquake.engine import global_ses

MOSAIC_DIR = os.path.dirname(mosaic_for_ses.__file__)
RUP_HDF5 = 'rups.hdf5'


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


def test_EUR_MIE():
    global_ses.MODELS = ['EUR', 'MIE']
    with general.chdir(MOSAIC_DIR):
        mdf = read_geometries('mosaic.geojson', 'name', 0.).set_index('code')
        with patch.dict(event_based.__dict__, mosaic_df=mdf):
            try:
                fnames = global_ses.main(MOSAIC_DIR, RUP_HDF5)
                dstore = base.run_calc('job.ini').datastore
                check(dstore, fnames)

                # only 1 site is associated to the site params
                dstore = base.run_calc('job_sites.ini').datastore
                assert dstore['avg_gmf'].shape == (2, 1, 1)
            finally:
                if os.path.exists(RUP_HDF5):
                    os.remove(RUP_HDF5)
