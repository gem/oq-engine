# -*- coding: utf-8 -*-

# Copyright (c) 2013, GEM Foundation.
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

"""DB writing functionality for Risk calculators."""

import itertools
from openquake.risklib import scientific
from openquake.engine.db import models


def loss_map(loss_map_id, assets, losses, std_devs=None, absolute=False):
    """
    Create :class:`openquake.engine.db.models.LossMapData`

    :param int loss_map_id:
        The ID of the output container.
    :param list assets:
        A list of instances of :class:`openquake.engine.db.models.ExposureData`
    :param loss:
        Loss values to be written.
    :param float std_devs:
        Standard devations on each loss.
    :param absolute:
        False if the provided losses are loss ratios
    """

    for i, asset in enumerate(assets):
        loss = losses[i]
        if std_devs is not None:
            std_dev = std_devs[i]
        else:
            std_dev = None

        if not absolute:
            loss *= asset.value
            if std_devs is not None:
                std_dev *= asset.value

        models.LossMapData.objects.create(
            loss_map_id=loss_map_id,
            asset_ref=asset.asset_ref,
            value=loss,
            std_dev=std_dev,
            location=asset.site)


def bcr_distribution(bcr_distribution_id, assets, bcr_data):
    """
    Create a new :class:`openquake.engine.db.models.BCRDistributionData` from
    `asset_output` and links it to the output container identified by
    `bcr_distribution_id`.

    :param int bcr_distribution_id:
        The ID of :class:`openquake.engine.db.models.BCRDistribution` instance
        that holds the BCR map.

    :param assets:
        A list of instance of :class:`openquake.engine.db.models.ExposureData`

    :param tuple bcr_data: a 3-tuple with
      1) eal_original: expected annual loss in the original model
      2) eal_retrofitted: expected annual loss in the retrofitted model
      3) bcr: Benefit Cost Ratio parameter.
    """
    for asset, (eal_original, eal_retrofitted, bcr) in zip(assets, bcr_data):
        models.BCRDistributionData.objects.create(
            bcr_distribution_id=bcr_distribution_id,
            asset_ref=asset.asset_ref,
            average_annual_loss_original=eal_original * asset.value,
            average_annual_loss_retrofitted=eal_retrofitted * asset.value,
            bcr=bcr,
            location=asset.site)


def loss_curve(loss_curve_id, assets, curves):
    """
    Stores and returns a :class:`openquake.engine.db.models.LossCurveData`
    where the data are got by `asset_output` and the
    :class:`openquake.engine.db.models.LossCurve` output container is
    identified by `loss_curve_id`.

    :param int loss_curve_id:
        The ID of the output container.
    :param asset:
        An instance of :class:`openquake.engine.db.models.ExposureData`.
    :param loss_ratios:
        A list of loss ratios.
    :param poes:
        A list of poes associated to `loss_ratios`.
    :param float average_loss_ratio:
        The average loss ratio of the curve.
    """

    for asset, (losses, poes) in itertools.izip(assets, curves):
        models.LossCurveData.objects.create(
            loss_curve_id=loss_curve_id,
            asset_ref=asset.asset_ref,
            location=asset.site,
            poes=poes,
            loss_ratios=losses,
            asset_value=asset.value,
            average_loss_ratio=scientific.average_loss(losses, poes))


def loss_fraction(loss_fraction_id, assets, values, fractions):
    """
    Create, save and return an instance of
    :class:`openquake.engine.db.models.LossFractionData` associated
    with `loss_fraction_id`, `value`, `location` and `absolute_loss`
    :param int loss_fraction_id:
       an ID to an output container instance
       of type :class:`openquake.engine.db.models.LossFraction
    :param list values:
       A list of value representing the fraction. In case of
       disaggregation by taxonomy it is a taxonomy string.
    :param assets: the assets, the fractions refer to
    :param absolute_losses:
       the absolute loss contributions of `values` in `assets`
    """
    for asset, value, fraction in zip(assets, values, fractions):
        models.LossFractionData.objects.create(
            loss_fraction_id=loss_fraction_id,
            value=value,
            location=asset.site,
            absolute_loss=fraction * asset.value)


###
### Damage Distributions
###

def damage_distribution(assets, fraction_matrix, dmg_state_ids):
    """
    Save the damage distribution for a given asset.
    :param assets:
       a list of ExposureData instances
    :param fraction_matrix:
       numpy array with the damage fractions for each asset
    :param dmg_state_ids:
       a list of  IDs of instances of
       :class:`openquake.engine.db.models.DmgState` ordered by `lsi`
    """
    for fractions, asset in zip(fraction_matrix, assets):
        fractions *= asset.number_of_units
        means, stds = scientific.mean_std(fractions)

        for mean, std, dmg_state_id in zip(means, stds, dmg_state_ids):
            models.DmgDistPerAsset.objects.create(
                dmg_state_id=dmg_state_id,
                mean=mean, stddev=std, exposure_data=asset)


def damage_distribution_per_taxonomy(fractions, dmg_state_ids, taxonomy):
    """
    Save the damage distribution for a given taxonomy, by summing over
    all assets.

    :param fractions: numpy array with the damage fractions
    :param dmg_state_ids:
       a list of  IDs of instances of
       :class:`openquake.engine.db.models.DmgState` ordered by `lsi`
    :param str: the taxonomy string
    """
    means, stddevs = scientific.mean_std(fractions)
    for dmg_state_id, mean, stddev in zip(dmg_state_ids, means, stddevs):
        models.DmgDistPerTaxonomy.objects.create(
            dmg_state_id=dmg_state_id,
            mean=mean, stddev=stddev, taxonomy=taxonomy)


def total_damage_distribution(fractions, dmg_state_ids):
    """
    Save the total distribution, by summing over all assets and taxonomies.

    :param fractions: numpy array with the damage fractions
    :param dmg_state_ids:
       a list of  IDs of instances of
       :class:`openquake.engine.db.models.DmgState` ordered by `lsi`
    """
    means, stds = scientific.mean_std(fractions)
    for mean, std, dmg_state in zip(means, stds, dmg_state_ids):
        models.DmgDistTotal.objects.create(
            dmg_state_id=dmg_state, mean=mean, stddev=std)
