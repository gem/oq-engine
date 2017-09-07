#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016-2017 GEM Foundation

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
from __future__ import division
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


def quantile_curve(quantile, curves, weights=None):
    """
    Compute the weighted quantile aggregate of a set of curves.

    :param quantile:
        Quantile value to calculate. Should be in the range [0.0, 1.0].
    :param curves:
        Array of R PoEs (possibly arrays)
    :param weights:
        Array-like of weights, 1 for each input curve, or None
    :returns:
        A numpy array representing the quantile aggregate
    """
    if not isinstance(curves, numpy.ndarray):
        curves = numpy.array(curves)
    R = len(curves)
    if weights is None:
        weights = numpy.ones(R) / R
    else:
        weights = numpy.array(weights)
        assert len(weights) == R, (len(weights), R)
    result = numpy.zeros(curves.shape[1:])
    for idx, _ in numpy.ndenumerate(result):
        data = numpy.array([a[idx] for a in curves])
        sorted_idxs = numpy.argsort(data)
        sorted_weights = weights[sorted_idxs]
        sorted_data = data[sorted_idxs]
        cum_weights = numpy.cumsum(sorted_weights)
        # get the quantile from the interpolated CDF
        result[idx] = numpy.interp(quantile, cum_weights, sorted_data)
    return result


def max_curve(values, weights=None):
    """
    Compute the maximum curve by taking the upper limits of the values;
    the weights are ignored and present only for API compatibility.
    The values can be arrays and then the maximum is taken pointwise:

    >>> max_curve([numpy.array([.3, .2]), numpy.array([.1, .4])])
    array([ 0.3,  0.4])
    """
    return numpy.max(values, axis=0)


def compute_pmap_stats(pmaps, stats, weights):
    """
    :param pmaps:
        a list of R probability maps
    :param stats:
        a sequence of S statistic functions
    :param weights:
        a list of R weights
    :returns:
        a probability map with S internal values
    """
    sids = set()
    p0 = next(iter(pmaps))
    L = p0.shape_y
    for pmap in pmaps:
        sids.update(pmap)
        assert pmap.shape_y == L, (pmap.shape_y, L)
    if len(sids) == 0:
        raise ValueError('All empty probability maps!')
    sids = numpy.array(sorted(sids), numpy.float32)
    nstats = len(stats)
    curves = numpy.zeros((len(pmaps), len(sids), L), numpy.float64)
    for i, pmap in enumerate(pmaps):
        for j, sid in enumerate(sids):
            if sid in pmap:
                curves[i][j] = pmap[sid].array[:, 0]
    out = p0.__class__.build(L, nstats, sids)
    for i, array in enumerate(compute_stats(curves, stats, weights)):
        for j, sid in numpy.ndenumerate(sids):
            out[sid].array[:, i] = array[j]
    return out


# NB: this is a function linear in the array argument
def compute_stats(array, stats, weights):
    """
    :param array:
        an array of R elements (which can be arrays)
    :param stats:
        a sequence of S statistic functions
    :param weights:
        a list of R weights
    :returns:
        an array of S elements (which can be arrays)
    """
    result = numpy.zeros((len(stats),) + array.shape[1:], array.dtype)
    for i, func in enumerate(stats):
        result[i] = apply_stat(func, array, weights)
    return result


# like compute_stats, but on a matrix of shape (N, R)
def compute_stats2(arrayNR, stats, weights):
    """
    :param arrayNR:
        an array of (N, R) elements
    :param stats:
        a sequence of S statistic functions
    :param weights:
        a list of R weights
    :returns:
        an array of (N, S) elements
    """
    newshape = list(arrayNR.shape)
    if newshape[1] != len(weights):
        raise ValueError('Got %d weights but %d values!' %
                         (len(weights), newshape[1]))
    newshape[1] = len(stats)  # number of statistical outputs
    newarray = numpy.zeros(newshape, arrayNR.dtype)
    data = [arrayNR[:, i] for i in range(len(weights))]
    for i, func in enumerate(stats):
        newarray[:, i] = apply_stat(func, data, weights)
    return newarray


def apply_stat(f, arraylist, *extra, **kw):
    """
    :param f: a callable arraylist -> array (of the same shape and dtype)
    :param arraylist: a list of arrays of the same shape and dtype
    :param extra: additional positional arguments
    :param kw: keyword arguments
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
