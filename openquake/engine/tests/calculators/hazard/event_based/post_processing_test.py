# Copyright (c) 2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import unittest

import numpy

from openquake.engine.calculators.hazard.event_based import (
    post_processing as pp)

from openquake.engine.tests.calculators.hazard.event_based import _pp_test_data as test_data


class GmvsToHazCurveTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.engine.calculators.hazard.event_based.\
post_processing.gmvs_to_haz_curve`.
    """

    def test_gmvs_to_haz_curve_site_1(self):
        expected_poes = [0.63578, 0.39347, 0.07965]
        imls = [0.01, 0.1, 0.2]
        gmvs = test_data.SITE_1_GMVS
        invest_time = 1.0  # years
        duration = 1000.0  # years

        actual_poes = pp.gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
        numpy.testing.assert_array_almost_equal(
            expected_poes, actual_poes, decimal=6)

    def test_gmvs_to_haz_curve_case_2(self):
        expected_poes = [0.63578, 0.28609, 0.02664]
        imls = [0.01, 0.1, 0.2]
        gmvs = test_data.SITE_2_GMVS
        invest_time = 1.0  # years
        duration = 1000.0  # years

        actual_poes = pp.gmvs_to_haz_curve(gmvs, imls, invest_time, duration)
        numpy.testing.assert_array_almost_equal(
            expected_poes, actual_poes, decimal=6)
