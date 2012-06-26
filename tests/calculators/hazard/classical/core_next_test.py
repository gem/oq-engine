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

from openquake.calculators.hazard.classical import core_next

from tests.utils import helpers


class ClassicalHazardCalculatorTestCase(unittest.TestCase):
    """
    Tests for the basic functions of the classical hazard calculator
    (pre_execute, execute, etc.).
    """

    def test_pre_execute_stores_site_model(self):
        cfg = helpers.demo_file(
            'simple_fault_demo_hazard/job_with_site_model.ini')
        job = helpers.get_hazard_job(cfg)

        calc = core_next.ClassicalHazardCalculator(job)

        calc.pre_execute()

    def test_pre_execute_no_site_model(self):
        pass
