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

###
### Constants & Defaults
###

DEFAULT_CURVE_RESOLUTION = 50


##
## Input models
##

class Asset(object):
    # FIXME (lp). Provide description
    def __init__(self, asset_ref, value, site,
                 number_of_units=1,
                 ins_limit=None, deductible=None,
                 retrofitting_cost=None):
        self.site = site
        self.value = value
        self.asset_ref = asset_ref
        self.ins_limit = ins_limit
        self.deductible = deductible
        self.number_of_units = number_of_units
        self.retrofitting_cost = retrofitting_cost


class VulnerabilityFunction(object):
    # FIXME (lp). Provide description
    def __init__(self, imls, mean_loss_ratios, covs, distribution):
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
        """
        self._check_vulnerability_data(
            imls, mean_loss_ratios, covs, distribution)
        self.imls = numpy.array(imls)
        self.mean_loss_ratios = numpy.array(mean_loss_ratios)
        self.covs = numpy.array(covs)
        self.distribution = distribution
        self.setUp()

    def setUp(self):
        self.max_iml = self.imls[-1]
        self.min_iml = self.imls[0]
        self.resolution = len(self.imls)
        self.stddevs = self.covs * self.mean_loss_ratios
        self._mlr_i1d = interpolate.interp1d(self.imls, self.mean_loss_ratios)
        self._covs_i1d = interpolate.interp1d(self.imls, self.covs)
        self._cov_for = lambda iml: self._covs_i1d(
            numpy.max(
                [numpy.min([iml, numpy.ones(len(iml)) * self.max_iml], axis=0),
                 numpy.ones(len(iml)) * self.min_iml], axis=0))

        if (self.covs > 0).any():
            if self.distribution == "LN":
                self.uncertainty = LogNormalDistribution()
            elif self.distribution == "BT":
                self.uncertainty = BetaDistribution()
        else:
            self.uncertainty = DegenerateDistribution()

    def __getstate__(self):
        return (self.imls, self.mean_loss_ratios, self.covs, self.distribution)

    def __setstate__(self, (imls, mean_loss_ratios, covs, distribution)):
        self.imls = imls
        self.mean_loss_ratios = mean_loss_ratios
        self.covs = covs
        self.distribution = distribution
        self.setUp()

    def seed(self, seed=None, correlation_type=None):
        self.uncertainty.epsilon_provider = EpsilonProvider(
            seed, correlation_type)

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
        # by interpolation and apply the uncertainty (if present)

        idxs = numpy.where(imls >= self.min_iml)[0]
        imls = numpy.array(imls)[idxs]
        means = self._mlr_i1d(imls)

        # apply uncertainty
        covs = self._cov_for(imls)
        ret[idxs] = self.uncertainty.apply(means, covs, covs * imls)

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
        loss_ratios = _evenly_spaced_loss_ratios(
            self.mean_loss_ratios, curve_resolution, [0.0], [1.0])

        # LREM has number of rows equal to the number of loss ratios
        # and number of columns equal to the number of imls
        lrem = numpy.empty((loss_ratios.size, self.imls.size), float)

        for row, loss_ratio in enumerate(loss_ratios):
            for col in range(self.resolution):
                mean_loss_ratio = self.mean_loss_ratios[col]
                loss_ratio_stddev = self.stddevs[col]

                lrem[row][col] = self.uncertainty.survival(
                    loss_ratio, mean_loss_ratio, loss_ratio_stddev)

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
                [numpy.mean(pair) for pair in pairwise(self.imls)] +
                [self.imls[-1] + ((self.imls[-1] - self.imls[-2]) / 2)])


##
## Output models
##


ClassicalOutput = collections.namedtuple(
    "ClassicalOutput",
    ["asset", "loss_ratio_curve", "loss_curve", "conditional_losses"])


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
    "ProbabilisticEventBasedOutput", ["asset", "losses",
    "loss_ratio_curve", "loss_curve", "insured_loss_ratio_curve",
    "insured_loss_curve", "insured_losses", "conditional_losses"])


ScenarioRiskOutput = collections.namedtuple(
    "ScenarioRiskOutput", ["asset", "losses"])

ScenarioRiskOutput.mean = property(
    lambda self: numpy.mean(self.losses))

ScenarioRiskOutput.standard_deviation = property(
    lambda self: numpy.std(self.losses, ddof=1))


##
## Sampling
##


class DegenerateDistribution(object):
    def apply(self, means, *_):
        return means

    def survival(self, *_):
        return 0


class LogNormalDistribution(object):
    def __init__(self):
        self.epsilon_provider = None

    def apply(self, means, covs, _):
        variance = (means * covs) ** 2
        epsilon = self.epsilon_provider.epsilon(len(means))
        sigma = numpy.sqrt(numpy.log((variance / means ** 2.0) + 1.0))
        mu = numpy.log(means ** 2.0 / numpy.sqrt(variance + means ** 2.0))
        return numpy.exp(mu + (epsilon * sigma))

    def survival(self, loss_ratio, mean, stddev):
        variance = stddev ** 2.0
        sigma = numpy.sqrt(numpy.log((variance / mean ** 2.0) + 1.0))
        mu = mean ** 2.0 / numpy.sqrt(variance + mean ** 2.0)
        return stats.lognorm.sf(loss_ratio, sigma, scale=mu)


class BetaDistribution(object):
    def apply(self, means, _, stddevs):
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


class EpsilonProvider(object):
    """
    Simple class for combining job configuration parameters and an `epsilon`
    method. See :py:meth:`EpsilonProvider.epsilon` for more information.
    """

    def __init__(self, seed=None, correlation_type=None):
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
            self._samples = self._generate()

    def _setup_rnd(self):
        self.rnd = random.Random()
        if self._seed is not None:
            self.rnd.seed(int(self._seed))
            numpy.random.seed(int(self._seed))

    def _generate(self):
        if self.rnd is None:
            self._setup_rnd()

        return self.rnd.normalvariate(0, 1)

    def epsilon(self, count=1):
        """Sample from the standard normal distribution for the given asset.

        For uncorrelated risk calculation jobs we sample the standard normal
        distribution for each asset.
        In the opposite case ("perfectly correlated" assets) we sample for each
        building typology i.e. two assets with the same typology will "share"
        the same standard normal distribution sample.
        """

        if self._correlation_type == "perfect":
            ret = [self._samples for _ in range(count)]
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
    :type vuln_function: :py:class:`risklib.scientific.VulnerabilityFunction`
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
    :type vuln_function: :py:class:`risklib.scientific.VulnerabilityFunction`
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
                      for x, y in pairwise(loss_ratios)])
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


###
### Utils
###

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    # b ahead one step; if b is empty do not raise StopIteration
    next(b, None)
    return itertools.izip(a, b)  # if a is empty will return an empty iter


def pairwise_mean(values):
    "Averages between a value and the next value in a sequence"
    return [numpy.mean(pair) for pair in pairwise(values)]


def pairwise_diff(values):
    "Differences between a value and the next value in a sequence"
    return [x - y for x, y in pairwise(values)]


def mean_std(fractions):
    """
    Given an N x M matrix, returns mean and std computed on the rows,
    i.e. two M-dimensional vectors.
    """
    return numpy.mean(fractions, axis=0), numpy.std(fractions, axis=0, ddof=1)
