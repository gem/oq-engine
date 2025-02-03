# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import ast
import copy
import bisect
import itertools
import collections
from pprint import pprint
from functools import lru_cache

import numpy
import pandas
from numpy.testing import assert_equal
from scipy import interpolate, stats
from openquake.baselib import hdf5, general

F64 = numpy.float64
F32 = numpy.float32
U32 = numpy.uint32
U64 = numpy.uint64
U16 = numpy.uint16
U8 = numpy.uint8

TWO32 = 2 ** 32
KNOWN_CONSEQUENCES = ['loss', 'loss_aep', 'loss_oep',
                      'pla_loss', 'pla_loss_aep', 'pla_loss_oep',
                      'losses', 'collapsed',
                      'injured', 'fatalities', 'homeless', 'non_operational']

PERILTYPE = numpy.array(['groundshaking', 'liquefaction', 'landslide'])
LOSSTYPE = numpy.array('''\
business_interruption contents nonstructural structural
occupants occupants_day occupants_night occupants_transit
structural+nonstructural structural+contents nonstructural+contents
structural+nonstructural+contents
structural+nonstructural_ins structural+contents_ins nonstructural+contents_ins
structural+nonstructural+contents_ins
structural_ins nonstructural_ins
reinsurance claim area number residents
structural+business_interruption nonstructural+business_interruption
contents+business_interruption
structural+nonstructural+business_interruption
structural+contents+business_interruption
nonstructural+contents+business_interruption
structural+nonstructural+contents+business_interruption
contents_ins business_interruption_ins
structural_ins+nonstructural_ins structural_ins+contents_ins
structural_ins+business_interruption_ins nonstructural_ins+contents_ins
nonstructural_ins+business_interruption_ins
contents_ins+business_interruption_ins
structural_ins+nonstructural_ins+contents_ins
structural_ins+nonstructural_ins+business_interruption_ins
structural_ins+contents_ins+business_interruption_ins
nonstructural_ins+contents_ins+business_interruption_ins
structural_ins+nonstructural_ins+contents_ins+business_interruption_ins
'''.split())

TOTLOSSES = [lt for lt in LOSSTYPE if '+' in lt]
LOSSID = {lt: i for i, lt in enumerate(LOSSTYPE)}


def _reduce(nested_dic):
    # reduce lists of floats into empty lists inside a nested dictionary
    # used for pretty printing purposes
    out = {}
    for k, dic in nested_dic.items():
        if isinstance(dic, list) and not isinstance(dic[0], (str, bytes)):
            out[k] = []
        elif isinstance(dic, dict):
            out[k] = _reduce(dic)
        else:
            out[k] = dic
    return out


def pairwise(iterable):
    """
    :param iterable: a sequence of N values (s0, s1, ...)
    :returns: N-1 pairs (s0, s1), (s1, s2), (s2, s3), ...

    >>> list(pairwise('ABC'))
    [('A', 'B'), ('B', 'C')]
    """
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
    def __init__(self, distname, rng, lratios=(), cols=None):
        self.distname = distname
        self.rng = rng
        self.arange = numpy.arange(len(lratios))  # for the PM distribution
        self.lratios = lratios  # for the PM distribution
        self.cols = cols  # for the PM distribution

    def get_losses(self, df, covs):
        vals = df['val'].to_numpy()
        if not self.rng or not covs:  # fast lane
            losses = vals * df['mean'].to_numpy()
        else:  # slow lane
            losses = vals * getattr(self, 'sample' + self.distname)(df)
        return losses

    def sampleLN(self, df):
        means = df['mean'].to_numpy()
        covs = df['cov'].to_numpy()
        eids = df['eid'].to_numpy()
        return self.rng.lognormal(eids, means, covs)

    def sampleBT(self, df):
        means = df['mean'].to_numpy()
        covs = df['cov'].to_numpy()
        eids = df['eid'].to_numpy()
        return self.rng.beta(eids, means, covs)

    def samplePM(self, df):
        eids = df['eid'].to_numpy()
        allprobs = df[self.cols].to_numpy()
        pmf = []
        for eid, probs in zip(eids, allprobs):  # probs by asset
            if probs.sum() == 0:  # oq-risk-tests/case_1g
                # means are zeros for events below the threshold
                pmf.append(0)
            else:
                pmf.append(stats.rv_discrete(
                    name='pmf', values=(self.arange, probs),
                    seed=self.rng.master_seed + eid).rvs())
        return self.lratios[pmf]

#
# Input models
#


