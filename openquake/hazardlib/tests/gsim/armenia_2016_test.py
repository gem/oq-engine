# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
Implements the set of tests for the adjustments of a selected set of
Ground Motion Prediction Equations proposed for application to PSHA in
Armenia

Each of the test tables is generated from the original GMPE tables, which are
subsequently modified using the adjustment factors presented in the module
openquake.hazardlib.gsim.armenia_2016
"""
import unittest
import numpy as np
from openquake.hazardlib.gsim.armenia_2016 import (AkkarEtAlRjb2014Armenia,
                                                   BindiEtAl2014RjbArmenia,
                                                   BooreEtAl2014LowQArmenia,
                                                   CauzziEtAl2014Armenia,
                                                   ChiouYoungs2014Armenia,
                                                   KaleEtAl2015Armenia,
                                                   KothaEtAl2016Armenia)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.01


class AkkarEtAlRjb2014ArmeniaTestCase(BaseGSIMTestCase):
    """
    Tests the Armenia calibrated adjustment of the Akkar et al. (2014)
    GMPE
    """
    GSIM_CLASS = AkkarEtAlRjb2014Armenia
    MEAN_FILE = "armenia_2016/AKKAR14_ARMENIA_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)


class BindiEtAl2014RjbArmeniaTestCase(AkkarEtAlRjb2014ArmeniaTestCase):
    """
    Tests the Armenia calibrated adjustment of the Bindi et al. (2014)
    GMPE
    """
    GSIM_CLASS = BindiEtAl2014RjbArmenia
    MEAN_FILE = "armenia_2016/BINDI14_ARMENIA_MEAN.csv"


class BooreEtAl2014LowQArmeniaTestCase(AkkarEtAlRjb2014ArmeniaTestCase):
    """
    Tests the Armenia calibrated adjustment of the Boore et al. (2014) Low Q
    GMPE
    """
    GSIM_CLASS = BooreEtAl2014LowQArmenia
    MEAN_FILE = "armenia_2016/BSSA14LOWQ_ARMENIA_MEAN.csv"


class CauzziEtAl2014ArmeniaTestCase(AkkarEtAlRjb2014ArmeniaTestCase):
    """
    Tests the Armenia calibrated adjustment of the Cauzzi et al. (2014) GMPE
    """
    GSIM_CLASS = CauzziEtAl2014Armenia
    MEAN_FILE = "armenia_2016/CAUZZI14_ARMENIA_MEAN.csv"


class ChiouYoungs2014ArmeniaTestCase(AkkarEtAlRjb2014ArmeniaTestCase):
    """
    Tests the Armenia calibrated adjustment of the Chiou & Youngs (2014) GMPE
    """
    GSIM_CLASS = ChiouYoungs2014Armenia
    MEAN_FILE = "armenia_2016/CY14_ARMENIA_MEAN.csv"


class KaleEtAl2015ArmeniaTestCase(AkkarEtAlRjb2014ArmeniaTestCase):
    """
    Tests the Armenia calibrated adjustment of the Kale et al. (2015) Turkey
    GMPE
    """
    GSIM_CLASS = KaleEtAl2015Armenia
    MEAN_FILE = "armenia_2016/KALE15_ARMENIA_MEAN.csv"


class KothaEtAl2016ArmeniaTestCase(AkkarEtAlRjb2014ArmeniaTestCase):
    """
    Tests the Armenia calibrated adjustment of the Kotha et al. (2016) Turkey
    GMPE
    """
    GSIM_CLASS = KothaEtAl2016Armenia
    MEAN_FILE = "armenia_2016/KOTHA16_ARMENIA_MEAN.csv"
