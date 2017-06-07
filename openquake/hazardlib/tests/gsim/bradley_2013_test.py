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

from openquake.hazardlib.gsim.bradley_2013 import Bradley2013, Bradley2013Volc

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Bradley2013TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Bradley2013

    # Tests developed using MATLAB code from Brendon Bradley
    # available at https://dl.dropboxusercontent.com/u/35408783/webpage/ ....
    # Software/GroundMotions/Bradley2010Gmpe.zip and described at
    # https://sites.google.com/site/brendonabradley/software/ ....
    # canterbury-earthquakes-data
    # Downloaded 26 March 2014.

    def test_mean_strike_slip(self):
        self.check('BRADLEY13/Bradley2013_MEAN_SS.csv',
                   max_discrep_percentage=0.1)

    def test_mean_reverse(self):
        self.check('BRADLEY13/Bradley2013_MEAN_RV.csv',
                   max_discrep_percentage=0.1)

    def test_mean_normal(self):
        self.check('BRADLEY13/Bradley2013_MEAN_NM.csv',
                   max_discrep_percentage=0.1)

    def test_inter_event_stddev_strike_slip(self):
        self.check('BRADLEY13/Bradley2013_INTER_EVENT_STDDEV_SS.csv',
                   max_discrep_percentage=0.1)

    def test_inter_event_stddev_reverse(self):
        self.check('BRADLEY13/Bradley2013_INTER_EVENT_STDDEV_RV.csv',
                   max_discrep_percentage=0.1)

    def test_inter_event_stddev_normal(self):
        self.check('BRADLEY13/Bradley2013_INTER_EVENT_STDDEV_NM.csv',
                   max_discrep_percentage=0.1)

    def test_intra_event_stddev_strike_slip(self):
        self.check('BRADLEY13/Bradley2013_INTRA_EVENT_STDDEV_SS.csv',
                   max_discrep_percentage=0.1)

    def test_intra_event_stddev_reverse(self):
        self.check('BRADLEY13/Bradley2013_INTRA_EVENT_STDDEV_RV.csv',
                   max_discrep_percentage=0.1)

    def test_intra_event_stddev_normal(self):
        self.check('BRADLEY13/Bradley2013_INTRA_EVENT_STDDEV_NM.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev_strike_slip(self):
        self.check('BRADLEY13/Bradley2013_TOTAL_STDDEV_SS.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev_reverse(self):
        self.check('BRADLEY13/Bradley2013_TOTAL_STDDEV_RV.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev_normal(self):
        self.check('BRADLEY13/Bradley2013_TOTAL_STDDEV_NM.csv',
                   max_discrep_percentage=0.1)


class Bradley2013VolcTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Bradley2013Volc

    # Tests developed using MATLAB code from Brendon Bradley
    # available at https://dl.dropboxusercontent.com/u/35408783/webpage/ ....
    # Software/GroundMotions/Bradley2010Gmpe.zip and described at
    # https://sites.google.com/site/brendonabradley/software/ ....
    # canterbury-earthquakes-data
    # Downloaded 26 March 2014.

    def test_mean(self):
        self.check('BRADLEY13/Bradley2013Volc_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_total_stddev(self):
        self.check('BRADLEY13/Bradley2013Volc_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1)

    def test_intra_event_stddev(self):
        self.check('BRADLEY13/Bradley2013Volc_INTRA_EVENT_STDDEV.csv',
                   max_discrep_percentage=0.1)

    def test_inter_event_stddev(self):
        self.check('BRADLEY13/Bradley2013Volc_INTER_EVENT_STDDEV.csv',
                   max_discrep_percentage=0.1)
