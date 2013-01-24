# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy
from risklib import scientific


def compute_on_assets(assets, hazard_getter, calculator):
    """
    Main entry to trigger a calculation over a set of homogeneous assets.

    :param assets: the set of assets where to trigger the computation on
    :type assets: an `iterator` over a collection of
        `:class:risklib.scientific.Asset`
    :param hazard_getter: the logic used to lookup the hazard defined
        on a single geographical site
    :type hazard_getter: `callable` that accepts as single parameter a
        geographical site and returns the hazard input for that site.
        The format of the hazard input depends on the type of calculator
        chosen and it is documented in detail in each calculator
    :param calculator: a specific calculator (classical, probabilistic
        event based, benefit cost ratio, scenario risk, scenario damage)
    :type calculator: `callable` that accepts as first parameter an
        instance of `risklib.models.input.Asset` and as second parameter the
        hazard input. It returns an instance of
        `risklib.scientific.Output` with the results of the
        computation for the given asset

    :raises: ValueError if the given assets are of different
    taxonomies. The check is only performed after that the second
    asset has been used
    """

    for asset in assets:
        hazard = hazard_getter(asset.site)
        yield calculator(asset, hazard)


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

    def __call__(self, asset, hazard):
        loss_ratio_curve = scientific.classical(
            self.vulnerability_function, self.loss_ratio_exceedance_matrix,
            hazard, self.steps)

        return scientific.ClassicalOutput(asset, loss_ratio_curve, None)


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

    def __call__(self, asset, hazard):
        funcs = self.fragility_functions
        fractions = numpy.array([
            funcs.ground_motion_value_fractions(gmv)
            * asset.number_of_units for gmv in hazard])
        return scientific.ScenarioDamageOutput(asset, fractions)


class ConditionalLosses(object):
    """
    Compute the conditional losses for each Probability
    of Exceedance given as input.
    """
    def __init__(self, conditional_loss_poes, loss_curve_calculator):
        self.conditional_loss_poes = conditional_loss_poes
        self.loss_curve_calculator = loss_curve_calculator

    def __call__(self, asset, hazard):
        asset_output = self.loss_curve_calculator(asset, hazard)
        cl = dict((poe,
                   scientific.conditional_loss(asset_output.loss_curve, poe))
                  for poe in self.conditional_loss_poes)
        return asset_output._replace(conditional_losses=cl)


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

    def __call__(self, asset, hazard):
        annual_loss_original = scientific.mean_loss(
            self.lcc_original(asset, hazard).loss_curve)

        annual_loss_retrofitted = scientific.mean_loss(
            self.lcc_retrofitted(asset, hazard).loss_curve)

        bcr = scientific.bcr(
            annual_loss_original,
            annual_loss_retrofitted, self.interest_rate,
            self.asset_life_expectancy, asset.retrofitting_cost)

        return scientific.BCROutput(
            asset, bcr, annual_loss_original, annual_loss_retrofitted)


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
            seed=None, correlation_type=None,
            curve_resolution=scientific.DEFAULT_CURVE_RESOLUTION):

        self.seed = seed
        self.correlation_type = correlation_type
        self.vulnerability_function = vulnerability_function
        self.time_span = time_span
        self.tses = tses
        self.curve_resolution = curve_resolution
        self.loss_ratios = None  # set in __call__

    def __call__(self, asset, hazard):
        self.vulnerability_function.seed(self.seed, self.correlation_type)

        self.loss_ratios = self.vulnerability_function(hazard)

        loss_ratio_curve = scientific.event_based(
            self.loss_ratios,
            tses=self.tses, time_span=self.time_span,
            curve_resolution=self.curve_resolution)

        losses = self.loss_ratios * asset.value

        return scientific.ProbabilisticEventBasedOutput(
            asset, losses, loss_ratio_curve, None, None, None)


# the aggregation design was discussed in
# https://mail.google.com/mail/u/0/#search/aggrega/13a9bbf82d91fa0d
def aggregate_losses(set_of_outputs, result=None):
    for asset_output in set_of_outputs:
        if result is None:  # first time
            result = numpy.copy(asset_output.losses)
        else:
            result += asset_output.losses  # mutate the copy
    return result


class InsuredLosses(object):
    """
    Insured losses calculator.
    """
    def __init__(self, losses_calculator):
        self.losses_calculator = losses_calculator

    def __call__(self, asset, hazard):
        asset_output = self.losses_calculator(asset, hazard)

        loss_curve = scientific.insured_losses(
            asset, self.losses_calculator.loss_ratios * asset.value,
            self.losses_calculator.tses, self.losses_calculator.time_span,
            self.losses_calculator.curve_resolution)

        return asset_output._replace(
            insured_losses=loss_curve,
            insured_loss_ratio_curve=loss_curve.rescale_abscissae(
                1 / asset.value))


class ScenarioRisk(object):
    """
    Scenario risk calculator. For each asset it produces:
        * mean / standard deviation of asset losses

    It also produces the following aggregate results:
        * aggregate losses
    """

    def __init__(self, vulnerability_function, seed, correlation_type):

        self.seed = seed
        self.correlation_type = correlation_type
        self.vulnerability_function = vulnerability_function

    def __call__(self, asset, hazard):
        self.vulnerability_function.seed(self.seed, self.correlation_type)

        loss_ratios = self.vulnerability_function(hazard)

        losses = loss_ratios * asset.value

        return scientific.ScenarioRiskOutput(asset, losses)
