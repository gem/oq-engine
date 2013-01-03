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
from risklib import (classical, event_based, scenario_damage,
                     benefit_cost_ratio, insured_loss)
from risklib.models import output


def compute_on_sites(sites, assets_getter, hazard_getter, calculator):
    """
    Main entry to trigger a calculation over geographical sites.

    For each site in `sites`, the function will:
        * load all the assets defined on that geographical site
        * load the hazard input defined on that geographical site
        * call the calculator for each asset and yield the calculator
        results for that single asset

    The assets lookup logic for a single site is completely up to the
    caller, as well as the logic to lookup the correct hazard on that site.
    Also, the are no constraints at all on how a single geographical site is
    represented, because they are just passed back to the client implementation
    of the assets and hazard getters to load the related inputs.

    :param sites: the set of sites where to trigger the computation on
    :type sites: an `iterator` over a collection of sites. No constraints
        are needed for the type of a single site
    :param assets_getter: the logic used to lookup the assets defined
        on a single geographical site
    :type assets_getter: `callable` that accepts as single parameter a
        geographical site and returns a set of `risklib.models.input.Asset`
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
        `risklib.models.output.*Output` with the results of the
        computation for the given asset
    """

    for site in sites:
        assets = assets_getter(site)
        hazard = hazard_getter(site)

        for asset in assets:
            yield calculator(asset, hazard)


def compute_on_assets(assets, hazard_getter, calculator):
    """
    Main entry to trigger a calculation over a set of assets.

    It works basically in the same way as `risklib.api.compute_on_sites`
    except that here we loop over the given assets.

    :param assets: the set of assets where to trigger the computation on
    :type assets: an `iterator` over a collection of
        `risklib.models.input.Asset`
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
        `risklib.models.output.*Output` with the results of the
        computation for the given asset
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
    def __init__(self, vulnerability_model, steps=10):
        self.vulnerability_model = vulnerability_model
        self.steps = steps
        self.matrices = dict(
            (taxonomy, classical._loss_ratio_exceedance_matrix(
                vulnerability_function, steps))
            for taxonomy, vulnerability_function
            in vulnerability_model.iteritems())

    def __call__(self, asset, hazard):
        vulnerability_function = self.vulnerability_model[asset.taxonomy]

        loss_ratio_curve = classical._loss_ratio_curve(
            vulnerability_function, self.matrices[asset.taxonomy],
            hazard, self.steps)

        loss_curve = loss_ratio_curve.rescale_abscissae(asset.value)

        return output.ClassicalOutput(
            asset, loss_ratio_curve, loss_curve, None)


class ScenarioDamage(object):
    """
    Scenario damage calculator. For each asset it produces:
        * a damage distribution
        * a collapse map

    It also produces the following aggregate results:
        * damage distribution per taxonomy
        * total damage distribution
    """

    def __init__(self, fragility_model, fragility_functions):
        self.fragility_model = fragility_model
        self.fragility_functions = fragility_functions

        # sum the fractions of all the assets with the same taxonomy
        self._fractions_per_taxonomy = {}

    def __call__(self, asset, hazard):
        taxonomy = asset.taxonomy

        damage_distribution_asset, fractions = (
            scenario_damage._damage_distribution_per_asset(
                asset,
                (self.fragility_model, self.fragility_functions[taxonomy]),
                hazard))

        collapse_map = scenario_damage._collapse_map(fractions)

        ddmatrix = scenario_damage._make_damage_distribution_matrix(
            self.fragility_model, hazard)

        asset_fractions = self._fractions_per_taxonomy.get(taxonomy, ddmatrix)
        self._fractions_per_taxonomy[taxonomy] = asset_fractions + fractions
        return output.ScenarioDamageOutput(
            asset, damage_distribution_asset, collapse_map)

    @property
    def damage_distribution_by_taxonomy(self):
        return self._fractions_per_taxonomy


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
                   classical._conditional_loss(asset_output.loss_curve, poe))
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
        annual_loss_original = benefit_cost_ratio.mean_loss(
            self.lcc_original(asset, hazard).loss_curve)

        annual_loss_retrofitted = benefit_cost_ratio.mean_loss(
            self.lcc_retrofitted(asset, hazard).loss_curve)

        bcr = benefit_cost_ratio.bcr(
            annual_loss_original,
            annual_loss_retrofitted, self.interest_rate,
            self.asset_life_expectancy, asset.retrofitting_cost)

        return output.BCROutput(
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
            self, vulnerability_model, seed=None, correlation_type=None,
            curve_resolution=event_based.DEFAULT_CURVE_RESOLUTION):

        self.seed = seed
        self.correlation_type = correlation_type
        self.vulnerability_model = vulnerability_model
        self.curve_resolution = curve_resolution

        self.loss_ratios = None
        self._aggregate_losses = None

    def __call__(self, asset, hazard):
        taxonomies = self.vulnerability_model.keys()
        vulnerability_function = self.vulnerability_model[asset.taxonomy]

        if self._aggregate_losses is None:
            self._aggregate_losses = numpy.zeros(len(hazard["IMLs"]))

        self.loss_ratios = event_based._compute_loss_ratios(
            vulnerability_function, hazard, asset, self.seed,
            self.correlation_type, taxonomies)

        loss_ratio_curve = event_based._loss_curve(
            self.loss_ratios, hazard['TSES'], hazard['TimeSpan'],
            curve_resolution=self.curve_resolution)

        losses = self.loss_ratios * asset.value
        loss_curve = loss_ratio_curve.rescale_abscissae(asset.value)

        self._aggregate_losses += losses

        return output.ProbabilisticEventBasedOutput(
            asset, losses, loss_ratio_curve, loss_curve,
            None, None, None, None)

    @property
    def aggregate_losses(self):
        return self._aggregate_losses


class InsuredLosses(object):
    """
    Insured losses calculator.
    """
    def __init__(self, losses_calculator):
        self.losses_calculator = losses_calculator

    def __call__(self, asset, hazard):
        asset_output = self.losses_calculator(asset, hazard)

        loss_curve = insured_loss.compute_insured_losses(
            asset, self.losses_calculator.loss_ratios * asset.value,
            hazard['TSES'], hazard['TimeSpan'],
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

    def __init__(self, vulnerability_model, seed, correlation_type):

        self.seed = seed
        self.correlation_type = correlation_type
        self.vulnerability_model = vulnerability_model

        self._aggregate_losses = None

    def __call__(self, asset, hazard):
        taxonomies = self.vulnerability_model.keys()
        vulnerability_function = self.vulnerability_model[asset.taxonomy]

        if self._aggregate_losses is None:
            self._aggregate_losses = numpy.zeros(len(hazard))

        loss_ratios = event_based._compute_loss_ratios(
            vulnerability_function, {"IMLs": hazard}, asset,
            self.seed, self.correlation_type, taxonomies)

        losses = loss_ratios * asset.value

        self._aggregate_losses += losses

        return output.ScenarioRiskOutput(asset, numpy.mean(losses),
                                         numpy.std(losses, ddof=1))

    @property
    def aggregate_losses(self):
        return self._aggregate_losses
