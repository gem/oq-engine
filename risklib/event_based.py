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

import math
import numpy
import random

from risklib import curve
from risklib.signals import EMPTY_CALLBACK
from risklib import classical

UNCORRELATED, PERFECTLY_CORRELATED = range(0, 2)


def compute(sites, assets_getter,
            vulnerability_model,
            hazard_getter,
            loss_histogram_bins,
            conditional_loss_poes,
            compute_insured_curve,
            seed, correlation_type,
            on_asset_complete=EMPTY_CALLBACK):

    aggregate_losses = None

    taxonomies = vulnerability_model.keys()

    for site in sites:
        assets = assets_getter(site)

        # the dict contains IMLs, TSES, TimeSpan
        point, hazard_dict = hazard_getter(site)

        if aggregate_losses is None:
            aggregate_losses = numpy.zeros(len(hazard_dict["IMLs"]))

        for asset in assets:
            vulnerability_function = vulnerability_model[asset.taxonomy]

            loss_ratios = _compute_loss_ratios(
                vulnerability_function, hazard_dict,
                asset,
                seed, correlation_type, taxonomies)
            loss_ratio_curve = _compute_loss_ratio_curve(
                vulnerability_function, hazard_dict,
                asset,
                loss_histogram_bins, loss_ratios,
                seed, correlation_type, taxonomies)

            loss_curve = classical._loss_curve(loss_ratio_curve, asset.value)

            loss_conditionals = dict([
                (loss_poe, classical._conditional_loss(loss_curve, loss_poe))
                for loss_poe in conditional_loss_poes])

            if compute_insured_curve:
                insured_curve = _compute_insured_loss_curve(asset, loss_curve)
            else:
                insured_curve = None

            on_asset_complete(
                asset, point, loss_ratio_curve,
                loss_curve, loss_conditionals, insured_curve)

            aggregate_losses += loss_ratios * asset.value

    return aggregate_losses


def aggregate_loss_curve(set_of_losses, tses, time_span, histogram_bins):
    """
    Compute the aggregate loss curve obtained by summing the given
    set of losses.

    :param set_of_losses: the set of losses.
    :type set_of_losses: list of 1d `numpy.array`
    :param tses: time representative of the stochastic event set.
    :type tses: float
    :param time_span: time span in which the ground motion fields (used
        to generate the given set of losses) are generated.
    :type time_span: float
    :param histogram_bins: number of bins used when building the
        histogram of losses.
    :type histogram_bins: int
    :returns: the aggregate loss curve.
    :rtype: an instance of `risklib.curve.Curve`
    """

    losses = sum(set_of_losses)
    loss_ratios_range = _compute_loss_ratios_range(losses, histogram_bins)

    probs_of_exceedance = _compute_probs_of_exceedance(
        _compute_rates_of_exceedance(_compute_cumulative_histogram(
        losses, loss_ratios_range), tses), time_span)

    return _generate_curve(loss_ratios_range, probs_of_exceedance)


class EpsilonProvider(object):
    """
    Simple class for combining job configuration parameters and an `epsilon`
    method. See :py:meth:`EpsilonProvider.epsilon` for more information.
    """

    def __init__(self, seed=None,
                 correlation_type=UNCORRELATED, taxonomies=None):
        """
        :param params: configuration parameters from the job configuration
        :type params: dict
        """
        self._samples = dict()
        self._correlation_type = correlation_type or UNCORRELATED
        self._seed = seed
        self.rnd = None

        if correlation_type == PERFECTLY_CORRELATED:
            self._setup_rnd()
            for taxonomy in taxonomies:
                self._samples[taxonomy] = self._generate()

    def _setup_rnd(self):
        self.rnd = random.Random()
        if self._seed is not None:
            self.rnd.seed(int(self._seed))

    def _generate(self):
        if self.rnd is None:
            self._setup_rnd()

        return self.rnd.normalvariate(0, 1)

    def epsilon(self, asset):
        """Sample from the standard normal distribution for the given asset.

        For uncorrelated risk calculation jobs we sample the standard normal
        distribution for each asset.
        In the opposite case ("perfectly correlated" assets) we sample for each
        building typology i.e. two assets with the same typology will "share"
        the same standard normal distribution sample.

        Two assets are considered to be of the same building typology if their
        taxonomy is the same. The asset's `taxonomy` is only needed for
        correlated jobs and unlikely to be available for uncorrelated ones.
        """

        if self._correlation_type == UNCORRELATED:
            return self._generate()
        elif self._correlation_type == PERFECTLY_CORRELATED:
            return self._samples[asset.taxonomy]
        else:
            raise ValueError('Invalid "ASSET_CORRELATION": %s' %
                             self._correlation_type)


