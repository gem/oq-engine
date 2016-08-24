#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
Utilities to compute mean and quantile curves
"""
import numpy


def mean_curve(values, weights=None):
    """
    Compute the mean by using numpy.average on the first axis.
    """
    if weights:
        weights = list(map(float, weights))
        assert abs(sum(weights) - 1.) < 1E-12, sum(weights) - 1.
    else:
        weights = [1. / len(values)] * len(values)
    if isinstance(values[0], (numpy.ndarray, list, tuple)):  # fast lane
        return numpy.average(values, axis=0, weights=weights)
    return sum(value * weight for value, weight in zip(values, weights))


def quantile_curve(curves, quantile, weights=None):
    """
    Compute the weighted quantile aggregate of a set of curves
    when using the logic tree end-branch enumeration approach, or just the
    standard quantile when using the sampling approach.

    :param curves:
        2D array-like of curve PoEs. Each row represents the PoEs for a single
        curve
    :param quantile:
        Quantile value to calculate. Should be in the range [0.0, 1.0].
    :param weights:
        Array-like of weights, 1 for each input curve, or None
    :returns:
        A numpy array representing the quantile aggregate
    """
    assert len(curves)
    if weights is None:
        # this implementation is an alternative to
        # numpy.array(mstats.mquantiles(curves, prob=quantile, axis=0))[0]
        # more or less copied from the scipy mquantiles function, just special
        # cased for what we need (and a lot faster)
        arr = numpy.array(curves).reshape(len(curves), -1)
        p = numpy.array(quantile)
        m = 0.4 + p * 0.2
        n = len(arr)
        aleph = n * p + m
        k = numpy.floor(aleph.clip(1, n - 1)).astype(int)
        gamma = (aleph - k).clip(0, 1)
        data = numpy.sort(arr, axis=0).transpose()
        qcurve = (1.0 - gamma) * data[:, k - 1] + gamma * data[:, k]
        return qcurve

    # Each curve needs to be associated with a weight
    assert len(weights) == len(curves)
    weights = numpy.array(weights, dtype=numpy.float64)

    result_curve = []
    np_curves = numpy.array(curves).reshape(len(curves), -1)
    np_weights = numpy.array(weights)
    for poes in np_curves.transpose():
        sorted_poe_idxs = numpy.argsort(poes)
        sorted_weights = np_weights[sorted_poe_idxs]
        sorted_poes = poes[sorted_poe_idxs]
        cum_weights = numpy.cumsum(sorted_weights)
        result_curve.append(numpy.interp(quantile, cum_weights, sorted_poes))

    shape = getattr(curves[0], 'shape', None)
    if shape:  # passed a sequence of arrays
        return numpy.array(result_curve).reshape(shape)
    else:  # passed a sequence of numbers
        return result_curve


def mean_quantiles(curves_by_rlz, quantiles=(), weights=None):
    """
    :param curves_by_rlz: a list of R arrays of shape N x L
    :param quantiles: a list of quantile PoEs (can be empty)
    :param weights: a list of R weights (or None)
    :returns: a list [mean, quantile...]
    """
    nsites = len(curves_by_rlz[0])
    return [mean_curve(curves_by_rlz, weights)] + [
        quantile_curve(curves_by_rlz, q, weights).reshape((nsites, -1))
        for q in quantiles]
