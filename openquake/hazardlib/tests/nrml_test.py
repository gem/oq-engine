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
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.geo import Point
from openquake.hazardlib.nrml import SourceModel

datadir = os.path.join(os.path.dirname(__file__), 'data', 'sections')


class MultiFaultSourceModelTestCase(unittest.TestCase):
    """ Tests reading a multi fault model """

    def test_load_mfs(self):
        sec_xml = os.path.join(datadir, 'sections_kite.xml')
        src_xml = os.path.join(datadir, 'sources.xml')
        conv = SourceConverter()
        sec = to_python(sec_xml, conv).sections
        expected = [Point(11, 45, 0), Point(11, 45.5, 10)]
        # Check geometry info
        self.assertEqual(expected[0], sec[1].surface.profiles[0].points[0])
        self.assertEqual(expected[1], sec[1].surface.profiles[0].points[1])
        self.assertEqual(sec[1].sec_id, 's2')
        ssm = to_python(src_xml, conv)
        self.assertIsInstance(ssm, SourceModel)

        rups = []
        ssm[0][0].sections = sec  # fix sections
        ssm[0][0].create_inverted_index()
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
