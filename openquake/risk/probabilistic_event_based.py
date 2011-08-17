# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
This module defines functions used to compute loss ratio and loss curves
using the probabilistic event based approach.
"""

import json
import math

from numpy import zeros, array, linspace
from numpy import histogram, where, mean

from openquake import kvs, shapes
from openquake.parser import vulnerability
from openquake.logs import LOG
from openquake.risk.common import collect, loop

DEFAULT_NUMBER_OF_SAMPLES = 25


def compute_loss_ratios(vuln_function, ground_motion_field_set,
        epsilon_provider, asset):
    """Compute the set of loss ratios using the set of
    ground motion fields passed.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - Time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    if vuln_function.is_empty:
        return array([])

    all_covs_are_zero = (vuln_function.covs <= 0.0).all()

    if all_covs_are_zero:
        return _mean_based(vuln_function, ground_motion_field_set)
    else:
        return _sampled_based(vuln_function, ground_motion_field_set,
                epsilon_provider, asset)


def _sampled_based(vuln_function, ground_motion_field_set,
        epsilon_provider, asset):
    """Compute the set of loss ratios when at least one CV
    (Coefficent of Variation) defined in the vulnerability function
    is greater than zero.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - Time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    loss_ratios = []

    means = vuln_function.loss_ratio_for(ground_motion_field_set["IMLs"])
    covs = vuln_function.cov_for(ground_motion_field_set["IMLs"])

    for mean_ratio, cov in zip(means, covs):
        if mean_ratio <= 0.0:
            loss_ratios.append(0.0)
        else:
            variance = (mean_ratio * cov) ** 2.0

            epsilon = epsilon_provider.epsilon(asset)
            sigma = math.sqrt(
                        math.log((variance / mean_ratio ** 2.0) + 1.0))

            mu = math.log(mean_ratio ** 2.0 / math.sqrt(
                    variance + mean_ratio ** 2.0))

            loss_ratios.append(math.exp(mu + (epsilon * sigma)))

    return array(loss_ratios)


def _mean_based(vuln_function, ground_motion_field_set):
    """Compute the set of loss ratios when the vulnerability function
    has all the CVs (Coefficent of Variation) set to zero.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - Time representative of the Stochastic Event Set (float)
    """

    loss_ratios = []
    retrieved = {}
    imls = vuln_function.imls

    # seems like with numpy you can only specify a single fill value
    # if the x_new is outside the range. Here we need two different values,
    # depending if the x_new is below or upon the defined values
    for ground_motion_field in ground_motion_field_set["IMLs"]:
        if ground_motion_field < imls[0]:
            loss_ratios.append(0.0)
        elif ground_motion_field > imls[-1]:
            loss_ratios.append(vuln_function.loss_ratios[-1])
        else:
            # The actual value is computed later
            mark = len(loss_ratios)
            retrieved[mark] = ground_motion_field_set['IMLs'][mark]
            loss_ratios.append(0.0)

    means = vuln_function.loss_ratio_for(retrieved.values())

    for mark, mean_ratio in zip(retrieved.keys(), means):
        loss_ratios[mark] = mean_ratio

    return array(loss_ratios)


def _compute_loss_ratios_range(loss_ratios, number_of_samples=None):
    """Compute the range of loss ratios used to build the loss ratio curve.

    The range is obtained by computing the set of evenly spaced numbers
    over the interval [min_loss_ratio, max_loss_ratio].

    :param loss_ratios: the set of loss ratios used.
    :type loss_ratios: numpy.ndarray
    :param number_of_samples: the number of samples used when computing
        the range of loss ratios. The default value is
        :py:data:`.DEFAULT_NUMBER_OF_SAMPLES`.
    :type number_of_samples: integer
    """

    if number_of_samples is None:
        number_of_samples = DEFAULT_NUMBER_OF_SAMPLES

    return linspace(loss_ratios.min(), loss_ratios.max(), number_of_samples)


def _compute_cumulative_histogram(loss_ratios, loss_ratios_range):
    "Compute the cumulative histogram."

    # ruptures (earthquake) occured but probably due to distance,
    # magnitude and soil conditions, no ground motion was felt at that location
    if (loss_ratios <= 0.0).all():
        return zeros(loss_ratios_range.size - 1)

    invalid_ratios = lambda ratios: where(array(ratios) <= 0.0)[0].size

    hist = histogram(loss_ratios, bins=loss_ratios_range)
    hist = hist[0][::-1].cumsum()[::-1]

    # ratios with value 0.0 must be deleted on the first bin
    hist[0] = hist[0] - invalid_ratios(loss_ratios)
    return hist


def _compute_rates_of_exceedance(cum_histogram, tses):
    """Compute the rates of exceedance for the given cumulative histogram
    using the given tses (tses is time span * number of realizations)."""

    if tses <= 0:
        raise ValueError("TSES is not supposed to be less than zero!")

    return (array(cum_histogram).astype(float) / tses)


def _compute_probs_of_exceedance(rates_of_exceedance, time_span):
    """Compute the probabilities of exceedance using the given rates of
    exceedance and the given time span."""

    poe = lambda rate: 1 - math.exp((rate * -1) * time_span)
    return array([poe(rate) for rate in rates_of_exceedance])


def compute_loss_ratio_curve(vuln_function, ground_motion_field_set,
        epsilon_provider, asset, number_of_samples=None):
    """Compute a loss ratio curve using the probabilistic event based approach.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - Time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    :param number_of_samples: the number of samples used when computing
        the range of loss ratios. The default value is
        :py:data:`.DEFAULT_NUMBER_OF_SAMPLES`.
    :type number_of_samples: integer
    """

    # with no gmfs (no earthquakes), an empty curve is enough
    if not ground_motion_field_set["IMLs"]:
        return shapes.EMPTY_CURVE

    loss_ratios = compute_loss_ratios(vuln_function,
            ground_motion_field_set, epsilon_provider, asset)

    loss_ratios_range = _compute_loss_ratios_range(
            loss_ratios, number_of_samples)

    probs_of_exceedance = _compute_probs_of_exceedance(
            _compute_rates_of_exceedance(_compute_cumulative_histogram(
            loss_ratios, loss_ratios_range), ground_motion_field_set["TSES"]),
            ground_motion_field_set["TimeSpan"])

    return _generate_curve(loss_ratios_range, probs_of_exceedance)


def _generate_curve(losses, probs_of_exceedance):
    """Generate a loss ratio (or loss) curve, given a set of losses
    and corresponding PoEs (Probabilities of Exceedance).

    This function is intended to be used internally.
    """

    mean_losses = collect(loop(losses, lambda x, y: mean([x, y])))
    return shapes.Curve(zip(mean_losses, probs_of_exceedance))


def _assets_keys_for_gmfs(job_id, gmfs_key):
    """Return the asset related to the GMFs given."""

    column, row = kvs.tokens.column_row_from_gmf_set_key(gmfs_key)

    key = kvs.tokens.asset_key(job_id, row, column)

    return kvs.get_client().lrange(key, 0, -1)


class AggregateLossCurve(object):
    """Aggregate a set of losses and produce the resulting loss curve."""

    @staticmethod
    def from_kvs(job_id, epsilon_provider):
        """Return an aggregate curve using the GMFs and assets
        stored in the underlying kvs system."""

        vuln_model = vulnerability.load_vuln_model_from_kvs(job_id)
        aggregate_curve = AggregateLossCurve(vuln_model, epsilon_provider)

        gmfs_keys = kvs.get_keys("%s*%s*" % (
                kvs.tokens.generate_job_key(job_id), kvs.tokens.GMF_KEY_TOKEN))

        LOG.debug("Found %s stored GMFs..." % len(gmfs_keys))
        asset_counter = 0

        for gmfs_key in gmfs_keys:
            assets = _assets_keys_for_gmfs(job_id, gmfs_key)

            for asset in assets:
                asset_counter += 1
                gmfs = kvs.get_value_json_decoded(gmfs_key)

                aggregate_curve.append(gmfs,
                        json.JSONDecoder().decode(asset))

        LOG.debug("Found %s stored assets..." % asset_counter)
        return aggregate_curve

    def __init__(self, vuln_model, epsilon_provider):
        self._tses = self._time_span = self._gmfs_length = None

        self.distribution = []
        self.vuln_model = vuln_model
        self.epsilon_provider = epsilon_provider

    def append(self, gmfs, asset):
        """Add the losses distribution identified by the given GMFs
        and asset to the set used to compute the aggregate curve."""

        if self.empty:
            self._initialize_parameters(gmfs)

        assert gmfs["TimeSpan"] == self._time_span
        assert gmfs["TSES"] == self._tses
        assert len(gmfs["IMLs"]) == self._gmfs_length

        if asset["vulnerabilityFunctionReference"] in self.vuln_model:
            loss_ratios = compute_loss_ratios(self.vuln_model[
                    asset["vulnerabilityFunctionReference"]], gmfs,
                    self.epsilon_provider, asset)

            self.distribution.append(loss_ratios * asset["assetValue"])
        else:
            LOG.debug("Unknown vulnerability function %s, asset %s will " \
                    "not be included in the aggregate computation"
                    % (asset["vulnerabilityFunctionReference"],
                    asset["assetID"]))

    def _initialize_parameters(self, gmfs):
        """Initialize the GMFs parameters."""
        self._tses = gmfs["TSES"]
        self._time_span = gmfs["TimeSpan"]
        self._gmfs_length = len(gmfs["IMLs"])

    @property
    def empty(self):
        """Return true is this aggregate curve has no losses
        associated, false otherwise."""
        return len(self.distribution) == 0

    @property
    def losses(self):
        """Return the losses used to compute the aggregate curve."""
        if self.empty:
            return array([])
        else:  # if needed because numpy returns a scalar if the list is empty
            return array(self.distribution).sum(axis=0)

    def compute(self, number_of_samples=None):
        """Compute the aggregate loss curve."""

        if self.empty:
            return shapes.EMPTY_CURVE

        losses = self.losses
        loss_range = _compute_loss_ratios_range(losses, number_of_samples)

        probs_of_exceedance = _compute_probs_of_exceedance(
                _compute_rates_of_exceedance(_compute_cumulative_histogram(
                losses, loss_range), self._tses), self._time_span)

        return _generate_curve(loss_range, probs_of_exceedance)
