# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.


"""
This module includes the scientific API of the oq-risklib
"""

import itertools

import numpy
from scipy import interpolate, stats

from openquake.risklib import curve, utils

###
### Constants & Defaults
###

DEFAULT_CURVE_RESOLUTION = 50


##
## Input models
##

class Asset(object):
    # FIXME (lp). Provide description
    def __init__(self, value,
                 number_of_units=1,
                 ins_limit=None, deductible=None,
                 retrofitting_cost=None):
        self.value = value
        self.ins_limit = ins_limit
        self.deductible = deductible
        self.number_of_units = number_of_units
        self.retrofitting_cost = retrofitting_cost


class VulnerabilityFunction(object):
    # FIXME (lp). Provide description
    def __init__(self, imls, mean_loss_ratios, covs, distribution_name):
        """
        :param list imls: Intensity Measure Levels for the
            vulnerability function. All values must be >= 0.0, values
            must be arranged in ascending order with no duplicates

        :param list mean_loss_ratios: Mean Loss ratio values, equal in
        length to imls, where 0.0 <= value <= 1.0.

        :param list covs: Coefficients of Variation. Equal in length
        to mean loss ratios. All values must be >= 0.0.

        :param str distribution_name: The probabilistic distribution
            related to this function.
        """
        self._check_vulnerability_data(
            imls, mean_loss_ratios, covs, distribution_name)
        self.imls = numpy.array(imls)
        self.mean_loss_ratios = numpy.array(mean_loss_ratios)
        self.covs = numpy.array(covs)
        self.distribution_name = distribution_name
        (self.max_iml, self.min_iml, self.resolution,
         self.stddevs, self._mlr_i1d, self._covs_i1d,
         self.distribution) = itertools.repeat(None, 7)
        self.init()

    def init(self):
        self.max_iml = self.imls[-1]
        self.min_iml = self.imls[0]
        self.resolution = len(self.imls)
        self.stddevs = self.covs * self.mean_loss_ratios
        self._mlr_i1d = interpolate.interp1d(self.imls, self.mean_loss_ratios)
        self._covs_i1d = interpolate.interp1d(self.imls, self.covs)

        if (self.covs > 0).any():
            self.distribution = DISTRIBUTIONS[self.distribution_name]()
        else:
            self.distribution = DegenerateDistribution()

    def init_distribution(self, asset_count=1, sample_num=1,
                          seed=None, correlation=0):

        self.distribution.init(asset_count, sample_num, seed, correlation)

    def _cov_for(self, imls):
        """
        Clip `imls` to the range associated with the support of the
        vulnerability function and returns the corresponding
        covariance values by linear interpolation. For instance
        if the range is [0.005, 0.0269] and the imls are
        [0.0049, 0.006, 0.027], the clipped imls are
        [0.005,  0.006, 0.0269].
        """
        clipped_up = numpy.min(
            [imls, numpy.ones(len(imls)) * self.max_iml], axis=0)
        clipped = numpy.max(
            [clipped_up, numpy.ones(len(imls)) * self.min_iml], axis=0)
        return self._covs_i1d(clipped)

    def __getstate__(self):
        return (self.imls, self.mean_loss_ratios,
                self.covs, self.distribution_name)

    def __setstate__(self, (imls, mean_loss_ratios, covs, distribution_name)):
        self.imls = imls
        self.mean_loss_ratios = mean_loss_ratios
        self.covs = covs
        self.distribution_name = distribution_name
        self.init()

    def _check_vulnerability_data(self, imls, loss_ratios, covs, distribution):
        assert imls == sorted(set(imls))
        assert all(x >= 0.0 for x in imls)
        assert len(covs) == len(imls)
        assert len(loss_ratios) == len(imls)
        assert all(x >= 0.0 for x in covs)
        assert all(x >= 0.0 and x <= 1.0 for x in loss_ratios)
        assert distribution in ["LN", "BT"]

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
        # by interpolation and sample the distribution

        idxs = numpy.where(imls >= self.min_iml)[0]
        imls = numpy.array(imls)[idxs]
        means = self._mlr_i1d(imls)

        # apply uncertainty
        covs = self._cov_for(imls)

        ret[idxs] = self.distribution.sample(means, covs, covs * imls)

        return ret

    def loss_ratio_exceedance_matrix(
            self, curve_resolution=DEFAULT_CURVE_RESOLUTION):
        """Compute the LREM (Loss Ratio Exceedance Matrix).

        :param vuln_function:
            The vulnerability function used to compute the LREM.
        :type vuln_function:
            :class:`openquake.risklib.vulnerability_function.\
            VulnerabilityFunction`
        :param int steps:
            Number of steps between loss ratios.
        """
        loss_ratios = _evenly_spaced_loss_ratios(
            self.mean_loss_ratios, curve_resolution, [0.0], [1.0])

        # LREM has number of rows equal to the number of loss ratios
        # and number of columns equal to the number of imls
        lrem = numpy.empty((loss_ratios.size, self.imls.size), float)

        for row, loss_ratio in enumerate(loss_ratios):
            for col in range(self.resolution):
                mean_loss_ratio = self.mean_loss_ratios[col]
                loss_ratio_stddev = self.stddevs[col]

                lrem[row][col] = self.distribution.survival(
                    loss_ratio, mean_loss_ratio, loss_ratio_stddev)

        return lrem

    def mean_imls(self):
        """
        Compute the mean IMLs (Intensity Measure Level)
        for the given vulnerability function.

        :param vulnerability_function: the vulnerability function where
            the IMLs (Intensity Measure Level) are taken from.
        :type vuln_function:
           :py:class:`openquake.risklib.vulnerability_function.\
VulnerabilityFunction`
        """
        return ([max(0, self.imls[0] - ((self.imls[1] - self.imls[0]) / 2))] +
                [numpy.mean(pair) for pair in utils.pairwise(self.imls)] +
                [self.imls[-1] + ((self.imls[-1] - self.imls[-2]) / 2)])


