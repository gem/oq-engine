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
    return functools.partial(
        utils.numpy_map,
        functools.partial(
            scientific.classical,
            vulnerability_function,
            steps=steps))


def EventBasedLossCurve(time_span, tses, curve_resolution):
    return functools.partial(
        utils.numpy_map,
        functools.partial(
            scientific.event_based,
            curve_resolution=curve_resolution,
            time_span=time_span, tses=tses))


def ProbabilisticLoss(
        vulnerability_function, seed, asset_correlation):
    return functools.partial(
        scientific.vulnerability_function_applier,
        vulnerability_function,
        seed=seed,
        asset_correlation=asset_correlation)


def InsuredLoss():
    return functools.partial(
        utils.numpy_map,
        scientific.insured_losses)


def Damage(fragility_functions):
    return functools.partial(
        utils.numpy_map,
        functools.partial(
            scientific.scenario_damage,
            fragility_functions))


def InsuredLossCurve(loss_curve_calculator):
    return utils.compose(
        loss_curve_calculator,
        functools.partial(
            utils.numpy_map,
            scientific.insured_losses))


class EventLossTable(object):
    def __call__(self, loss_matrix, event_ids):
        return collections.Counter(
            dict(zip(event_ids, numpy.sum(loss_matrix, axis=1))))


class LossMap(object):
    def __init__(self, poes):
        self.poes = poes or []

    def __call__(self, curves):
        def single_map(curve, poe):
            losses, poes = curve
            return scientific.conditional_loss_ratio(losses, poes, poe)

        return [[single_map(curve, poe) for curve in curves]
                for poe in self.poes]
