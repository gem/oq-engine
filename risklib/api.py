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

from risklib.models import output
from risklib import classical as classical_functions
from risklib import event_based as event_based_functions
from risklib import benefit_cost_ratio as bcr_functions
from risklib import scenario_damage as scenario_damage_functions
from risklib import insured_loss as insured_loss_functions


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
        self.matrices = dict([(taxonomy,
        classical_functions._loss_ratio_exceedance_matrix(
        vulnerability_function, steps))
        for taxonomy, vulnerability_function in vulnerability_model.items()])

    def __call__(self, asset, hazard):
        vulnerability_function = self.vulnerability_model[asset.taxonomy]

        loss_ratio_curve = classical_functions._loss_ratio_curve(
            vulnerability_function, self.matrices[asset.taxonomy],
            hazard, self.steps)

        loss_curve = classical_functions._loss_curve(
            loss_ratio_curve, asset.value)

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
            scenario_damage_functions._damage_distribution_per_asset(asset,
            (self.fragility_model, self.fragility_functions[taxonomy]),
            hazard))

        collapse_map = scenario_damage_functions._collapse_map(fractions)

        asset_fractions = self._fractions_per_taxonomy.get(taxonomy,
            scenario_damage_functions._make_damage_distribution_matrix(
            self.fragility_model, hazard))

        self._fractions_per_taxonomy[taxonomy] = asset_fractions + fractions
        return output.ScenarioDamageOutput(
            asset, damage_distribution_asset, collapse_map)

    @property
    def damage_distribution_by_taxonomy(self):
        return self._fractions_per_taxonomy


def conditional_losses(conditional_loss_poes, loss_curve_calculator):
    """
    Compute the conditional losses for each Probability
    of Exceedance given as input.
    """

    def conditional_losses_wrapped(asset, hazard):
        asset_output = loss_curve_calculator(asset, hazard)

        return asset_output._replace(
            conditional_losses=classical_functions._conditional_losses(
            asset_output.loss_curve, conditional_loss_poes))

    return conditional_losses_wrapped


def bcr(loss_curve_calculator_original, loss_curve_calculator_retrofitted,
    interest_rate, asset_life_expectancy):
    """
    Compute the Benefit Cost Ratio. For each asset, it produces:
        * the benefit cost ratio
        * the expected annual loss
        * the expect annual loss retrofitted
    """

    def bcr_wrapped(asset, hazard):
        expected_annual_loss_original = bcr_functions.mean_loss(
            loss_curve_calculator_original(asset, hazard).loss_curve)

        expected_annual_loss_retrofitted = bcr_functions.mean_loss(
            loss_curve_calculator_retrofitted(asset, hazard).loss_curve)

        bcr = bcr_functions.bcr(expected_annual_loss_original,
            expected_annual_loss_retrofitted, interest_rate,
            asset_life_expectancy, asset.retrofitting_cost)

        return output.BCROutput(
            asset, bcr, expected_annual_loss_original,
            expected_annual_loss_retrofitted)

    return bcr_wrapped


class ProbabilisticEventBased(object):
    """
    Probabilistic event based calculator. For each asset it produces:
        * a set of losses
        * a loss ratio curve
        * a loss curve

    It also produces the following aggregate results:
        * aggregate loss curve
    """

    def __init__(self, vulnerability_model, loss_histogram_bins,
        seed, correlation_type):

        self.seed = seed
        self.correlation_type = correlation_type
        self.vulnerability_model = vulnerability_model
        self.loss_histogram_bins = loss_histogram_bins

        self._aggregate_losses = None

    def __call__(self, asset, hazard):
        taxonomies = self.vulnerability_model.keys()
        vulnerability_function = self.vulnerability_model[asset.taxonomy]

        if self._aggregate_losses is None:
            self._aggregate_losses = numpy.zeros(len(hazard["IMLs"]))

        loss_ratios = event_based_functions._compute_loss_ratios(
            vulnerability_function, hazard, asset, self.seed,
            self.correlation_type, taxonomies)

        loss_ratio_curve = event_based_functions.compute_loss_ratio_curve(
            vulnerability_function, hazard, asset, self.loss_histogram_bins,
            loss_ratios, self.seed, self.correlation_type, taxonomies)

        losses = loss_ratios * asset.value
        loss_curve = loss_ratio_curve.rescale_abscissae(asset.value)

        self._aggregate_losses += losses

        return output.ProbabilisticEventBasedOutput(asset, losses,
            loss_ratio_curve, loss_curve, None, None, None, None)

    @property
    def aggregate_losses(self):
        return self._aggregate_losses


def insured_losses(losses_calculator):
    """
    Insured losses calculator.
    """

    def insured_losses_wrapped(asset, hazard):
        asset_output = losses_calculator(asset, hazard)

        return asset_output._replace(
            insured_losses=insured_loss_functions.compute_insured_losses(
            asset, asset_output.losses))

    return insured_losses_wrapped


def insured_curves(vulnerability_model, loss_histogram_bins, seed,
    correlation_type, insured_losses_calculator):
    """
    Insured (loss ratio / loss) curves calculator.
    """

    def insured_curves_wrapped(asset, hazard):
        taxonomies = vulnerability_model.keys()
        asset_output = insured_losses_calculator(asset, hazard)
        vulnerability_function = vulnerability_model[asset.taxonomy]

        insured_loss_ratio_curve = (
            event_based_functions.compute_loss_ratio_curve(
                vulnerability_function, hazard, asset, loss_histogram_bins,
                loss_ratios=asset_output.insured_losses, seed=seed,
                correlation_type=correlation_type, taxonomies=taxonomies))

        insured_loss_ratio_curve.x_values = (
            insured_loss_ratio_curve.x_values / asset.value)

        insured_loss_curve = (
            insured_loss_ratio_curve.rescale_abscissae(asset.value))

        return asset_output._replace(
            insured_loss_ratio_curve=insured_loss_ratio_curve,
            insured_loss_curve=insured_loss_curve)

    return insured_curves_wrapped


class ScenarioRisk(object):
    """
    Scenario risk calculator. For each asset it produces:
        * mean / standard deviation of asset losses

    It also produces the following aggregate results:
        * aggregate losses
    """

    def __init__(self, vulnerability_model, seed,
        correlation_type, insured=False):

        self.seed = seed
        self.insured = insured
        self.correlation_type = correlation_type
        self.vulnerability_model = vulnerability_model

        self._aggregate_losses = None

    def __call__(self, asset, hazard):
        taxonomies = self.vulnerability_model.keys()
        vulnerability_function = self.vulnerability_model[asset.taxonomy]

        if self._aggregate_losses is None:
            self._aggregate_losses = numpy.zeros(len(hazard))

        loss_ratios = event_based_functions._compute_loss_ratios(
            vulnerability_function, {"IMLs": hazard}, asset,
            self.seed, self.correlation_type, taxonomies)

        losses = loss_ratios * asset.value

        if self.insured:
            losses = insured_loss_functions.compute_insured_losses(
                asset, losses)

        self._aggregate_losses += losses

        return output.ScenarioRiskOutput(asset, numpy.mean(losses),
            numpy.std(losses, ddof=1))

    @property
    def aggregate_losses(self):
        return self._aggregate_losses