class VulnerabilityFunction(object):
    dtype = numpy.dtype([('iml', F64), ('loss_ratio', F64), ('cov', F64)])
    seed = None  # to be overridden
    kind = 'vulnerability'

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
        self.retro = False
        if covs is not None:
            self.covs = numpy.array(covs)
        else:
            self.covs = numpy.zeros(self.imls.shape)
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
        # scipy does not handle correctly the limit case stddev = 0.
        # In that case, when `mean` > 0 the survival function
        # approaches to a step function, otherwise (`mean` == 0) we
        # returns 0
        if stddev == 0:
            return numpy.piecewise(
                loss_ratio, [loss_ratio > mean or not mean], [0, 1])
        if self.distribution_name == 'LN':
            variance = stddev ** 2.0
            sigma = numpy.sqrt(numpy.log((variance / mean ** 2.0) + 1.0))
            mu = mean ** 2.0 / numpy.sqrt(variance + mean ** 2.0)
            return stats.lognorm.sf(loss_ratio, sigma, scale=mu)
        elif self.distribution_name == 'BT':
            return stats.beta.sf(loss_ratio, *_alpha_beta(mean, stddev))
        else:
            raise NotImplementedError(self.distribution_name)

    def __call__(self, asset_df, gmf_df, col, rng=None, minloss=0):
        """
        :param asset_df: a DataFrame with A assets
        :param gmf_df: a DataFrame of GMFs for the given assets
        :param col: GMF column associated to the IMT (i.e. "gmv_0")
        :param rng: a MultiEventRNG or None
        :returns: a DataFrame with columns eid, aid, loss
        """
        if asset_df is None:  # in the tests
            asset_df = pandas.DataFrame(dict(aid=0, val=1), [0])
        ratio_df = self.interpolate(gmf_df, col)  # really fast
        if self.distribution_name == 'PM':  # special case
            lratios = F64(self.loss_ratios)
            cols = [col for col in ratio_df.columns if isinstance(col, int)]
        else:
            lratios = ()
            cols = None
        df = ratio_df.join(asset_df, how='inner')
        sampler = Sampler(self.distribution_name, rng, lratios, cols)
        covs = not hasattr(self, 'covs') or self.covs.any()
        losses = sampler.get_losses(df, covs)
        ok = losses > minloss
        if self.distribution_name == 'PM':  # special case
            variances = numpy.zeros(len(losses))
        else:
            variances = (losses * df['cov'].to_numpy())**2
        return pandas.DataFrame(dict(eid=df.eid[ok], aid=df.aid[ok],
                                     variance=variances[ok], loss=losses[ok]))

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
                self.covs, self.distribution_name, self.retro)

    def __setstate__(self, state):
        self.id = state[0]
        self.imt = state[1]
        self.imls = state[2]
        self.mean_loss_ratios = state[3]
        self.covs = state[4]
        self.distribution_name = state[5]
        self.retro = state[6]
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
        self.retro = False
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
                self.probs, self.distribution_name, self.retro)

    def __setstate__(self, state):
        self.id = state[0]
        self.imt = state[1]
        self.imls = state[2]
        self.loss_ratios = state[3]
        self.probs = state[4]
        self.distribution_name = state[5]
        self.retro = state[6]
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
    kind = 'fragility'

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
            result[imls <= self.no_damage_limit] = 0
        return result

    def __repr__(self):
        return '<%s(%s, %s, %s)>' % (
            self.__class__.__name__, self.limit_state, self.mean, self.stddev)


