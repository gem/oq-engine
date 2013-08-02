# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013, GEM Foundation.
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
import mock

from openquake.engine.calculators.risk import validation
from openquake.engine.db import models


class HazardIMTTestCase(unittest.TestCase):
    def test_get_errors(self):
        calc = mock.Mock()
        calc.risk_models = {
            'tax1': {
                'loss1': models.RiskModel('imt1', None, None)},
            'tax2': {
                'loss2': models.RiskModel('imt2', None, None)}}
        calc.hc.get_imts = mock.Mock(return_value=['imt1', 'imt2'])
        val = validation.HazardIMT(calc)

        self.assertIsNone(val.get_errors())
        calc.hc.get_imts = mock.Mock(return_value=['imt1'])
        self.assertEqual(("There is no hazard output for: imt2. "
                          "The available IMTs are: imt1."), val.get_errors())
