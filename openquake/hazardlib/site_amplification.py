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
from openquake.baselib.general import group_array
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.probability_map import ProbabilityCurve
from openquake.commonlib.oqvalidation import check_same_levels


class Amplifier(object):
    """
    :param imtls: intensity measure types and levels DictArray
    :param ampl_funcs: an ArrayWrapper containing amplification functions
    :param alevels: levels used for the amplified curves
    """
    def __init__(self, imtls, ampl_funcs, alevels):
        self.imtls = imtls
        self.alevels = alevels
        self.periods, self.levels = check_same_levels(imtls)
        imls = ampl_funcs.imls
        imts = [from_string(imt) for imt in ampl_funcs.dtype.names[2:]
                if not imt.startswith('sigma_')]
        m_indices = self.digitize(
            'period', self.periods, [imt.period for imt in imts])
        self.imtdict = {imt: str(imts[m]) for m, imt in zip(m_indices, imtls)}
        l_indices = self.digitize('level', self.levels, imls)
        L = len(l_indices)
        self.alpha = {}  # code, imt -> alphas
        self.sigma = {}  # code, imt -> sigmas
        has_sigma = any(imt.startswith('sigma_')
                        for imt in ampl_funcs.dtype.names[2:])
        for code, arr in group_array(ampl_funcs, 'amplification').items():
            for m in set(m_indices):
                im = str(imts[m])
                self.alpha[code, im] = alpha = numpy.zeros(L)
                self.sigma[code, im] = sigma = numpy.zeros(L)
                idx = 0
                for rec in arr[l_indices]:
                    alpha[idx] = rec[im]
                    if has_sigma:
                        sigma[idx] = rec['sigma_' + im]
                    idx += 1

    def digitize(self, name, values, bins):
        """
        :param name: 'period' or 'level'
        :param values: periods or levels
        :param bins: available periods or levels
        :returns: the indices of the values in the bins
        """
        if max(values) > max(bins):
            raise ValueError(
                f'The {name} {max(values)} is outside the bins {bins}')
        if min(values) < min(bins):
            raise ValueError(
                f'The {name} {min(values)} is outside the bins {bins}')
        return numpy.digitize(values, bins) - 1

    def amplify_one(self, ampl_code, imt, poes):
        """
        :param ampl_code: 2-letter code for the amplification function
        :param imt: an intensity measure type
        :param poes: the original PoEs
        :returns: the amplified PoEs
        """
        stored_imt = self.imtdict[imt]
        alphas = self.alpha[ampl_code, stored_imt]
        sigmas = self.sigma[ampl_code, stored_imt]
        ampl_poes = numpy.zeros_like(self.alevels)
        for l, p, a, s in zip(self.levels, -numpy.diff(poes), alphas, sigmas):
            ampl_poes += (1. - norm.cdf(self.alevels / l, loc=a, scale=s)) * p
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
                new = self.amplify_one(ampl_code, imt, pcurve.array[slc, 0])
                lst.append(new)
            out.append(ProbabilityCurve(numpy.concatenate(lst).reshape(-1, 1)))
        return out
