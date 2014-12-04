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


"""
This module contains several utilities that once instantiated/called
returns callables useful to compute artifacts for multiple assets
"""

import functools

import numpy

from openquake.risklib import scientific, utils


def ClassicalLossCurve(vulnerability_function, hazard_imls, steps):
    """
    :param vulnerability_function:
       a :class:`openquake.risklib.scientific.VulnerabilityFunction`
       instance used to compute loss curves by using the Classical PSHA-based
       algorithm
    :param hazard_imls:
        the hazard intensity measure type and levels
    :param int steps:
       the number of steps used in the Classical PSHA-based algorithm
    :returns:
       a function that can be applied to a set of hazard curves.
       See :func:`openquake.risklib.scientific.classical` for more details
    """
    return functools.partial(
        utils.numpy_map,
        functools.partial(
            scientific.classical,
            vulnerability_function,
            hazard_imls,
            steps=steps))


def EventBasedLossCurve(time_span, tses, curve_resolution):
    """
    :param int time_span:
       The investigation time considered by the event based algorithm
    :param int tses:
       The time of the stochastic event set considered
    :param int curve_resolution:
       The resolution (number of values) the loss curve will be built on
    :returns:
       a function that can be applied to a set of loss values.
       See :func:`openquake.risklib.scientific.event_based` for more details
    """

    return functools.partial(
        utils.numpy_map,
        functools.partial(
            scientific.event_based,
            curve_resolution=curve_resolution,
            time_span=time_span, tses=tses))


class LossMap(object):
    def __init__(self, poes):
        self.poes = poes or []

    def __call__(self, curves):
        def single_map(curve, poe):
            losses, poes = curve
            return scientific.conditional_loss_ratio(losses, poes, poe)

        return numpy.array(
            [[single_map(curve, poe) for curve in curves]
             for poe in self.poes]).reshape((len(self.poes), len(curves)))


def exposure_statistics(
        loss_curves, map_poes, weights, quantiles, post_processing):
    """
    Compute exposure statistics for N assets and R realizations.

    :param loss_curves:
        a list with N loss curves data. Each item holds a 2-tuple with
        1) the loss ratios on which the curves have been defined on
        2) the poes of the R curves
    :param map_poes:
        a numpy array with P poes used to compute loss maps
    :param weights:
        a list of N weights used to compute mean/quantile weighted statistics
    :param quantiles:
        the quantile levels used to compute quantile results
    :param post_processing:
       a module providing #weighted_quantile_curve, #quantile_curve,
       #mean_curve

    :returns:
        a tuple with six elements:
            1. a numpy array with N mean loss curves
            2. a numpy array with N mean average losses
            3. a numpy array with P x N mean map values
            4. a numpy array with Q x N quantile loss curves
            5. a numpy array with Q x N quantile average loss values
            6. a numpy array with Q x P quantile map values
    """
    curve_resolution = len(loss_curves[0][0])
    map_nr = len(map_poes)

    # Collect per-asset statistic along the last dimension of the
    # following arrays
    mean_curves = numpy.zeros((0, 2, curve_resolution))
    mean_average_losses = numpy.array([])
    mean_maps = numpy.zeros((map_nr, 0))
    quantile_curves = numpy.zeros((len(quantiles), 0, 2, curve_resolution))
    quantile_average_losses = numpy.zeros((len(quantiles), 0,))
    quantile_maps = numpy.zeros((len(quantiles), map_nr, 0))

    for loss_ratios, curves_poes in loss_curves:
        _mean_curve, _mean_maps, _quantile_curves, _quantile_maps = (
            asset_statistics(
                loss_ratios, curves_poes,
                quantiles, weights, map_poes, post_processing))

        mean_curves = numpy.vstack(
            (mean_curves, _mean_curve[numpy.newaxis, :]))
        mean_average_losses = numpy.append(
            mean_average_losses, scientific.average_loss(*_mean_curve))

        mean_maps = numpy.hstack((mean_maps, _mean_maps[:, numpy.newaxis]))
        quantile_curves = numpy.hstack(
            (quantile_curves, _quantile_curves[:, numpy.newaxis]))

        _quantile_average_losses = numpy.array(
            [scientific.average_loss(losses, poes)
             for losses, poes in _quantile_curves])
        quantile_average_losses = numpy.hstack(
            (quantile_average_losses,
             _quantile_average_losses[:, numpy.newaxis]))
        quantile_maps = numpy.dstack(
            (quantile_maps, _quantile_maps[:, :, numpy.newaxis]))

    return (mean_curves, mean_average_losses, mean_maps,
            quantile_curves, quantile_average_losses, quantile_maps)


def asset_statistics(
        losses, curves_poes, quantiles, weights, poes, post_processing):
    """
    Compute output statistics (mean/quantile loss curves and maps)
    for a single asset

    :param losses:
       the losses on which the loss curves are defined
    :param curves_poes:
       a numpy matrix with the poes of the different curves
    :param list quantiles:
       an iterable over the quantile levels to be considered for
       quantile outputs
    :param list poes:
       the poe taken into account for computing loss maps
    :returns:
       a tuple with
       1) mean loss curve
       2) a list of quantile curves
       3) mean loss map
       4) a list of quantile loss maps
    """
    mean_curve = numpy.array([losses, post_processing.mean_curve(
        curves_poes, weights)])
    mean_map = LossMap(poes)([mean_curve]).reshape(len(poes))
    quantile_curves = numpy.array(
        [[losses, quantile_curve(post_processing, weights)(
          curves_poes, quantile)]
         for quantile in quantiles]).reshape((len(quantiles), 2, len(losses)))
    quantile_maps = LossMap(poes)(quantile_curves).transpose()

    return (mean_curve, mean_map, quantile_curves, quantile_maps)


def quantile_curve(post_processing, weights):
    """
    Helper functions that wraps the `post_processing` object

    :param post_processing:
       a module providing #weighted_quantile_curve, #quantile_curve,
       #mean_curve
    :param list weights:
       the weights associated with each realization. If all the elements are
       `None`, implicit weights are taken into account
    :returns:
        a function that a quantile curve given curve poes and
        the quantile value in input
    """
    if weights[0] is None:  # implicit weights
        return post_processing.quantile_curve
    else:
        return lambda poes, quantile: post_processing.weighted_quantile_curve(
            poes, weights, quantile)