##
## Output models
##


ClassicalOutput = collections.namedtuple(
    "ClassicalOutput",
    ["asset", "loss_ratio_curve", "conditional_losses"])

ClassicalOutput.loss_curve = property(
    lambda self: self.loss_ratio_curve.rescale_abscissae(self.asset.value))

ScenarioDamageOutput = collections.namedtuple(
    "ScenarioDamageOutput", ["asset", "fractions"])

ScenarioDamageOutput.damage_distribution_asset = property(
    lambda self: mean_std(self.fractions))


def collapse_map(self):
    mean, std = self.damage_distribution_asset
    return mean[-1], std[-1]  # last column of the damage distribution
ScenarioDamageOutput.collapse_map = property(collapse_map)


BCROutput = collections.namedtuple(
    "BCROutput", ["asset", "bcr", "eal_original", "eal_retrofitted"])


ProbabilisticEventBasedOutput = collections.namedtuple(
    "ProbabilisticEventBasedOutput",
    ["asset", "losses", "loss_ratio_curve", "insured_loss_ratio_curve",
     "insured_losses", "conditional_losses"])

ProbabilisticEventBasedOutput.loss_curve = property(
    lambda self: self.loss_ratio_curve.rescale_abscissae(self.asset.value))

ProbabilisticEventBasedOutput.insured_loss_curve = property(
    lambda self: self.insured_loss_ratio_curve.rescale_abscissae(
        self.asset.value))

ScenarioRiskOutput = collections.namedtuple(
    "ScenarioRiskOutput", ["asset", "losses"])

ScenarioRiskOutput.mean = property(
    lambda self: numpy.mean(self.losses))

ScenarioRiskOutput.standard_deviation = property(
    lambda self: numpy.std(self.losses, ddof=1))


##
## Distribution & Sampling
##
DISTRIBUTIONS = utils.Register()


class Distribution(object):
    """
    A Distribution class models continuous probability distribution of
    random variables used to sample losses of a set of assets. It is
    usually registered with a name (e.g. LN, BT) by using
    :class:`openquake.risklib.utils.Register`
    """

    def init(self, asset_count=1, sample_count=1, seed=None, correlation=0):
        """
        Abstract method to be extended by derived classes. It must be
        called before any previous use of the method `sample`. It
        initialize the random number generator and it may be
        overridden to precompute random values with a given
        correlation among assets.

        :param int asset_count: the expected number of assets

        :param int sample_count: the expected number of samples for
        each asset

        :param int seed: the seed used to initialize the random number
        generator

        :param float correlation: a value between 0 (inclusive) and 1
        that indicates the correlation between samples across
        different assets.
        """
        pass

    def sample(self, means, covs=None, stddevs=None):
        """
        :returns: sample a set of losses
        :param means: an array of mean losses
        :param covs: an array of covariances
        :param stddevs: an array of stddevs
        """
        pass

    def survival(self, loss_ratio, mean, stddev):
        """
        Return the survival function of the distribution with `mean`
        and `stddev` applied to `loss_ratio`
        """
        pass


