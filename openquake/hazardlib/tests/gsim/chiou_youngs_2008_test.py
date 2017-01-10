# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.chiou_youngs_2008 import ChiouYoungs2008

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ChiouYoungs2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2008

    # First five tests use data ported from Kenneth Campbell
    # tables for verifying NGA models, available from OpenSHA, see
    # http://opensha.usc.edu/docs/opensha/NGA/Campbell_NGA_tests.zip
    # This data is distributed under different license, see LICENSE.txt
    # in tests/gsim/data/NGA

    def test_total_stddev_hanging_wall_strike_slip_measured(self):
        self.check('NGA/CY08/CY08_SIGMEAS_MS_HW_SS.csv',
                    max_discrep_percentage=0.015)

    def test_total_stddev_hanging_wall_strike_slip_inferred(self):
        self.check('NGA/CY08/CY08_SIGINFER_MS_HW_SS.csv',
                   max_discrep_percentage=0.015)

    def test_mean_hanging_wall_normal_slip(self):
        self.check('NGA/CY08/CY08_MEDIAN_MS_HW_NM.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_reversed_slip(self):
        self.check('NGA/CY08/CY08_MEDIAN_MS_HW_RV.csv',
                   max_discrep_percentage=0.05)

    def test_mean_hanging_wall_strike_slip(self):
        self.check('NGA/CY08/CY08_MEDIAN_MS_HW_SS.csv',
                   max_discrep_percentage=0.05)

    def test_inter_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY08/CY08_INTER_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.002)

    def test_intra_event_stddev(self):
        # data generated from opensha
        self.check('NGA/CY08/CY08_INTRA_EVENT_SIGMA.csv',
                   max_discrep_percentage=0.001)
