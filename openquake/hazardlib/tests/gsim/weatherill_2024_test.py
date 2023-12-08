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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
"""

"""
from openquake.hazardlib.gsim.weatherill_2024 import (
    Weatherill2024ESHM20AvgSA, Weatherill2024ESHM20SlopeGeologyAvgSA,
    Weatherill2024ESHM20AvgSAHomoskedastic)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.01


class Weatherill2024ESHM20AvgSATestCase(BaseGSIMTestCase):
    GSIM_CLASS = Weatherill2024ESHM20AvgSA

    def test_all(self):
        self.check(
            "weatherill_2024/ESHM20_AvgSA_mean.csv",
            "weatherill_2024/ESHM20_AvgSA_total_stddev_ergodic.csv",
            "weatherill_2024/ESHM20_AvgSA_inter_event_stddev.csv",
            "weatherill_2024/ESHM20_AvgSA_intra_event_stddev_ergodic.csv",
            max_discrep_percentage=MAX_DISCREP)

    def test_nonergodic_stddev(self):
        self.check(
            "weatherill_2024/ESHM20_AvgSA_total_stddev_nonergodic.csv",
            "weatherill_2024/ESHM20_AvgSA_intra_event_stddev_nonergodic.csv",
            max_discrep_percentage=MAX_DISCREP, ergodic=False)

    def test_with_sigma_mu_c3_adjustments(self):
        self.check(
            "weatherill_2024/ESHM20_AvgSA_adjustments_mean.csv",
            max_discrep_percentage=MAX_DISCREP,
            sigma_mu_epsilon=1.0, c3_epsilon=-1.0)


class Weatherill2024ESHM20SlopeGeologyAvgSATestCase(BaseGSIMTestCase):
    GSIM_CLASS = Weatherill2024ESHM20SlopeGeologyAvgSA

    def test_all(self):
        self.check(
            "weatherill_2024/ESHM20_AvgSA_slope_geology_mean.csv",
            "weatherill_2024/ESHM20_AvgSA_slope_geology_total_stddev.csv",
            "weatherill_2024/ESHM20_AvgSA_slope_geology_inter_event_stddev.csv",
            "weatherill_2024/ESHM20_AvgSA_slope_geology_intra_event_stddev.csv",
            max_discrep_percentage=MAX_DISCREP)


class Weatherill2024ESHM20AvgSAHomoskedasticTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Weatherill2024ESHM20AvgSAHomoskedastic

    def test_all(self):
        self.check(
            "weatherill_2024/ESHM20_AvgSA_homoskedastic_total_stddev.csv",
            "weatherill_2024/ESHM20_AvgSA_homoskedastic_inter_event_stddev.csv",
            "weatherill_2024/ESHM20_AvgSA_homoskedastic_intra_event_stddev.csv",
            max_discrep_percentage=MAX_DISCREP)
