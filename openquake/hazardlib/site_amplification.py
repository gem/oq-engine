# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from itertools import cycle
import numpy
from scipy.stats import norm
from openquake.baselib.general import group_array
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.probability_map import ProbabilityCurve
from openquake.commonlib.oqvalidation import check_same_levels


# this is necessary since norm.cdf for scale=0 returns NaNs
def norm_cdf(x, a, s):
    """
    Gaussian cumulative distribution function; if s=0, returns an
    Heaviside function instead. NB: for x=a, 0.5 is returned for all s.

    >>> norm_cdf(1.2, 1, .1)
    0.9772498680518208
    >>> norm_cdf(1.2, 1, 0)
    1.0
    >>> norm_cdf(.8, 1, .1)
    0.022750131948179216
    >>> norm_cdf(.8, 1, 0)
    0.0
    >>> norm_cdf(1, 1, .1)
    0.5
    >>> norm_cdf(1, 1, 0)
    0.5
    """
    if s == 0:
        return numpy.heaviside(x - a, .5)
    else:
        return norm.cdf(x, loc=a, scale=s)


def digitize(name, values, edges):
    """
    :param name: 'period' or 'level'
    :param values: periods or levels
    :param edges: available periods or levels
    :returns: the indices of the values in the bins

    If there are V values and E edges this functions returns an array
    with V elements in the range 0 .. E - 1; for instance:

    >>> digitize('period', [0, .1, .2], [0, .05, .1, .15, .20, .25])
    array([0, 2, 4])
    """
    if max(values) > max(edges):
        raise ValueError(
            f'The {name} {max(values)} is outside the edges {edges}')
    if min(values) < min(edges):
        raise ValueError(
            f'The {name} {min(values)} is outside the edges {edges}')
    edges = edges.copy()
    edges[-1] += 1E-5
    return numpy.digitize(values, edges) - 1


def check_unique(array, kfields, fname):
    for k, rows in group_array(array, *kfields).items():
        if len(rows) > 1:
            msg = 'Found duplicates %s' % rows[kfields]
            if fname:
                msg = '%s: %s' % (fname, msg)
            raise ValueError(msg)


def midlevels(levels):
    return numpy.diff(levels) / 2 + levels[:-1]


