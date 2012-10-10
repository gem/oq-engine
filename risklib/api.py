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

from risklib import classical as classical_functions


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
    represented, because they are just passed to the client implementation
    of the assets and hazard getters to load the related inputs.

    :param sites: the set of sites where to trigger the computation on
    :type sites: an `iterator` over a collection of sites. No constraints
        are needed for the type of a single site
    :param assets_getter: the logic used to lookup the assets defined
        on a single geographical site
    :type assets_getter: `callable` that accepts as single parameter a
        geographical site and returns a set of `risklib.models.Asset`
    :param hazard_getter: the logic used to lookup the hazard defined
        on a single geographical site
    :type hazard_getter: `callable` that accepts as single parameter a
        geographical site and returns the hazard input for that site.
        The format of the hazard input depends on the type of calculator
        chosen and it is documented in detail in each calculator
    :param calculator: a specific calculator (classical, probabilistic
        event based, benefit cost ratio, scenario risk, scenario damage)
    :type calculator: `callable` that accepts as first parameter an
        instance of `risklib.models.Asset` and as second parameter the
        hazard input. It returns an instance of `risklib.api.AssetOutput`
        with the results of the computation for the given asset
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
    :type assets: an `iterator` over a collection of `risklib.models.Asset`
    :param hazard_getter: the logic used to lookup the hazard defined
        on a single geographical site
    :type hazard_getter: `callable` that accepts as single parameter a
        geographical site and returns the hazard input for that site.
        The format of the hazard input depends on the type of calculator
        chosen and it is documented in detail in each calculator
    :param calculator: a specific calculator (classical, probabilistic
        event based, benefit cost ratio, scenario risk, scenario damage)
    :type calculator: `callable` that accepts as first parameter an
        instance of `risklib.models.Asset` and as second parameter the
        hazard input. It returns an instance of `risklib.api.AssetOutput`
        with the results of the computation for the given asset
    """

    for asset in assets:
        hazard = hazard_getter(asset.site)
        yield calculator(asset, hazard)


def classical(vulnerability_model, steps=10):
    """
    Classical calculator. For each asset it produces:
        * a loss curve
        * a loss ratio curve
        * a set of conditional losses
    """

    matrices = dict([(taxonomy,
        classical_functions._loss_ratio_exceedance_matrix(
        vulnerability_function, steps))
        for taxonomy, vulnerability_function in vulnerability_model.items()])

    def wrapped(asset, hazard):
        vulnerability_function = vulnerability_model[asset.taxonomy]

        loss_ratio_curve = classical_functions._loss_ratio_curve(
            vulnerability_function, matrices[asset.taxonomy], hazard, steps)

        loss_curve = classical_functions._loss_curve(
            loss_ratio_curve, asset.value)

        asset_output = AssetOutput()

        asset_output.asset = asset
        asset_output.loss_curve = loss_curve
        asset_output.loss_ratio_curve = loss_ratio_curve

        return asset_output

    return wrapped


def conditional_losses(conditional_loss_poes, function):
    """
    Compute the conditional losses for each Probability
    of Exceedance given as input.
    """

    def wrapped(asset, hazard):
        asset_output = function(asset, hazard)

        conditional_losses = classical_functions._conditional_losses(
            asset_output.loss_curve, conditional_loss_poes)

        asset_output.conditional_losses = conditional_losses

        return asset_output

    return wrapped


class AssetOutput(object): pass
