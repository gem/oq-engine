# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.


import unittest
import mock

import numpy

from openquake.risklib import workflows

aaae = numpy.testing.assert_array_almost_equal


def asset(values, deductibles=None,
          insurance_limits=None,
          retrofitting_values=None):
    return workflows.Asset('a1', 'taxonomy', 1, (0, 0), values,
                           1, deductibles, insurance_limits,
                           retrofitting_values)


class ScenarioTestCase(unittest.TestCase):
    loss_type = 'structural'

    def test_call(self):
        vf = mock.MagicMock()
        calc = workflows.Scenario('PGA', 'TAXO', vf, True)

        assets = [asset(
            dict(structural=10),
            deductibles=dict(structural=0.1),
            insurance_limits=dict(structural=0.8))] * 4

        calc.risk_functions[self.loss_type].apply_to = mock.Mock(
            return_value=numpy.empty((4, 2)))

        out = calc(self.loss_type, assets, mock.Mock(), mock.Mock())

        self.assertEqual((4, 2), out.loss_matrix.shape)
        self.assertEqual((2,), out.aggregate_losses.shape)
        self.assertEqual((4, 2), out.insured_loss_matrix.shape)
        self.assertEqual((2,), out.insured_losses.shape)

    def test_call_no_insured(self):
        vf = mock.MagicMock()
        calc = workflows.Scenario('PGA', 'TAXO', vf, False)

        assets = [asset(dict(structural=10))] * 4
        vf = calc.risk_functions[self.loss_type]
        vf.apply_to = mock.Mock(return_value=numpy.empty((4, 2)))

        out = calc(self.loss_type, assets, mock.Mock(), mock.Mock())

        self.assertEqual((4, 2), out.loss_matrix.shape)
        self.assertEqual((2,), out.aggregate_losses.shape)
        self.assertIsNone(out.insured_loss_matrix)
        self.assertIsNone(out.insured_losses)


class DamageTest(unittest.TestCase):
    def test_generator(self):
        with mock.patch('openquake.risklib.scientific.scenario_damage') as m:
            fragility_functions = mock.Mock()
            calc = workflows.Damage(
                'PGA', 'TAXO', dict(damage=fragility_functions))
            calc('damage', 'assets', 'hazard', None)
            self.assertEqual(m.call_count, 6)  # called 3 x 2 times
