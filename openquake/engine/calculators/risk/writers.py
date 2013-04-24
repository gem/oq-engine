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

import numpy
from scipy import interpolate
from openquake.risklib import scientific

from openquake.engine import logs
from openquake.engine.calculators import post_processing
from openquake.engine.db import models


def loss_map_data(loss_map_id, asset, loss_ratio, std_dev=None):
    """
    Create :class:`openquake.engine.db.models.LossMapData`

    :param int loss_map_id:
        The ID of the output container.
    :param asset:
        An instance of :class:`openquake.engine.db.models.ExposureData`.
    :param float value:
        Loss ratio value.
    :param float std_dev:
        Standard devation on loss ratios.
    """

    if std_dev is not None:
        std_dev = std_dev * asset.value

    return models.LossMapData.objects.create(
        loss_map_id=loss_map_id,
        asset_ref=asset.asset_ref,
        value=loss_ratio * asset.value,
        std_dev=std_dev,
        location=asset.site)


def bcr_distribution(
        bcr_distribution_id, asset, eal_original, eal_retrofitted, bcr):
    """
    Create a new :class:`openquake.engine.db.models.BCRDistributionData` from
    `asset_output` and links it to the output container identified by
    `bcr_distribution_id`.

    :param int bcr_distribution_id:
        The ID of :class:`openquake.engine.db.models.BCRDistribution` instance
        that holds the BCR map.

    :param asset:
        An instance of :class:`openquake.engine.db.models.ExposureData`.

    :param float eal_original:
        Expected annual loss in the original model for the asset.
    :param float eal_retrofitted:
        Expected annual loss in the retrofitted model for the asset.
    :param float bcr:
        Benefit Cost Ratio parameter.
    """
    models.BCRDistributionData.objects.create(
        bcr_distribution_id=bcr_distribution_id,
        asset_ref=asset.asset_ref,
        average_annual_loss_original=eal_original * asset.value,
        average_annual_loss_retrofitted=eal_retrofitted * asset.value,
        bcr=bcr,
        location=asset.site)


def loss_curve(loss_curve_id, asset, poes, loss_ratios, average_loss_ratio):
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
    return models.LossCurveData.objects.create(
        loss_curve_id=loss_curve_id,
        asset_ref=asset.asset_ref,
        location=asset.site,
        poes=poes,
        loss_ratios=loss_ratios,
        asset_value=asset.value,
        average_loss_ratio=average_loss_ratio)


