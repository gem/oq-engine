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

import numpy
from scipy.stats import norm
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


def check_unique(df, kfields, fname):
    for k, rows in df.groupby(kfields):
        if len(rows) > 1:
            msg = 'Found duplicates for %s' % str(k)
            if fname:
                msg = '%s: %s' % (fname, msg)
            raise ValueError(msg)


class Amplifier(object):
    """
    Amplification class with methods .amplify and .amplify_gmfs.

    :param imtls:
        Intensity measure types and levels DictArray M x I
    :param ampl_df:
        A DataFrame containing amplification functions.
    :param amplevels:
        Intensity levels used for the amplified curves (if None, use the
        levels from the imtls dictionary)
    """
    def __init__(self, imtls, ampl_df, amplevels=None):
        if not imtls:
            raise ValueError('There are no intensity_measure_types!')
        fname = getattr(ampl_df, 'fname', None)
        self.imtls = imtls
        self.amplevels = amplevels
        self.vs30_ref = ampl_df.vs30_ref
        has_levels = 'level' in ampl_df.columns
        if has_levels:
            check_unique(ampl_df, ['ampcode', 'level'], fname)
        else:
            check_unique(ampl_df, ['ampcode'], fname)
        missing = set(imtls) - set(ampl_df.columns[has_levels:])
        if missing:
            raise ValueError('The amplification table does not contain %s'
                             % missing)
        if amplevels is None:  # for event based
            self.periods = [from_string(imt).period for imt in imtls]
        else:
            self.periods, levels = check_same_levels(imtls)
        self.coeff = {}  # code -> dataframe
        self.ampcodes = []
        cols = list(imtls)
        if has_levels:
            cols.append('level')
        for col in ampl_df.columns:
            if col.startswith('sigma_'):
                cols.append(col)
        for code, df in ampl_df.groupby('ampcode'):
            self.ampcodes.append(code)
            if has_levels:
                self.coeff[code] = df[cols].set_index('level')
            else:
                self.coeff[code] = df[cols]
        if amplevels is not None:  # PoEs amplification
            self.midlevels = numpy.diff(levels) / 2 + levels[:-1]  # shape I-1
            self.ialphas = {}  # code -> array of length I-1
            self.isigmas = {}  # code -> array of length I-1
            for code in self.coeff:
                for imt in imtls:
                    self.ialphas[code, imt], self.isigmas[code, imt] = (
                        self._interp(code, imt, self.midlevels))

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
        ialphas = self.ialphas[ampl_code, imt]
        isigmas = self.isigmas[ampl_code, imt]
        A, G = len(self.amplevels), poes.shape[1]
        ampl_poes = numpy.zeros((A, G))
        for g in range(G):
            p_occ = -numpy.diff(poes[:, g])
            for mid, p, a, s in zip(self.midlevels, p_occ, ialphas, isigmas):
                #
                # This computes the conditional probabilities of exceeding
                # defined values of shaking on soil given a value of shaking
                # on rock. 'mid' is the value of ground motion on rock to
                # which we associate the probability of occurrence 'p'. 'a'
                # is the median amplification factor and 's' is the standard
                # deviation of the logarithm of amplification.
                #
                # In the case of an amplification function without uncertainty
                # (i.e. sigma is zero) this will return values corresponding
                # to 'p' times 1 (if the value of shaking on rock will be
                # larger than the value of shaking on soil) or 0 (if the
                # value of shaking on rock will be smaller than the value of
                # shaking on soil)s
                #
                logaf = numpy.log(self.amplevels/mid)
                poes = (1.0-norm_cdf(logaf, numpy.log(a), s))
                ampl_poes[:, g] += (1.0-norm_cdf(logaf, numpy.log(a), s)) * p
                #print("mid {:6.4f} prb {:6.4f} median {:6.4f} std {:6.4f}".format(mid, p, a, s))
                #print(ampl_poes[:, g])
                #print("poes", poes)
                #print("\n")
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

    def _interp(self, ampl_code, imt_str, imls):
        # returns ialpha, isigma for the given levels
        coeff = self.coeff[ampl_code]
        if len(coeff) == 1:  # there is single coefficient for all levels
            ones = numpy.ones_like(imls)
            ialpha = float(coeff[imt_str]) * ones
            try:
                isigma = float(coeff['sigma_' + imt_str]) * ones
            except KeyError:
                isigma = numpy.zeros_like(imls)  # shape E
        else:
            alpha = coeff[imt_str]
            try:
                sigma = coeff['sigma_' + imt_str]
            except KeyError:
                isigma = numpy.zeros_like(imls)  # shape E
            else:
                isigma = numpy.interp(imls, alpha.index, sigma)  # shape E
            ialpha = numpy.interp(imls, alpha.index, alpha)  # shape E
        return ialpha, isigma

    def _amplify_gmvs(self, ampl_code, gmvs, imt_str):
        # gmvs is an array of shape E
        ialpha, isigma = self._interp(ampl_code, imt_str, gmvs)
        uncert = numpy.random.normal(numpy.zeros_like(gmvs), isigma)
        return numpy.exp(numpy.log(ialpha * gmvs) + uncert)

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
