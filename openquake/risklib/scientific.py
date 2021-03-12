# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
This module includes the scientific API of the oq-risklib
"""
import copy
import bisect
import itertools
import collections
from functools import lru_cache

import numpy
import pandas
from numpy.testing import assert_equal
from scipy import interpolate, stats, sparse

from openquake.baselib.general import CallableDict, AccumDict, humansize

F64 = numpy.float64
F32 = numpy.float32
U32 = numpy.uint32
U16 = numpy.uint16
U8 = numpy.uint8


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    # b ahead one step; if b is empty do not raise StopIteration
    next(b, None)
    return zip(a, b)  # if a is empty will return an empty iter


def fine_graining(points, steps):
    """
    :param points: a list of floats
    :param int steps: expansion steps (>= 2)

    >>> fine_graining([0, 1], steps=0)
    [0, 1]
    >>> fine_graining([0, 1], steps=1)
    [0, 1]
    >>> fine_graining([0, 1], steps=2)
    array([0. , 0.5, 1. ])
    >>> fine_graining([0, 1], steps=3)
    array([0.        , 0.33333333, 0.66666667, 1.        ])
    >>> fine_graining([0, 0.5, 0.7, 1], steps=2)
    array([0.  , 0.25, 0.5 , 0.6 , 0.7 , 0.85, 1.  ])

    N points become S * (N - 1) + 1 points with S > 0
    """
    if steps < 2:
        return points
    ls = numpy.concatenate([numpy.linspace(x, y, num=steps + 1)[:-1]
                            for x, y in pairwise(points)])
    return numpy.concatenate([ls, [points[-1]]])


# sampling functions
class Sampler(object):
    def __init__(self, distname, rng, covs, cols=None, minloss=0):
        self.distname = distname
        self.rng = rng
        self.covs = covs
        self.cols = cols
        self.minloss = minloss
        self.get_losses = getattr(self, 'sample' + distname)

    def cutoff(self, losses):
        losses[losses < self.minloss] = 0
        return losses

    def sampleLN(self, eid, df):
        means = df['mean'].to_numpy()
        vals = df['val'].to_numpy()
        if self.covs.sum():
            covs = df['cov'].to_numpy()
            sigma = numpy.sqrt(numpy.log(1 + covs ** 2))
            div = numpy.sqrt(1 + covs ** 2)
            eps = self.rng.normal(eid, len(df))
            return self.cutoff(means * vals * numpy.exp(eps * sigma) / div)
        else:  # ignore_covs = true or all covs are really zero
            return self.cutoff(means * vals)

    def sampleBT(self, eid, df):
        means = df['mean'].to_numpy()
        vals = df['val'].to_numpy()
        if self.covs.sum():
            stddevs = means * df['cov'].to_numpy()
            return self.cutoff(vals * self.rng.beta(eid, means, stddevs))
        else:  # ignore_covs = true or all covs are really zero
            return self.cutoff(means * vals)

    def samplePM(self, eid, df):
        pmf = []
        arange = numpy.arange(len(self.covs))
        for probs in df[self.cols].to_numpy():  # probs by asset
            if probs.sum() == 0:  # oq-risk-tests/case_1g
                # means are zeros for events below the threshold
                continue
            pmf.append(stats.rv_discrete(
                name='pmf', values=(arange, probs),
                seed=self.rng.master_seed + eid
            ).rvs())
        if pmf:
            return self.cutoff(self.covs[pmf] * df.val.to_numpy())
        else:
            return numpy.zeros(len(df.aid))

#
# Input models
#


class VulnerabilityFunction(object):
    dtype = numpy.dtype([('iml', F64), ('loss_ratio', F64), ('cov', F64)])
    seed = None  # to be overridden

    def __init__(self, vf_id, imt, imls, mean_loss_ratios, covs=None,
                 distribution="LN"):
        """
        A wrapper around a probabilistic distribution function
        (currently, the Log-normal ("LN") and Beta ("BT")
        distributions are supported amongst the continuous probability
        distributions. For specifying a discrete probability
        distribution refer to the class VulnerabilityFunctionWithPMF.
        It is meant to be pickeable to allow distributed computation.
        The only important method is `.__call__`, which applies
        the vulnerability function to a given set of ground motion
        fields and epsilons and return a loss matrix with N x R
        elements.

        :param str vf_id: Vulnerability Function ID
        :param str imt: Intensity Measure Type as a string

        :param list imls: Intensity Measure Levels for the
            vulnerability function. All values must be >= 0.0, values
            must be arranged in ascending order with no duplicates

        :param list mean_loss_ratios: Mean Loss ratio values, equal in
        length to imls, where value >= 0.

        :param list covs: Coefficients of Variation. Equal in length
        to mean loss ratios. All values must be >= 0.0.

        :param str distribution_name: The probabilistic distribution
            related to this function.
        """
        self.id = vf_id
        self.imt = imt
        self._check_vulnerability_data(
            imls, mean_loss_ratios, covs, distribution)
        self.imls = numpy.array(imls)
        self.mean_loss_ratios = numpy.array(mean_loss_ratios)

        if covs is not None:
            self.covs = numpy.array(covs)
        else:
            self.covs = numpy.zeros(self.imls.shape)

        anycovs = self.covs.any()
        for lr, cov in zip(self.mean_loss_ratios, self.covs):
            if lr == 0 and cov > 0:
                msg = ("It is not valid to define a mean loss ratio = 0 "
                       "with a corresponding coefficient of variation > 0")
                raise ValueError(msg)
            if cov < 0:
                raise ValueError(
                    'Found a negative coefficient of variation in %s' %
                    self.covs)
            if distribution == 'BT':
                if lr == 0:  # possible with cov == 0
                    pass
                elif lr > 1:
                    raise ValueError(
                        'The meanLRs must be below 1, got %s' % lr)
                elif cov == 0 and anycovs:
                    raise ValueError(
                        'Found a zero coefficient of variation in %s' %
                        self.covs)
                elif cov ** 2 > 1 / lr - 1:
                    # see https://github.com/gem/oq-engine/issues/4841
                    raise ValueError(
                        'The coefficient of variation %s > %s does not '
                        'satisfy the requirement 0 < sig < sqrt[mu × (1 - mu)]'
                        ' in %s' % (cov, numpy.sqrt(1 / lr - 1), self))

        self.distribution_name = distribution

    def init(self):
        # called by CompositeRiskModel and by __setstate__
        self.covs = F64(self.covs)
        self.mean_loss_ratios = F64(self.mean_loss_ratios)
        self._stddevs = self.covs * self.mean_loss_ratios
        self._mlr_i1d = interpolate.interp1d(self.imls, self.mean_loss_ratios)
        self._covs_i1d = interpolate.interp1d(self.imls, self.covs)

    def interpolate(self, gmf_df, col):
        """
        :param gmf_df:
           DataFrame of GMFs
        :returns:
           DataFrame of interpolated loss ratios and covs
        """
        gmvs = gmf_df[col].to_numpy()
        dic = dict(eid=gmf_df.eid.to_numpy(),
                   mean=numpy.zeros(len(gmvs)),
                   cov=numpy.zeros(len(gmvs)))
        # gmvs are clipped to max(iml)
        gmvs_curve = numpy.piecewise(
            gmvs, [gmvs > self.imls[-1]], [self.imls[-1], lambda x: x])
        ok = gmvs_curve >= self.imls[0]  # indices over the minimum
        curve_ok = gmvs_curve[ok]
        dic['mean'][ok] = self._mlr_i1d(curve_ok)
        dic['cov'][ok] = self._cov_for(curve_ok)
        return pandas.DataFrame(dic, gmf_df.sid)

    def survival(self, loss_ratio, mean, stddev):
        """
        Compute the survival probability based on the underlying
        distribution.
        """
        if self.distribution_name == 'LN':
            # scipy does not handle correctly the limit case stddev = 0.
            # In that case, when `mean` > 0 the survival function
            # approaches to a step function, otherwise (`mean` == 0) we
            # returns 0
            if stddev == 0:
                return numpy.piecewise(
                    loss_ratio, [loss_ratio > mean or not mean], [0, 1])
            variance = stddev ** 2.0
            sigma = numpy.sqrt(numpy.log((variance / mean ** 2.0) + 1.0))
            mu = mean ** 2.0 / numpy.sqrt(variance + mean ** 2.0)
            return stats.lognorm.sf(loss_ratio, sigma, scale=mu)
        elif self.distribution_name == 'BT':
            return stats.beta.sf(loss_ratio, *_alpha_beta(mean, stddev))
        else:
            raise NotImplementedError(self.distribution_name)

    def __call__(self, asset_df, gmf_df, col, rng=None, AE=None, minloss=0):
        """
        :param asset_df: a DataFrame with A assets
        :param gmf_df: a DataFrame of GMFs for the given assets
        :param rng: a MultiEventRNG or None
        :param AE: a pair of integers (A, E)
        :returns: a matrix of losses of shape (A, E)
        """
        testmode = asset_df is None and AE is None
        if testmode:  # in the tests
            asset_df = pandas.DataFrame(dict(aid=0, val=1), [0])
            AE = len(asset_df), len(gmf_df)
        ratio_df = self.interpolate(gmf_df, col)
        if self.distribution_name == 'PM':  # special case
            covs = F64(self.loss_ratios)
            cols = [col for col in ratio_df.columns if isinstance(col, int)]
        else:
            covs = self.covs
            cols = None
        sampler = Sampler(self.distribution_name, rng, covs, cols, minloss)
        loss_matrix = sparse.dok_matrix(AE)
        memory = ratio_df.memory_usage().sum()
        print(humansize(memory), self.id)
        if memory > 1E8:  # more then 100 MB
            # perform a lot of small joins
            for eid, df in ratio_df.groupby('eid'):
                join = df.join(asset_df, how='inner')
                loss_matrix[join.aid, eid] = sampler.get_losses(eid, join)
        else:
            # perform a single big join
            for eid, df in ratio_df.join(asset_df, how='inner').groupby('eid'):
                loss_matrix[df.aid, eid] = sampler.get_losses(eid, df)
        if testmode:
            loss_matrix = loss_matrix.todense()
        return loss_matrix

    def strictly_increasing(self):
        """
        :returns:
          a new vulnerability function that is strictly increasing.
          It is built by removing piece of the function where the mean
          loss ratio is constant.
        """
        imls, mlrs, covs = [], [], []

        previous_mlr = None
        for i, mlr in enumerate(self.mean_loss_ratios):
            if previous_mlr == mlr:
                continue
            else:
                mlrs.append(mlr)
                imls.append(self.imls[i])
                covs.append(self.covs[i])
                previous_mlr = mlr

        return self.__class__(
            self.id, self.imt, imls, mlrs, covs, self.distribution_name)

    def mean_loss_ratios_with_steps(self, steps):
        """
        Split the mean loss ratios, producing a new set of loss ratios. The new
        set of loss ratios always includes 0.0 and 1.0

        :param int steps:
            the number of steps we make to go from one loss
            ratio to the next. For example, if we have [0.5, 0.7]::

             steps = 1 produces [0.0,  0.5, 0.7, 1]
             steps = 2 produces [0.0, 0.25, 0.5, 0.6, 0.7, 0.85, 1]
             steps = 3 produces [0.0, 0.17, 0.33, 0.5, 0.57, 0.63,
                                 0.7, 0.8, 0.9, 1]
        """
        loss_ratios = self.mean_loss_ratios

        if min(loss_ratios) > 0.0:
            # prepend with a zero
            loss_ratios = numpy.concatenate([[0.0], loss_ratios])

        if max(loss_ratios) < 1.0:
            # append a 1.0
            loss_ratios = numpy.concatenate([loss_ratios, [1.0]])

        return fine_graining(loss_ratios, steps)

    def _cov_for(self, imls):
        """
        Clip `imls` to the range associated with the support of the
        vulnerability function and returns the corresponding
        covariance values by linear interpolation. For instance
        if the range is [0.005, 0.0269] and the imls are
        [0.0049, 0.006, 0.027], the clipped imls are
        [0.005,  0.006, 0.0269].
        """
        return self._covs_i1d(
            numpy.piecewise(
                imls,
                [imls > self.imls[-1], imls < self.imls[0]],
                [self.imls[-1], self.imls[0], lambda x: x]))

    def __getstate__(self):
        return (self.id, self.imt, self.imls, self.mean_loss_ratios,
                self.covs, self.distribution_name)

    def __setstate__(self, state):
        self.id = state[0]
        self.imt = state[1]
        self.imls = state[2]
        self.mean_loss_ratios = state[3]
        self.covs = state[4]
        self.distribution_name = state[5]
        self.init()

    def _check_vulnerability_data(self, imls, loss_ratios, covs, distribution):
        assert_equal(imls, sorted(set(imls)))
        assert all(x >= 0.0 for x in imls)
        assert covs is None or len(covs) == len(imls)
        assert len(loss_ratios) == len(imls)
        assert all(x >= 0.0 for x in loss_ratios)
        assert covs is None or all(x >= 0.0 for x in covs)
        assert distribution in ["LN", "BT", "PM"]

    @lru_cache()
    def loss_ratio_exceedance_matrix(self, loss_ratios):
        """
        Compute the LREM (Loss Ratio Exceedance Matrix).
        """
        # LREM has number of rows equal to the number of loss ratios
        # and number of columns equal to the number of imls
        lrem = numpy.empty((len(loss_ratios), len(self.imls)))
        for row, loss_ratio in enumerate(loss_ratios):
            for col, (mean_loss_ratio, stddev) in enumerate(
                    zip(self.mean_loss_ratios, self._stddevs)):
                lrem[row, col] = self.survival(
                    loss_ratio, mean_loss_ratio, stddev)
        return lrem

    @lru_cache()
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
        return numpy.array(
            [max(0, self.imls[0] - (self.imls[1] - self.imls[0]) / 2.)] +
            [numpy.mean(pair) for pair in pairwise(self.imls)] +
            [self.imls[-1] + (self.imls[-1] - self.imls[-2]) / 2.])

    def __repr__(self):
        return '<VulnerabilityFunction(%s, %s)>' % (self.id, self.imt)


class VulnerabilityFunctionWithPMF(VulnerabilityFunction):
    """
    Vulnerability function with an explicit distribution of probabilities

    :param str vf_id: vulnerability function ID
    :param str imt: Intensity Measure Type
    :param imls: intensity measure levels (L)
    :param ratios: an array of mean ratios (M)
    :param probs: a matrix of probabilities of shape (M, L)
    """
    def __init__(self, vf_id, imt, imls, loss_ratios, probs):
        self.id = vf_id
        self.imt = imt
        self._check_vulnerability_data(imls, loss_ratios, probs)
        self.imls = imls
        self.loss_ratios = loss_ratios
        self.probs = probs
        self.distribution_name = "PM"

        # to be set in .init(), called also by __setstate__
        (self._probs_i1d, self.distribution) = None, None
        self.init()

        ls = [('iml', F32)] + [('prob-%s' % lr, F32) for lr in loss_ratios]
        self._dtype = numpy.dtype(ls)

    def init(self):
        self._probs_i1d = interpolate.interp1d(self.imls, self.probs)

    def __getstate__(self):
        return (self.id, self.imt, self.imls, self.loss_ratios,
                self.probs, self.distribution_name)

    def __setstate__(self, state):
        self.id = state[0]
        self.imt = state[1]
        self.imls = state[2]
        self.loss_ratios = state[3]
        self.probs = state[4]
        self.distribution_name = state[5]
        self.init()

    def _check_vulnerability_data(self, imls, loss_ratios, probs):
        assert all(x >= 0.0 for x in imls)
        assert all(x >= 0.0 for x in loss_ratios)
        assert all([1.0 >= x >= 0.0 for x in y] for y in probs)
        assert probs.shape[0] == len(loss_ratios)
        assert probs.shape[1] == len(imls)

    # MN: in the test gmvs_curve is of shape (5,), self.probs of shape (7, 8)
    # self.imls of shape (8,) and the returned means have shape (5, 7)
    def interpolate(self, gmf_df, col):
        """
        :param gmvs:
           DataFrame of GMFs
        :param col:           name of the column to consider
        :returns:
           DataFrame of interpolated probabilities
        """
        # gmvs are clipped to max(iml)
        M = len(self.probs)
        gmvs = gmf_df[col].to_numpy()
        dic = {m: numpy.zeros_like(gmvs) for m in range(M)}
        dic['eid'] = gmf_df.eid.to_numpy()
        gmvs_curve = numpy.piecewise(
            gmvs, [gmvs > self.imls[-1]], [self.imls[-1], lambda x: x])
        ok = gmvs_curve >= self.imls[0]  # indices over the minimum
        for m, probs in enumerate(self._probs_i1d(gmvs_curve[ok])):
            dic[m][ok] = probs
        return pandas.DataFrame(dic, gmf_df.sid)

    @lru_cache()
    def loss_ratio_exceedance_matrix(self, loss_ratios):
        """
        Compute the LREM (Loss Ratio Exceedance Matrix).
        Required for the Classical Risk and BCR Calculators.
        Currently left unimplemented as the PMF format is used only for the
        Scenario and Event Based Risk Calculators.

        :param int steps:
            Number of steps between loss ratios.
        """
        # TODO: to be implemented if the classical risk calculator
        # needs to support the pmf vulnerability format

    def __repr__(self):
        return '<VulnerabilityFunctionWithPMF(%s, %s)>' % (self.id, self.imt)


# this is meant to be instantiated by riskmodels.get_risk_functions
class VulnerabilityModel(dict):
    """
    Container for a set of vulnerability functions. You can access each
    function given the IMT and taxonomy with the square bracket notation.

    :param str id: ID of the model
    :param str assetCategory: asset category (i.e. buildings, population)
    :param str lossCategory: loss type (i.e. structural, contents, ...)

    All such attributes are None for a vulnerability model coming from a
    NRML 0.4 file.
    """
    def __init__(self, id=None, assetCategory=None, lossCategory=None):
        self.id = id
        self.assetCategory = assetCategory
        self.lossCategory = lossCategory

    def __repr__(self):
        return '<%s %s %s>' % (
            self.__class__.__name__, self.lossCategory, sorted(self))


# ############################## fragility ############################### #

class FragilityFunctionContinuous(object):

    def __init__(self, limit_state, mean, stddev, minIML, maxIML, nodamage=0):
        self.limit_state = limit_state
        self.mean = mean
        self.stddev = stddev
        self.minIML = minIML
        self.maxIML = maxIML
        self.no_damage_limit = nodamage

    def __call__(self, imls):
        """
        Compute the Probability of Exceedance (PoE) for the given
        Intensity Measure Levels (IMLs).
        """
        # it is essentially to make a copy of the intensity measure levels,
        # otherwise the minIML feature in continuous fragility functions will
        # change the levels, thus breaking case_master for OQ_DISTRIBUTE=no
        if self.minIML or self.maxIML:
            imls = numpy.array(imls)
        variance = self.stddev ** 2.0
        sigma = numpy.sqrt(numpy.log(
            (variance / self.mean ** 2.0) + 1.0))

        mu = self.mean ** 2.0 / numpy.sqrt(
            variance + self.mean ** 2.0)

        if self.maxIML:
            imls[imls > self.maxIML] = self.maxIML
        if self.minIML:
            imls[imls < self.minIML] = self.minIML
        result = stats.lognorm.cdf(imls, sigma, scale=mu)
        if self.no_damage_limit:
            result[imls < self.no_damage_limit] = 0
        return result

    def __repr__(self):
        return '<%s(%s, %s, %s)>' % (
            self.__class__.__name__, self.limit_state, self.mean, self.stddev)


class FragilityFunctionDiscrete(object):

    def __init__(self, limit_state, imls, poes, no_damage_limit=None):
        self.limit_state = limit_state
        self.imls = imls
        self.poes = poes
        if len(imls) != len(poes):
            raise ValueError('%s: %d levels but %d poes' % (
                limit_state, len(imls), len(poes)))
        self._interp = None
        self.no_damage_limit = no_damage_limit

    @property
    def interp(self):
        if self._interp is not None:
            return self._interp
        self._interp = interpolate.interp1d(self.imls, self.poes,
                                            bounds_error=False)
        return self._interp

    def __call__(self, imls):
        """
        Compute the Probability of Exceedance (PoE) for the given
        Intensity Measure Levels (IMLs).
        """
        highest_iml = self.imls[-1]
        imls = numpy.array(imls)
        if imls.sum() == 0.0:
            return numpy.zeros_like(imls)
        imls[imls > highest_iml] = highest_iml
        result = self.interp(imls)
        if self.no_damage_limit:
            result[imls < self.no_damage_limit] = 0
        return result

    # so that the curve is pickeable
    def __getstate__(self):
        return dict(limit_state=self.limit_state,
                    poes=self.poes, imls=self.imls, _interp=None,
                    no_damage_limit=self.no_damage_limit)

    def __eq__(self, other):
        return (self.poes == other.poes and self.imls == other.imls and
                self.no_damage_limit == other.no_damage_limit)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<%s(%s, %s, %s)>' % (
            self.__class__.__name__, self.limit_state, self.imls, self.poes)


class FragilityFunctionList(list):
    """
    A list of fragility functions with common attributes; there is a
    function for each limit state.
    """
    # NB: the list is populated after instantiation by .append calls
    def __init__(self, array, **attrs):
        self.array = array
        vars(self).update(attrs)

    def mean_loss_ratios_with_steps(self, steps):
        """For compatibility with vulnerability functions"""
        return fine_graining(self.imls, steps)

    def build(self, limit_states, discretization, steps_per_interval):
        """
        :param limit_states: a sequence of limit states
        :param discretization: continouos fragility discretization parameter
        :param steps_per_interval: steps_per_interval parameter
        :returns: a populated FragilityFunctionList instance
        """
        new = copy.copy(self)
        new.clear()
        add_zero = (self.format == 'discrete' and
                    self.nodamage and self.nodamage <= self.imls[0])
        new.imls = build_imls(new, discretization)
        if steps_per_interval > 1:
            new._interp_imls = build_imls(  # passed to classical_damage
                new, discretization, steps_per_interval)
        for i, ls in enumerate(limit_states):
            data = self.array[i]
            if self.format == 'discrete':
                if add_zero:
                    if len(self.imls) == len(data):  # add no_damage
                        imls = [self.nodamage] + self.imls
                    else:  # already added
                        imls = self.imls
                    new.append(FragilityFunctionDiscrete(
                        ls, imls, numpy.concatenate([[0.], data]),
                        self.nodamage))
                else:
                    new.append(FragilityFunctionDiscrete(
                        ls, self.imls, data, self.nodamage))
            else:  # continuous
                new.append(FragilityFunctionContinuous(
                    ls, data[0], data[1],  # mean and stddev
                    self.minIML, self.maxIML, self.nodamage))
        return new

    def __repr__(self):
        kvs = ['%s=%s' % item for item in vars(self).items()]
        return '<FragilityFunctionList %s>' % ', '.join(kvs)


class ConsequenceModel(dict):
    """
    Dictionary of consequence functions. You can access each
    function given its name with the square bracket notation.

    :param str id: ID of the model
    :param str assetCategory: asset category (i.e. buildings, population)
    :param str lossCategory: loss type (i.e. structural, contents, ...)
    :param str description: description of the model
    :param limitStates: a list of limit state strings
    """

    def __init__(self, id, assetCategory, lossCategory, description,
                 limitStates):
        self.id = id
        self.assetCategory = assetCategory
        self.lossCategory = lossCategory
        self.description = description
        self.limitStates = limitStates

    def __repr__(self):
        return '<%s %s %s %s>' % (
            self.__class__.__name__, self.lossCategory,
            ', '.join(self.limitStates), ' '.join(sorted(self)))


def build_imls(ff, continuous_fragility_discretization,
               steps_per_interval=0):
    """
    Build intensity measure levels from a fragility function. If the function
    is continuous, they are produced simply as a linear space between minIML
    and maxIML. If the function is discrete, they are generated with a
    complex logic depending on the noDamageLimit and the parameter
    steps per interval.

    :param ff: a fragility function object
    :param continuous_fragility_discretization: .ini file parameter
    :param steps_per_interval:  .ini file parameter
    :returns: generated imls
    """
    if ff.format == 'discrete':
        imls = ff.imls
        if ff.nodamage and ff.nodamage < imls[0]:
            imls = [ff.nodamage] + imls
        if steps_per_interval > 1:
            gen_imls = fine_graining(imls, steps_per_interval)
        else:
            gen_imls = imls
    else:  # continuous
        gen_imls = numpy.linspace(ff.minIML, ff.maxIML,
                                  continuous_fragility_discretization)
    return gen_imls


# this is meant to be instantiated by riskmodels.get_fragility_model
class FragilityModel(dict):
    """
    Container for a set of fragility functions. You can access each
    function given the IMT and taxonomy with the square bracket notation.

    :param str id: ID of the model
    :param str assetCategory: asset category (i.e. buildings, population)
    :param str lossCategory: loss type (i.e. structural, contents, ...)
    :param str description: description of the model
    :param limitStates: a list of limit state strings
    """

    def __init__(self, id, assetCategory, lossCategory, description,
                 limitStates):
        self.id = id
        self.assetCategory = assetCategory
        self.lossCategory = lossCategory
        self.description = description
        self.limitStates = limitStates

    def __repr__(self):
        return '<%s %s %s %s>' % (
            self.__class__.__name__, self.lossCategory,
            self.limitStates, sorted(self))

# ########################### random generators  ###########################


def _alpha_beta(mean, stddev):
    c = (1 - mean) / stddev ** 2 - 1 / mean
    return c * mean ** 2, c * (mean - mean ** 2)


class MultiEventRNG(object):
    """
    An object ``MultiEventRNG(master_seed, eids, asset_correlation=0)``
    has a method ``.get(A, eids)`` which returns a matrix of (A, E)
    normally distributed random numbers.
    If the ``asset_correlation`` is 1 the numbers are the same.

    >>> rng = MultiEventRNG(
    ...     master_seed=42, eids=[0, 1, 2], asset_correlation=1)
    >>> rng.normal(eid=1, size=3)
    array([-2.46861114, -2.46861114, -2.46861114])
    >>> rng.beta(1, means=numpy.array([.5]*3), stddevs=numpy.array([.05]*3))
    array([0.4372343 , 0.57308132, 0.56392573])
    """
    def __init__(self, master_seed, eids, asset_correlation=0):
        self.master_seed = master_seed
        self.asset_correlation = asset_correlation
        self.rng = {}
        for eid in eids:
            ph = numpy.random.Philox(self.master_seed + eid)
            self.rng[eid] = numpy.random.Generator(ph)

    def normal(self, eid, size):
        """
        :param eid: event ID
        :param size: number of assets affected by the given event
        :returns: array of dtype float32
        """
        rng = self.rng[eid]
        if self.asset_correlation:
            return numpy.ones(size) * rng.normal()
        else:
            return rng.normal(size=size)

    def beta(self, eid, means, stddevs):
        """
        :param eid: event ID
        :param means: array of floats in the range 0..1
        :param stddevs: array of floats in the range 0..1 with the same shape
        :returns: array of floats following the beta distribution

        This function works properly even when some or all of the stddevs
        are zero: in that case it returns the means since the distribution
        becomes extremelyn peaked. It also works properly when some one or
        all of the means are zero, returning zero in that case.
        """
        # NB: you should not expect a smooth limit for the case of stddev->0
        # since the random number generator will advance of a different number
        # of steps with stddev == 0 and stddev != 0
        res = numpy.array(means)
        ok = (means != 0) & (stddevs != 0)  # nonsingular values
        alpha, beta = _alpha_beta(means[ok], stddevs[ok])
        res[ok] = self.rng[eid].beta(alpha, beta)
        return res


#
# Event Based
#

CurveParams = collections.namedtuple(
    'CurveParams',
    ['index', 'loss_type', 'curve_resolution', 'ratios', 'user_provided'])


#
# Scenario Damage
#

def scenario_damage(fragility_functions, gmvs):
    """
    :param fragility_functions: a list of D - 1 fragility functions
    :param gmvs: an array of E ground motion values
    :returns: an array of (D, E) damage fractions
    """
    lst = [numpy.ones_like(gmvs)]
    for f, ff in enumerate(fragility_functions):  # D - 1 functions
        lst.append(ff(gmvs))
    lst.append(numpy.zeros_like(gmvs))
    # convert a (D + 1, E) array into a (D, E) array
    arr = pairwise_diff(numpy.array(lst))
    arr[arr < 1E-7] = 0  # sanity check
    return arr

#
# Classical Damage
#


def annual_frequency_of_exceedence(poe, t_haz):
    """
    :param poe: array of probabilities of exceedence
    :param t_haz: hazard investigation time
    :returns: array of frequencies (with +inf values where poe=1)
    """
    arr = 1. - poe
    arr[arr == 0] = 1E-16  # cutoff to avoid log(0)
    return - numpy.log(arr) / t_haz


def classical_damage(
        fragility_functions, hazard_imls, hazard_poes,
        investigation_time, risk_investigation_time,
        steps_per_interval=1):
    """
    :param fragility_functions:
        a list of fragility functions for each damage state
    :param hazard_imls:
        Intensity Measure Levels
    :param hazard_poes:
        hazard curve
    :param investigation_time:
        hazard investigation time
    :param risk_investigation_time:
        risk investigation time
    :param steps_per_interval:
        steps per interval
    :returns:
        an array of M probabilities of occurrence where M is the numbers
        of damage states.
    """
    if steps_per_interval > 1:  # interpolate
        imls = numpy.array(fragility_functions._interp_imls)
        min_val, max_val = hazard_imls[0], hazard_imls[-1]
        assert min_val > 0, hazard_imls  # sanity check
        numpy.putmask(imls, imls < min_val, min_val)
        numpy.putmask(imls, imls > max_val, max_val)
        poes = interpolate.interp1d(hazard_imls, hazard_poes)(imls)
    else:
        imls = hazard_imls
        poes = numpy.array(hazard_poes)
    afe = annual_frequency_of_exceedence(poes, investigation_time)
    annual_frequency_of_occurrence = pairwise_diff(
        pairwise_mean([afe[0]] + list(afe) + [afe[-1]]))
    poes_per_damage_state = []
    for ff in fragility_functions:
        fx = annual_frequency_of_occurrence @ ff(imls)
        poe_per_damage_state = 1. - numpy.exp(-fx * risk_investigation_time)
        poes_per_damage_state.append(poe_per_damage_state)
    poos = pairwise_diff([1] + poes_per_damage_state + [0])
    return poos

#
# Classical
#


def classical(vulnerability_function, hazard_imls, hazard_poes, loss_ratios):
    """
    :param vulnerability_function:
        an instance of
        :py:class:`openquake.risklib.scientific.VulnerabilityFunction`
        representing the vulnerability function used to compute the curve.
    :param hazard_imls:
        the hazard intensity measure type and levels
    :type hazard_poes:
        the hazard curve
    :param loss_ratios:
        a tuple of C loss ratios
    :returns:
        an array of shape (2, C)
    """
    assert len(hazard_imls) == len(hazard_poes), (
        len(hazard_imls), len(hazard_poes))
    vf = vulnerability_function
    imls = vf.mean_imls()
    lrem = vf.loss_ratio_exceedance_matrix(loss_ratios)

    # saturate imls to hazard imls
    min_val, max_val = hazard_imls[0], hazard_imls[-1]
    numpy.putmask(imls, imls < min_val, min_val)
    numpy.putmask(imls, imls > max_val, max_val)

    # interpolate the hazard curve
    poes = interpolate.interp1d(hazard_imls, hazard_poes)(imls)

    # compute the poos
    pos = pairwise_diff(poes)
    lrem_po = numpy.empty(lrem.shape)
    for idx, po in enumerate(pos):
        lrem_po[:, idx] = lrem[:, idx] * po  # column * po
    return numpy.array([loss_ratios, lrem_po.sum(axis=1)])


# used in classical_risk only
def conditional_loss_ratio(loss_ratios, poes, probability):
    """
    Return the loss ratio corresponding to the given PoE (Probability
    of Exceendance). We can have four cases:

      1. If `probability` is in `poes` it takes the bigger
         corresponding loss_ratios.

      2. If it is in `(poe1, poe2)` where both `poe1` and `poe2` are
         in `poes`, then we perform a linear interpolation on the
         corresponding losses

      3. if the given probability is smaller than the
         lowest PoE defined, it returns the max loss ratio .

      4. if the given probability is greater than the highest PoE
         defined it returns zero.

    :param loss_ratios: an iterable over non-decreasing loss ratio
                        values (float)
    :param poes: an iterable over non-increasing probability of
                 exceedance values (float)
    :param float probability: the probability value used to
                              interpolate the loss curve
    """
    assert len(loss_ratios) >= 3, loss_ratios
    rpoes = poes[::-1]
    if probability > poes[0]:  # max poes
        return 0.0
    elif probability < poes[-1]:  # min PoE
        return loss_ratios[-1]
    if probability in poes:
        return max([loss
                    for i, loss in enumerate(loss_ratios)
                    if probability == poes[i]])
    else:
        interval_index = bisect.bisect_right(rpoes, probability)

        if interval_index == len(poes):  # poes are all nan
            return float('nan')
        elif interval_index == 1:  # boundary case
            x1, x2 = poes[-2:]
            y1, y2 = loss_ratios[-2:]
        else:
            x1, x2 = poes[-interval_index-1:-interval_index + 1]
            y1, y2 = loss_ratios[-interval_index-1:-interval_index + 1]

        return (y2 - y1) / (x2 - x1) * (probability - x1) + y1


#
# Insured Losses
#

def insured_losses(losses, deductible, insured_limit):
    """
    :param losses: an array of ground-up loss ratios
    :param float deductible: the deductible limit in fraction form
    :param float insured_limit: the insured limit in fraction form

    Compute insured losses for the given asset and losses, from the point
    of view of the insurance company. For instance:

    >>> insured_losses(numpy.array([3, 20, 101]), 5, 100)
    array([ 0, 15, 95])

    - if the loss is 3 (< 5) the company does not pay anything
    - if the loss is 20 the company pays 20 - 5 = 15
    - if the loss is 101 the company pays 100 - 5 = 95
    """
    return numpy.piecewise(
        losses,
        [losses < deductible, losses > insured_limit],
        [0, insured_limit - deductible, lambda x: x - deductible])


def insured_loss_curve(curve, deductible, insured_limit):
    """
    Compute an insured loss ratio curve given a loss ratio curve

    :param curve: an array 2 x R (where R is the curve resolution)
    :param float deductible: the deductible limit in fraction form
    :param float insured_limit: the insured limit in fraction form

    >>> losses = numpy.array([3, 20, 101])
    >>> poes = numpy.array([0.9, 0.5, 0.1])
    >>> insured_loss_curve(numpy.array([losses, poes]), 5, 100)
    array([[ 3.        , 20.        ],
           [ 0.85294118,  0.5       ]])
    """
    losses, poes = curve[:, curve[0] <= insured_limit]
    limit_poe = interpolate.interp1d(
        *curve, bounds_error=False, fill_value=1)(deductible)
    return numpy.array([
        losses,
        numpy.piecewise(poes, [poes > limit_poe], [limit_poe, lambda x: x])])


#
# Benefit Cost Ratio Analysis
#


def bcr(eal_original, eal_retrofitted, interest_rate,
        asset_life_expectancy, asset_value, retrofitting_cost):
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
    return ((eal_original - eal_retrofitted) * asset_value *
            (1 - numpy.exp(- interest_rate * asset_life_expectancy)) /
            (interest_rate * retrofitting_cost))


# ####################### statistics #################################### #

def pairwise_mean(values):
    "Averages between a value and the next value in a sequence"
    return numpy.array([numpy.mean(pair) for pair in pairwise(values)])


def pairwise_diff(values):
    "Differences between a value and the next value in a sequence"
    return numpy.array([x - y for x, y in pairwise(values)])


def mean_std(fractions):
    """
    Given an N x M matrix, returns mean and std computed on the rows,
    i.e. two M-dimensional vectors.
    """
    n = fractions.shape[0]
    if n == 1:  # avoid warnings when computing the stddev
        return fractions[0], numpy.ones_like(fractions[0]) * numpy.nan
    return numpy.mean(fractions, axis=0), numpy.std(fractions, axis=0, ddof=1)


def loss_maps(curves, conditional_loss_poes):
    """
    :param curves: an array of loss curves
    :param conditional_loss_poes: a list of conditional loss poes
    :returns: a composite array of loss maps with the same shape
    """
    loss_maps_dt = numpy.dtype([('poe-%s' % poe, F32)
                                for poe in conditional_loss_poes])
    loss_maps = numpy.zeros(curves.shape, loss_maps_dt)
    for idx, curve in numpy.ndenumerate(curves):
        for poe in conditional_loss_poes:
            loss_maps['poe-%s' % poe][idx] = conditional_loss_ratio(
                curve['losses'], curve['poes'], poe)
    return loss_maps


def broadcast(func, composite_array, *args):
    """
    Broadcast an array function over a composite array
    """
    dic = {}
    dtypes = []
    for name in composite_array.dtype.names:
        dic[name] = func(composite_array[name], *args)
        dtypes.append((name, dic[name].dtype))
    res = numpy.zeros(dic[name].shape, numpy.dtype(dtypes))
    for name in dic:
        res[name] = dic[name]
    return res


# TODO: remove this from openquake.risklib.qa_tests.bcr_test
def average_loss(lc):
    """
    Given a loss curve array with `poe` and `loss` fields,
    computes the average loss on a period of time.

    :note: As the loss curve is supposed to be piecewise linear as it
           is a result of a linear interpolation, we compute an exact
           integral by using the trapeizodal rule with the width given by the
           loss bin width.
    """
    losses, poes = (lc['loss'], lc['poe']) if lc.dtype.names else lc
    return -pairwise_diff(losses) @ pairwise_mean(poes)


def normalize_curves_eb(curves):
    """
    A more sophisticated version of normalize_curves, used in the event
    based calculator.

    :param curves: a list of pairs (losses, poes)
    :returns: first losses, all_poes
    """
    # we assume non-decreasing losses, so losses[-1] is the maximum loss
    non_zero_curves = [(losses, poes)
                       for losses, poes in curves if losses[-1] > 0]
    if not non_zero_curves:  # no damage. all zero curves
        return curves[0][0], numpy.array([poes for _losses, poes in curves])
    else:  # standard case
        max_losses = [losses[-1] for losses, _poes in non_zero_curves]
        reference_curve = non_zero_curves[numpy.argmax(max_losses)]
        loss_ratios = reference_curve[0]
        curves_poes = [interpolate.interp1d(
            losses, poes, bounds_error=False, fill_value=0)(loss_ratios)
            for losses, poes in curves]
        # fix degenerated case with flat curve
        for cp in curves_poes:
            if numpy.isnan(cp[0]):
                cp[0] = 0
    return loss_ratios, numpy.array(curves_poes)


def build_loss_curve_dt(curve_resolution, insured_losses=False):
    """
    :param curve_resolution:
        dictionary loss_type -> curve_resolution
    :param insured_losses:
        configuration parameter
    :returns:
       loss_curve_dt
    """
    lc_list = []
    for lt in sorted(curve_resolution):
        C = curve_resolution[lt]
        pairs = [('losses', (F32, C)), ('poes', (F32, C))]
        lc_dt = numpy.dtype(pairs)
        lc_list.append((str(lt), lc_dt))
    if insured_losses:
        for lt in sorted(curve_resolution):
            C = curve_resolution[lt]
            pairs = [('losses', (F32, C)), ('poes', (F32, C))]
            lc_dt = numpy.dtype(pairs)
            lc_list.append((str(lt) + '_ins', lc_dt))
    loss_curve_dt = numpy.dtype(lc_list) if lc_list else None
    return loss_curve_dt


def return_periods(eff_time, num_losses):
    """
    :param eff_time: ses_per_logic_tree_path * investigation_time
    :param num_losses: used to determine the minimum period
    :returns: an array of 32 bit periods

    Here are a few examples:

    >>> return_periods(1, 1)
    Traceback (most recent call last):
       ...
    ValueError: eff_time too small: 1
    >>> return_periods(2, 2)
    array([1, 2], dtype=uint32)
    >>> return_periods(2, 10)
    array([1, 2], dtype=uint32)
    >>> return_periods(100, 2)
    array([ 50, 100], dtype=uint32)
    >>> return_periods(1000, 1000)
    array([   1,    2,    5,   10,   20,   50,  100,  200,  500, 1000],
          dtype=uint32)
    """
    if eff_time < 2:
        raise ValueError('eff_time too small: %s' % eff_time)
    if num_losses < 2:
        raise ValueError('num_losses too small: %s' % num_losses)
    min_time = eff_time / num_losses
    period = 1
    periods = []
    loop = True
    while loop:
        for val in [1, 2, 5]:
            time = period * val
            if time >= min_time:
                if time > eff_time:
                    loop = False
                    break
                periods.append(time)
        period *= 10
    return U32(periods)


def losses_by_period(losses, return_periods, num_events=None, eff_time=None):
    """
    :param losses: array of simulated losses
    :param return_periods: return periods of interest
    :param num_events: the number of events (>= number of losses)
    :param eff_time: investigation_time * ses_per_logic_tree_path
    :returns: interpolated losses for the return periods, possibly with NaN

    NB: the return periods must be ordered integers >= 1. The interpolated
    losses are defined inside the interval min_time < time < eff_time
    where min_time = eff_time /num_events. On the right of the interval they
    have NaN values; on the left zero values.
    If num_events is not passed, it is inferred from the number of losses;
    if eff_time is not passed, it is inferred from the longest return period.
    Here is an example:

    >>> losses = [3, 2, 3.5, 4, 3, 23, 11, 2, 1, 4, 5, 7, 8, 9, 13]
    >>> losses_by_period(losses, [1, 2, 5, 10, 20, 50, 100], 20)
    array([ 0. ,  0. ,  0. ,  3.5,  8. , 13. , 23. ])
    """
    P = len(return_periods)
    assert len(losses)
    if isinstance(losses, list):
        losses = numpy.array(losses)
    num_losses = len(losses)
    if num_events is None:
        num_events = num_losses
    elif num_events < num_losses:
        raise ValueError(
            'There are not enough events (%d<%d) to compute the loss curve'
            % (num_events, num_losses))
    if eff_time is None:
        eff_time = return_periods[-1]
    losses = numpy.sort(losses)
    # num_losses < num_events: just add zeros
    num_zeros = num_events - num_losses
    if num_zeros:
        newlosses = numpy.zeros(num_events, losses.dtype)
        newlosses[num_events-num_losses:num_events] = losses
        losses = newlosses
    periods = eff_time / numpy.arange(num_events, 0., -1)
    num_left = sum(1 for rp in return_periods if rp < periods[0])
    num_right = sum(1 for rp in return_periods if rp > periods[-1])
    rperiods = [rp for rp in return_periods if periods[0] <= rp <= periods[-1]]
    curve = numpy.zeros(len(return_periods), losses.dtype)
    logr, logp = numpy.log(rperiods), numpy.log(periods)
    for idx, _ in numpy.ndenumerate(losses[0]):
        tup = idx + (slice(num_left, P-num_right),)
        curve[tup] = numpy.interp(logr, logp, losses[idx])
        tup = idx + (slice(P-num_right, None),)
        curve[tup] = numpy.nan
    return curve


class LossCurvesMapsBuilder(object):
    """
    Build losses curves and maps for all loss types at the same time.

    :param conditional_loss_poes: a list of PoEs, possibly empty
    :param return_periods: ordered array of return periods
    :param loss_dt: composite dtype for the loss types
    :param weights: weights of the realizations
    :param num_events: number of events for each realization
    :param eff_time: ses_per_logic_tree_path * hazard investigation time
    """
    def __init__(self, conditional_loss_poes, return_periods, loss_dt,
                 weights, num_events, eff_time, risk_investigation_time):
        self.conditional_loss_poes = conditional_loss_poes
        self.return_periods = return_periods
        self.loss_dt = loss_dt
        self.weights = weights
        self.num_events = num_events
        self.eff_time = eff_time
        if return_periods.sum() == 0:
            self.poes = 1
        else:
            self.poes = 1. - numpy.exp(
                - risk_investigation_time / return_periods)

    # used in post_risk
    def build_curve(self, losses, rlzi):
        return losses_by_period(
            losses, self.return_periods, self.num_events[rlzi], self.eff_time)


class AggLossTable(AccumDict):
    """
    :param aggkey: dictionary tuple -> integer
    :param loss_names: primary loss types + secondary loss types
    """
    @classmethod
    def new(cls, aggkey, loss_names):
        self = cls()
        self.aggkey = {key: k for k, key in enumerate(aggkey)}
        self.aggkey[()] = len(aggkey)
        self.loss_names = loss_names
        self.accum = 0
        return self

    def aggregate(self, out, aggby):
        """
        Populate the event loss table
        """
        assets = out['assets']

        # populate outputs
        if aggby == ['id']:
            kid = {o: self.aggkey[o + 1, ] for o in assets['ordinal']}
        elif aggby == ['site_id']:
            kid = {rec['ordinal']: self.aggkey[rec['site_id'] + 1, ]
                   for rec in assets}
        elif aggby:
            kid = {rec['ordinal']: self.aggkey[tuple(rec[aggby])]
                   for rec in assets}
        else:
            kid = {}

        # aggregation
        K = len(self.aggkey) - 1
        for lni, ln in enumerate(self.loss_names):
            for (aid, eid), loss in out[ln].items():
                self[eid, K, lni] += loss
                # this is the slow part, if aggregate_by is given
                if kid:
                    self[eid, kid[aid], lni] += loss

    def to_dframe(self):
        """
        Convert the AggLosTable into a DataFrame
        """
        out = AccumDict(accum=[])  # col -> values
        for (eid, kid, lid), loss in self.items():
            out['event_id'].append(eid)
            out['agg_id'].append(kid)
            out['loss_id'].append(lid)
            out['loss'].append(loss)
        out['event_id'] = U32(out['event_id'])
        out['agg_id'] = U32(out['agg_id'])
        out['loss_id'] = U8(out['loss_id'])
        return pandas.DataFrame(out)


class InsuredLosses(object):
    """
    There is an insured loss for each loss type in the policy dictionary.
    """
    def __init__(self, policy_name, policy_dict):
        self.policy_name = policy_name
        self.policy_dict = policy_dict
        self.outputs = [lt + '_ins' for lt in policy_dict]

    def update(self, out):
        """
        :param out: a dictionary with keys assets and loss_types
        """
        for asset in out['assets']:
            aid = asset['ordinal']
            policy_idx = asset[self.policy_name]
            for lt in self.policy_dict:
                avalue = asset['value-' + lt]
                ded, lim = self.policy_dict[lt][policy_idx]
                mat = out[lt][aid].tocoo()
                out[lt + '_ins'][aid, mat.col] = insured_losses(
                    mat.data, ded * avalue, lim * avalue)


# not used anymore
def make_epsilons(matrix, seed, correlation):
    """
    Given a matrix of shape (A, E) returns a matrix of the same shape
    obtained by applying the multivariate_normal distribution to
    A points and E samples, by starting from the given seed and
    correlation.
    """
    if seed is not None:
        numpy.random.seed(seed)
    A = len(matrix)
    E = len(matrix[0])
    if not correlation:  # avoid building the covariance matrix
        return numpy.random.normal(size=(E, A)).transpose()
    means_vector = numpy.zeros(A)
    covariance_matrix = (numpy.ones((A, A)) * correlation +
                         numpy.diag(numpy.ones(A)) * (1 - correlation))
    return numpy.random.multivariate_normal(
        means_vector, covariance_matrix, E).transpose()


# ####################### Consequences ##################################### #

consequence = CallableDict()


@consequence.add('losses')
def economic_losses(coeffs, asset, dmgdist, loss_type):
    """
    :param coeffs: coefficients per damage state
    :param asset: asset record
    :param dmgdist: an array of probabilies of shape (E, D - 1)
    :param loss_type: loss type string
    :returns: array of economic losses of length E
    """
    return dmgdist @ coeffs * asset['value-' + loss_type]


if __name__ == '__main__':
    # plots of the beta distribution in terms of mean and stddev
    # see https://en.wikipedia.org/wiki/Beta_distribution
    import matplotlib.pyplot as plt
    x = numpy.arange(0, 1, .01)

    def beta(mean, stddev):
        a, b = _alpha_beta(numpy.array([mean]*100),
                           numpy.array([stddev]*100))
        return stats.beta.pdf(x, a, b)

    rng = MultiEventRNG(42, [1])
    ones = numpy.ones(100)
    vals = rng.beta(1, .5 * ones, .05 * ones)
    print(vals.mean(), vals.std())
    # print(vals)
    vals = rng.beta(1, .5 * ones, .01 * ones)
    print(vals.mean(), vals.std())
    # print(vals)
    plt.plot(x, beta(.5, .05), label='.5[.05]')
    plt.plot(x, beta(.5, .01), label='.5[.01]')
    plt.legend()
    plt.show()
