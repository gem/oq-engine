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
import scipy.stats as sts
from openquake.baselib.general import AccumDict
from openquake.baselib.performance import Monitor
from openquake.hazardlib.imt import from_string


def get_uneven_bins_edges(lefts, num_bins):
    """

    :param lefts:
        The left edge of each bin + the largest right edge
    :param num_bins:
        The number of bins in each interval. Cardinality num(lefts) - 1
    :returns:
        A :class:`numpy.ndarray` instance
    """
    assert len(lefts) == len(num_bins) + 1, (len(lefts), len(num_bins))
    tmp = []
    for i, (left, numb) in enumerate(zip(lefts[:-1], num_bins)):
        low = 0 if i == 0 else 1
        nu = numb if i == len(num_bins) else numb + 1
        tmp.extend(numpy.linspace(left, lefts[i+1], nu)[low:])
    return numpy.array(tmp)


def update_mrd(ctxt: numpy.recarray, cm, crosscorr, mrd, monitor=Monitor()):
    """
    This computes the mean rate density by means of the multivariate
    normal function available in scipy.

    :param ctxt:
        A context array for a single site
    :param cm:
        A ContextMaker
    :param crosscorr:
        A cross correlation model
    :param mrd:
        An array with shape |imls| x |imls| x |gmms|
    """
    # Correlation matrix
    im1, im2 = cm.imtls
    imts = [from_string(im1), from_string(im2)]
    corrm = crosscorr.get_cross_correlation_mtx(imts)

    # Compute mean and standard deviation
    [mea, sig, _, _] = cm.get_mean_stds([ctxt])

    # Get the logarithmic IMLs
    ll1 = numpy.log(cm.imtls[im1])
    ll2 = numpy.log(cm.imtls[im2])
    grids = make_grids(ll1, ll2)

    # Update the MRD matrix. mea and sig have shape: G x L x N where G is
    # the number of GMMs, L is the number of intensity measure types and N
    # is the number of sites
    trate = 0
    for g, _ in enumerate(cm.gsims):
        for i, ctx in enumerate(ctxt):

            # Covariance and correlation mtxs
            slc0 = numpy.index_exp[g, :, i]
            slc1 = numpy.index_exp[g, 0, i]
            slc2 = numpy.index_exp[g, 1, i]
            cov = corrm[0, 1] * (sig[slc1] * sig[slc2])
            comtx = numpy.array([[sig[slc1]**2, cov], [cov, sig[slc2]**2]])

            # Compute the MRD for the current rupture
            mvn  = sts.multivariate_normal(mea[slc0], comtx)
            with monitor:  # this is ultra-slow!
                partial = get_mrd(mvn, grids)

            # Check
            msg = f'{numpy.max(partial):.8f}'
            if numpy.max(partial) > 1:
                raise ValueError(msg)

            # Scaling the joint PMF by the rate of occurrence of the
            # rupture. TODO address the case where we have the poes
            # instead of rates. MRD has shape: |imls| x |imls| x
            # |sites| x |gmms|
            mrd[:, :, g] += ctx.occurrence_rate * partial
            trate += ctx.occurrence_rate


def make_grids(ll1, ll2):
    # from two arrays of length L+1 to 4 arrays of shape (L, L, 2)
    lst = [(ll1[:-1], ll2[:-1]), (ll1[1:], ll2[:-1]),
           (ll1[:-1], ll2[1:]), (ll1[1:], ll2[1:])]
    grids = []
    for i, (ll1, ll2) in enumerate(lst):
        grid = numpy.meshgrid(ll1, ll2)
        grids.append(numpy.dstack(grid))  # shape (L, L, 2) -> (L, L)
    return grids


def get_mrd(mvn, grids):
    """
    :param mvn: a multivariate normal instance
    :param grids: a list of 4 arrays of shape (L, L)
    :returns: an array of shape (L, L)
    """
    # compute lower-left lower-right upper-left upper-right values
    LL, LR, UL, UR = 0, 1, 2, 3
    vals = mvn.cdf(grids)  # shape (4, L, L)
    partial = vals[UR] - vals[UL] - vals[LR] + vals[LL]
    # remove values below zero (mostly numerical errors)
    partial[partial < 0] = 0.0
    return partial


