# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2022, GEM Foundation
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
        The number of bins in each interval. Cardinality |lefts| - 1
    :returns:
        A :class:`numpy.ndarray` instance
    """
    tmp = []
    for i, (left, numb) in enumerate(zip(lefts[:-1], num_bins)):
        low = 0 if i == 0 else 1
        nu = numb if i == len(num_bins) else numb + 1
        tmp.extend(numpy.linspace(left, lefts[i+1], nu)[low:])
    return numpy.array(tmp)


def update_mrd(ctx: numpy.recarray, cm, crosscorr, mrd, rng):
    """
    This computes the mean rate density by means of the multivariate
    normal function available in scipy.

    :param ctx:
        A context array
    :param cm:
        A ContextMaker
    :param crosscorr:
        A cross correlation model
    :param mrd:
        An array with shape |imls| x |imls| x |sites| x |gmms|
    :param rng:
        Random number generator used in multivariate_normal
    """
    # Correlation matrix
    im1, im2 = cm.imtls
    imts = [from_string(im1), from_string(im2)]
    corrm = crosscorr.get_cross_correlation_mtx(imts)

    # Compute mean and standard deviation
    [mea, sig, _, _] = cm.get_mean_stds([ctx])

    # Get the logarithmic IMLs
    ll1 = numpy.log(cm.imtls[im1])
    ll2 = numpy.log(cm.imtls[im2])

    # Update the MRD matrix. mea and sig have shape: G x L x N where G is
    # the number of GMMs, L is the number of intensity measure types and N
    # is the number of sites
    trate = 0
    for g, _ in enumerate(cm.gsims):
        for i, ctx in enumerate(ctx):

            # The the site ID
            sid = ctx.sids

            # Covariance and correlation mtxs
            slc0 = numpy.index_exp[g, :, i]
            slc1 = numpy.index_exp[g, 0, i]
            slc2 = numpy.index_exp[g, 1, i]
            cov = corrm[0, 1] * (sig[slc1] * sig[slc2])
            comtx = numpy.array([[sig[slc1]**2, cov], [cov, sig[slc2]**2]])

            # Compute the MRD for the current rupture
            partial = _get_mrd_one_rupture(mea[slc0], comtx, ll1, ll2, rng)

            # Check
            msg = f'{numpy.max(partial):.8f}'
            if numpy.max(partial) > 1:
                raise ValueError(msg)

            # Scaling the joint PMF by the rate of occurrence of the
            # rupture. TODO address the case where we have the poes
            # instead of rates. MRD has shape: |imls| x |imls| x
            # |sites| x |gmms|
            mrd[:, :, sid, g] += ctx.occurrence_rate * partial
            trate += ctx.occurrence_rate


def _get_mrd_one_rupture(means, comtx, im1, im2, rng):
    # :param means:
    #     The two values of the mean
    # :param comtx:
    #     The covariance matrix
    # :param im1:
    #     The intensity measure levels for the first IMT
    # :param im2:
    #     The intensity measure levels for the second IMT
    # :returns:
    #     A 2D array

    # Create bivariate gaussian distribution.
    mvn = sts.multivariate_normal(means, comtx, seed=rng)

    # Lower-left
    x1, x2 = numpy.meshgrid(im1[:-1], im2[:-1], sparse=False)
    vals_ll = mvn.cdf(numpy.dstack((x1, x2)))
    # Lower-right
    x1, x2 = numpy.meshgrid(im1[1:], im2[:-1], sparse=False)
    vals_lr = mvn.cdf(numpy.dstack((x1, x2)))
    # Upper-left
    x1, x2 = numpy.meshgrid(im1[:-1], im2[1:], sparse=False)
    vals_ul = mvn.cdf(numpy.dstack((x1, x2)))
    # Upper-right
    x1, x2 = numpy.meshgrid(im1[1:], im2[1:], sparse=False)
    vals_ur = mvn.cdf(numpy.dstack((x1, x2)))

    # Compute the values in each cell
    partial = vals_ur - vals_ul - vals_lr + vals_ll

    # Remove values that go below zero (mostly numerical errors)
    partial[partial < 0] = 0.0

    return partial


def update_mrd_indirect(ctx, cm, crosscorr, mrd, be_mea, be_sig,
                        rng, monitor=Monitor()):
    """
    This computes the mean rate density by means of the multivariate
    normal function available in scipy. Compared to the function `update_mrd`
    in this case we create a 4D matrix (very sparse) where we store the
    mean and std for the IMTs considered.

    :param ctx:
        A context array
    :param cm:
        A ContextMaker instance
    :param crosscorr:
        A cross correlation model
    :param mrd:
        An array with shape |imls| x |imls| x |sites| x |gmms|
    :param be_mea:
        Bin edges mean
    :param be_sig:
        Bin edges std
    :param rng:
        Random number generator used in multivariate_normal
    """
    len_be_mea = len(be_mea)
    len_be_sig = len(be_sig)

    # Correlation matrix
    keys = list(cm.imtls)
    imts = [from_string(k) for k in keys]
    corrm = crosscorr.get_cross_correlation_mtx(imts)

    # Compute mean and standard deviation
    [mea, sig, _, _] = cm.get_mean_stds([ctx])

    # Get the logarithmic IMLs
    ll1 = numpy.log(cm.imtls[keys[0]])
    ll2 = numpy.log(cm.imtls[keys[1]])

    # Unique site IDs
    unique_sids = numpy.unique(ctx.sids)  # the test has a single site

    # mea and sig shape: G x L x N where G is the number of GMMs, L is the
    # number of intensity measure types and N is the number of sites
    R, M1, M2, S1, S2 = 0, 1, 2, 3, 4
    for gid, _ in enumerate(cm.gsims):
        for sid in unique_sids:
            rates = AccumDict(accum=numpy.zeros(5))
            mask = ctx.sids == sid

            # Slices
            slc1 = numpy.index_exp[gid, 0, mask]
            slc2 = numpy.index_exp[gid, 1, mask]

            # Find indexes needed for binning the results
            i_mea1 = numpy.searchsorted(be_mea, mea[slc1])
            i_mea2 = numpy.searchsorted(be_mea, mea[slc2])
            i_sig1 = numpy.searchsorted(be_sig, sig[slc1])
            i_sig2 = numpy.searchsorted(be_sig, sig[slc2])

            # Fix the last index
            i_mea1[i_mea1 == len_be_mea] = len_be_mea - 1
            i_mea2[i_mea2 == len_be_mea] = len_be_mea - 1
            i_sig1[i_sig1 == len_be_sig] = len_be_sig - 1
            i_sig2[i_sig2 == len_be_sig] = len_be_sig - 1

            # Stacking results
            idx, = numpy.where(mask)
            for i, m1, m2, s1, s2 in zip(idx, i_mea1, i_mea2, i_sig1, i_sig2):
                key = (m1, m2, s1, s2)
                rate = rates[key]
                rate[R] += ctx.occurrence_rate[i]
                rate[M1] += ctx.occurrence_rate[i] * mea[gid, 0, i]
                rate[M2] += ctx.occurrence_rate[i] * mea[gid, 1, i]
                rate[S1] += ctx.occurrence_rate[i] * sig[gid, 0, i]
                rate[S2] += ctx.occurrence_rate[i] * sig[gid, 1, i]

            # Compute MRD for all the combinations of GM and STD
            for key, rate in rates.items():
                # Covariance matrix
                tsig1 = rate[S1] / rate[R]
                tsig2 = rate[S2] / rate[R]
                cov = corrm[0, 1] * tsig1 * tsig2
                comtx = numpy.array([[tsig1**2, cov], [cov, tsig2**2]])

                # Get the MRD. The mean GM representing each bin is a weighted
                # mean (based on the rate of occurrence) of the GM from each
                # rupture
                with monitor:
                    means = [rate[M1] / rate[R], rate[M2] / rate[R]]
                    partial = _get_mrd_one_rupture(means, comtx, ll1, ll2, rng)

                # Updating the MRD for site sid and ground motion model gid
                mrd[:, :, sid, gid] += rate[R] * partial
