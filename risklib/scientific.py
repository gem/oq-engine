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


"""
This module includes the scientific API of the oq-risklib
"""

import collections
import random
import itertools

import numpy
from scipy import interpolate, stats

from risklib import curve
from risklib import classical

###
### Constants & Defaults
###

DEFAULT_CURVE_RESOLUTION = 50



##
## Input models
##

class Asset(object):
    # FIXME (lp). Provide description
    def __init__(self, asset_ref, taxonomy, value, site,
                 number_of_units=1,
                 ins_limit=None, deductible=None,
                 retrofitting_cost=None):
        self.site = site
        self.value = value
        self.taxonomy = taxonomy
        self.asset_ref = asset_ref
        self.ins_limit = ins_limit
        self.deductible = deductible
        self.number_of_units = number_of_units
        self.retrofitting_cost = retrofitting_cost


class VulnerabilityFunction(object):
    # FIXME (lp). Provide description
    def __init__(self, imls, mean_loss_ratios, covs, distribution,
                 taxonomy):
        """
        :param list imls: Intensity Measure Levels for the
            vulnerability function. All values must be >= 0.0, values
            must be arranged in ascending order with no duplicates

        :param list mean_loss_ratios: Mean Loss ratio values, equal in
        length to imls, where 0.0 <= value <= 1.0.

        :param list covs: Coefficients of Variation. Equal in length
        to mean loss ratios. All values must be >= 0.0.

        :param string distribution: The probabilistic distribution
            related to this function.

        :param string taxonomy: the taxonomy related to this function
        """
        self._check_vulnerability_data(
            imls, mean_loss_ratios, covs, distribution)
        self.imls = numpy.array(imls)
        self.max_iml = self.imls[-1]
        self.min_iml = self.imls[0]

        self.resolution = len(imls)
        self.mean_loss_ratios = numpy.array(mean_loss_ratios)
        self.covs = numpy.array(covs)
        self.distribution = distribution
        self._mlr_i1d = interpolate.interp1d(self.imls, self.mean_loss_ratios)
        self._covs_i1d = interpolate.interp1d(self.imls, self.covs)
        self._cov_for = lambda iml: self._covs_i1d(
            numpy.max(
                [numpy.min([iml, numpy.ones(len(iml)) * self.max_iml], axis=0),
                numpy.ones(len(iml)) * self.min_iml], axis=0))
        self.epsilon_provider = None
        self.taxonomy = taxonomy

    def seed(self, seed=None, correlation_type=None, taxonomies=None):
        self.epsilon_provider = EpsilonProvider(
            seed, correlation_type, taxonomies)

    def _check_vulnerability_data(self, imls, loss_ratios, covs, distribution):
        assert imls == sorted(set(imls))
        assert all(x >= 0.0 for x in imls)
        assert len(covs) == len(imls)
        assert len(loss_ratios) == len(imls)
        assert all(x >= 0.0 for x in covs)
        assert all(x >= 0.0 and x <= 1.0 for x in loss_ratios)
        assert distribution in ["LN", "BT"]

    @property
    def stddevs(self):
        """
        Convenience method: returns a list of calculated Standard Deviations
        """
        return self.covs * self.mean_loss_ratios

    def __call__(self, imls):
        """
        Given IML values, interpolate the corresponding loss ratio
        value(s) on the curve.

        Input IML value(s) is/are clipped to IML range defined for this
        vulnerability function.

        :param float array iml: IML value

        :returns: :py:class:`numpy.ndarray` containing a number of interpolated
            values equal to the size of the input (1 or many)
        """
        # for imls < min(iml) we return a loss of 0 (default)
        ret = numpy.zeros(len(imls))

        # imls are clipped to max(iml)
        imls = numpy.min([numpy.ones(len(imls)) * self.max_iml,
                          imls], axis=0)

        # for imls such that iml > min(iml) we get a mean loss ratio
        # by interpolation and apply the uncertainty (if present)

        idxs = numpy.where(imls >= self.min_iml)[0]
        imls = numpy.array(imls)[idxs]
        means = self._mlr_i1d(imls)

        # apply uncertainty
        if (self.covs > 0).any():
            covs = self._cov_for(imls)
            stddevs = covs * imls

            if self.distribution == 'BT':
                alpha = _alpha_value(means, stddevs)
                beta = _beta_value(means, stddevs)
                values = stats.beta.sf(means, alpha, beta)
            elif self.distribution == 'LN':
                variance = (means * covs) ** 2
                epsilon = self.epsilon_provider.epsilon(
                    self.taxonomy, len(means))
                sigma = numpy.sqrt(
                    numpy.log((variance / means ** 2.0) + 1.0))
                mu = numpy.log(means ** 2.0 / numpy.sqrt(
                    variance + means ** 2.0))
                values = numpy.exp(mu + (epsilon * sigma))
            ret[idxs] = values
        else:
            ret[idxs] = means

        return ret

    def loss_ratio_exceedance_matrix(
            self, curve_resolution=DEFAULT_CURVE_RESOLUTION):
        """Compute the LREM (Loss Ratio Exceedance Matrix).

        :param vuln_function:
            The vulnerability function used to compute the LREM.
        :type vuln_function:
            :class:`risklib.vulnerability_function.VulnerabilityFunction`
        :param int steps:
            Number of steps between loss ratios.
        """
        loss_ratios = classical._evenly_spaced_loss_ratios(
            self.mean_loss_ratios, curve_resolution, [0.0], [1.0])

        # LREM has number of rows equal to the number of loss ratios
        # and number of columns equal to the number of imls
        lrem = numpy.empty((loss_ratios.size, self.imls.size), float)

        for row, loss_ratio in enumerate(loss_ratios):
            for col in range(self.resolution):
                mean_loss_ratio = self.mean_loss_ratios[col]
                loss_ratio_stddev = self.stddevs[col]

                # FIXME(lp): Refactor this out
                if self.distribution == "BT":
                    lrem[row][col] = stats.beta.sf(
                        loss_ratio,
                        _alpha_value(
                            mean_loss_ratio, loss_ratio_stddev),
                        _beta_value(
                            mean_loss_ratio, loss_ratio_stddev))
                elif self.distribution == "LN":
                    variance = loss_ratio_stddev ** 2.0
                    sigma = numpy.sqrt(
                        numpy.log((variance / mean_loss_ratio ** 2.0) + 1.0))
                    mu = numpy.exp(
                        numpy.log(
                            mean_loss_ratio ** 2.0 /
                            numpy.sqrt(variance + mean_loss_ratio ** 2.0)))
                    lrem[row][col] = stats.lognorm.sf(
                        loss_ratio, sigma, scale=mu)

        return lrem

    def mean_imls(self):
        """
        Compute the mean IMLs (Intensity Measure Level)
        for the given vulnerability function.

        :param vulnerability_function: the vulnerability function where
            the IMLs (Intensity Measure Level) are taken from.
        :type vuln_function:
           :py:class:`risklib.vulnerability_function.VulnerabilityFunction`
        """
        return ([max(0, self.imls[0] - ((self.imls[1] - self.imls[0]) / 2))] +
                [numpy.mean(x) for x in zip(self.imls, self.imls[1:])] +
                [self.imls[-1] + ((self.imls[-1] - self.imls[-2]) / 2)])


