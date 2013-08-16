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


"""
This module contains several utilities that once instantiated/called
returns callables useful to compute artifacts for multiple assets
"""

import functools
import collections

import numpy

from openquake.risklib import scientific, utils


def ClassicalLossCurve(vulnerability_function, steps):
    """
    :param vulnerability_function:
       a :class:`openquake.risklib.scientific.VulnerabilityFunction`
       instance used to compute loss curves by using the Classical PSHA-based
       algorithm
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


def ProbabilisticLoss(
        vulnerability_function, seed=None, asset_correlation=0):
    """
    :param vulnerability_function:
       a :class:`openquake.risklib.scientific.VulnerabilityFunction`
       instance used to losses
    :param float seed: a seed used to initialize the rng
    :param float asset_correlation:
       a value between 0 and 1 used to derive correlation of generated
       losses between different assets of the same taxonomy.
    """
    return functools.partial(
        scientific.vulnerability_function_applier,
        vulnerability_function,
        seed=seed,
        asset_correlation=asset_correlation)


def Damage(fragility_functions):
    """
    :param fragility_functions:
       an iterator over callables used as fragility functions. E.g.
       a :class:`openquake.risklib.scientific.FragilityFunctionContinuous`
       instance
    """
    return functools.partial(
        utils.numpy_map,
        functools.partial(
            scientific.scenario_damage,
            fragility_functions))


class EventLossTable(object):
    def __call__(self, loss_matrix, event_ids):
        """
        Compute the event loss table given a loss matrix and a set of event
        ids.

        :param loss_matrix:
           a numpy array of losses shaped N x E, where E is the number
           of events and N the number of samplings

        :param event_ids:
           a numpy array holding E event ids
        """
        if numpy.array(loss_matrix).ndim == 1:
            return collections.Counter()

        return collections.Counter(
            dict(zip(event_ids, numpy.sum(loss_matrix, axis=1))))


class LossMap(object):
    def __init__(self, poes):
        self.poes = poes or []

    def __call__(self, curves):
        def single_map(curve, poe):
            losses, poes = curve
            return scientific.conditional_loss_ratio(losses, poes, poe)

        return numpy.array(
            [[single_map(curve, poe) for curve in curves]
             for poe in self.poes])


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
         for quantile in quantiles])
    quantile_maps = LossMap(poes)(quantile_curves)

    return (mean_curve, quantile_curves, mean_map, quantile_maps)


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