def _compute_loss_ratios(vuln_function, gmf_set,
                         asset,
                         seed=None,
                         correlation_type=None,
                         taxonomies=None):
    """Compute the set of loss ratios using the set of
    ground motion fields passed.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: ground motion fields used to compute the loss ratios
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - time representative of the Stochastic Event Set (float)
    :param seed:
      the seed used for the rnd generator
    :param correlation_type
      UNCORRELATED or PERFECTLY_CORRELATED
    :param taxonomies
      a list of considered taxonomies
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    if vuln_function.is_empty:
        return numpy.array([])

    all_covs_are_zero = (vuln_function.covs <= 0.0).all()

    if all_covs_are_zero:
        return _mean_based(vuln_function, gmf_set)
    else:
        epsilon_provider = EpsilonProvider(seed, correlation_type, taxonomies)
        return _sampled_based(vuln_function, gmf_set, epsilon_provider, asset)


def _sampled_based(vuln_function, gmf_set, epsilon_provider, asset):
    """Compute the set of loss ratios when at least one CV
    (Coefficent of Variation) defined in the vulnerability function
    is greater than zero.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: ground motion fields used to compute the loss ratios
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    loss_ratios = []

    for ground_motion_field in gmf_set["IMLs"]:
        if ground_motion_field < vuln_function.imls[0]:
            loss_ratios.append(0.0)
        else:
            if ground_motion_field > vuln_function.imls[-1]:
                ground_motion_field = vuln_function.imls[-1]

            mean_ratio = vuln_function.loss_ratio_for(ground_motion_field)

            cov = vuln_function.cov_for(ground_motion_field)
            variance = (mean_ratio * cov) ** 2.0

            epsilon = epsilon_provider.epsilon(asset)
            sigma = math.sqrt(
                math.log((variance / mean_ratio ** 2.0) + 1.0))

            mu = math.log(mean_ratio ** 2.0 / math.sqrt(
                variance + mean_ratio ** 2.0))

            loss_ratios.append(math.exp(mu + (epsilon * sigma)))

    return numpy.array(loss_ratios)


def _mean_based(vuln_function, gmf_set):
    """Compute the set of loss ratios when the vulnerability function
    has all the CVs (Coefficent of Variation) set to zero.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: the set of ground motion
        fields used to compute the loss ratios.
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - time representative of the Stochastic Event Set (float)
    """

    loss_ratios = []
    retrieved = {}
    imls = vuln_function.imls

    # seems like with numpy you can only specify a single fill value
    # if the x_new is outside the range. Here we need two different values,
    # depending if the x_new is below or upon the defined values
    for ground_motion_field in gmf_set["IMLs"]:
        if ground_motion_field < imls[0]:
            loss_ratios.append(0.0)
        elif ground_motion_field > imls[-1]:
            loss_ratios.append(vuln_function.loss_ratios[-1])
        else:
            # The actual value is computed later
            mark = len(loss_ratios)
            retrieved[mark] = gmf_set['IMLs'][mark]
            loss_ratios.append(0.0)

    means = vuln_function.loss_ratio_for(retrieved.values())

    for mark, mean_ratio in zip(retrieved.keys(), means):
        loss_ratios[mark] = mean_ratio

    return numpy.array(loss_ratios)


def _compute_loss_ratios_range(loss_ratios, loss_histogram_bins):
    """Compute the range of loss ratios used to build the loss ratio curve.

    The range is obtained by computing the set of evenly spaced numbers
    over the interval [min_loss_ratio, max_loss_ratio].

    :param loss_ratios: the set of loss ratios used.
    :type loss_ratios: numpy.ndarray
    :param int loss_histogram_bins:
        The number of bins to use in the computed loss histogram.
    """
    return numpy.linspace(
        loss_ratios.min(), loss_ratios.max(), loss_histogram_bins)