class FragilityFunctionDiscrete(object):
    kind = 'fragility'

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
    kind = 'fragility'

    # NB: the list is populated after instantiation by .append calls
    def __init__(self, array, **attrs):
        self.array = array
        vars(self).update(attrs)

    def mean_loss_ratios_with_steps(self, steps):
        """For compatibility with vulnerability functions"""
        return fine_graining(self.imls, steps)

    def build(self, limit_states, discretization=20, steps_per_interval=1):
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
    kind = 'consequence'

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
    >>> eids = numpy.array([1] * 3)
    >>> means = numpy.array([.5] * 3)
    >>> covs = numpy.array([.1] * 3)
    >>> rng.lognormal(eids, means, covs)
    array([0.38892466, 0.38892466, 0.38892466])
    >>> rng.beta(eids, means, covs)
    array([0.4372343 , 0.57308132, 0.56392573])
    >>> fractions = numpy.array([[[.8, .1, .1]]])
    >>> rng.discrete_dmg_dist([0], fractions, [10])
    array([[[8, 2, 0]]], dtype=uint32)
    """
    def __init__(self, master_seed, eids, asset_correlation=0):
        self.master_seed = master_seed
        self.asset_correlation = asset_correlation
        self.rng = {}
        for eid in eids:
            # NB: int below is necessary for totally mysterious reasons:
            # a calculation on cluster1 #41904 failed with a floating
            # point seed, but I cannot reproduce the issue
            ph = numpy.random.Philox(int(self.master_seed + eid))
            self.rng[eid] = numpy.random.Generator(ph)

    def _get_eps(self, eid, corrcache):
        if self.asset_correlation:
            try:
                return corrcache[eid]
            except KeyError:
                corrcache[eid] = eps = self.rng[eid].normal()
                return eps
        return self.rng[eid].normal()

    def lognormal(self, eids, means, covs):
        """
        :param eids: event IDs
        :param means: array of floats in the range 0..1
        :param covs: array of floats with the same shape
        :returns: array of floats
        """
        corrcache = {}
        eps = numpy.array([self._get_eps(eid, corrcache) for eid in eids])
        sigma = numpy.sqrt(numpy.log(1 + covs ** 2))
        div = numpy.sqrt(1 + covs ** 2)
        return means * numpy.exp(eps * sigma) / div

    # NB: asset correlation is ignored
    def beta(self, eids, means, covs):
        """
        :param eids: event IDs
        :param means: array of floats in the range 0..1
        :param covs: array of floats with the same shape
        :returns: array of floats following the beta distribution

        This function works properly even when some or all of the stddevs
        are zero: in that case it returns the means since the distribution
        becomes extremely peaked. It also works properly when some one or
        all of the means are zero, returning zero in that case.
        """
        # NB: you should not expect a smooth limit for the case of on cov->0
        # since the random number generator will advance of a different number
        # of steps with cov == 0 and cov != 0
        res = numpy.array(means)
        ok = (means != 0) & (covs != 0)  # nonsingular values
        alpha, beta = _alpha_beta(means[ok], means[ok] * covs[ok])
        res[ok] = [self.rng[eid].beta(alpha[i], beta[i])
                   for i, eid in enumerate(eids[ok])]
        return res

    def discrete_dmg_dist(self, eids, fractions, numbers):
        """
        Converting fractions into discrete damage distributions using bincount
        and random.choice.

        :param eids: E event IDs
        :param fractions: array of shape (A, E, D)
        :param numbers: A asset numbers
        :returns: array of integers of shape (A, E, D)
        """
        A, E, D = fractions.shape
        assert len(eids) == E, (len(eids), E)
        assert len(numbers) == A, (len(eids), A)
        ddd = numpy.zeros(fractions.shape, U32)
        for e, eid in enumerate(eids):
            choice = self.rng[eid].choice
            for a, n in enumerate(numbers):
                frac = fractions[a, e]  # shape D
                states = choice(D, n, p=frac/frac.sum())  # n states
                # ex. [0, 0, 0, 1, 0, 0, 0, 1, 0, 0], 8 times 0, 2 times 1
                ddd[a, e] = numpy.bincount(states, minlength=D)
        return ddd

    def boolean_dist(self, probs, num_sims):
        """
        Convert E probabilities into an array of (E, S)
        booleans, being S the number of secondary simulations.

        >>> rng = MultiEventRNG(master_seed=42, eids=[0, 1, 2])
        >>> dist = rng.boolean_dist(probs=[.1, .2, 0.], num_sims=100)
        >>> dist.sum(axis=1)  # around 10% and 20% respectively
        array([12., 17.,  0.])
        """
        E = len(self.rng)
        assert len(probs) == E, (len(probs), E)
        booldist = numpy.zeros((E, num_sims))
        for e, eid, prob in zip(range(E), self.rng, probs):
            if prob > 0:
                booldist[e] = self.rng[eid].random(num_sims) < prob
        return booldist


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
    :param poe: array of probabilities of exceedence in time t_haz
    :param t_haz: hazard investigation time
    :returns: array of frequencies (with +inf values where poe=1)
    """
    # replace 1 with the closest to 1 float64 number to avoid log(1-1)
    poe[poe == 1.] = .9999999999999999
    return - numpy.log(1-poe) / t_haz


