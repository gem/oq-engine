# The Hazard Library
# Copyright (C) 2014 GEM Foundation
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
from openquake.hazardlib.gsim.chiou_youngs_2014_near_fault import ChiouYoungs2014NearFaultEffect


from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ChiouYoungs2014NearFaultTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014NearFaultEffect

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, available from OpenSHA, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip
    # This data is distributed under different license, see LICENSE.txt
    # in tests/gsim/data/NGA

    def test_mean_hanging_wall_normal_slip(self):
        self.check('NGA/CY14_NF/CY14_MEDIAN_MS_HW_RV_CDPP.csv',
                   max_discrep_percentage=0.05)
