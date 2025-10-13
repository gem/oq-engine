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
from openquake.commonlib.expo_to_hdf5 import store
from openquake.commonlib.expo_count import count_assets
from openquake.commonlib.datastore import create_job_dstore

ae = numpy.testing.assert_equal
EXPECTED_ASSETS = sorted([
    b'COLRes_89558',
    b'HTIInd_124',
    b'TWNRes_0',
    b'TWNRes_1',
    b'TWNRes_2',
    b'TWNRes_3',
    b'TWNRes_4',
    b'TWNRes_5',
    b'TWNRes_6',
    b'TWNRes_7',
    b'TWNRes_8',
    b'TWNRes_9',
    b'TURRes_971000',
    b'COLRes_325763',
    b'HTIInd_394',
    b'HTIInd_2564',
    b'HTIInd_2925',
    b'HTIInd_2991',
    b'TURRes_1867459',
    b'COLRes_276440',
    b'COLRes_256836',
    b'COLRes_279883',
    b'HTIInd_368',
    b'HTIInd_2544',
    b'HTIInd_2756',
    b'TURRes_1425004',
    b'TURRes_2265963',
    b'COLRes_216273',
    b'TURRes_2050206',
    b'COLRes_13074'])

EXPECTED_ID1s = sorted([
    b'?',
    b'COL903931.0',
    b'COL903934.0',
    b'COL903951.0',
    b'COL903957.0',
    b'COL903960.0',
    b'HTI901001.0',
    b'HTI901003.0',
    b'HTI901004.0',
    b'HTI901005.0',
    b'HTI901007.0',
    b'HTI901009.0',
    b'TUR901304.0',
    b'TUR901314.0',
    b'TUR901328.0',
    b'TUR901337.0',
    b'TUR901347.0',
    b'TWNA',
    b'TWNB'])

EXPECTED_NAME2s = [
    '?', 'ACIGÖL', 'ANTAKYA', 'Arauquita', 'Bogota', 'Cali',
    'Croix-des-Bouquets', 'Iles', 'KOCASİNAN', 'Port-de-Paix', 'Saint-Marc',
    'Sincelejo', 'Taitung County', 'Taitung County', 'TÜRKELİ',
    'le Cap-Haïtien', 'le Trou-du-Nord', 'les Cayes', 'ÇAYIRALAN']


def test_expo_to_hdf5():
    grm_dir = os.path.join(os.path.dirname(__file__), 'data')
    expo1_xml = os.path.join(grm_dir, 'Exposure_Taiwan.xml')
    expo2_xml = os.path.join(grm_dir, 'Exposure_Haiti.xml')
    expo3_xml = os.path.join(grm_dir, 'Exposure_Colombia.xml')
    expo4_xml = os.path.join(grm_dir, 'Exposure_Turkiye.xml')
    job, dstore = create_job_dstore()
    with job, dstore:
        store([expo1_xml, expo2_xml, expo3_xml, expo4_xml], grm_dir,
              True, dstore)
        assets = sorted(dstore['assets/ASSET_ID'][:])
        ae(assets, EXPECTED_ASSETS)
        assert len(dstore['assets/ID_1']) == 30

        ID1s = sorted(dstore['tagcol/ID_1'])
        ae(ID1s, EXPECTED_ID1s)

        NAME2s = sorted(dstore['NAME_2'][:])
        assert [x.decode('utf8') for x in NAME2s] == EXPECTED_NAME2s

        slices = dstore['assets/slice_by_hex6'][:]
        assert len(slices) == 16

    # test count_assets
    ca = count_assets(dstore.filename)
    assert ca == [('832d05', 1), ('832d10', 1), ('832da1', 1), ('834c8a', 1),
                  ('836606', 1), ('836672', 1), ('8366d1', 1), ('8366e4', 1),
                  ('8366f1', 1), ('836724', 1), ('836725', 1), ('836726', 1),
                  ('832d11', 2), ('8366e0', 2), ('834c88', 4), ('834b84', 10)]