def probability_of_exceedance(afoe, t_risk):
    """
    :param afoe: array of annual frequencies of exceedence
    :param t_risk: risk investigation time
    :returns: array of probabilities of exceedance in time t_risk
    """
    return 1 - numpy.exp(-t_risk * afoe)


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
        an array of D probabilities of occurrence where D is the numbers
        of damage states.
    """
    if steps_per_interval > 1:  # interpolate
        imls = numpy.array(fragility_functions._interp_imls)
        min_val, max_val = hazard_imls[0], hazard_imls[-1]
        assert min_val > 0, hazard_imls  # sanity check
        imls[imls < min_val] = min_val
        imls[imls > max_val] = max_val
        poes = interpolate.interp1d(hazard_imls, hazard_poes)(imls)
    else:
        imls = hazard_imls
        poes = numpy.array(hazard_poes)

    # convert the hazard probabilities of exceedance to
    # annual frequencies of exceedance, and then occurrence
    afoes = annual_frequency_of_exceedence(poes, investigation_time)
    afoos = pairwise_diff(
        pairwise_mean([afoes[0]] + list(afoes) + [afoes[-1]]))
    poes_per_dmgstate = []
    for ff in fragility_functions:
        fx = afoos @ ff(imls)
        poe_per_dmgstate = 1. - numpy.exp(-fx * risk_investigation_time)
        poes_per_dmgstate.append(poe_per_dmgstate)
    poos = pairwise_diff([1] + poes_per_dmgstate + [0])
    return poos

#
# Classical Risk
#


def classical(vulnerability_function, hazard_imls, hazard_poes, loss_ratios,
              investigation_time, risk_investigation_time):
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
    :param investigation_time:
        hazard investigation time
    :param risk_investigation_time:
        risk investigation time
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
    imls[imls < min_val] = min_val
    imls[imls > max_val] = max_val

    # interpolate the hazard curve
    poes = interpolate.interp1d(hazard_imls, hazard_poes)(imls)
    if abs((1-poes).mean()) < 1E-4:  # flat curve
        raise ValueError('The hazard curve is flat (all ones) probably due to '
                         'a (hazard) investigation time too large')

    # convert the hazard probabilities of exceedance ot annual
    # frequencies of exceedance, and then occurrence
    afoes = annual_frequency_of_exceedence(poes, investigation_time)
    afoos = pairwise_diff(afoes)

    # compute the annual frequency of exceedance of the loss ratios
    # lrem = loss ratio exceedance matrix
    lr_afoes = numpy.empty(lrem.shape)
    for idx, afoo in enumerate(afoos):
        lr_afoes[:, idx] = lrem[:, idx] * afoo  # column * afoo
    lr_poes = probability_of_exceedance(
        lr_afoes.sum(axis=1), risk_investigation_time)
    return numpy.array([loss_ratios, lr_poes])


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

    :param loss_ratios: non-decreasing loss ratio values (float32)
    :param poes: non-increasing probabilities of exceedance values (float32)
    :param float probability: the probability value used to
                              interpolate the loss curve
    """
    assert len(loss_ratios) >= 3, loss_ratios
    probability = numpy.float32(probability)
    if not isinstance(loss_ratios, numpy.ndarray):
        loss_ratios = numpy.float32(loss_ratios)
    if not isinstance(poes, numpy.ndarray):
        poes = numpy.float32(poes)
    rpoes = poes[::-1]
    if probability > poes[0]:  # max poes
        return 0.0
    elif probability < poes[-1]:  # min PoE
        return loss_ratios[-1]
    if probability in poes:
        return loss_ratios[probability == poes].max()
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

def insured_losses(losses, deductible, insurance_limit):
    """
    :param losses: array of ground-up losses
    :param deductible: array of deductible values
    :param insurance_limit: array of insurance limit values

    Compute insured losses for the given asset and losses, from the point
    of view of the insurance company. For instance:

    >>> insured_losses(numpy.array([3, 20, 101]),
    ...                numpy.array([5, 5, 5]), numpy.array([100, 100, 100]))
    array([ 0, 15, 95])

    - if the loss is 3 (< 5) the company does not pay anything
    - if the loss is 20 the company pays 20 - 5 = 15
    - if the loss is 101 the company pays 100 - 5 = 95
    """
    assert isinstance(losses, numpy.ndarray), losses
    if not isinstance(deductible, numpy.ndarray):
        deductible = numpy.full_like(losses, deductible)
    if not isinstance(insurance_limit, numpy.ndarray):
        insurance_limit = numpy.full_like(losses, insurance_limit)
    assert (deductible < insurance_limit).all()
    small = losses < deductible
    big = losses > insurance_limit
    out = losses - deductible
    out[small] = 0.
    out[big] = insurance_limit[big] - deductible[big]
    return out


