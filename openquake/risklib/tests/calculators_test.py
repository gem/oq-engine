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


import mock
import unittest
import numpy
from openquake.risklib import VulnerabilityFunction
from openquake.risklib import calculators


class ClassicalLossCurveTest(unittest.TestCase):
    def setUp(self):
        vf = VulnerabilityFunction([0.4, 0.7], [0.1, 0.9])
        self.calc = calculators.ClassicalLossCurve(vf, steps=3)
        self.hazard_imls = numpy.linspace(0, 1, 10)

    def test_generator(self):
        vf = mock.Mock()
        steps = mock.Mock()
        with mock.patch('openquake.risklib.scientific.classical') as m:
            calc = calculators.ClassicalLossCurve(vf, steps)
            calc([1, 2, 3])

            self.assertEqual([((vf, 1), {'steps': steps}),
                              ((vf, 2), {'steps': steps}),
                              ((vf, 3), {'steps': steps})], m.call_args_list)

    def test_one_hazard_curve(self):
        hazard_curve = zip(self.hazard_imls, numpy.linspace(1, 0, 10))
        ((losses, poes),) = self.calc([hazard_curve])
        numpy.testing.assert_almost_equal(
            [0., 0.03333333, 0.06666667, 0.1, 0.36666667,
             0.63333333, 0.9, 0.93333333, 0.96666667, 1.], losses)
        numpy.testing.assert_almost_equal(
            [0.6, 0.6, 0.6, 0.6, 0.3, 0.3, 0.3, 0., 0., 0.], poes)

    def test_no_hazard_curves(self):
        loss_curves = self.calc([])

        self.assertFalse(loss_curves)

    def test_multi_hazard_curves(self):
        hazard_curve1 = zip(self.hazard_imls, numpy.linspace(1, 0, 10))
        hazard_curve2 = zip(self.hazard_imls, numpy.linspace(1, 0.1, 10))
        (losses1, poes1), (losses2, poes2) = self.calc(
            [hazard_curve1, hazard_curve2])

        numpy.testing.assert_almost_equal(
            numpy.array([0., 0.03333333, 0.06666667, 0.1, 0.36666667,
                         0.63333333, 0.9, 0.93333333, 0.96666667, 1.]),
            losses1)

        # losses are equal because hazard imls are equal
        numpy.testing.assert_almost_equal(losses1, losses2)

        numpy.testing.assert_almost_equal(
            [0.6, 0.6, 0.6, 0.6, 0.3, 0.3, 0.3, 0., 0., 0.], poes1)

        numpy.testing.assert_almost_equal(
            [0.54, 0.54, 0.54, 0.54, 0.27, 0.27, 0.27, 0., 0., 0.], poes2)


class EventBasedLossCurveTest(unittest.TestCase):
    def setUp(self):
        self.resolution = 5
        self.calc = calculators.EventBasedLossCurve(1, 10, self.resolution)

    def test_generator(self):
        resolution = mock.Mock()
        time_span = mock.Mock()
        tses = mock.Mock()

        with mock.patch('openquake.risklib.scientific.event_based') as m:
            calc = calculators.EventBasedLossCurve(time_span, tses, resolution)
            calc([1, 2, 3])

            self.assertEqual([((1,), dict(curve_resolution=resolution,
                                          time_span=time_span,
                                          tses=tses)),
                              ((2,), dict(curve_resolution=resolution,
                                          time_span=time_span,
                                          tses=tses)),
                              ((3,), dict(curve_resolution=resolution,
                                          time_span=time_span,
                                          tses=tses))], m.call_args_list)

    def test_one_array_of_losses(self):
        losses = numpy.linspace(0, 1, 1000)
        ((losses, poes),) = self.calc([losses])
        numpy.testing.assert_almost_equal(
            numpy.linspace(0, 1, self.resolution), losses)

        numpy.testing.assert_almost_equal([1, 1, 1, 1, 0], poes)

    def test_no_losses(self):
        loss_curves = self.calc([])

        self.assertFalse(loss_curves)

    def test_multi_losses(self):
        set1 = numpy.linspace(0, 0.5, 1000)
        set2 = numpy.linspace(0.5, 1, 1000)
        (losses1, poes1), (losses2, poes2) = self.calc([set1, set2])

        numpy.testing.assert_almost_equal(
            numpy.linspace(0, 0.5, self.resolution),
            losses1)

        numpy.testing.assert_almost_equal(
            numpy.linspace(0, 1, self.resolution),
            losses2)

        numpy.testing.assert_almost_equal([1, 1, 1, 1, 0], poes1)

        numpy.testing.assert_almost_equal([1, 1, 1, 1, 0], poes2)


class ProbabilisticLossTest(unittest.TestCase):
    def test_generator(self):
        vf = mock.Mock()
        seed = mock.Mock()
        asset_correlation = mock.Mock()

        fn = 'openquake.risklib.scientific.vulnerability_function_applier'

        with mock.patch(fn) as m:
            calc = calculators.ProbabilisticLoss(vf, seed, asset_correlation)
            calc([1, 2, 3])

            self.assertEqual(
                m.call_args_list,
                [((vf, [1, 2, 3]), {'seed': seed,
                                    'asset_correlation': asset_correlation})])