class DegenerateDistribution(Distribution):
    """
    The degenerate distribution. E.g. a distribution with a delta
    corresponding to the mean.
    """
    def init(self, *args):
        pass

    def sample(self, means, *_):
        return means

    def survival(self, *_):
        return 0


@DISTRIBUTIONS.add('LN')
class LogNormalDistribution(Distribution):
    """
    Model a distribution of a random variable whoose logarithm are
    normally distributed.

    :attr epsilons: A matrix of random numbers generated with
    :func:`numpy.random.multivariate_normal` with dimensions
    assets_num x samples_num.

    :attr epsilon_idx: a counter used in sampling to iterate over the
    attribute `epsilons`
    """
    def __init__(self):
        self.epsilons = None
        self.epsilon_idx = 0

    def init(self, asset_count=1, samples=1, seed=None, correlation=0):
        if seed is not None:
            numpy.random.seed(seed)

        means_vector = numpy.zeros(asset_count)
        covariance_matrix = (
            numpy.ones((asset_count, asset_count)) * correlation +
            numpy.diag(numpy.ones(asset_count)) * (1 - correlation))
        self.epsilons = numpy.random.multivariate_normal(
            means_vector, covariance_matrix, samples).transpose()
        self.epsilon_idx = 0

    def sample(self, means, covs, _):
        if self.epsilons is None:
            raise ValueError("A LogNormalDistribution must be initialized "
                             "before you can use it")
        epsilons = self.epsilons[self.epsilon_idx]
        self.epsilon_idx += 1
        variance = (means * covs) ** 2
        sigma = numpy.sqrt(numpy.log((variance / means ** 2.0) + 1.0))
        mu = numpy.log(means ** 2.0 / numpy.sqrt(variance + means ** 2.0))

        return numpy.exp(mu + (epsilons[0:len(sigma)] * sigma))

    def survival(self, loss_ratio, mean, stddev):
        variance = stddev ** 2.0
        sigma = numpy.sqrt(numpy.log((variance / mean ** 2.0) + 1.0))
        mu = mean ** 2.0 / numpy.sqrt(variance + mean ** 2.0)
        return stats.lognorm.sf(loss_ratio, sigma, scale=mu)


