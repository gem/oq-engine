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


import unittest

from openquake.calculators.hazard.scenario.core import gmf_realiz_per_task


class ScenarioHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the main methods of the scenario hazard calculator.
    """

    def test_num_realizations_per_task(self):
        num_concur_tasks = 32
        gmf_realizations = 100
        realiz_per_task = [3 for i in range(num_concur_tasks)]
        realiz_per_task.append(4)

        self.assertEqual(33, len(realiz_per_task))
        self.assertEqual((True, realiz_per_task), gmf_realiz_per_task(
            gmf_realizations, num_concur_tasks))

        gmf_realizations = 96
        realiz_per_task = [3 for i in range(num_concur_tasks)]

        self.assertEqual((False, realiz_per_task), gmf_realiz_per_task(
            gmf_realizations, num_concur_tasks))

