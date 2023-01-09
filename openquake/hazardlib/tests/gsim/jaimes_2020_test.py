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

from openquake.hazardlib.gsim.jaimes_2020 import (
    JaimesEtAl2020SSlab,
    JaimesEtAl2020SSlabVert,
    JaimesEtAl2020SSlabVHratio)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# The verification tables were generated using a the Matlab implementation 
# created by M.A. Jaimes Téllez (first author). The format of the tables 
# was adapted to the requirements of the OQ tests. 


class JaimesEtAl2020SSlabTestCase(BaseGSIMTestCase):
    """
    Test GMPE from Jaimes et al. (2020) for the horizontal component
    """
    GSIM_CLASS = JaimesEtAl2020SSlab
    def test_all(self):
        self.check('JA20/JA20_SSLAB_MEAN.csv',
                   'JA20/JA20_SSLAB_STD_TOTAL.csv',
                   'JA20/JA20_SSLAB_STD_INTER.csv',
                   'JA20/JA20_SSLAB_STD_INTRA.csv',
                   max_discrep_percentage=0.1,
                   std_discrep_percentage=0.1)


class JaimesEtAl2020SSlabVertTestCase(BaseGSIMTestCase):
    """
    Test GMPE from Jaimes et al. (2020) for the vertical component
    """
    GSIM_CLASS = JaimesEtAl2020SSlabVert
    def test_all(self):
        self.check('JA20/JA20_SSLABVERT_MEAN.csv',
                   'JA20/JA20_SSLABVERT_TOTAL.csv',
                   'JA20/JA20_SSLABVERT_INTER.csv',
                   'JA20/JA20_SSLABVERT_INTRA.csv',
                   max_discrep_percentage=0.1,
                   std_discrep_percentage=0.1)


class JaimesEtAl2020SSlabVHratioTestCase(BaseGSIMTestCase):
    """
    Test GMPE from Jaimes et al. (2020) for the V/H ratio
    """
    GSIM_CLASS = JaimesEtAl2020SSlabVHratio
    def test_all(self):
        self.check('JA20/JA20_SSLAB_VHRATIO_MEAN.csv',
                   'JA20/JA20_SSLAB_VHRATIO_TOTAL.csv',
                   'JA20/JA20_SSLAB_VHRATIO_INTER.csv',
                   'JA20/JA20_SSLAB_VHRATIO_INTRA.csv',
                   max_discrep_percentage=0.1,
                   std_discrep_percentage=0.1)
