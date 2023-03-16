# The Hazard Library
# Copyright (C) 2023 GEM Foundation
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
"""
Test cases 01–10 are based on the verification tests described in the
USGS ShakeMap 4.1 Manual.
Ref: Worden, C. B., E. M. Thompson, M. Hearne, and D. J. Wald (2020). 
ShakeMap Manual Online: technical manual, user’s guide, and software guide, 
U.S. Geological Survey. DOI: https://doi.org/10.5066/F7D21VPQ, see
https://usgs.github.io/shakemap/manual4_0/tg_verification.html`.
"""
import unittest

from openquake.hazardlib.calc.conditioned_gmfs import \
    get_conditioned_mean_and_covariance
from openquake.hazardlib.cross_correlation import GodaAtkinson2009
from openquake.hazardlib.tests.calc import \
    _conditioned_gmfs_test_data as test_data


class SetUSGSTestCase(unittest.TestCase):
    def test_case_0001(self):
        rupture = test_data.RUP
        gmm = test_data.ZeroMeanGMM()
        station_sitecol = test_data.CASE01_STATION_SITECOL
        station_data = test_data.CASE01_STATION_DATA
        observed_imt_strs = test_data.CASE01_OBSERVED_IMTS
        target_sitecol = test_data.CASE01_TARGET_SITECOL
        target_imts = test_data.CASE01_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = GodaAtkinson2009()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        maximum_distance = test_data.MAX_DIST
        mean_covs = get_conditioned_mean_and_covariance(
            rupture,
            gmm,
            station_sitecol,
            station_data,
            observed_imt_strs,
            target_sitecol,
            target_imts,
            spatial_correl,
            cross_correl_between,
            cross_correl_within,
            maximum_distance,
        )
