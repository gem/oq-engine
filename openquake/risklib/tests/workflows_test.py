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
        self.patch = mock.patch('openquake.risklib.workflows.calculators')
        self.calcs = self.patch.start()
        self.calcs.LossMap = mock.MagicMock
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
        self.patch.stop()

    def test_call_one_realization(self):
        assets = [workflows.Asset(dict(structural=10))]
        curves = [mock.Mock()]
        data = ((1, assets, curves),)
        ret = list(self.workflow(data))

        self.assertEqual(1, len(ret))
        hid, output = ret[0]

        self.assertEqual(assets, output.assets)
        self.assertEqual(1, hid)
        self.assertIsNone(self.workflow._loss_curves)

        self.assertEqual(
            [((self.vf, 3), {})],
            self.calcs.ClassicalLossCurve.call_args_list)

    def test_call_three_realizations(self):
        assets = [workflows.Asset(dict(structural=10))] * 4

        curves = []
        for _ in range(0, 4):
            m = mock.Mock()
            m.__nonzero__ = mock.Mock()
            m.__nonzero__.return_value = True
            curves.append(m)

        data = ((1, assets, curves[0]),
                (2, assets, curves[1]),
                (3, assets, curves[2]),)

        i = 0
        for i, (hid, output) in enumerate(self.workflow(data), 1):
            self.assertEqual(assets, output.assets)
            self.assertEqual(i, hid)

        self.assertEqual(3, i)
        self.assertIsNotNone(self.workflow._loss_curves)

        self.assertEqual(
            [((self.vf, 3), {})],
            self.calcs.ClassicalLossCurve.call_args_list)

    def test_statistics(self):
        self.assertIsNone(self.workflow.statistics(mock.Mock(),
                                                   mock.Mock(),
                                                   mock.Mock()))
        assets = [workflows.Asset(dict(structural=10))] * 4
        curves = [mock.Mock()] * 4
        quantiles = [0.3, 0.7, 0.8, 0.9]

        self.calcs.asset_statistics.return_value = (
            numpy.empty((2, 10)), numpy.empty((len(quantiles), 2, 10)),
            numpy.empty(len(self.poes + self.poes_disagg)),
            numpy.empty((len(quantiles), len(self.poes + self.poes_disagg))))

        self.calcs.asset_statistic_fractions.return_value = (
            numpy.empty(len(self.poes_disagg)),
            numpy.empty((len(quantiles), len(self.poes_disagg))))

        data = ((1, assets, curves[0]),
                (2, assets, curves[1]),
                (3, assets, curves[2]),)

        list(self.workflow(data))

        post_proc = mock.MagicMock()
        stats = self.workflow.statistics(
            numpy.linspace(0.5, 0.8, 3), quantiles, post_proc)

        self.assertEqual(assets, stats.assets)
        self.assertEqual((4, 2, 10), stats.mean_curves.shape)
        self.assertEqual((len(self.poes), 4), stats.mean_maps.shape)
        self.assertEqual((len(self.poes_disagg), 4),
                         stats.mean_fractions.shape)
        self.assertEqual((len(quantiles), 4, 2, 10),
                         stats.quantile_curves.shape)
        self.assertEqual((len(quantiles), len(self.poes), 4),
                         stats.quantile_maps.shape)
        self.assertEqual((len(quantiles), len(self.poes_disagg), 4),
                         stats.quantile_fractions.shape)

    def test_statistics_no_quantiles(self):
        assets = [workflows.Asset(dict(structural=10))] * 4
        curves = [mock.Mock()] * 4
        quantiles = []

        self.calcs.asset_statistics.return_value = (
            numpy.empty((2, 10)),
            numpy.empty((len(quantiles), 2, 10)),
            numpy.empty(len(self.poes + self.poes_disagg)),
            numpy.empty((0, len(self.poes + self.poes_disagg))))

        data = ((1, assets, curves[0]),
                (2, assets, curves[1]),
                (3, assets, curves[2]),)

        list(self.workflow(data))

        post_proc = mock.MagicMock()
        stats = self.workflow.statistics(
            numpy.linspace(0.5, 0.8, 3),
            quantiles, post_proc)

        self.assertEqual(assets, stats.assets)
        self.assertEqual((4, 2, 10), stats.mean_curves.shape)
        self.assertEqual((len(self.poes), 4), stats.mean_maps.shape)
        self.assertEqual((len(self.poes_disagg), 4),
                         stats.mean_fractions.shape)
        self.assertEqual((len(quantiles), 4, 2, 10),
                         stats.quantile_curves.shape)
        self.assertEqual((len(quantiles), len(self.poes), 4),
                         stats.quantile_maps.shape)
        self.assertEqual((len(quantiles), len(self.poes_disagg), 4),
                         stats.quantile_fractions.shape)


