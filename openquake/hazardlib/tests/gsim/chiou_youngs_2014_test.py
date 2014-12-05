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
from openquake.hazardlib.gsim.chiou_youngs_2014 import (ChiouYoungs2014,
                                                        ChiouYoungs2014PEER)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ChiouYoungs2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, available from OpenSHA, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip
    # This data is distributed under different license, see LICENSE.txt
    # in tests/gsim/data/NGA

    def test_mean_hanging_wall_normal_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_NM.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_RV.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_SS.csv',
                   max_discrep_percentage=0.05)

    def test_inter_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY14/CY14_INTER_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.05)

    def test_intra_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY14/CY14_INTRA_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.05)

    def test_total_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY14/CY14_TOTAL_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.05)


class ChiouYoungs2014PEERTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2014PEER

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, available from OpenSHA, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip
    # This data is distributed under different license, see LICENSE.txt
    # in tests/gsim/data/NGA
    def test_mean_hanging_wall_normal_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_NM.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_RV.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('NGA/CY14/CY14_MEDIAN_MS_HW_SS.csv',
                   max_discrep_percentage=0.05)
    
    def test_total_event_stddev(self):
        # Total Sigma fixes at 0.65
        self.check('NGA/CY14/CY14_TOTAL_EVENT_SIGMA_PEER.csv',
                   max_discrep_percentage=0.05)