def insurance_losses(asset_df, losses_by_lt, policy_df):
    """
    :param asset_df: DataFrame of assets
    :param losses_by_lt: loss_type -> DataFrame[eid, aid, variance, loss]
    :param policy_df: a DataFrame of policies
    """
    asset_policy_df = asset_df.join(
        policy_df.set_index('policy'), on='policy', how='inner')
    for lt in policy_df.loss_type.unique():
        if '+' in lt:
            # add a key like structural+nonstructural to losses_by_lt
            total_losses(asset_df, losses_by_lt, lt)
    for lt, out in list(losses_by_lt.items()):
        if len(out) == 0:
            continue
        adf = asset_policy_df[asset_policy_df.loss_type == lt]
        new = out[numpy.isin(out.aid, adf.index)]
        if len(new) == 0:
            continue
        new['variance'] = 0.
        j = new.join(adf, on='aid', how='inner')
        if '+' in lt:
            lst = [j['value-' + ltype].to_numpy() for ltype in lt.split('+')]
            values = numpy.sum(lst, axis=0)  # shape num_values
        else:
            values = j['value-' + lt].to_numpy()
        aids = j.aid.to_numpy()
        losses = j.loss.to_numpy()
        deds = j.deductible.to_numpy() * values
        lims = j.insurance_limit.to_numpy() * values
        ids_of_invalid_assets = aids[deds > lims]
        if len(ids_of_invalid_assets):
            invalid_assets = set(ids_of_invalid_assets)
            raise ValueError(
                f"Please check deductible values. Values larger than the"
                f" insurance limit were found for asset(s) {invalid_assets}.")
        new['loss'] = insured_losses(losses, deds, lims)
        losses_by_lt[lt + '_ins'] = new


def total_losses(asset_df, losses_by_lt, kind, ideduc=False):
    """
    :param asset_df: DataFrame of assets
    :param losses_by_lt: lt -> DataFrame[eid, aid]
    :param kind: kind of total loss (i.e. "structural+nonstructural")
    :param ideduc: if True compute the insurance claim
    """
    ltypes = kind.split('+')
    losses_by_lt[kind] = df = _agg([losses_by_lt[lt] for lt in ltypes])
    # event loss table eid aid variance loss
    if ideduc:
        loss = df.loss.to_numpy()
        ideductible = asset_df.ideductible[df.aid].to_numpy()
        df = df.copy()
        df['loss'] = numpy.maximum(loss - ideductible, 0)
        losses_by_lt['claim'] = df


def insurance_loss_curve(curve, deductible, insurance_limit):
    """
    Compute an insured loss ratio curve given a loss ratio curve

    :param curve: an array 2 x R (where R is the curve resolution)
    :param float deductible: the deductible limit in fraction form
    :param float insurance_limit: the insured limit in fraction form

    >>> losses = numpy.array([3, 20, 101])
    >>> poes = numpy.array([0.9, 0.5, 0.1])
    >>> insurance_loss_curve(numpy.array([losses, poes]), 5, 100)
    array([[ 3.        , 20.        ],
           [ 0.85294118,  0.5       ]])
    """
    losses, poes = curve[:, curve[0] <= insurance_limit]
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


def pla_factor(df):
    """
    Post-Loss-Amplification factor interpolator.
    To be instantiated with a DataFrame with columns
    return_period and pla_factor.
    """
    factors = df.pla_factor.to_numpy()  # ordered from 1 to maxvalue
    return interpolate.interp1d(df.return_period.to_numpy(),
                                factors,
                                bounds_error=False,
                                fill_value=(1., factors[-1]))


# ####################### statistics #################################### #

def pairwise_mean(values):
    """
    Averages between a value and the next value in a sequence
    """
    return numpy.array([numpy.mean(pair) for pair in pairwise(values)])


def pairwise_diff(values, addlast=False):
    """
    Differences between a value and the next value in a sequence.
    If addlast is set the last value is added to the difference,
    i.e. N values are returned instead of N-1.
    """
    diff = [x - y for x, y in pairwise(values)]
    if addlast:
        diff.append(values[-1])
    return numpy.array(diff)


def dds_to_poes(dmg_dists):
    """
    Convert an array of damage distributions into an array of PoEs

    >>> dds_to_poes([[.7, .2, .1], [0., 0., 1.0]])
    array([[1. , 0.3, 0.1],
           [1. , 1. , 1. ]])
    """
    arr = numpy.fliplr(numpy.fliplr(dmg_dists).cumsum(axis=1))
    return arr


def compose_dds(dmg_dists):
    """
    Compose an array of N damage distributions:

    >>> compose_dds([[.6, .2, .1, .1], [.5, .3 ,.1, .1]])
    array([0.3 , 0.34, 0.17, 0.19])
    """
    poes_per_dmgstate = general.pprod(dds_to_poes(dmg_dists), axis=0)
    return pairwise_diff(poes_per_dmgstate, addlast=True)


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