def _compute_cumulative_histogram(loss_ratios, loss_ratios_range):
    "Compute the cumulative histogram."

    # ruptures (earthquake) occured but probably due to distance,
    # magnitude and soil conditions, no ground motion was felt at that location
    if (loss_ratios <= 0.0).all():
        return numpy.zeros(loss_ratios_range.size - 1)

    invalid_ratios = lambda ratios: numpy.where(
        numpy.array(ratios) <= 0.0)[0].size

    hist = numpy.histogram(loss_ratios, bins=loss_ratios_range)
    hist = hist[0][::-1].cumsum()[::-1]

    # ratios with value 0.0 must be deleted on the first bin
    hist[0] = hist[0] - invalid_ratios(loss_ratios)
    return hist


def _compute_rates_of_exceedance(cum_histogram, tses):
    """Compute the rates of exceedance for the given cumulative histogram
    using the given tses (tses is time span * number of realizations)."""

    if tses <= 0:
        raise ValueError("TSES is not supposed to be less than zero!")

    return (numpy.array(cum_histogram).astype(float) / tses)


def _compute_probs_of_exceedance(rates_of_exceedance, time_span):
    """Compute the probabilities of exceedance using the given rates of
    exceedance and the given time span."""

    poe = lambda rate: 1 - math.exp((rate * -1) * time_span)
    return numpy.array([poe(rate) for rate in rates_of_exceedance])


def _generate_curve(losses, probs_of_exceedance):
    """Generate a loss ratio (or loss) curve, given a set of losses
    and corresponding PoEs (Probabilities of Exceedance).

    This function is intended to be used internally.
    """

    mean_losses = [numpy.mean([x, y]) for x, y in zip(losses, losses[1:])]
    return curve.Curve(zip(mean_losses, probs_of_exceedance))


def _compute_loss_ratio_curve(vuln_function, gmf_set,
                             asset, loss_histogram_bins, loss_ratios=None,
                             seed=None, correlation_type=None,
                             taxonomies=None):
    """Compute a loss ratio curve using the probabilistic event based approach.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param gmf_set: the set of ground motion
        fields used to compute the loss ratios.
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - Time representative of the Stochastic Event Set (float)
    :param seed:
      the seed used for the rnd generator
    :param correlation_type
      UNCORRELATED or PERFECTLY_CORRELATED
    :param taxonomies
      a list of considered taxonomies
    :param asset: the asset used to compute the loss ratios.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposureModelFile`
    :param int loss_histogram_bins:
        The number of bins to use in the computed loss histogram.
    """

    # with no gmfs (no earthquakes), an empty curve is enough
    if not gmf_set["IMLs"]:
        return curve.EMPTY_CURVE

    if loss_ratios is None:
        loss_ratios = _compute_loss_ratios(
            vuln_function, gmf_set, asset,
            seed, correlation_type, taxonomies)

    loss_ratios_range = _compute_loss_ratios_range(
        loss_ratios, loss_histogram_bins)

    probs_of_exceedance = _compute_probs_of_exceedance(
        _compute_rates_of_exceedance(_compute_cumulative_histogram(
            loss_ratios, loss_ratios_range), gmf_set["TSES"]),
        gmf_set["TimeSpan"])

    return _generate_curve(loss_ratios_range, probs_of_exceedance)


def _compute_insured_loss_curve(asset, loss_curve):
    """
    Compute an insured loss curve.
    :param asset: the asset used to compute the insured loss curve.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposureModelFile`
    :param loss_curve: a loss curve.
    :type loss_curve: a :py:class:`openquake.shapes.Curve` instance.
    """
    insured_losses = _compute_insured_losses(asset, loss_curve.x_values)

    return curve.Curve(zip(insured_losses, loss_curve.y_values))


def _insurance_boundaries_defined(asset):
    """
    Check if limit and deductibles values have been defined for the asset.

    :param asset: the asset used to compute the losses.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance
    """

    if (asset.ins_limit >= 0 and asset.deductible >= 0):
        return True
    else:
        raise RuntimeError('Insurance boundaries for asset %s are not defined'
                           % asset.asset_ref)


def _compute_insured_losses(asset, losses):
    """
    Compute insured losses for the given asset using the related set of ground
    motion values and vulnerability function.

    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance.
    :param losses: an array of loss values multiplied by the asset value.
    :type losses: a 1-dimensional :py:class:`numpy.ndarray` instance.
    """

    if _insurance_boundaries_defined(asset):
        for i, value in enumerate(losses):
            if value < asset.deductible:
                losses[i] = 0
            else:
                if value > asset.ins_limit:
                    losses[i] = asset.ins_limit
    return losses
