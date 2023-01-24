# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
from openquake.hazardlib.stats import truncnorm_sf


def outdict(M, N, P, start, stop):
    """
    :param M: number of IMTs
    :param N: number of sites
    :param P: number of IMLs
    :param start: index
    :param stop: index > start
    """
    return {_g: numpy.zeros((M, N, 3, P)) for _g in range(start, stop)}


def _cs_out(mean_stds, probs, rho, imti, imls, cs_poes,
            phi_b, invtime, c, _c=None):
    M, N, O, P = c.shape
    U = len(probs) // N

    # For every site
    for n in range(N):
        # NB: to understand the code below, consider the case with
        # N=3 sites and U=2 ruptures; then there are N*U=6 indices:
        # 0: first site
        # 1: second site
        # 2: third site
        # 3: first site
        # 4: second site
        # 5: third site
        # i.e. idxs = [0, 3], [1, 4], [2, 5] for sites 0, 1, 2
        slc = slice(n, N * U, N)  # U indices

        mu = mean_stds[0, :, slc]  # shape (M, U)
        sig = mean_stds[1, :, slc]  # shape (M, U)

        for p, iml in enumerate(imls):

            # Calculate the contribution of each rupture to the total
            # probability of occurrence for the reference IMT. Both
            # `eps` and `poes` have shape U
            eps = (numpy.log(iml) - mu[imti]) / sig[imti]
            poes = truncnorm_sf(phi_b, eps)

            # Converting to rates and dividing by the rate of
            # exceedance of the reference IMT and level
            ws = -numpy.log((1. - probs[slc]) ** poes) / invtime

            # Normalizing by the AfE for the investigated IMT and level
            ws /= -numpy.log(1. - cs_poes[p])

            # weights not summing up to 1
            c[:, n, 0, p] = ws.sum()

            # For each intensity measure type
            for m in range(len(mu)):

                # Equation 14 in Lin et al. (2013)
                term1 = mu[m] + rho[m] * eps * sig[m]
                c[m, n, 1, p] = ws @ term1

                # This is executed only if we already have the final CS
                if _c is not None:

                    # Equation 15 in Lin et al. (2013)
                    term2 = sig[m] * (1. - rho[m]**2)**0.5
                    term3 = term1 - _c[m, n, 1, p]
                    c[m, n, 2, p] = ws @ (term2**2 + term3**2)


# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.845.163&rep=rep1&type=pdf
def get_cs_out(cmaker, ctx, imti, imls, _c=None):
    """
    Compute the contributions to the conditional spectra, in a form
    suitable for later composition.

    NB: at the present if works only for poissonian contexts

    :param ctx:
       a context array
    :param imti:
        IMT index in the range 0..M-1
    :param imls:
        P intensity measure levels for the IMT specified by the index;
        they are in correspondence with the probabilities in cmaker.poes
    :param _c:
        The previously computed contribution. This is used for the
        calculation of the stddev contribution.
    :returns:
        a dictionary g -> array where g is an index and the array has shape
        (M, N, O, P) with O=3

    """
    assert cmaker.tom
    assert len(imls) == len(cmaker.poes), (len(cmaker.poes), len(imls))
    sids, counts = numpy.unique(ctx.sids, return_counts=True)
    assert len(set(counts)) == 1, counts  # must be all equal
    N = len(sids)
    G = len(cmaker.gsims)
    M = len(cmaker.imtls)
    P = len(imls)

    # This is the output dictionary as explained above
    out = outdict(M, N, P, cmaker.gidx.min(), cmaker.gidx.max() + 1)

    mean_stds = cmaker.get_mean_stds([ctx])  # (4, G, M, N*U)
    imt_ref = cmaker.imts[imti]
    rho = numpy.array([cmaker.cross_correl.get_correlation(imt_ref, imt)
                       for imt in cmaker.imts])

    # This computes the probability of at least one occurrence
    # probs = 1 - exp(-occurrence_rates*time_span). NOTE that we
    # assume the contexts here are homogenous i.e. they either use
    # the occurrence rate or the probability of occurrence in the
    # investigation time
    if len(ctx.probs_occur[0]):
        probs = numpy.array([numpy.sum(p[1:]) for p in ctx.probs_occur])
    else:
        probs = cmaker.tom.get_probability_one_or_more_occurrences(
            ctx.occurrence_rate)  # shape N * U
    # For every GMM
    for i, g in enumerate(cmaker.gidx):
        _cs_out(mean_stds[:, i], probs, rho, imti, imls, cmaker.poes,
                cmaker.phi_b, cmaker.investigation_time,
                out[g], _c if _c is not None else None)
    return out


def cond_spectra(cmaker, srcs, sitecol, imt_ref, imls):
    """
    :param cmaker: a ContextMaker with a given TRT
    :param srcs: seismic sources of the given TRT
    :param sitecol: a SiteCollection object
    :param imt_ref: reference Intensity Measure Type (as a string)
    :param imls: Intensity Measure Levels corresponding to the poes
    :returns: conditional spectra and sigmas for the given imls as arrays
              of shape (G, M, N, P)
    """
    imti = list(cmaker.imtls).index(imt_ref)
    [ctx] = cmaker.from_srcs(srcs, sitecol)
    out0 = get_cs_out(cmaker, ctx, imti, imls)  # g -> MNOP
    mean = numpy.mean([out0[g] for g in out0], axis=0)  # MNOP
    out = get_cs_out(cmaker, ctx, imti, imls, mean)  # g -> MNOP
    G, M, N, P = len(cmaker.gsims), len(cmaker.imtls), len(sitecol), len(imls)
    spectra = numpy.zeros((G, M, N, P))
    s_sigma = numpy.zeros((G, M, N, P))
    for g, arr in out.items():
        spectra[g] = numpy.exp(arr[:, :, 1] / arr[:, :, 0])
        s_sigma[g] = numpy.sqrt(arr[:, :, 2] / arr[:, :, 0])
    return spectra, s_sigma
