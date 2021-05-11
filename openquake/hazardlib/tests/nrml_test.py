# The Hazard Library
# Copyright (C) 2012-2021 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import unittest
import numpy as np
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.sourceconverter import (
    FaultSectionConverter, SourceConverter)
from openquake.hazardlib.geo import Point
from openquake.hazardlib.nrml import SourceModel

datadir = os.path.join(os.path.dirname(__file__), 'data', 'sections')


class KiteFaultSectionsTestCase(unittest.TestCase):
    """ Tests reading an .xml file wiith sections """

    def setUp(self):
        fname = 'sections_kite.xml'
        self.fname = os.path.join(datadir, fname)

    def test_load_kite(self):
        conv = FaultSectionConverter()
        sec = to_python(self.fname, conv)
        expected = [Point(11, 45, 0), Point(11, 45.5, 10)]
        # Check geometry info
        self.assertEqual(expected[0], sec[1].surface.profiles[0].points[0])
        self.assertEqual(expected[1], sec[1].surface.profiles[0].points[1])
        self.assertEqual(sec[1].sec_id, 's2')


class MultiFaultSourceModelTestCase(unittest.TestCase):
    """ Tests reading a multi fault model """

    def setUp(self):
        fname = 'sources.xml'
        self.fname = os.path.join(datadir, fname)

    def test_load_mfs(self):
        conv = SourceConverter()
        ssm = to_python(self.fname, conv)
        self.assertIsInstance(ssm, SourceModel)

        rups = []
        for rup in ssm[0][0].iter_ruptures():
            rups.append(rup)

        # Check data for the second rupture
        msg = 'Rake for rupture #0 is wrong'
        self.assertEqual(rups[0].rake, 90.0, msg)
        # Check data for the second rupture
        msg = 'Rake for rupture #1 is wrong'
        self.assertEqual(rups[1].rake, -90.0, msg)
        # Check mfd
        expected = np.array([0.9, 0.1])
        np.testing.assert_almost_equal(rups[1].probs_occur, expected)
