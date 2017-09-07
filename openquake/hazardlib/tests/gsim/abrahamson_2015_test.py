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

from openquake.hazardlib.gsim.abrahamson_2015 import (
    AbrahamsonEtAl2015SInter,
    AbrahamsonEtAl2015SInterHigh,
    AbrahamsonEtAl2015SInterLow,
    AbrahamsonEtAl2015SSlab,
    AbrahamsonEtAl2015SSlabHigh,
    AbrahamsonEtAl2015SSlabLow)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AbrahamsonEtAl2015SInterTestCase(BaseGSIMTestCase):
    """
    Tests the Abrahamson et al. (2015) BC Hydro model for subduction
    interface earthquakes with the central magnitude scaling term
    """
    GSIM_CLASS = AbrahamsonEtAl2015SInter
    MEAN_FILE = "BCHYDRO/BCHYDRO_SINTER_CENTRAL_MEAN.csv"
    TOTAL_FILE = "BCHYDRO/BCHYDRO_SINTER_CENTRAL_STDDEV_TOTAL.csv"
    INTER_FILE = "BCHYDRO/BCHYDRO_SINTER_CENTRAL_STDDEV_INTER.csv"
    INTRA_FILE = "BCHYDRO/BCHYDRO_SINTER_CENTRAL_STDDEV_INTRA.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE,
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check(self.INTER_FILE,
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check(self.INTRA_FILE,
                   max_discrep_percentage=0.1)


class AbrahamsonEtAl2015SInterHighTestCase(AbrahamsonEtAl2015SInterTestCase):
    """
    Tests the Abrahamson et al. (2015) BC Hydro model for subduction
    interface earthquakes with the high magnitude scaling term
    """
    GSIM_CLASS = AbrahamsonEtAl2015SInterHigh
    MEAN_FILE = "BCHYDRO/BCHYDRO_SINTER_HIGH_MEAN.csv"
    TOTAL_FILE = "BCHYDRO/BCHYDRO_SINTER_HIGH_STDDEV_TOTAL.csv"
    INTER_FILE = "BCHYDRO/BCHYDRO_SINTER_HIGH_STDDEV_INTER.csv"
    INTRA_FILE = "BCHYDRO/BCHYDRO_SINTER_HIGH_STDDEV_INTRA.csv"


class AbrahamsonEtAl2015SInterLowTestCase(AbrahamsonEtAl2015SInterTestCase):
    """
    Tests the Abrahamson et al. (2015) BC Hydro model for subduction
    interface earthquakes with the low magnitude scaling term
    """
    GSIM_CLASS = AbrahamsonEtAl2015SInterLow
    MEAN_FILE = "BCHYDRO/BCHYDRO_SINTER_LOW_MEAN.csv"
    TOTAL_FILE = "BCHYDRO/BCHYDRO_SINTER_LOW_STDDEV_TOTAL.csv"
    INTER_FILE = "BCHYDRO/BCHYDRO_SINTER_LOW_STDDEV_INTER.csv"
    INTRA_FILE = "BCHYDRO/BCHYDRO_SINTER_LOW_STDDEV_INTRA.csv"


class AbrahamsonEtAl2015SSlabTestCase(AbrahamsonEtAl2015SInterTestCase):
    """
    Tests the Abrahamson et al. (2015) BC Hydro model for subduction
    in-slab earthquakes with the central magnitude scaling term
    """
    GSIM_CLASS = AbrahamsonEtAl2015SSlab
    MEAN_FILE = "BCHYDRO/BCHYDRO_SSLAB_CENTRAL_MEAN.csv"
    TOTAL_FILE = "BCHYDRO/BCHYDRO_SSLAB_CENTRAL_STDDEV_TOTAL.csv"
    INTER_FILE = "BCHYDRO/BCHYDRO_SSLAB_CENTRAL_STDDEV_INTER.csv"
    INTRA_FILE = "BCHYDRO/BCHYDRO_SSLAB_CENTRAL_STDDEV_INTRA.csv"


class AbrahamsonEtAl2015SSlabHighTestCase(AbrahamsonEtAl2015SInterTestCase):
    """
    Tests the Abrahamson et al. (2015) BC Hydro model for subduction
    in-slab earthquakes with the high magnitude scaling term
    """
    GSIM_CLASS = AbrahamsonEtAl2015SSlabHigh
    MEAN_FILE = "BCHYDRO/BCHYDRO_SSLAB_HIGH_MEAN.csv"
    TOTAL_FILE = "BCHYDRO/BCHYDRO_SSLAB_HIGH_STDDEV_TOTAL.csv"
    INTER_FILE = "BCHYDRO/BCHYDRO_SSLAB_HIGH_STDDEV_INTER.csv"
    INTRA_FILE = "BCHYDRO/BCHYDRO_SSLAB_HIGH_STDDEV_INTRA.csv"


class AbrahamsonEtAl2015SSlabLowTestCase(AbrahamsonEtAl2015SInterTestCase):
    """
    Tests the Abrahamson et al. (2015) BC Hydro model for subduction
    in-slab earthquakes with the high magnitude scaling term
    """
    GSIM_CLASS = AbrahamsonEtAl2015SSlabLow
    MEAN_FILE = "BCHYDRO/BCHYDRO_SSLAB_LOW_MEAN.csv"
    TOTAL_FILE = "BCHYDRO/BCHYDRO_SSLAB_LOW_STDDEV_TOTAL.csv"
    INTER_FILE = "BCHYDRO/BCHYDRO_SSLAB_LOW_STDDEV_INTER.csv"
    INTRA_FILE = "BCHYDRO/BCHYDRO_SSLAB_LOW_STDDEV_INTRA.csv"
