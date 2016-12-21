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
    if weights is None:
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
    weights = numpy.array(weights)

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


# NB: this is a function linear in the array argument
def compute_stats(array, quantiles, weights):
    """
    :param array:
        an array of R elements (which can be arrays)
    :param quantile:
        a list of Q quantiles
    :param weights:
        a list of R weights
    :returns:
        an array of Q + 1 elements (which can be arrays)
    """
    result = numpy.zeros((len(quantiles) + 1,) + array.shape[1:], array.dtype)
    result[0] = mean_curve(array, weights)
    for i, q in enumerate(quantiles, 1):
        qc = quantile_curve(array, q, weights)
        result[i] = qc[0] if len(qc) == 1 else qc  # this is ugly
    return result


# like compute_stats, but on a matrix of shape (N, R)
def compute_stats2(arrayNR, quantiles, weights):
    """
    :param arrayNR:
        an array of (N, R) elements
    :param quantile:
        a list of Q quantiles
    :param weights:
        a list of R weights
    :returns:
        an array of (N, Q + 1) elements
    """
    newshape = list(arrayNR.shape)
    newshape[1] = len(quantiles) + 1  # number of statistical outputs
    newarray = numpy.zeros(newshape, arrayNR.dtype)
    data = [arrayNR[:, i] for i in range(len(weights))]
    newarray[:, 0] = apply_stat(mean_curve, data, weights)
    for i, q in enumerate(quantiles, 1):
        newarray[:, i] = apply_stat(quantile_curve, data, q, weights)
    return newarray


def apply_stat(f, arraylist, *extra, **kw):
    """
    :param f: a callable arraylist -> array (of the same shape and dtype)
    :param arraylist: a list of arrays of the same shape and dtype
    :param extra: additional arguments
    :returns: an array of the same shape and dtype

    Broadcast statistical functions to composite arrays. Here is an example:

    >>> dt = numpy.dtype([('a', (float, 2)), ('b', float)])
    >>> a1 = numpy.array([([1, 2], 3)], dt)
    >>> a2 = numpy.array([([4, 5], 6)], dt)
    >>> apply_stat(mean_curve, [a1, a2])
    array([([2.5, 3.5], 4.5)], 
          dtype=[('a', '<f8', (2,)), ('b', '<f8')])
    """
    dtype = arraylist[0].dtype
    shape = arraylist[0].shape
    if dtype.names:  # composite array
        new = numpy.zeros(shape, dtype)
        for name in dtype.names:
            new[name] = f([arr[name] for arr in arraylist], *extra, **kw)
        return new
    else:  # simple array
        return f(arraylist, *extra, **kw)
