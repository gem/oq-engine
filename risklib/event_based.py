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
import random
import itertools

import numpy
from scipy import interpolate

from risklib import curve
from risklib import classical

UNCORRELATED, PERFECTLY_CORRELATED = range(0, 2)
DEFAULT_CURVE_RESOLUTION = 50


def aggregate_loss_curve(set_of_losses, tses, time_span,
                         curve_resolution=DEFAULT_CURVE_RESOLUTION):
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

    :param curve_resolution
    :type curve_resolution: integer

    :returns: the aggregate loss curve.
    :rtype: an instance of `risklib.curve.Curve`
    """
    aggregate_losses = sum(set_of_losses)

    return _loss_curve(aggregate_losses, tses, time_span,
                       curve_resolution=curve_resolution)


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
    :type vuln_function: :py:class:`risklib.vulnerability_function.VulnerabilityFunction`
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
    if not vuln_function:
        return numpy.array([])

    all_covs_are_zero = (vuln_function.covs <= 0.0).all()

    if all_covs_are_zero:
        return vuln_function.loss_ratio_for(gmf_set["IMLs"])
    else:
        epsilon_provider = EpsilonProvider(seed, correlation_type, taxonomies)
        return _sample_based(vuln_function, gmf_set, epsilon_provider, asset)


def _sample_based(vuln_function, gmf_set, epsilon_provider, asset):
    """Compute the set of loss ratios when at least one CV
    (Coefficent of Variation) defined in the vulnerability function
    is greater than zero.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`risklib.vulnerability_function.VulnerabilityFunction`
    :param gmf_set: ground motion fields used to compute the loss ratios
    :type gmf_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
        **TimeSpan** - time span parameter (float)
        **TSES** - time representative of the Stochastic Event Set (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sample based algorithm.
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

            if vuln_function.is_beta:
                stddev = cov * mean_ratio
                alpha = classical._alpha_value(mean_ratio, stddev)
                beta = classical._beta_value(mean_ratio, stddev)
                loss_ratios.append(numpy.random.beta(alpha, beta, size=None))
            else:
                variance = (mean_ratio * cov) ** 2.0
                epsilon = epsilon_provider.epsilon(asset)
                sigma = math.sqrt(
                    math.log((variance / mean_ratio ** 2.0) + 1.0))

                mu = math.log(mean_ratio ** 2.0 / math.sqrt(
                    variance + mean_ratio ** 2.0))

                loss_ratios.append(math.exp(mu + (epsilon * sigma)))

    return numpy.array(loss_ratios)


def _probs_of_exceedance(rates, time_span):
    """
    Compute the probabilities of exceedance using the given rates of
    exceedance and the given time span.
    """

    return 1 - numpy.exp(-rates * time_span)


def _loss_curve(loss_values, tses, time_span,
                curve_resolution=DEFAULT_CURVE_RESOLUTION):
    """
    Compute a loss (or loss ratio) curve.

    :param loss_values: The loss ratios (or the losses) computed by
    applying the vulnerability function

    :param tses: Time representative of the stochastic event set

    :param time_span: Investigation Time spanned by the hazard input

    :param curve_resolution: The number of points the output curve is
    defined by
    """
    sorted_loss_values = numpy.sort(loss_values)[::-1]

    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        # b ahead one step; if b is empty do not raise StopIteration
        next(b, None)
        return itertools.izip(a, b)  # if a is empty will return an empty iter

    # We compute the rates of exceedances by iterating over loss
    # values and counting the number of distinct loss values less than
    # the current loss. This is a workaround for a rounding error, ask Luigi
    # for the details
    times = [index
             for index, (previous_val, val) in
             enumerate(pairwise(sorted_loss_values))
             if not numpy.allclose([val], [previous_val])]

    # if there are less than 2 distinct loss values, we will keep the
    # endpoints
    if len(times) < 2:
        times = [0, len(sorted_loss_values) - 1]

    sorted_loss_values = sorted_loss_values[times]
    rates_of_exceedance = numpy.array(times) / float(tses)

    poes = _probs_of_exceedance(rates_of_exceedance, time_span)
    reference_poes = numpy.linspace(poes.min(), poes.max(), curve_resolution)

    values = interpolate.interp1d(poes, sorted_loss_values)(reference_poes)

    return curve.Curve(zip(values, reference_poes))
