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
from openquake.commonlib.expo_to_hdf5 import store
from openquake.commonlib.datastore import create_job_dstore


def test_expo_to_hdf5():
    expo1_xml = os.path.join(os.path.dirname(__file__),
                             'data', 'grm_exposure.xml')
    expo2_xml = os.path.join(os.path.dirname(__file__),
                             'data', 'Exposure_Haiti.xml')
    expo3_xml = os.path.join(os.path.dirname(__file__),
                             'data', 'Exposure_Colombia.xml')
    job, dstore = create_job_dstore()
    with job, dstore:
        store([expo1_xml, expo2_xml], True, dstore)
        assets = list(dstore['assets/ASSET_ID'][:])
        assert assets == [b'HTIInd_124', b'TWNRes_0', b'TWNRes_1', b'TWNRes_2',
                          b'TWNRes_3', b'TWNRes_4', b'TWNRes_5', b'TWNRes_6',
                          b'TWNRes_7', b'TWNRes_8', b'TWNRes_9', b'HTIInd_394',
                          b'HTIInd_2564', b'HTIInd_2925', b'HTIInd_2991',
                          b'HTIInd_368', b'HTIInd_2544', b'HTIInd_2756']
        id1s = list(dstore['assets/ID_1'][:])
        assert id1s == [5, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8,
                        4, 1, 3, 3, 6, 2, 2]

        ID1s = list(dstore['tagcol/ID_1'])
        assert ID1s == [b'?', b'HTI901001.0', b'HTI901003.0', b'HTI901004.0',
                        b'HTI901005.0', b'HTI901007.0', b'HTI901009.0',
                        b'TWNA', b'TWNB']
