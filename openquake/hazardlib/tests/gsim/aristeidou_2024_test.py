# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
Implements the comprehensive test suite for the Aristeidou,
Shahnazaryan, and O'Reilly GMM (2024)
Test data generated using an independent code written by the original authors.
The published article and supplemental material can be found in:
https://doi.org/10.1016/j.soildyn.2024.108851
"""

from openquake.hazardlib.gsim.aristeidou_2024 import (
    AristeidouEtAl2024,
    AristeidouEtAl2024Geomean,
    AristeidouEtAl2024RotD100)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AristeidouEtAl2024TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AristeidouEtAl2024
    MEAN_FILE = 'ASO24/ASO24_ROTD50_MEAN.csv'
    STD_INTRA_FILE = 'ASO24/ASO24_ROTD50_STD_INTRA.csv'
    STD_INTER_FILE = 'ASO24/ASO24_ROTD50_STD_INTER.csv'
    STD_TOTAL_FILE = 'ASO24/ASO24_ROTD50_STD_TOTAL.csv'

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.STD_INTRA_FILE,
                   self.STD_INTER_FILE,
                   self.STD_TOTAL_FILE,
                   max_discrep_percentage=0.4)


class AristeidouEtAl2024GeomeanTestCase(AristeidouEtAl2024TestCase):
    GSIM_CLASS = AristeidouEtAl2024Geomean
    MEAN_FILE = 'ASO24/ASO24_GEOMEAN_MEAN.csv'
    STD_INTRA_FILE = 'ASO24/ASO24_GEOMEAN_STD_INTRA.csv'
    STD_INTER_FILE = 'ASO24/ASO24_GEOMEAN_STD_INTER.csv'
    STD_TOTAL_FILE = 'ASO24/ASO24_GEOMEAN_STD_TOTAL.csv'


class AristeidouEtAl2024RotD100TestCase(AristeidouEtAl2024TestCase):
    GSIM_CLASS = AristeidouEtAl2024RotD100
    MEAN_FILE = 'ASO24/ASO24_ROTD100_MEAN.csv'
    STD_INTRA_FILE = 'ASO24/ASO24_ROTD100_STD_INTRA.csv'
    STD_INTER_FILE = 'ASO24/ASO24_ROTD100_STD_INTER.csv'
    STD_TOTAL_FILE = 'ASO24/ASO24_ROTD100_STD_TOTAL.csv'