class Amplifier(object):
    """
    Amplification class with methods .amplify and .amplify_gmfs.

    :param imtls:
        intensity measure types and levels DictArray M x I
    :param ampl_funcs:
        an ArrayWrapper containing amplification functions
    :param amplevels:
        intensity levels used for the amplified curves (if None, use the
        levels from the imtls dictionary)
    """
    def __init__(self, imtls, ampl_funcs, amplevels=None):
        if not imtls:
            raise ValueError('There are no intensity_measure_types!')
        fname = getattr(ampl_funcs, 'fname', None)
        self.imtls = imtls
        self.vs30_ref = ampl_funcs.vs30_ref
        has_levels = 'level' in ampl_funcs.dtype.names
        if has_levels:
            self.imls = imls = numpy.array(sorted(set(ampl_funcs['level'])))
            check_unique(ampl_funcs.array, ['ampcode', 'level'], fname)
        else:
            self.imls = imls = ()
            check_unique(ampl_funcs.array, ['ampcode'], fname)
        cols = (ampl_funcs.dtype.names[2:] if has_levels
                else ampl_funcs.dtype.names[1:])
        imts = [from_string(imt) for imt in cols
                if not imt.startswith('sigma_')]
        if imtls.isnan():  # for event based
            self.periods = [from_string(imt).period for imt in imtls]
            self.midlevels = midlevels(imls if len(imls) else [0, 0])
        else:
            self.periods, levels = check_same_levels(imtls)
            self.amplevels = levels if amplevels is None else amplevels
            self.midlevels = midlevels(levels)
        m_indices = digitize(
            'period', self.periods, [imt.period for imt in imts])
        if len(imls) <= 1:  # 1 level means same values for all levels
            l_indices = [0]
        else:
            l_indices = digitize('level', self.midlevels, imls)
        L = len(l_indices)
        self.imtdict = {imt: str(imts[m]) for m, imt in zip(m_indices, imtls)}
        self.alpha = {}  # code, imt -> alphas
        self.sigma = {}  # code, imt -> sigmas
        self.ampcodes = []
        for code, arr in group_array(ampl_funcs, 'ampcode').items():
            self.ampcodes.append(code)
            for m in set(m_indices):
                im = str(imts[m])
                self.alpha[code, im] = alpha = numpy.zeros(L)
                self.sigma[code, im] = sigma = numpy.zeros(L)
                idx = 0
                import pdb; pdb.set_trace()
                for rec in arr[l_indices]:
                    alpha[idx] = rec[im]
                    try:
                        sigma[idx] = rec['sigma_' + im]
                    except ValueError:  # missing sigma
                        pass
                    idx += 1

    def check(self, vs30, vs30_tolerance):
        """
        Raise a ValueError if some vs30 is different from vs30_ref
        within the tolerance. Called by the engine.
        """
        if (numpy.abs(vs30 - self.vs30_ref) > vs30_tolerance).any():
            raise ValueError('Some vs30 in the site collection is different '
                             'from vs30_ref=%d over the tolerance of %d' %
                             (self.vs30_ref, vs30_tolerance))

    def amplify_one(self, ampl_code, imt, poes):
        """
        :param ampl_code: code for the amplification function
        :param imt: an intensity measure type
        :param poes: the original PoEs as an array of shape (I, G)
        :returns: the amplified PoEs as an array of shape (A, G)
        """
        if isinstance(poes, list):  # in the tests
            poes = numpy.array(poes).reshape(-1, 1)
        if ampl_code == b'' and len(self.ampcodes) == 1:
            # manage the case of a site collection with empty ampcode
            ampl_code = self.ampcodes[0]
        stored_imt = self.imtdict[imt]
        alphas = self.alpha[ampl_code, stored_imt]  # array with I-1 elements
        sigmas = self.sigma[ampl_code, stored_imt]  # array with I-1 elements
        A, G = len(self.amplevels), poes.shape[1]
        ampl_poes = numpy.zeros((A, G))
        for g in range(G):
            p_occ = -numpy.diff(poes[:, g])
            for mid, p, a, s in zip(
                    self.midlevels, p_occ, cycle(alphas), cycle(sigmas)):
                ampl_poes[:, g] += (1-norm_cdf(self.amplevels/mid, a, s)) * p
        return ampl_poes

    def amplify(self, ampl_code, pcurves):
        """
        :param ampl_code: 2-letter code for the amplification function
        :param pcurves: a list of ProbabilityCurves containing PoEs
        :returns: amplified ProbabilityCurves
        """
        out = []
        for pcurve in pcurves:
            lst = []
            for imt in self.imtls:
                slc = self.imtls(imt)
                new = self.amplify_one(ampl_code, imt, pcurve.array[slc])
                lst.append(new)
            out.append(ProbabilityCurve(numpy.concatenate(lst)))
        return out

    def _amplify_gmvs(self, ampl_code, gmvs, imt_str):
        # gmvs is an array of shape E
        imt = self.imtdict[imt_str]
        alphas = self.alpha[ampl_code, imt]  # shape L
        sigmas = self.sigma[ampl_code, imt]  # shape L
        if len(self.imls):  # there are multiple alphas, sigmas
            ialphas = numpy.interp(gmvs, self.midlevels, alphas)  # shape E
            isigmas = numpy.interp(gmvs, self.midlevels, sigmas)  # shape E
        else:  # there is a single alpha, sigma
            ialphas = alphas[0]
            isigmas = sigmas[0]
        uncert = numpy.random.normal(numpy.zeros_like(gmvs), isigmas)
        return numpy.exp(numpy.log(ialphas * gmvs) + uncert)

    def amplify_gmfs(self, ampcodes, gmvs, imts, seed=0):
        """
        Amplify in-place the gmvs array of shape (M, N, E)

        :param ampcodes: N codes for the amplification functions
        :param gmvs: ground motion values
        :param imts: intensity measure types
        :param seed: seed used when adding the uncertainty
        """
        numpy.random.seed(seed)
        for m, imt in enumerate(imts):
            for i, (ampcode, arr) in enumerate(zip(ampcodes, gmvs[m])):
                gmvs[m, i] = self._amplify_gmvs(ampcode, arr, str(imt))