class ProbabilisticEventBasedTest(unittest.TestCase):
    def setUp(self):
        self.patch = mock.patch('openquake.risklib.workflows.calculators')
        self.calcs = self.patch.start()
        self.vf = mock.MagicMock()
        self.poes = [0.1, 0.2]
        self.workflow = workflows.ProbabilisticEventBased(
            self.vf, 1, 0.75, 50, 1000, 20, self.poes, True)
        self.workflow.maps.poes = self.poes

    def tearDown(self):
        self.patch.stop()

    def test_call_one_realization(self):
        assets = [workflows.Asset(dict(structural=10),
                                  dict(structural=0.1),
                                  dict(structural=0.8))]
        hazard = (mock.Mock(), mock.Mock())
        data = ((1, assets, hazard),)
        self.workflow.losses.return_value = numpy.empty((1, 100))
        self.workflow.event_loss.return_value = collections.Counter((1, 1))

        ret = list(self.workflow("structural", data))

        self.assertEqual(1, len(ret))
        hid, output = ret[0]

        self.assertEqual(assets, output.assets)
        self.assertEqual(1, hid)
        self.assertIsNone(self.workflow._loss_curves)

        self.assertEqual(
            [((self.vf, 1, 0.75), {})],
            self.calcs.ProbabilisticLoss.call_args_list)

        self.assertEqual(
            [((50, 1000, 20), {})],
            self.calcs.EventBasedLossCurve.call_args_list)

        self.assertEqual(
            [((), {})],
            self.calcs.EventLossTable.call_args_list)

    def test_call_three_realizations(self):
        assets = [workflows.Asset(dict(structural=10),
                                  dict(structural=0.1),
                                  dict(structural=0.8))] * 4
        hazard = [(mock.Mock(), mock.Mock())] * 3

        self.workflow.losses.return_value = numpy.empty((4, 100))
        self.workflow.event_loss.return_value = collections.Counter((1, 1))
        self.workflow.curves.return_value = numpy.empty((4, 2, 10))

        data = ((1, assets, hazard[0]),
                (2, assets, hazard[1]),
                (3, assets, hazard[2]),)

        i = 0
        for i, (hid, output) in enumerate(
                self.workflow("structural", data), 1):
            self.assertEqual(assets, output.assets)
            self.assertEqual(i, hid)

            self.assertEqual(
                [((self.vf, 1, 0.75), {})],
                self.calcs.ProbabilisticLoss.call_args_list)

            self.assertEqual(
                [((50, 1000, 20), {})],
                self.calcs.EventBasedLossCurve.call_args_list)

            self.assertEqual(
                [((), {})],
                self.calcs.EventLossTable.call_args_list)

        self.assertEqual(3, i)
        self.assertIsNotNone(self.workflow._loss_curves)

    def test_statistics(self):
        self.assertIsNone(self.workflow.statistics(mock.Mock(),
                                                   mock.Mock(),
                                                   mock.Mock()))
        assets = [workflows.Asset(dict(structural=10),
                                  dict(structural=0.1),
                                  dict(structural=0.8))] * 4
        hazard = [(mock.Mock(), mock.Mock())] * 3
        data = ((1, assets, hazard[0]),
                (2, assets, hazard[1]),
                (3, assets, hazard[2]),)

        quantiles = [0.3, 0.7, 0.8, 0.9]

        self.workflow.losses.return_value = numpy.random.random((4, 100))
        self.workflow.event_loss.return_value = collections.Counter((1, 1))
        self.workflow.curves.return_value = numpy.random.random((4, 2, 10))

        self.calcs.asset_statistics.return_value = (
            numpy.empty((2, 10)), numpy.empty((len(quantiles), 2, 10)),
            numpy.empty(len(self.poes)),
            numpy.empty((len(quantiles), len(self.poes))))

        list(self.workflow("structural", data))

        post_proc = mock.MagicMock()
        stats = self.workflow.statistics(
            numpy.linspace(0.5, 0.8, 3),
            quantiles, post_proc)

        self.assertEqual(assets, stats.assets)
        self.assertEqual((4, 2, 10), stats.mean_curves.shape)
        self.assertEqual((len(self.poes), 4), stats.mean_maps.shape)
        self.assertEqual((len(quantiles), 4, 2, 10),
                         stats.quantile_curves.shape)
        self.assertEqual((len(quantiles), len(self.poes), 4),
                         stats.quantile_maps.shape)

    def test_statistics_no_quantiles(self):
        assets = [workflows.Asset(dict(structural=10),
                                  dict(structural=0.1),
                                  dict(structural=0.8))] * 4
        hazard = [(mock.Mock(), mock.Mock())] * 3
        data = ((1, assets, hazard[0]),
                (2, assets, hazard[1]),
                (3, assets, hazard[2]),)

        quantiles = []

        self.workflow.losses.return_value = numpy.random.random((4, 100))
        self.workflow.event_loss.return_value = collections.Counter((1, 1))
        self.workflow.curves.return_value = numpy.random.random((4, 2, 10))

        self.calcs.asset_statistics.return_value = (
            numpy.empty((2, 10)), numpy.empty((len(quantiles), 2, 10)),
            numpy.empty(len(self.poes)),
            numpy.zeros((len(quantiles), len(self.poes))))

        list(self.workflow("structural", data))

        post_proc = mock.MagicMock()
        stats = self.workflow.statistics(
            numpy.linspace(0.5, 0.8, 3),
            quantiles, post_proc)

        self.assertEqual((len(quantiles), 4, 2, 10),
                         stats.quantile_curves.shape)
        self.assertEqual((len(quantiles), len(self.poes), 4),
                         stats.quantile_maps.shape)


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

    def test_call_one_realization(self):
        assets = [workflows.Asset(dict(structural=10),
                                  retrofitting_values=dict(structural=10))]
        curves = [mock.Mock()]
        curves_retro = [mock.Mock()]
        data = ((1, assets, curves, curves_retro),)
        ret = list(self.workflow("structural", data))

        self.assertEqual(1, len(ret))
        hid, _output = ret[0]

        self.assertEqual(1, hid)

        self.assertEqual(
            [((self.vf, 3), {}), ((self.vf_retro, 3), {})],
            self.calcs.ClassicalLossCurve.call_args_list)

    def test_call_three_realizations(self):
        assets = [workflows.Asset(
            dict(structural=10),
            retrofitting_values=dict(structural=10))] * 4

        curves = [mock.Mock()] * 4
        curves_retro = [mock.Mock()] * 4

        data = ((1, assets, curves[0], curves_retro[0]),
                (2, assets, curves[1], curves_retro[1]),
                (3, assets, curves[2], curves_retro[2]),)

        i = 0
        for i, (hid, _output) in enumerate(
                self.workflow("structural", data), 1):
            self.assertEqual(i, hid)

        self.assertEqual(3, i)

        self.assertEqual(
            [((self.vf, 3), {}),
             ((self.vf_retro, 3), {})],
            self.calcs.ClassicalLossCurve.call_args_list)
