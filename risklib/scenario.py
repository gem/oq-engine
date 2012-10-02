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

from risklib.signals import EMPTY_CALLBACK
from risklib import event_based


def compute(sites, assets_getter,
            vulnerability_model,
            hazard_getter,
            compute_insured_losses,
            seed, correlation_type,
            on_asset_complete=EMPTY_CALLBACK):

    taxonomies = vulnerability_model.keys()

    aggregate_losses = None

    for site in sites:
        assets = assets_getter(site)

        ground_motion_values = hazard_getter(site)

        if aggregate_losses is None:
            aggregate_losses = numpy.zeros(len(ground_motion_values))

        for asset in assets:
            vulnerability_function = vulnerability_model[asset.taxonomy]

            loss_ratios = event_based._compute_loss_ratios(
                vulnerability_function, {'IMLs': ground_motion_values},
                asset,
                seed, correlation_type, taxonomies)
            losses = loss_ratios * asset.value

            if compute_insured_losses:
                losses = event_based._compute_insured_losses(asset, losses)

            aggregate_losses += losses

            on_asset_complete(asset,
                              numpy.mean(losses),
                              numpy.std(losses, ddof=1))

    return aggregate_losses
