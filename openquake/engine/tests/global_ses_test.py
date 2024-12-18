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
from openquake.baselib import general
from openquake.qa_tests_data import mosaic_for_ses
from openquake.commonlib.readinput import read_geometries
from openquake.calculators import base, event_based
from openquake.engine import global_ses

MOSAIC_DIR = os.path.dirname(mosaic_for_ses.__file__)


def test_EUR_MIE():
    global_ses.MODELS = ['EUR', 'MIE']
    with general.chdir(MOSAIC_DIR):
        mdf = read_geometries('mosaic.geojson', 'name', 0.).set_index('code')
        with patch.dict(event_based.__dict__, mosaic_df=mdf):
            try:
                global_ses.main(MOSAIC_DIR, 'rups.hdf5')
                dstore = base.run_calc('job.ini').datastore
                assert dstore['avg_gmf'].shape == (2, 167, 1)
            finally:
                if os.path.exists('rups.hdf5'):
                    os.remove('rups.hdf5')