def build_loss_curve_dt(curve_resolution, insurance_losses=False):
    """
    :param curve_resolution:
        dictionary loss_type -> curve_resolution
    :param insurance_losses:
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
    if insurance_losses:
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
    :returns: an array of periods of dtype uint32

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


def maximum_probable_loss(losses, return_period, eff_time, sorting=True):
    """
    :returns: Maximum Probable Loss at the given return period

    >>> losses = [1000., 0., 2000., 1500., 780., 900., 1700., 0., 100., 200.]
    >>> maximum_probable_loss(losses, 2000, 10_000)
    900.0
    """
    return losses_by_period(losses, [return_period], len(losses), eff_time,
                            sorting)['curve'][0]


def fix_losses(orig_losses, num_events, eff_time=0, sorting=True):
    """
    Possibly add zeros and sort the passed losses.

    :param orig_losses: an array of size num_losses
    :param num_events: an integer >= num_losses
    :returns: three arrays of size num_events
    """
    if sorting:
        sorting_idxs = numpy.argsort(orig_losses)
    else:
        sorting_idxs = slice(None)
    sorted_losses = orig_losses[sorting_idxs]

    # add zeros on the left if there are less losses than events.
    num_losses = len(sorted_losses)
    if num_events > num_losses:
        losses = numpy.zeros(num_events, sorted_losses.dtype)
        losses[num_events - num_losses:num_events] = sorted_losses
    elif num_losses == num_events:
        losses = sorted_losses
    elif num_events < num_losses:
        raise ValueError('More losses (%d) than events (%d) ??' %
                         (num_losses, num_events))
    eperiods = eff_time / numpy.arange(num_events, 0., -1)
    return losses, sorting_idxs, eperiods


def losses_by_period(losses, return_periods, num_events, eff_time=None,
                     sorting=True, name='curve', pla_factor=None):
    # NB: sorting = False is used in test_claim
    """
    :param losses:
        simulated losses as an array, list or DataFrame column
    :param return_periods:
        return periods of interest
    :param num_events:
        the number of events (>= number of losses)
    :param eff_time:
        investigation_time * ses_per_logic_tree_path
    :returns:
         a dictionary with the interpolated losses for the return periods,
         possibly with NaNs and possibly also a post-loss-amplified curve

    NB: the return periods must be ordered integers >= 1. The interpolated
    losses are defined inside the interval min_time < time < eff_time
    where min_time = eff_time /num_events. On the right of the interval they
    have NaN values; on the left zero values.
    If num_events is not passed, it is inferred from the number of losses;
    if eff_time is not passed, it is inferred from the longest return period.
    Here is an example:

    >>> losses = [3, 2, 3.5, 4, 3, 23, 11, 2, 1, 4, 5, 7, 8, 9, 13]
    >>> losses_by_period(losses, [1, 2, 5, 10, 20, 50, 100], 20)
    {'curve': array([ 0. ,  0. ,  0. ,  3.5,  8. , 13. , 23. ])}
    """
    P = len(return_periods)
    assert len(losses)
    if isinstance(losses, list):
        losses = numpy.array(losses)
    elif hasattr(losses, 'to_numpy'):  # DataFrame
        losses = losses.to_numpy()
    if eff_time is None:
        eff_time = return_periods[-1]
    losses, _sorting_idxs, eperiods = fix_losses(
        losses, num_events, eff_time, sorting)
    num_left = sum(1 for rp in return_periods if rp < eperiods[0])
    num_right = sum(1 for rp in return_periods if rp > eperiods[-1])
    rperiods = [rp for rp in return_periods
                if eperiods[0] <= rp <= eperiods[-1]]
    logr, loge = numpy.log(rperiods), numpy.log(eperiods)
    curve = numpy.zeros(len(return_periods), losses.dtype)
    curve[num_left:P - num_right] = numpy.interp(logr, loge, losses)
    curve[P - num_right:] = numpy.nan
    res = {name: curve}
    if pla_factor:
        pla = numpy.zeros(len(return_periods), losses.dtype)
        pla[num_left:P - num_right] = numpy.interp(
            logr, loge, losses * pla_factor(eperiods))
        pla[P - num_right:] = numpy.nan
        res['pla_' + name] = pla
    return res


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
                 weights, eff_time, risk_investigation_time, pla_factor=None):
        if return_periods[-1] > eff_time:
            raise ValueError(
                'The return_period %s is longer than the eff_time per rlz %s'
                % (return_periods[-1], eff_time))
        self.conditional_loss_poes = conditional_loss_poes
        self.return_periods = return_periods
        self.loss_dt = loss_dt
        self.weights = weights
        self.eff_time = eff_time
        if return_periods.sum() == 0:
            self.poes = 1
        else:
            self.poes = 1. - numpy.exp(
                - risk_investigation_time / return_periods)
        self.pla_factor = pla_factor

    # used in post_risk, for normal loss curves and reinsurance curves
    def build_curve(self, years, col, losses, agg_types, loss_type, ne):
        """
        Compute the requested curves
        (AEP and OEP curves only if years is not None)
        """
        # NB: agg_types can be the string "ep, aep, oep"
        periods = self.return_periods
        dic = {}
        agg_types_list = agg_types.split(', ')
        if 'ep' in agg_types_list:
            res = losses_by_period(losses, periods, ne, self.eff_time,
                                   name=col, pla_factor=self.pla_factor)
            dic.update(res)
        if len(years):
            gby = pandas.DataFrame(
                dict(year=years, loss=losses)).groupby('year')
            # see specs in https://github.com/gem/oq-engine/issues/8971
            if 'aep' in agg_types_list:
                dic.update(losses_by_period(
                    gby.loss.sum(), periods, ne, self.eff_time,
                    name=col + '_aep', pla_factor=self.pla_factor))
            if 'oep' in agg_types_list:
                dic.update(losses_by_period(
                    gby.loss.max(), periods, ne, self.eff_time,
                    name=col + '_oep', pla_factor=self.pla_factor))
        return dic


def _agg(loss_dfs, weights=None):
    # average loss DataFrames with fields (eid, aid, variance, loss)
    # NB: if there are weights the DataFrames are changed!!
    if weights is not None:
        for loss_df, w in zip(loss_dfs, weights):
            loss_df['variance'] *= w
            loss_df['loss'] *= w
    return pandas.concat(loss_dfs).groupby(['aid', 'eid']).sum().reset_index()


class RiskComputer(dict):
    """
    A callable dictionary of risk models able to compute average losses
    according to the taxonomy mapping. It also computes secondary losses
    *after* the average (this is a hugely simplifying approximation).

    :param crm: a CompositeRiskModel
    :param asset_df: a DataFrame of assets with the same taxonomy
    """
    def __init__(self, crm, taxidx, country_str='?'):
        oq = crm.oqparam
        self.D = len(crm.damage_states)
        self.P = len(crm.perils)
        self.calculation_mode = oq.calculation_mode
        self.loss_types = crm.loss_types
        self.minimum_asset_loss = oq.minimum_asset_loss  # lt->float
        self.wdic = {}  # (riskid, peril) -> weight
        tm = crm.tmap_df[crm.tmap_df.taxi == taxidx]
        for country, peril, riskid, weight in zip(
                tm.country, tm.peril, tm.risk_id, tm.weight):
            if country == '?' or country_str in country:
                self[riskid] = crm._riskmodels[riskid]
                if peril == '*':
                    for per in crm.perils:
                        self.wdic[riskid, per] = weight
                else:
                    self.wdic[riskid, peril] = weight

    def output(self, asset_df, haz, sec_losses=(), rndgen=None):
        """
        Compute averages by using the taxonomy mapping

        :param asset_df: assets on the same site with the same taxonomy
        :param haz: a DataFrame of GMFs or an array of PoEs
        :param sec_losses: a list of functions updating the loss dict
        :param rndgen: None or MultiEventRNG instance
        :yields: dictionaries {loss_type: loss_output}
        """
        dic = collections.defaultdict(list)  # peril, lt -> outs
        weights = collections.defaultdict(list)  # peril, lt -> weights
        perils = {'groundshaking'}
        for riskid, rm in self.items():
            for (peril, lt), res in rm(asset_df, haz, rndgen).items():
                # res is an array of fractions of shape (A, E, D)
                weights[peril, lt].append(self.wdic[riskid, peril])
                dic[peril, lt].append(res)
                perils.add(peril)
        for peril in sorted(perils):
            out = {}
            for lt in self.minimum_asset_loss:
                outs = dic[peril, lt]
                if len(outs) == 0:  # can happen for nonstructural_ins
                    continue
                elif len(outs) > 1 and hasattr(outs[0], 'loss'):
                    # computing the average dataframe for event_based_risk/case_8
                    out[lt] = _agg(outs, weights[peril, lt])
                elif len(outs) > 1:
                    # for oq-risk-tests/test/event_based_damage/inputs/cali/job.ini
                    out[lt] = numpy.average(outs, weights=weights[peril, lt], axis=0)
                else:
                    out[lt] = outs[0]
            if hasattr(haz, 'eid'):  # event based
                for update_losses in sec_losses:
                    update_losses(asset_df, out)
            yield out

    def get_dd5(self, adf, gmf_df, rng=None, C=0, crm=None):
        """
        :param adf:
            DataFrame of assets on the given site with the same taxonomy
        :param gmf_df:
            GMFs on the given site for E events
        :param rng:
            MultiEvent random generator or None
        :param C:
            Number of consequences
        :returns:
            damage distribution of shape (P, A, E, L, D+C)
        """
        A = len(adf)
        E = len(gmf_df)
        L = len(self.loss_types)
        D = self.D
        assets = adf.to_records()
        if rng is None:
            number = assets['value-number']
        else:
            number = assets['value-number'] = U32(assets['value-number'])
        dd5 = numpy.zeros((self.P, A, E, L, D + C), F32)
        outs = self.output(adf, gmf_df)  # dicts loss_type -> array
        for p, out in enumerate(outs):
            for li, lt in enumerate(self.loss_types):
                fractions = out[lt]  # shape (A, E, Dc)
                if rng is None:
                    for a in range(A):
                        dd5[p, a, :, li, :D] = fractions[a] * number[a]
                else:
                    # this is a performance distaster; for instance
                    # the Messina test in oq-risk-tests becomes 12x
                    # slower even if it has only 25_736 assets
                    dd5[p, :, :, li, :D] = rng.discrete_dmg_dist(
                        gmf_df.eid, fractions, number)

        if crm:
            csqs = crm.get_consequences()
            df = crm.tmap_df[crm.tmap_df.taxi == assets[0]['taxonomy']]
            csq = crm.compute_csq(assets, dd5[:, :, :, :, :D], df, crm.oqparam)
            csqidx = {dc: i for i, dc in enumerate(csqs, D)}
            for (cons, li), values in csq.items():
                dd5[:, :, :, li, csqidx[cons]] = values  # (P, A, E)
        return dd5

    def todict(self):
        """
        :returns: a literal dict describing the RiskComputer
        """
        rfdic = {}
        for rm in self.values():
            for peril, rfdict in rm.risk_functions.items():
                for lt, rf in rfdict.items():
                    dic = ast.literal_eval(hdf5.obj_to_json(rf))
                    if getattr(rf, 'retro', False):
                        retro = ast.literal_eval(hdf5.obj_to_json(rf.retro))
                        dic['openquake.risklib.scientific.VulnerabilityFunction'][
                            'retro'] = retro
                    rfdic['%s#%s#%s' % (rf.peril, lt, rf.id)] = dic
        dic = dict(risk_functions=rfdic, calculation_mode=self.calculation_mode)
        if any(mal for mal in self.minimum_asset_loss.values()):
            dic['minimum_asset_loss'] = self.minimum_asset_loss
        if any(self.wdic[k] != 1 for k in self.wdic):
            dic['wdic'] = {'%s#%s' % k: v for k, v in self.wdic.items()},
        return dic

    def pprint(self):
        dic = _reduce(self.todict())
        pprint(dic)


# ####################### Consequences ##################################### #


def consequence(consequence, assets, coeff, loss_type, time_event):
    """
    :param consequence: kind of consequence
    :param assets: asset array (shape A)
    :param coeff: composite array of coefficients of shape (A, E)
    :param time_event: time event string
    :returns: array of shape (A, E)
    """
    if consequence not in KNOWN_CONSEQUENCES:
        raise NotImplementedError(consequence)
    if consequence.startswith('losses'):
        res = (assets['value-' + loss_type].reshape(-1, 1) *
               coeff) / assets['value-number'].reshape(-1, 1)
        return res
    elif consequence in ['collapsed', 'non_operational']:
        return coeff
    elif consequence in ['injured', 'fatalities']:
        # NOTE: time_event default is 'avg'
        values = assets[f'occupants_{time_event}'] / assets['value-number']
        return values.reshape(-1, 1) * coeff
    elif consequence == 'homeless':
        values = assets['value-residents'] / assets['value-number']
        return values.reshape(-1, 1) * coeff
    else:
        raise NotImplementedError(consequence)


def get_agg_value(consequence, agg_values, agg_id, xltype, time_event):
    """
    :returns:
        sum of the values corresponding to agg_id for the given consequence
    """
    if consequence not in KNOWN_CONSEQUENCES:
        raise NotImplementedError(consequence)
    aval = agg_values[agg_id]
    if consequence in ['collapsed', 'non_operational']:
        return aval['number']
    elif consequence in ['injured', 'fatalities']:
        # NOTE: time_event default is 'avg'
        return aval[f'occupants_{time_event}']
    elif consequence == 'homeless':
        return aval['residents']
    elif 'loss' in consequence:
        if xltype.endswith('_ins'):
            xltype = xltype[:-4]
        if '+' in xltype:  # total loss type
            return sum(aval[lt] for lt in xltype.split('+'))
        try:
            return aval[xltype]
        except ValueError:  # liquefaction, landslide
            return 0
    else:
        raise NotImplementedError(consequence)


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
