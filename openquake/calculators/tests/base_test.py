# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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

import unittest
import mock
from openquake.baselib.general import gettemp
from openquake.baselib import hdf5
from openquake.calculators import base


class FakeParams(hdf5.LiteralAttrs):
    export_dir = '/tmp'
    hazard_calculation_id = None
    inputs = {'job_ini': gettemp('fake_job.ini')}
    concurrent_tasks = 0
    minimum_magnitude = 0

    def to_params(self):
        return {}


class ErrorCalculator(base.BaseCalculator):
    def pre_execute(self):
        pass

    def execute(self):
        1 / 0

    def post_execute(self):
        pass


class BaseCalculatorTestCase(unittest.TestCase):
    def test_critical(self):
        calc = ErrorCalculator(FakeParams())
        with mock.patch('logging.error') as error, mock.patch(
                'logging.critical') as critical:
            self.assertRaises(ZeroDivisionError, calc.run)
        self.assertEqual(error.call_count, 0)
        self.assertEqual(critical.call_count, 1)
