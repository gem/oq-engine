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
    _loss_ratio_exceedance_matrix,
    _loss_ratio_curve, _loss_curve)


def compute(sites, assets_getter,
            vulnerability_model, vulnerability_model_retrofitted,
            hazard_curve_getter, steps,
            interest_rate, asset_life_expectancy,
            on_asset_complete=EMPTY_CALLBACK):

    loss_ratio_exceedance_matrices = dict(
        [(taxonomy, _loss_ratio_exceedance_matrix(
            vulnerability_function, steps))
         for taxonomy, vulnerability_function in vulnerability_model.items()])

    loss_ratio_exceedance_retrofitted_matrices = dict(
        [(taxonomy, _loss_ratio_exceedance_matrix(
            vulnerability_function, steps))
         for taxonomy, vulnerability_function
         in vulnerability_model_retrofitted.items()])

    for site in sites:
        assets = assets_getter(site)

        hazard_curve = hazard_curve_getter(site)

        for asset in assets:
            eal_original = _expected_annual_loss(asset, vulnerability_model,
                                        loss_ratio_exceedance_matrices,
                                        hazard_curve, steps)
            eal_retrofitted = _expected_annual_loss(
                asset, vulnerability_model_retrofitted,
                loss_ratio_exceedance_retrofitted_matrices,
                hazard_curve, steps)
            bcr = _bcr(eal_original, eal_retrofitted,
                       interest_rate, asset_life_expectancy,
                       asset.retrofitting_cost)
            on_asset_complete(asset, bcr, eal_original, eal_retrofitted)


def _expected_annual_loss(
        asset, vulnerability_model, loss_ratio_exceedance_matrices,
                 hazard_curve, steps):
    vulnerability_function = vulnerability_model[asset.taxonomy]
    loss_ratio_curve = _loss_ratio_curve(
        vulnerability_function,
        loss_ratio_exceedance_matrices[asset.taxonomy],
        hazard_curve, steps)
    loss_curve = _loss_curve(loss_ratio_curve, asset.value)
    return _mean_loss(loss_curve)


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


def _mean_loss(curve):
    """Compute the mean loss (or loss ratio) for the given curve."""

    mid_curve = _mean_loss_ratio_curve(curve)
    return sum(i * j for i, j in zip(
            mid_curve.abscissae, mid_curve.ordinates))


def _mean_loss_ratio_curve(loss_ratio_curve):
    """Compute a loss ratio curve that has PoOs
    (Probabilities of Occurrence) as Y values."""

    loss_ratios = loss_ratio_curve.abscissae
    pes = loss_ratio_curve.ordinates

    ratios = [numpy.mean([x, y])
              for x, y in zip(loss_ratios, loss_ratios[1:])]
    mid_pes = [numpy.mean([x, y])
              for x, y in zip(pes, pes[1:])]

    loss_ratio_pe_mid_curve = Curve(zip(ratios, mid_pes))

    loss_ratios = loss_ratio_pe_mid_curve.abscissae
    pes = loss_ratio_pe_mid_curve.ordinates

    ratios = [numpy.mean([x, y])
              for x, y in zip(loss_ratios, loss_ratios[1:])]

    pos = [x - y for x, y in zip(pes, pes[1:])]

    return Curve(zip(ratios, pos))
