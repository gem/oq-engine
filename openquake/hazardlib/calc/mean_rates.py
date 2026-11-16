# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025-2026 GEM Foundation
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

import numpy
from openquake.hazardlib.rmap_maker import get_cmakers, get_unique_inverse

F32 = numpy.float32
CUTOFF = 1E-12


def to_rates(probs, itime=1, minrate=0.):
    """
    Convert an array of probabilities into an array of rates

    >>> numpy.round(to_rates(numpy.array([.8])), 6)
    array([1.609438])
    """
    pnes = 1. - probs
    pnes[pnes == 0] = 1E-45  # minimum 32 bit float
    # NB: the test most sensitive to 1E-45 and 1E-12 is case_78
    rates = - numpy.log(pnes) / itime
    rates[rates < CUTOFF] = minrate
    rates[rates > 100.] = 100.
    return rates


def to_probs(rates, itime=1):
    """
    Convert an array of rates into an array of probabilities

    >>> numpy.round(to_probs(numpy.array([1.609438])), 6)
    array([0.8])
    """
    return 1. - numpy.exp(- rates * itime)


def get_gweights(src_groups, full_lt):
    """
    :returns: the weights of the gids of the rates, with shape (Gt, M+1),
        numbered as in get_cmakers, i.e. with the same unique trt_smrs
    """
    all_trt_smrs = [sg[0].trt_smrs for sg in src_groups]
    unique_trt_smrs, _inverse = get_unique_inverse(all_trt_smrs)
    return full_lt.g_weights(unique_trt_smrs)


def get_rmap(src_groups, full_lt, sitecol, oq):
    """
    :returns: a MapArray of rates with shape (N, L, Gt)
    """
    oq.use_rates = True
    oq.disagg_by_src = False
    all_trt_smrs = [sg[0].trt_smrs for sg in src_groups]
    cmakers = get_cmakers(all_trt_smrs, full_lt, oq)
    rmap = cmakers.get_rmap(src_groups, sitecol)
    return rmap, cmakers


def calc_mean_rates(rmap, gweights, wget, imtls):
    """
    :returns: mean hazard rates as an array of shape (N, M, L1)
    """
    L1 = imtls.size // len(imtls)
    N = len(rmap.array)
    M = len(imtls)
    if len(gweights.shape) == 1:  # fast_mean
        return (rmap.array @ gweights).reshape(N, M, L1)
    rates = numpy.zeros((N, M, L1))
    for m, imt in enumerate(imtls):
        rates[:, m, :] = rmap.array[:, imtls(imt), :] @ wget(gweights, imt)
    return rates


# useful for debugging
def calc_mcurves(src_groups, sitecol, full_lt, oq):
    """
    Compute the mean hazard curves with use_rates. This is less
    efficient than the algorithm used in the engine and can run out
    of memory. It is meant to generate the expected results in small tests.

    :param src_groups: a list of source groups
    :param sitecol: a SiteCollection instance
    :param full_lt: a FullLogicTree instance
    :param oq: an OqParam instance
    :returns: an array of probabilities of shape (N, M, L1), and Gt weights
    """
    assert oq.use_rates
    rmap, cmakers = get_rmap(src_groups, full_lt, sitecol, oq)
    gweights = get_gweights(src_groups, full_lt)  # shape (Gt, M+1)
    rates = calc_mean_rates(rmap, gweights, full_lt.gsim_lt.wget, oq.imtls)
    # the default weights are returned, as in the case without IMT-dependent
    # weights, while the rates are computed with the IMT-dependent ones
    return to_probs(rates), gweights[:, -1]
