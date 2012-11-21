# Copyright (c) 2010-2012, GEM Foundation.
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


from tests.utils import helpers
import unittest

from openquake.db import models
from django.contrib.gis.geos.point import Point

from openquake.calculators.risk import hazard_getters


class HazardCurveGetterPerAssetTestCase(unittest.TestCase):
    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            'classical_psha_based_risk/job.ini',
            'simple_fault_demo_hazard/job.ini')

        models.HazardCurveData.objects.create(
            hazard_curve=self.job.risk_calculation.hazard_output.hazardcurve,
            poes=[0.2, 0.3, 0.4],
            location="POINT(3 3)")

    def test_call(self):
        getter = hazard_getters.HazardCurveGetterPerAsset(
            self.job.risk_calculation.hazard_output.hazardcurve.id)

        self.assertEqual([(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
                         getter(Point(1, 1)))

        self.assertEqual([(0.1, 0.2), (0.2, 0.3), (0.3, 0.4)],
                         getter(Point(4, 4)))
