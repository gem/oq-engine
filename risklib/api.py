# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
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
from risklib import scientific


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
        self.loss_ratio_exceedance_matrix = (
            vulnerability_function.loss_ratio_exceedance_matrix(steps))

    def __call__(self, assets, hazard_curves):
        return [
            scientific.ClassicalOutput(
                asset,
                scientific.classical(
                    self.vulnerability_function,
                    self.loss_ratio_exceedance_matrix,
                    hazard_curves[i],
                    self.steps),
                None)
            for i, asset in enumerate(assets)]


class ScenarioDamage(object):
    """
    Scenario damage calculator producing a damage distribution for each asset,
    i.e. a matrix NxM where N is the number of realizations of the ground
    motion field and M is the numbers of damage states. fragility_functions
    is a dictionary associating to each taxonomy a FragilityFunctionSeq object.
    """
    def __init__(self, fragility_model, fragility_functions_map):
        self.fragility_model = fragility_model
        self.fragility_functions = fragility_functions_map

    def __call__(self, assets, ground_motion_fields):
        return [
            scientific.ScenarioDamageOutput(
                asset,
                numpy.array([
                    self.fragility_functions.ground_motion_value_fractions(gmv)
                    * asset.number_of_units
                    for gmv in ground_motion_fields[i]]))
            for i, asset in enumerate(assets)]


class ConditionalLosses(object):
    """
    Compute the conditional losses for each Probability
    of Exceedance given as input.
    """
    def __init__(self, conditional_loss_poes, loss_curve_calculator):
        self.conditional_loss_poes = conditional_loss_poes
        self.loss_curve_calculator = loss_curve_calculator

    def __call__(self, assets, hazard):
        asset_outputs = self.loss_curve_calculator(assets, hazard)

        return [
            asset_output._replace(
                conditional_losses=dict(
                    (poe,
                     scientific.conditional_loss(asset_output.loss_curve, poe))
                    for poe in self.conditional_loss_poes))
            for asset_output in asset_outputs]


class BCR(object):
    """
    Compute the Benefit Cost Ratio. For each asset, it produces:
    * the benefit cost ratio
    * the expected annual loss
    * the expect annual loss retrofitted
    """
    def __init__(self, loss_curve_calculator_original,
                 loss_curve_calculator_retrofitted,
                 interest_rate, asset_life_expectancy):
        self.lcc_original = loss_curve_calculator_original
        self.lcc_retrofitted = loss_curve_calculator_retrofitted
        self.interest_rate = interest_rate
        self.asset_life_expectancy = asset_life_expectancy

    def __call__(self, assets, hazard):
        original_losses = self.lcc_original(assets, hazard)
        retrofitted_losses = self.lcc_retrofitted(assets, hazard)

        original_annual_losses = [
            scientific.mean_loss(original_losses[i].loss_curve)
            for i in range(0, len(assets))]

        retrofitted_annual_losses = [
            scientific.mean_loss(retrofitted_losses[i].loss_curve)
            for i in range(0, len(assets))]

        return [
            scientific.BCROutput(
                asset,
                scientific.bcr(
                    original_annual_losses[i],
                    retrofitted_annual_losses[i],
                    self.interest_rate,
                    self.asset_life_expectancy,
                    asset.retrofitting_cost),
                original_annual_losses[i],
                retrofitted_annual_losses[i])
            for i, asset in enumerate(assets)]


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

        # needed in external calculator.
        self.loss_ratios = None  # set in __call__

    def __call__(self, assets, ground_motion_fields):
        self.vulnerability_function.init_distribution(
            len(assets), len(ground_motion_fields[0]),
            self.seed, self.correlation)

        self.loss_ratios = [
            self.vulnerability_function(ground_motion_fields[i])
            for i in range(0, len(assets))]

        return [
            scientific.ProbabilisticEventBasedOutput(
                asset,
                self.loss_ratios[i] * asset.value,
                scientific.event_based(
                    self.loss_ratios[i],
                    tses=self.tses, time_span=self.time_span,
                    curve_resolution=self.curve_resolution),
                None, None, None)
            for i, asset in enumerate(assets)]


class InsuredLosses(object):
    """
    Insured losses calculator.
    """
    def __init__(self, losses_calculator):
        self.losses_calculator = losses_calculator

    def __call__(self, assets, ground_motion_fields):
        asset_outputs = self.losses_calculator(assets, ground_motion_fields)

        ret = []
        for i, asset_output in enumerate(asset_outputs):
            loss_curve = scientific.insured_losses(
                assets[i],
                self.losses_calculator.loss_ratios[i] * assets[i].value,
                self.losses_calculator.tses, self.losses_calculator.time_span,
                self.losses_calculator.curve_resolution)

            ret.append(asset_output._replace(
                insured_losses=loss_curve,
                insured_loss_ratio_curve=loss_curve.rescale_abscissae(
                    1 / asset_output.asset.value)))

        return ret


class Scenario(object):
    def __init__(self, vulnerability_function,
                 seed=None, correlation=0):
        self.seed = seed
        self.correlation = correlation
        self.vulnerability_function = vulnerability_function

    def __call__(self, assets, ground_motion_fields):
        self.vulnerability_function.init_distribution(
            len(assets), len(ground_motion_fields[0]),
            self.seed, self.correlation)

        return [
            scientific.ScenarioRiskOutput(
                asset,
                (self.vulnerability_function(ground_motion_fields[i]) *
                 asset.value))
            for i, asset in enumerate(assets)]
