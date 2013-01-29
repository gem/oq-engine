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

from openquake.calculators.hazard.scenario.core import realizations_per_task


class ScenarioHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the main methods of the scenario hazard calculator.
    """

    def test_realizations_per_task(self):
        num_concur_tasks = 32
        num_realizations = 1000
        realizations = [31 for i in range(32)]
        realizations.append(8)

        self.assertEqual(33, len(realizations))
        self.assertEqual((True, realizations), realizations_per_task(
            num_realizations, num_concur_tasks))

        num_concur_task = 32
        num_realizations = 96
        realizations = [3 for i in range(32)]

        self.assertEqual((False, realizations), realizations_per_task(
            num_realizations, num_concur_tasks))