def update_mrd_indirect(ctx, cm, corrm, be_mea, be_sig, mrd, monitor=Monitor()):
    """
    This computes the mean rate density by means of the multivariate
    normal function available in scipy. Compared to the function `update_mrd`
    in this case we create a 4D matrix (very sparse) where we store the
    mean and std for the IMTs considered.

    :param ctx:
        A context array for a single site
    :param cm:
        A ContextMaker instance
    :param corrm:
        A cross correlation matrix
    :param mrd:
        An array with shape |imls| x |imls| x |gmms|
    :param be_mea:
        Bin edges mean
    :param be_sig:
        Bin edges std
    """
    C = len(ctx)
    len_be_mea = len(be_mea)
    len_be_sig = len(be_sig)

    # Compute mean and standard deviation
    [mea, sig, _, _] = cm.get_mean_stds([ctx])

    # Get the logarithmic IMLs
    imt1, imt2 = cm.imtls
    ll1 = cm.loglevels[imt1]
    ll2 = cm.loglevels[imt2]
    grids = make_grids(ll1, ll2)

    # mea and sig shape: G x M x N where G is the number of GMMs, M is the
    # number of intensity measure types and N is the number ruptures
    R, M1, M2, S1, S2 = 0, 1, 2, 3, 4
    for gid in range(len(cm.gsims)):
        # Slices
        slc1 = numpy.index_exp[gid, 0]
        slc2 = numpy.index_exp[gid, 1]

        # Find indexes needed for binning the results (fast)
        i_mea1 = numpy.searchsorted(be_mea, mea[slc1])
        i_mea2 = numpy.searchsorted(be_mea, mea[slc2])
        i_sig1 = numpy.searchsorted(be_sig, sig[slc1])
        i_sig2 = numpy.searchsorted(be_sig, sig[slc2])

        # Fix the last index (fast)
        i_mea1[i_mea1 == len_be_mea] = len_be_mea - 1
        i_mea2[i_mea2 == len_be_mea] = len_be_mea - 1
        i_sig1[i_sig1 == len_be_sig] = len_be_sig - 1
        i_sig2[i_sig2 == len_be_sig] = len_be_sig - 1

        # Stacking results (fast)
        acc = AccumDict(accum=numpy.zeros(5))
        for i, m1, m2, s1, s2 in zip(range(C), i_mea1, i_mea2, i_sig1, i_sig2):
            key = (m1, m2, s1, s2)
            arr = acc[key]
            arr[R] += ctx.occurrence_rate[i]
            arr[M1] += ctx.occurrence_rate[i] * mea[gid, 0, i]
            arr[M2] += ctx.occurrence_rate[i] * mea[gid, 1, i]
            arr[S1] += ctx.occurrence_rate[i] * sig[gid, 0, i]
            arr[S2] += ctx.occurrence_rate[i] * sig[gid, 1, i]

        # Compute MRD for all the combinations of GM and STD
        for key, arr in acc.items():
            # Covariance matrix
            tsig1 = arr[S1] / arr[R]
            tsig2 = arr[S2] / arr[R]
            cov = corrm[0, 1] * tsig1 * tsig2
            comtx = numpy.array([[tsig1**2, cov], [cov, tsig2**2]])

            # Get the MRD. The mean GM representing each bin is a weighted
            # mean (based on the rate of occurrence) of the GM from each
            # rupture
            means = [arr[M1] / arr[R], arr[M2] / arr[R]]
            mvn = sts.multivariate_normal(means, comtx)
            with monitor:  # this is ultra-slow!
                partial = get_mrd(mvn, grids)

            # Updating the MRD for site sid and ground motion model gid
            mrd[:, :, gid] += arr[R] * partial


def calc_mean_rate_dist(ctx, nsites, cmaker, crosscorr, imt1, imt2,
                        bins_mea, bins_sig, method='indirect', mon=Monitor()):
    """
    :param ctx: a context array
    :param num_sites: total number of sites (small)
    :param cmaker: a ContextMaker instance
    :param crosscorr: a CrossCorrelation instance
    :param str imt1: first IMT to consider (must be inside cmaker.imtls)
    :param str imt2: second IMT to consider (must be inside cmaker.imtls)
    :param bins_mea: bins for the mean
    :param bins_sig: bins for the standard deviation
    :param method: a string 'direct' or 'indirect'
    """
    cm = cmaker.restrict([imt1, imt2])
    G = len(cm.gsims)
    len1 = len(cm.imtls[imt1]) - 1
    corrm = crosscorr.get_cross_correlation_mtx(cm.imts)
    mrd = numpy.zeros((len1, len1, nsites, G))
    for sid in range(nsites):
        if method == 'direct':
            update_mrd(
                ctx[ctx.sids == sid], cm, crosscorr, mrd[:, :, sid], mon)
        else:
            update_mrd_indirect(
                ctx[ctx.sids == sid], cm, corrm,
                bins_mea, bins_sig, mrd[:, :, sid], mon)
    return mrd
