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

from openquake.hazardlib.gsim.berge_thierry_2003 import (
    BergeThierryEtAl2003SIGMA, BergeThierryEtAl2003MwW,
    BergeThierryEtAl2003MwL_MED, BergeThierryEtAl2003MwL_ITA,
    BergeThierryEtAl2003MwL_GBL, BergeThierryEtAl2003Ms)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# test data generated from hazardlib implementation. Test data from
# original authors are needed for more robust testing

class BergeThierryEtAl2003SIGMATestCase(BaseGSIMTestCase):
    """ Test the original Berge-Thierry et al. with SIGMA recommendations
    for the standard deviation """
    GSIM_CLASS = BergeThierryEtAl2003SIGMA

    def test_all(self):
        self.check('B03/BergeThierryEtAl2003SIGMA_MEAN.csv',
                   'B03/BergeThierryEtAl2003SIGMA_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1)


class BergeThierryEtAl2003MwWTestCase(BaseGSIMTestCase):
    """ Test the Berge-Thierry et al. for Mw - Weatherill et al., 2016
    conversion equation """
    GSIM_CLASS = BergeThierryEtAl2003MwW

    def test_all(self):
        self.check('B03/BergeThierryEtAl2003MwW_MEAN.csv',
                   'B03/BergeThierryEtAl2003MwW_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1)


class BergeThierryEtAl2003MsTestCase(BaseGSIMTestCase):
    """ Test the original Berge-Thierry et al., 2003 in Ms """
    GSIM_CLASS = BergeThierryEtAl2003Ms

    def test_all(self):
        self.check('B03/BergeThierryEtAl2003Ms_MEAN.csv',
                   'B03/BergeThierryEtAl2003Ms_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1)


class BergeThierryEtAl2003MwL_MEDTestCase(BaseGSIMTestCase):
    """ Test the Berge-Thierry et al. for Mw - Lolli et al., 2014
    conversion equation with coefficients for MED area """
    GSIM_CLASS = BergeThierryEtAl2003MwL_MED

    def test_all(self):
        self.check('B03/BergeThierryEtAl2003MwL_MED_MEAN.csv',
                   'B03/BergeThierryEtAl2003MwL_MED_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1)


class BergeThierryEtAl2003MwL_ITATestCase(BaseGSIMTestCase):
    """ Test the Berge-Thierry et al. for Mw - Lolli et al., 2014
    conversion equation with coefficients for ITA area """
    GSIM_CLASS = BergeThierryEtAl2003MwL_ITA

    def test_all(self):
        self.check('B03/BergeThierryEtAl2003MwL_ITA_MEAN.csv',
                   'B03/BergeThierryEtAl2003MwL_ITA_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.3,
                   std_discrep_percentage=0.1)


class BergeThierryEtAl2003MwL_GBLTestCase(BaseGSIMTestCase):
    """ Test the Berge-Thierry et al. for Mw - Lolli et al., 2014
    conversion equation with coefficients for GBL area """
    GSIM_CLASS = BergeThierryEtAl2003MwL_GBL

    def test_all(self):
        self.check('B03/BergeThierryEtAl2003MwL_GBL_MEAN.csv',
                   'B03/BergeThierryEtAl2003MwL_GBL_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.3,
                   std_discrep_percentage=0.1)
