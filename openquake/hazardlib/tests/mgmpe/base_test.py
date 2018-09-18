# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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

import unittest

from openquake.hazardlib.mgmpe.base import MGMPE
from openquake.hazardlib.imt import PGA, PGV, SA


class MGMPETestCase(unittest.TestCase):

    def test_instantiation_single_instance(self):
        """ Tests the instantiation using a single GMPE instance """
        mgmpe = MGMPE(mgmpe=['BooreEtAl2014'])
        expected = set(PGA, PGV, SA)
        self.assertTrue(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPESl == expected)

    def test_instantiation_multiple_instances(self):
        """ Tests the instantiation using a single GMPE instance """
        # mgmpe = MGMPE([BooreEtAl2014])
        pass
