# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import tempfile
import unittest
import numpy
from openquake.commonlib.datastore import DataStore
from openquake.hazardlib.rmap_maker import read_unc_ts_sets


class ReadUncTsSetsTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dstore = DataStore(
            os.path.join(self.tmp.name, 'rates.hdf5'), mode='a')
        self.addCleanup(self.dstore.close)

    def test_missing(self):
        # Event-based and imported curves may have no rate-set metadata.
        self.assertIsNone(read_unc_ts_sets(self.dstore))

    def test_closed(self):
        # Preserve stored gid numbering, including non-sorted input.
        sets = [numpy.array(ts, numpy.uint32) for ts in [(2,), (0, 1)]]
        self.dstore.hdf5.save_vlen('unc_ts_sets', sets)
        self.dstore.close()
        self.assertEqual(read_unc_ts_sets(self.dstore), [(2,), (0, 1)])
        self.assertEqual(self.dstore.hdf5, ())

    def test_parent(self):
        # Child calculations inherit attribution from the parent.
        self.dstore.hdf5.save_vlen(
            'unc_ts_sets', [numpy.array([0, 1], numpy.uint32)])
        child = DataStore(os.path.join(self.tmp.name, 'child.hdf5'))
        self.addCleanup(child.close)
        child.parent = self.dstore
        self.assertEqual(read_unc_ts_sets(child), [(0, 1)])
