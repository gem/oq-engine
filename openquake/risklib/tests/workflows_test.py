# -*- coding: utf-8 -*-

# Copyright (c) 2013, GEM Foundation.
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

import collections
import numpy

from openquake.risklib import workflows


class ClassicalTest(unittest.TestCase):
    def setUp(self):
        self.patch1 = mock.patch('openquake.risklib.workflows.calculators')
        self.calcs = self.patch1.start()
        self.calcs.LossMap = mock.MagicMock

        self.patch2 = mock.patch(
            'openquake.risklib.workflows.scientific.average_loss')
        average_loss = self.patch2.start()
        average_loss.return_value = 3

        self.vf = mock.MagicMock()
        self.poes = [0.1, 0.2]
        self.poes_disagg = [0.1, 0.2, 0.3]
        self.workflow = workflows.Classical(
            self.vf, 3, self.poes, self.poes_disagg)
        self.workflow.maps.poes = self.poes
        self.workflow.fractions = lambda curves: numpy.empty((len(curves), 3))
        self.workflow.fractions.poes = self.poes_disagg
        self.workflow.curves.return_value = numpy.empty((4, 2, 10))

    def tearDown(self):
        self.patch1.stop()
        self.patch2.stop()

    def test_call(self):
        assets = [workflows.Asset(dict(structural=10))]
        curves = [mock.Mock()]
        output = self.workflow("structural", assets, curves)

        self.assertEqual(assets, output.assets)

        self.assertEqual(
            [((self.vf, 3), {})],
            self.calcs.ClassicalLossCurve.call_args_list)
        self.assertIsNone(
            self.workflow.statistics(
                [], mock.Mock(), mock.Mock(), mock.Mock()))

        numpy.testing.assert_allclose(
            numpy.ones((4,)) * 3, output.average_losses)


class ProbabilisticEventBasedTest(unittest.TestCase):
    def setUp(self):
        self.patch1 = mock.patch('openquake.risklib.workflows.calculators')
        self.calcs = self.patch1.start()

        self.patch2 = mock.patch(
            'openquake.risklib.workflows.scientific.average_loss')
        average_loss = self.patch2.start()
        average_loss.return_value = 3

        self.patch3 = mock.patch('numpy.std')
        std = self.patch3.start()
        std.return_value = 0.1

        self.vf = mock.MagicMock()
        self.poes = [0.1, 0.2]
        self.workflow = workflows.ProbabilisticEventBased(
            self.vf, 1, 0.75, 50, 1000, 20, self.poes, True)
        self.workflow.maps.poes = self.poes
        self.workflow.curves = mock.Mock(return_value=numpy.empty((3, 2, 20)))

    def tearDown(self):
        self.patch1.stop()
        self.patch2.stop()
        self.patch3.stop()

    def test_call(self):
        assets = [workflows.Asset(dict(structural=10),
                                  dict(structural=0.1),
                                  dict(structural=0.8))]
        hazard = (mock.Mock(), mock.Mock())
        self.workflow.losses.return_value = numpy.empty((1, 100))
        self.workflow.event_loss.return_value = collections.Counter((1, 1))

        output = self.workflow("structural", assets, hazard)

        self.assertEqual(assets, output.assets)

        self.assertEqual(
            [((self.vf, 1, 0.75), {})],
            self.calcs.ProbabilisticLoss.call_args_list)

        self.assertEqual(
            [((50, 1000, 20), {})],
            self.calcs.EventBasedLossCurve.call_args_list)

        self.assertEqual(
            [((), {})],
            self.calcs.EventLossTable.call_args_list)

        numpy.testing.assert_allclose(
            numpy.ones((3,)) * 3, output.average_losses)

        numpy.testing.assert_allclose(
            numpy.ones((3,)) * 0.1, output.stddev_losses)

    def test_normalize_all_trivial(self):
        poes = numpy.linspace(1, 0, 11)
        losses = numpy.zeros(11)
        curves = [[losses, poes], [losses, poes / 2]]
        exp_losses, (poes1, poes2) = self.workflow._normalize_curves(curves)

        numpy.testing.assert_allclose(exp_losses, losses)
        numpy.testing.assert_allclose(poes1, poes)
        numpy.testing.assert_allclose(poes2, poes / 2)

    def test_normalize_one_trivial(self):
        trivial = [numpy.zeros(6), numpy.linspace(1, 0, 6)]
        curve = [numpy.linspace(0., 1., 6), numpy.linspace(1., 0., 6)]
        with numpy.errstate(invalid='ignore', divide='ignore'):
            exp_losses, (poes1, poes2) = self.workflow._normalize_curves(
                [trivial, curve])

        numpy.testing.assert_allclose(exp_losses, curve[0])
        numpy.testing.assert_allclose(poes1, [numpy.nan, 0., 0., 0., 0., 0.])
        numpy.testing.assert_allclose(poes2, curve[1])


class ClassicalBCRTest(unittest.TestCase):
    def setUp(self):
        self.patch = mock.patch('openquake.risklib.workflows.calculators')
        self.calcs = self.patch.start()
        self.vf = mock.MagicMock()
        self.vf_retro = mock.MagicMock()
        self.workflow = workflows.ClassicalBCR(
            self.vf, self.vf_retro, 3, 0.1, 30)
        self.workflow.curves_orig.return_value = numpy.empty((4, 2, 10))
        self.workflow.curves_retro.return_value = numpy.empty((4, 2, 10))

    def tearDown(self):
        self.patch.stop()

    def test_call(self):
        assets = [workflows.Asset(dict(structural=10),
                                  retrofitting_values=dict(structural=10))]
        curves = [mock.Mock()]
        curves_retro = [mock.Mock()]
        self.workflow("structural", assets, curves, curves_retro)

        self.assertEqual(
            [((self.vf, 3), {}), ((self.vf_retro, 3), {})],
            self.calcs.ClassicalLossCurve.call_args_list)


class ScenarioTestCase(unittest.TestCase):
    def test_call(self):
        vf = mock.MagicMock()
        calc = workflows.Scenario(vf, 0, 0, True)

        assets = [workflows.Asset(
            dict(structural=10),
            deductibles=dict(structural=0.1),
            insurance_limits=dict(structural=0.8))] * 4

        hazard = (mock.Mock(), mock.Mock())
        calc.losses = mock.Mock(return_value=numpy.empty((4, 2)))

        (loss_ratio_matrix, aggregate_losses,
         insured_loss_matrix, insured_losses) = (
             calc("structural", assets, hazard))

        self.assertEqual((4, 2), loss_ratio_matrix.shape)
        self.assertEqual((2,), aggregate_losses.shape)
        self.assertEqual((4, 2), insured_loss_matrix.shape)
        self.assertEqual((2,), insured_losses.shape)

    def test_call_no_insured(self):
        vf = mock.MagicMock()
        calc = workflows.Scenario(vf, 0, 0, False)

        assets = [workflows.Asset(dict(structural=10))] * 4
        hazard = (mock.Mock(), mock.Mock())
        calc.losses = mock.Mock(return_value=numpy.empty((4, 2)))

        (loss_ratio_matrix, aggregate_losses,
         insured_loss_matrix, insured_losses) = (
             calc("structural", assets, hazard))

        self.assertEqual((4, 2), loss_ratio_matrix.shape)
        self.assertEqual((2,), aggregate_losses.shape)
        self.assertIsNone(insured_loss_matrix)
        self.assertIsNone(insured_losses)