@DISTRIBUTIONS.add('BT')
class BetaDistribution(Distribution):
    def sample(self, means, _, stddevs):
        alpha = self._alpha(means, stddevs)
        beta = self._beta(means, stddevs)
        return numpy.random.beta(alpha, beta, size=None)

    def survival(self, loss_ratio, mean, stddev):
        return stats.beta.sf(loss_ratio,
                             self._alpha(mean, stddev),
                             self._beta(mean, stddev))

    @staticmethod
    def _alpha(mean, stddev):
        return ((1 - mean) / stddev ** 2 - 1 / mean) * mean ** 2

    @staticmethod
    def _beta(mean, stddev):
        return ((1 - mean) / stddev ** 2 - 1 / mean) * (mean - mean ** 2)

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

    # We compute the rates of exceedances by iterating over loss
    # values and counting the number of distinct loss values less than
    # the current loss. This is a workaround for a rounding error, ask Luigi
    # for the details
    times = [index
             for index, (previous_val, val) in
             enumerate(utils.pairwise(sorted_loss_values))
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


##
## Classical
##

def classical(vuln_function, lrem, hazard_curve_values, steps):
    """Compute a loss ratio curve for a specific hazard curve (e.g., site),
    by applying a given vulnerability function.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.

    This is the main (and only) public function of this module.

    :param vuln_function: the vulnerability function used
        to compute the curve.
    :type vuln_function: \
    :py:class:`openquake.risklib.scientific.VulnerabilityFunction`
    :param hazard_curve_values: the hazard curve used to compute the curve.
    :type hazard_curve_values: an association list with the
    imls/values of the hazard curve
    :param int steps:
        Number of steps between loss ratios.
    """
    lrem_po = _loss_ratio_exceedance_matrix_per_poos(
        vuln_function, lrem, hazard_curve_values)
    loss_ratios = _evenly_spaced_loss_ratios(
        vuln_function.mean_loss_ratios, steps, [0.0], [1.0])
    return curve.Curve(zip(loss_ratios, lrem_po.sum(axis=1)))


def _loss_ratio_exceedance_matrix_per_poos(
        vuln_function, lrem, hazard_curve_values):
    """Compute the LREM * PoOs (Probability of Occurence) matrix.

    :param vuln_function: the vulnerability function used
        to compute the matrix.
    :type vuln_function: \
    :py:class:`openquake.risklib.scientific.VulnerabilityFunction`
    :param hazard_curve: the hazard curve used to compute the matrix.
    :type hazard_curve_values: an association list with the hazard
    curve imls/values
    :param lrem: the LREM used to compute the matrix.
    :type lrem: 2-dimensional :py:class:`numpy.ndarray`
    """
    lrem = numpy.array(lrem)
    lrem_po = numpy.empty(lrem.shape)
    imls = vuln_function.mean_imls()
    if hazard_curve_values:
        # compute the PoOs (Probability of Occurence) from the PoEs
        pos = curve.Curve(hazard_curve_values).ordinate_diffs(imls)
        for idx, po in enumerate(pos):
            lrem_po[:, idx] = lrem[:, idx] * po  # column * po
    return lrem_po


def _evenly_spaced_loss_ratios(loss_ratios, steps, first=(), last=()):
    """
    Split the loss ratios, producing a new set of loss ratios.

    :param loss_ratios: the loss ratios to split.
    :type loss_ratios: list of floats
    :param int steps: the number of steps we make to go from one loss
        ratio to the next. For example, if we have [1.0, 2.0]:

        steps = 1 produces [1.0, 2.0]
        steps = 2 produces [1.0, 1.5, 2.0]
        steps = 3 produces [1.0, 1.33, 1.66, 2.0]
    :param first: optional array of ratios to put first (ex. [0.0])
    :param last: optional array of ratios to put last (ex. [1.0])
    """
    loss_ratios = numpy.concatenate([first, loss_ratios, last])
    ls = numpy.concatenate([numpy.linspace(x, y, num=steps + 1)[:-1]
                            for x, y in utils.pairwise(loss_ratios)])
    return numpy.concatenate([ls, [loss_ratios[-1]]])


def conditional_loss(a_curve, probability):
    """
    Return the loss (or loss ratio) corresponding to the given
    PoE (Probability of Exceendance).

    Return the max loss (or loss ratio) if the given PoE is smaller
    than the lowest PoE defined.

    Return zero if the given PoE is greater than the
    highest PoE defined.
    """
    # the loss curve is always decreasing
    if a_curve.ordinate_out_of_bounds(probability):
        if probability < a_curve.ordinates[-1]:  # min PoE
            return a_curve.abscissae[-1]  # max loss
        else:
            return 0.0

    return a_curve.abscissa_for(probability)

###
### Calculator modifiers
###


##
## Insured Losses
##


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

##
## Benefit Cost Ratio Analysis
##


def bcr(eal_original, eal_retrofitted, interest_rate,
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
            * (1 - numpy.exp(- interest_rate * asset_life_expectancy))
            / (interest_rate * retrofitting_cost))


def mean_loss(a_curve):
    """
    Compute the mean loss (or loss ratio) for the given curve.
    For instance, for a curve with four values [(x1, y1), (x2, y2), (x3, y3),
    (x4, y4)], returns

     x1 + 2x2 + x3  x2 + 2x3 + x4     y1 - y3  y2 - y4
    (-------------, -------------) . (-------, -------)
           4              4               2        4
    """
    # FIXME. Needs more documentation.
    mean_ratios = pairwise_mean(
        pairwise_mean(a_curve.abscissae))
    mean_pes = pairwise_diff(
        pairwise_mean(a_curve.ordinates))
    return numpy.dot(mean_ratios, mean_pes)


def pairwise_mean(values):
    "Averages between a value and the next value in a sequence"
    return [numpy.mean(pair) for pair in utils.pairwise(values)]


def pairwise_diff(values):
    "Differences between a value and the next value in a sequence"
    return [x - y for x, y in utils.pairwise(values)]


def mean_std(fractions):
    """
    Given an N x M matrix, returns mean and std computed on the rows,
    i.e. two M-dimensional vectors.
    """
    return numpy.mean(fractions, axis=0), numpy.std(fractions, axis=0, ddof=1)
