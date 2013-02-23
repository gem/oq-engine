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

from openquake.engine.calculators.hazard.scenario.core import \
    task_arg_generator


class ScenarioHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests the task_arg_generator utility.
    """

    def test_task_arg_generator_few_gmfs(self):
        args = list(task_arg_generator(
            number_of_ground_motion_fields=2,
            num_concurrent_tasks=3))
        # generate a single task with 2 spare realization
        self.assertEqual(args, [(0, 2)])

    def test_task_arg_generator_many_gmfs(self):
        args = list(task_arg_generator(
            number_of_ground_motion_fields=7,
            num_concurrent_tasks=3))
        # generate 3 tasks with 2 realizations each, plus a task with a spare
        # realization
        self.assertEqual(
            args, [(0, 2), (1, 2), (2, 2),
                   (0, 1)])

    def test_task_arg_generator_no_spare(self):
        args = list(task_arg_generator(
            number_of_ground_motion_fields=6,
            num_concurrent_tasks=3))
        # generate 3 tasks with 2 realizations each
        self.assertEqual(args, [(0, 2), (1, 2), (2, 2)])