##
## Output models
##


ClassicalOutput = collections.namedtuple(
    "ClassicalOutput",
    ["asset", "loss_ratio_curve", "loss_curve", "conditional_losses"])


ScenarioDamageOutput = collections.namedtuple(
    "ScenarioDamageOutput",
    ["asset", "damage_distribution_asset", "collapse_map"])


BCROutput = collections.namedtuple(
    "BCROutput", ["asset", "bcr", "eal_original", "eal_retrofitted"])


ProbabilisticEventBasedOutput = collections.namedtuple(
    "ProbabilisticEventBasedOutput", ["asset", "losses",
    "loss_ratio_curve", "loss_curve", "insured_loss_ratio_curve",
    "insured_loss_curve", "insured_losses", "conditional_losses"])


ScenarioRiskOutput = collections.namedtuple(
    "ScenarioRiskOutput", ["asset", "mean", "standard_deviation"])


##
## Sampling
##


def _alpha_value(mean_loss_ratio, stddev):
    """
    Compute alpha value

    :param mean_loss_ratio: current loss ratio
    :type mean_loss_ratio: float

    :param stdev: current standard deviation
    :type stdev: float


    :returns: computed alpha value
    """

    return (((1 - mean_loss_ratio) / stddev ** 2 - 1 / mean_loss_ratio) *
            mean_loss_ratio ** 2)


def _beta_value(mean_loss_ratio, stddev):
    """
    Compute beta value

    :param mean_loss_ratio: current loss ratio
    :type mean_loss_ratio: float

    :param stdev: current standard deviation
    :type stdev: float


    :returns: computed beta value
    """
    return (((1 - mean_loss_ratio) / stddev ** 2 - 1 / mean_loss_ratio) *
            (mean_loss_ratio - mean_loss_ratio ** 2))


class EpsilonProvider(object):
    """
    Simple class for combining job configuration parameters and an `epsilon`
    method. See :py:meth:`EpsilonProvider.epsilon` for more information.
    """

    def __init__(self, seed=None,
                 correlation_type=None, taxonomies=None):
        """
        :param params: configuration parameters from the job configuration
        :type params: dict
        """
        self._samples = dict()
        self._correlation_type = correlation_type
        self._seed = seed
        self.rnd = None

        if correlation_type == "perfect":
            self._setup_rnd()
            for taxonomy in taxonomies:
                self._samples[taxonomy] = self._generate()

    def _setup_rnd(self):
        self.rnd = random.Random()
        if self._seed is not None:
            self.rnd.seed(int(self._seed))
            numpy.random.seed(int(self._seed))

    def _generate(self):
        if self.rnd is None:
            self._setup_rnd()

        return self.rnd.normalvariate(0, 1)

    def epsilon(self, taxonomy, count=1):
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

        if self._correlation_type == "perfect":
            ret = [self._samples[taxonomy] for _ in range(count)]
        else:
            ret = [self._generate() for _ in range(count)]

        if count == 1:
            return ret[0]
        else:
            return ret


###
### Calculators
###

##
## Event Based
##

def event_based(loss_values, tses, time_span,
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

    poes = 1 - numpy.exp(-rates_of_exceedance * time_span)
    reference_poes = numpy.linspace(poes.min(), poes.max(), curve_resolution)

    values = interpolate.interp1d(poes, sorted_loss_values)(reference_poes)

    return curve.Curve(zip(values, reference_poes))


###
### Calculator modifiers
###


def insured_losses(asset, losses, tses, timespan, curve_resolution):
    """
    Compute insured losses for the given asset using the related set of ground
    motion values and vulnerability function.

    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: an :py:class:`openquake.db.model.ExposureData` instance.
    :param losses: an array of loss values multiplied by the asset value.
    :type losses: a 1-dimensional :py:class:`numpy.ndarray` instance.
    """

    undeductible_losses = losses[losses >= asset.deductible]

    losses = numpy.concatenate((
        numpy.zeros(losses[losses < asset.deductible].shape),
        numpy.min(
            [undeductible_losses,
             numpy.ones(undeductible_losses.shape) * asset.ins_limit], 0)))

    return event_based(losses, tses, timespan, curve_resolution)