def curve_statistics(
        mean_loss_curve_id, quantile_loss_curve_ids,
        mean_loss_map_ids, quantile_loss_map_ids,
        mean_loss_fraction_ids, quantile_loss_fraction_ids,
        weights, assets, loss_ratio_curve_matrix, hazard_montecarlo_p,
        conditional_loss_poes, poes_disagg, assume_equal):
    """
    :param int mean_loss_curve_id:
      the ID of the mean loss curve output container
    :param dict quantile_loss_curve_id:
      it maps quantile values to IDs of quantile loss curve output containers
    :param dict mean_loss_map_id:
      it maps poes to IDs of mean loss map output containers
    :param dict quantile_loss_map_ids:
      it maps quantile values to dicts poe -> ID of loss map output container
    :param dict mean_loss_fraction_ids:
      it maps poes to IDs of mean loss fraction output containers
    :param dict quantile_loss_fraction_ids:
      it maps quantile values to dicts poe -> ID of loss fraction output
      containers
    :param weights:
      the weights of each realization considered
    :param assets:
      the assets on which we are computing the statistics
    :param loss_ratio_curve_matrix:
      a numpy 2d array that stores the individual loss curves for each asset
      in `assets`
    :param bool hazard_montecarlo_p:
      True when explicit mean/quantiles calculation is used
    :param list conditional_loss_poes:
      The poes taken into account to compute the loss maps
    :param list poes_disagg:
      The poes taken into account to compute the loss maps needed for
      disaggregation
    :param str assume_equal:
      equal to "support" if loss curves has the same abscissae, or "image" if
      they have the same ordinates
    """

    for i, asset in enumerate(assets):
        loss_ratio_curves = loss_ratio_curve_matrix[:, i]

        if assume_equal == 'support':
            loss_ratios = loss_ratio_curves[0].abscissae
            curves_poes = [curve.ordinates for curve in loss_ratio_curves]
        elif assume_equal == 'image':
            non_trivial_curves = [curve
                                  for curve in loss_ratio_curves
                                  if curve.abscissae[-1] > 0]
            if not non_trivial_curves:  # no damage. all trivial curves
                logs.LOG.info("No damages in asset %s" % asset)
                loss_ratios = loss_ratio_curves[0].abscissae
                curves_poes = [curve.ordinates for curve in loss_ratio_curves]
            else:  # standard case
                max_losses = [lc.abscissae[-1] for lc in non_trivial_curves]
                reference_curve = non_trivial_curves[numpy.argmax(max_losses)]
                loss_ratios = reference_curve.abscissae
                curves_poes = [interpolate.interp1d(
                    curve.abscissae, curve.ordinates,
                    bounds_error=False, fill_value=0)(loss_ratios)
                    for curve in loss_ratio_curves]
        else:
            raise NotImplementedError

        quantiles_poes = dict()

        for quantile, quantile_loss_curve_id in (
                quantile_loss_curve_ids.items()):
            if hazard_montecarlo_p:
                q_curve = post_processing.weighted_quantile_curve(
                    curves_poes, weights, quantile)
            else:
                q_curve = post_processing.quantile_curve(curves_poes, quantile)

            quantiles_poes[quantile] = q_curve.tolist()

            loss_curve(
                quantile_loss_curve_id,
                asset,
                quantiles_poes[quantile],
                loss_ratios,
                scientific.average_loss(loss_ratios, quantiles_poes[quantile]))

        # then mean loss curve
        mean_poes = None
        if mean_loss_curve_id:
            mean_curve = post_processing.mean_curve(curves_poes, weights)
            mean_poes = mean_curve.tolist()

            loss_curve(
                mean_loss_curve_id,
                asset,
                mean_poes,
                loss_ratios,
                scientific.average_loss(loss_ratios, mean_poes))

        # mean and quantile loss maps
        loss_ratios = loss_ratio_curve_matrix[0, 0].abscissae

        for poe in conditional_loss_poes:
            loss_map_data(
                mean_loss_map_ids[poe],
                asset,
                scientific.conditional_loss_ratio(loss_ratios, mean_poes, poe))
            for quantile, poes in quantiles_poes.items():
                loss_map_data(
                    quantile_loss_map_ids[quantile][poe],
                    asset,
                    scientific.conditional_loss_ratio(loss_ratios, poes, poe))

        # mean and quantile loss fractions (only disaggregation by
        # taxonomy is supported here)
        for poe in poes_disagg:
            loss_fraction_data(
                mean_loss_fraction_ids[poe],
                value=asset.taxonomy,
                location=asset.site,
                absolute_loss=scientific.conditional_loss_ratio(
                    loss_ratios, mean_poes, poe) * asset.value)
            for quantile, poes in quantiles_poes.items():
                loss_fraction_data(
                    quantile_loss_fraction_ids[quantile][poe],
                    value=asset.taxonomy,
                    location=asset.site,
                    absolute_loss=scientific.conditional_loss_ratio(
                        loss_ratios, poes, poe) * asset.value)


def loss_fraction_data(loss_fraction_id, value, location, absolute_loss):
    """
    Create, save and return an instance of
    :class:`openquake.engine.db.models.LossFractionData` associated
    with `loss_fraction_id`, `value`, `location` and `absolute_loss`
    :param int loss_fraction_id:
       an ID to an output container instance
       of type :class:`openquake.engine.db.models.LossFraction
    :param str value:
       A value representing the fraction. In case of disaggregation by taxonomy
       it is a taxonomy string.
    :param point location: the location, the fraction refers to
    :param float absolute_loss:
       the absolute loss contribution of `value` in `location`
    """

    return models.LossFractionData.objects.create(
        loss_fraction_id=loss_fraction_id,
        value=value,
        location=location,
        absolute_loss=absolute_loss)


###
### Damage Distributions
###

def damage_distribution_per_asset(fractions, rc_id, asset):
    """
    Save the damage distribution for a given asset.

    :param fractions: numpy array with the damage fractions
    :param rc_id: the risk_calculation_id
    :param asset: an ExposureData instance
    """
    dmg_states = models.DmgState.objects.filter(risk_calculation__id=rc_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddpa = models.DmgDistPerAsset(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi],
            exposure_data=asset)
        ddpa.save()


def damage_distribution_per_taxonomy(fractions, rc_id, taxonomy):
    """
    Save the damage distribution for a given taxonomy, by summing over
    all assets.

    :param fractions: numpy array with the damage fractions
    :param int rc_id: the risk_calculation_id
    :param str: the taxonomy string
    """
    dmg_states = models.DmgState.objects.filter(risk_calculation__id=rc_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddpt = models.DmgDistPerTaxonomy(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi],
            taxonomy=taxonomy)
        ddpt.save()


def total_damage_distribution(fractions, rc_id):
    """
    Save the total distribution, by summing over all assets and taxonomies.

    :param fractions: numpy array with the damage fractions
    :param int rc_id: the risk_calculation_id
    """
    dmg_states = models.DmgState.objects.filter(risk_calculation__id=rc_id)
    mean, std = scientific.mean_std(fractions)
    for dmg_state in dmg_states:
        lsi = dmg_state.lsi
        ddt = models.DmgDistTotal(
            dmg_state=dmg_state,
            mean=mean[lsi], stddev=std[lsi])
        ddt.save()
