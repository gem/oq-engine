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


import mock
import unittest
import numpy
import itertools
from openquake.risklib import calculators


class LossMapTest(unittest.TestCase):
    def setUp(self):
        losses = numpy.linspace(0, 10, 11)
        poes = numpy.linspace(1, 0, 11)
        self.curves = [(losses, poes), (losses * 2, poes)]

    def test_no_poes(self):
        self.assertEqual(0, calculators.LossMap([])(self.curves).size)

    def test_one_poe(self):
        numpy.testing.assert_allclose(
            [[3.5, 7]], calculators.LossMap([0.65])(self.curves))

    def test_more_poes(self):
        numpy.testing.assert_allclose(
            [[4.5, 9], [5, 10]],
            calculators.LossMap([0.55, 0.5])(self.curves))


class AssetStatisticsTestCase(unittest.TestCase):
    BASE_EXPECTED_POES = numpy.linspace(1, 0, 11)

    def setUp(self):
        self.losses = numpy.linspace(0, 1, 11)

    # fake post_processing module singleton
    class post_processing(object):
        @staticmethod
        def mean_curve(_curve_poes, _weights):
            return (AssetStatisticsTestCase.BASE_EXPECTED_POES)

        @staticmethod
        def weighted_quantile_curve(_curve_poes, _weights, quantile):
            return -AssetStatisticsTestCase.BASE_EXPECTED_POES * quantile

        @staticmethod
        def quantile_curve(_curve_poes, quantile):
            return AssetStatisticsTestCase.BASE_EXPECTED_POES * quantile

    def test_compute_stats_no_quantiles_no_poes(self):
        (mean_curve, mean_maps, quantile_curves, quantile_maps) = (
            calculators.asset_statistics(
                self.losses, mock.Mock(), [],
                [None], [], self.post_processing))

        numpy.testing.assert_allclose(mean_curve,
                                      (self.losses, self.BASE_EXPECTED_POES))

        self.assertEqual(0, quantile_curves.size)
        self.assertEqual(0, mean_maps.size)
        self.assertEqual(0, quantile_maps.size)

    def test_compute_stats_quantiles_weighted(self):
        (mean_curve, mean_maps, quantile_curves, quantile_maps) = (
            calculators.asset_statistics(
                self.losses, mock.Mock(),
                quantiles=[0.1, 0.2],
                poes=[],
                weights=[0.1, 0.2],
                post_processing=self.post_processing))

        numpy.testing.assert_allclose(
            mean_curve, (self.losses, self.BASE_EXPECTED_POES))

        q1, q2 = quantile_curves
        numpy.testing.assert_allclose(
            q1, (self.losses, -self.BASE_EXPECTED_POES * 0.1))
        numpy.testing.assert_allclose(
            q2, (self.losses, -self.BASE_EXPECTED_POES * 0.2))

        self.assertEqual(0, mean_maps.size)
        self.assertEqual(0, quantile_maps.size)

    def test_compute_stats_quantiles_montecarlo(self):
        (mean_curve, mean_maps, quantile_curves, quantile_maps) = (
            calculators.asset_statistics(
                self.losses, mock.Mock(),
                quantiles=[0.1, 0.2],
                poes=[],
                weights=[None, None],
                post_processing=self.post_processing))

        numpy.testing.assert_allclose(
            mean_curve, (self.losses, self.BASE_EXPECTED_POES))

        q1, q2 = quantile_curves
        numpy.testing.assert_allclose(
            q1, (self.losses, self.BASE_EXPECTED_POES * 0.1))
        numpy.testing.assert_allclose(
            q2, (self.losses, self.BASE_EXPECTED_POES * 0.2))

        self.assertEqual(0, mean_maps.size)
        self.assertEqual(0, quantile_maps.size)

    def test_compute_stats_quantile_poes(self):
        (mean_curve, mean_map, quantile_curves, quantile_maps) = (
            calculators.asset_statistics(
                self.losses, mock.Mock(),
                quantiles=[0.1, 0.2],
                poes=[0.2, 0.8],
                weights=[None],
                post_processing=self.post_processing))

        numpy.testing.assert_allclose(
            mean_curve, (self.losses, self.BASE_EXPECTED_POES))
        q1, q2 = quantile_curves
        numpy.testing.assert_allclose(
            q1, (self.losses, self.BASE_EXPECTED_POES * 0.1))
        numpy.testing.assert_allclose(
            q2, (self.losses, self.BASE_EXPECTED_POES * 0.2))

        numpy.testing.assert_allclose(mean_map, [0.8, 0.2])

        numpy.testing.assert_allclose(quantile_maps, numpy.zeros((2, 2)))

    def test_exposure(self):
        resolution = 10

        # testing exposure_statistics with arrays of different shapes
        for quantile_nr, poe_nr, asset_nr in itertools.product(
                range(3), range(3), range(1, 4)):
            with mock.patch(
                    'openquake.risklib.calculators.asset_statistics') as m:
                m.return_value = (numpy.empty((2, resolution)),
                                  numpy.empty(poe_nr),
                                  numpy.empty((quantile_nr, 2, resolution)),
                                  numpy.empty((quantile_nr, poe_nr)))

                loss_curves = numpy.empty((asset_nr, 2, resolution))

                (mean_curves, mean_average_losses, mean_maps,
                 quantile_curves, quantile_average_losses, quantile_maps) = (
                    calculators.exposure_statistics(loss_curves,
                                                    numpy.empty(poe_nr),
                                                    numpy.empty(asset_nr),
                                                    numpy.empty(quantile_nr),
                                                    mock.Mock()))

                self.assertEqual((asset_nr, 2, resolution), mean_curves.shape)
                self.assertEqual((asset_nr, ), mean_average_losses.shape)
                self.assertEqual((poe_nr, asset_nr), mean_maps.shape)
                self.assertEqual((quantile_nr, asset_nr, 2, resolution),
                                 quantile_curves.shape)
                self.assertEqual((quantile_nr, asset_nr),
                                 quantile_average_losses.shape)
                self.assertEqual((quantile_nr, poe_nr, asset_nr),
                                 quantile_maps.shape)
