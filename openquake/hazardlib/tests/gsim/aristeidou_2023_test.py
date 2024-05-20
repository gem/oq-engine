# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

"""
Implements the comprehensive test suite for the Aristeidou, Tarbali, and
O'Reilly GMM (2023)
Test data generated using an independent code written by the original authors.
The published article and supplemental material can be found in:
https://journals.sagepub.com/doi/suppl/10.1193/100614eqs151m
"""

from openquake.hazardlib.gsim.aristeidou_2023 import (
    AristeidouEtAl2023,
    AristeidouEtAl2023RotD100)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AristeidouEtAl2023TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AristeidouEtAl2023
    MEAN_FILE = 'ATO23/ATO23_ROTD50_MEAN.csv'
    STD_INTRA_FILE = 'ATO23/ATO23_ROTD50_STD_INTRA.csv'
    STD_INTER_FILE = 'ATO23/ATO23_ROTD50_STD_INTER.csv'
    STD_TOTAL_FILE = 'ATO23/ATO23_ROTD50_STD_TOTAL.csv'

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.STD_INTRA_FILE,
                   self.STD_INTER_FILE,
                   self.STD_TOTAL_FILE,
                   max_discrep_percentage=0.1)


class AristeidouEtAl2023RotD100TestCase(AristeidouEtAl2023TestCase):
    GSIM_CLASS = AristeidouEtAl2023RotD100
    MEAN_FILE = 'ATO23/ATO23_ROTD100_MEAN.csv'
    STD_INTRA_FILE = 'ATO23/ATO23_ROTD100_STD_INTRA.csv'
    STD_INTER_FILE = 'ATO23/ATO23_ROTD100_STD_INTER.csv'
    STD_TOTAL_FILE = 'ATO23/ATO23_ROTD100_STD_TOTAL.csv'
