# coding=utf-8
# Copyright (c) 2010-2013, GEM Foundation.
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

import numpy
from openquake.risklib import scientific


class Classical(object):
    """
    Classical calculator. For each asset it produces:
    * a loss curve
    * a loss ratio curve
    * a set of conditional losses
    """
    def __init__(self, vulnerability_function, steps=10):
        self.vulnerability_function = vulnerability_function
        self.steps = steps

    def __call__(self, hazard_curves):
        return [scientific.classical(
            self.vulnerability_function, hazard_curve, steps=self.steps)
            for hazard_curve in hazard_curves]


class ProbabilisticEventBased(object):
    """
    Probabilistic event based calculator. For each asset it produces:
        * a set of losses
        * a loss ratio curve
        * a loss curve

    It also produces the following aggregate results:
        * aggregate loss curve
    """

    def __init__(
            self, vulnerability_function,
            time_span, tses,
            seed=None, correlation=0,
            curve_resolution=scientific.DEFAULT_CURVE_RESOLUTION):

        self.seed = seed
        self.correlation = correlation
        self.vulnerability_function = vulnerability_function
        self.time_span = time_span
        self.tses = tses
        self.curve_resolution = curve_resolution

    def __call__(self, ground_motion_fields):
        if not len(ground_motion_fields):
            return numpy.array([[]]), []

        self.vulnerability_function.init_distribution(
            len(ground_motion_fields), len(ground_motion_fields[0]),
            self.seed, self.correlation)

        loss_ratios = [
            self.vulnerability_function(ground_motion_field)
            for ground_motion_field in ground_motion_fields]

        return (loss_ratios,
                [scientific.event_based(
                    asset_loss_ratios,
                    tses=self.tses, time_span=self.time_span,
                    curve_resolution=self.curve_resolution)
                    for asset_loss_ratios in loss_ratios])


class Scenario(object):
    def __init__(self, vulnerability_function, seed=None, correlation=0):
        self.seed = seed
        self.correlation = correlation
        self.vulnerability_function = vulnerability_function

    def __call__(self, ground_motion_fields):
        if not len(ground_motion_fields):
            return numpy.array([[]])

        self.vulnerability_function.init_distribution(
            len(ground_motion_fields), len(ground_motion_fields[0]),
            self.seed, self.correlation)

        return map(self.vulnerability_function, ground_motion_fields)


class ScenarioDamage(object):
    """
    Scenario damage calculator producing a damage distribution for each asset,
    i.e. a matrix NxM where N is the number of realizations of the ground
    motion field and M is the numbers of damage states. Take in input a
    FragilityFunctionSequence object.
    """
    def __init__(self, ffs):
        self.ffs = ffs

    def __call__(self, ground_motion_fields):
        """
        The ground motion field is a list of ground motion values
        (one array for each site). Returns a list of arrays (one per site).
        """
        return [
            scientific.scenario_damage(self.ffs, asset_gmvs)
            for asset_gmvs in ground_motion_fields]
