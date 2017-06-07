# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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

from openquake.hazardlib.gsim.edwards_fah_2013a import (
    EdwardsFah2013Alpine10Bars,
    EdwardsFah2013Alpine20Bars,
    EdwardsFah2013Alpine30Bars,
    EdwardsFah2013Alpine50Bars,
    EdwardsFah2013Alpine60Bars,
    EdwardsFah2013Alpine75Bars,
    EdwardsFah2013Alpine90Bars,
    EdwardsFah2013Alpine120Bars
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

"""
Testing the single station GMPEs magnitude-distance dependent
"""


class EdwardsFah2013Alpine10BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine10Bars

    def test_mean(self):
        self.check('EF13a/alp_sd10_table.csv', max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13a/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Alpine20BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine20Bars

    def test_mean(self):
        self.check('EF13a/alp_sd20_table.csv', max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13a/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Alpine30BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine30Bars

    def test_mean(self):
        self.check('EF13a/alp_sd30_table.csv', max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13a/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Alpine50BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine50Bars

    def test_mean(self):
        self.check('EF13a/alp_sd50_table.csv', max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13a/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Alpine75BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine75Bars

    def test_mean(self):
        self.check('EF13a/alp_sd75_table.csv', max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13a/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Alpine90BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine90Bars

    def test_mean(self):
        self.check('EF13a/alp_sd90_table.csv', max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13a/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Alpine120BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Alpine120Bars

    def test_mean(self):
        self.check('EF13a/alp_sd120_table.csv', max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13a/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)