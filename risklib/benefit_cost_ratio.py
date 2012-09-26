# -*- coding: utf-8 -*-

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
from math import exp

from risklib.curve import Curve
from risklib.signals import EMPTY_CALLBACK
from risklib.classical import (
    compute_lrem, compute_loss_ratio_curve, compute_loss_curve)


def compute_benefit_cost_ratio(sites, assets_getter,
                vulnerability_model, vulnerability_model_retrofitted,
                hazard_curve_getter, steps,
                interest_rate, asset_life_expectancy,
                on_asset_complete=EMPTY_CALLBACK):

    loss_ratio_exceedance_matrices = dict(
        [(taxonomy, compute_lrem(vulnerability_function, steps))
         for taxonomy, vulnerability_function in vulnerability_model.items()])

    loss_ratio_exceedance_retrofitted_matrices = dict(
        [(taxonomy, compute_lrem(vulnerability_function, steps))
         for taxonomy, vulnerability_function
         in vulnerability_model_retrofitted.items()])

    for site in sites:
        assets = assets_getter(site)

        hazard_curve = hazard_curve_getter(site)

        for asset in assets:
            eal_original = _compute_eal(asset, vulnerability_model,
                                        loss_ratio_exceedance_matrices,
                                        hazard_curve, steps)
            eal_retrofitted = _compute_eal(
                asset, vulnerability_model_retrofitted,
                loss_ratio_exceedance_retrofitted_matrices,
                hazard_curve, steps)
            bcr = _bcr(eal_original, eal_retrofitted,
                       interest_rate, asset_life_expectancy,
                       asset.retrofitting_cost)
            on_asset_complete(asset, bcr, eal_original, eal_retrofitted)


def _compute_eal(asset, vulnerability_model, loss_ratio_exceedance_matrices,
                 hazard_curve, steps):
    vulnerability_function = vulnerability_model[asset.taxonomy]
    loss_ratio_curve = compute_loss_ratio_curve(
        vulnerability_function,
        loss_ratio_exceedance_matrices[asset.taxonomy],
        hazard_curve, steps)
    loss_curve = compute_loss_curve(loss_ratio_curve, asset.value)
    return _compute_mean_loss(loss_curve)


def _bcr(eal_original, eal_retrofitted, interest_rate,
                asset_life_expectancy, retrofitting_cost):
    """
    Compute the Benefit-Cost Ratio.

    BCR = (EALo - EALr)(1-exp(-r*t))/(r*C)

    Where:

    * BCR -- Benefit cost ratio
    * EALo -- Expected annual loss for original asset
    * EALr -- Expected annual loss for retrofitted asset
    * r -- Interest rate
    * t -- Life expectancy of the asset
    * C -- Retrofitting cost
    """
    return ((eal_original - eal_retrofitted)
            * (1 - exp(- interest_rate * asset_life_expectancy))
            / (interest_rate * retrofitting_cost))


def _compute_mean_loss(curve):
    """Compute the mean loss (or loss ratio) for the given curve."""

    mid_curve = _compute_mid_po(_compute_mid_mean_pe(curve))
    return sum(i * j for i, j in zip(
            mid_curve.abscissae, mid_curve.ordinates))


def _compute_mid_po(loss_ratio_pe_mid_curve):
    """Compute a loss ratio curve that has PoOs
    (Probabilities of Occurrence) as Y values."""

    loss_ratios = loss_ratio_pe_mid_curve.abscissae
    pes = loss_ratio_pe_mid_curve.ordinates

    ratios = [numpy.mean([x, y])
              for x, y in zip(loss_ratios, loss_ratios[1:])]

    pos = [x - y for x, y in zip(pes, pes[1:])]

    return Curve(zip(ratios, pos))


def _compute_mid_mean_pe(loss_ratio_curve):
    """Compute a new loss ratio curve taking the mean values."""

    loss_ratios = loss_ratio_curve.abscissae
    pes = loss_ratio_curve.ordinates

    ratios = [numpy.mean([x, y])
              for x, y in zip(loss_ratios, loss_ratios[1:])]
    mid_pes = [numpy.mean([x, y])
              for x, y in zip(pes, pes[1:])]

    return Curve(zip(ratios, mid_pes))
