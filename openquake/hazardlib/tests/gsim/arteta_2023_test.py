# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

from openquake.hazardlib.gsim.arteta_2023 import (
    ArtetaEtAl2023_Vs30, ArtetaEtAl2023)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

"""
Module imports :class:`ArtetaEtAl2023_Vs30`,`ArtetaEtAl2023`
The test tables were created from a *.xlsx file created by the authors
"""


class ArtetaEtAl2023_Vs30Test(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation and the within-event
    standard deviation. The between events std is implicitly tested
    """

    GSIM_CLASS = ArtetaEtAl2023_Vs30

    def test_median(self):
        self.check('arteta2023_NoSam/ARTETAETAL2023_Vs30_NoSAm_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std(self):
        self.check('arteta2023_NoSam/ARTETAETAL2023_Vs30_NoSAm_Sigma.csv',
                   'arteta2023_NoSam/ARTETAETAL2023_Vs30_NoSAm_Phi.csv',
                   'arteta2023_NoSam/ARTETAETAL2023_Vs30_NoSAm_Tau.csv',
                   max_discrep_percentage=0.1)


class ArtetaEtAl2023_Test(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation and the within-event
    standard deviation. The between events std is implicitly tested
    """

    GSIM_CLASS = ArtetaEtAl2023

    def test_median(self):
        self.check('arteta2023_NoSam/ARTETAETAL2023_NoSAm_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std(self):
        self.check('arteta2023_NoSam/ARTETAETAL2023_NoSAm_Sigma.csv',
                   'arteta2023_NoSam/ARTETAETAL2023_NoSAm_Phi.csv',
                   'arteta2023_NoSam/ARTETAETAL2023_NoSAm_Tau.csv',
                   max_discrep_percentage=0.1)
