# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2016-2025 GEM Foundation
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
"""
Utilities to compute mean and quantile curves
"""
import math
import numpy
import pandas
from scipy.stats import norm
from openquake.baselib.general import AccumDict, agg_probs
from openquake.baselib.performance import compile
try:
    import numba
    SQRT05 = math.sqrt(0.5)

    @numba.vectorize("float64(float64)")
    def ndtr(z):
        return 0.5 * (1.0 + math.erf(z * SQRT05))
except ImportError:
    from scipy.special import ndtr


@compile(["float64[:,:](float64, float64[:,:])",
          "float64[:](float64, float64[:])"])
def truncnorm_sf(phi_b, values):
    """
    Fast survival function for truncated normal distribution.
    Assumes zero mean, standard deviation equal to one and symmetric
    truncation. It is faster than using scipy.stats.truncnorm.sf.

    :param phi_b:
         ndtr(truncation_level); assume phi_b > .5
    :param values:
         Numpy array of values as input to a survival function for the given
         distribution.
    :returns:
         Numpy array of survival function results in a range between 0 and 1.
         For phi_b close to .5 returns a step function 1 1 1 1 .5 0 0 0 0 0.
    """
    # notation from http://en.wikipedia.org/wiki/Truncated_normal_distribution.
    # given that mu = 0 and sigma = 1, we have alpha = a and beta = b.
    # "CDF" in comments refers to cumulative distribution function
    # of non-truncated distribution with that mu and sigma values.
    # assume symmetric truncation, that is ``a = - truncation_level``
    # and ``b = + truncation_level``.
    # calculate Z as ``Z = CDF(b) - CDF(a)``, here we assume that
    # ``CDF(a) == CDF(- truncation_level) == 1 - CDF(b)``
    z = phi_b * 2. - 1.

    # calculate the result of survival function of ``values``,
    # and restrict it to the interval where probability is defined --
    # 0..1. here we use some transformations of the original formula
    # that is ``SF(x) = 1 - (CDF(x) - CDF(a)) / Z`` in order to minimize
    # number of arithmetic operations and function calls:
    # ``SF(x) = (Z - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(a) - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(x)) / Z``.
    return ((phi_b - ndtr(values)) / z).clip(0., 1.)


def norm_cdf(x, a, s):
    """
    Gaussian cumulative distribution function; if s=0, returns an
    Heaviside function instead. NB: for x=a, 0.5 is returned for all s.

    >>> round(norm_cdf(1.2, 1, .1), 10)
    0.9772498681
    >>> norm_cdf(1.2, 1, 0)
    1.0
    >>> round(norm_cdf(.8, 1, .1), 10)
    0.0227501319
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


def calc_momenta(array, weights):
    """
    :param array: an array of shape (E, ...)
    :param weights: an array of length E
    :returns: an array of shape (3, ...) with the first 3 statistical moments
    """
    momenta = numpy.zeros((3,) + array.shape[1:])
    momenta[0] = weights.sum()
    momenta[1] = numpy.einsum('i,i...', weights, array)
    momenta[2] = numpy.einsum('i,i...', weights, array**2)
    return momenta


def calc_avg_std(momenta):
    """
    :param momenta: an array of shape (2, ...) obtained via calc_momenta
    :param totweight: total weight to divide for
    :returns: an array of shape (2, ...) with average and standard deviation

    >>> arr = numpy.array([[2, 4, 6], [3, 5, 7]])
    >>> weights = numpy.ones(2)
    >>> calc_avg_std(calc_momenta(arr, weights))
    array([[2.5, 4.5, 6.5],
           [0.5, 0.5, 0.5]])
    """
    avgstd = numpy.zeros_like(momenta[1:])
    avgstd[0] = avg = momenta[1] / momenta[0]
    # make sure the variance is positive (due to numeric errors can be -1E-9)
    var = numpy.maximum(momenta[2] / momenta[0] - avg ** 2, 0.)
    avgstd[1] = numpy.sqrt(var)
    return avgstd


def avg_std(array, weights=None):
    """
    :param array: an array of shape E, ...
    :param weights: an array of length E (or None for equal weights)
    :returns: an array of shape (2, ...) with average and standard deviation

    >>> avg_std(numpy.array([[2, 4, 6], [3, 5, 7]]))
    array([[2.5, 4.5, 6.5],
           [0.5, 0.5, 0.5]])
    """
    if weights is None:
        weights = numpy.ones(len(array))
    return calc_avg_std(calc_momenta(array, weights))


def geom_avg_std(array, weights=None):
    """
    :returns: geometric mean and geometric stddev (see
              https://en.wikipedia.org/wiki/Log-normal_distribution)
    """
    return numpy.exp(avg_std(numpy.log(array), weights))


def mean_curve(values, weights=None):
    """
    Compute the mean by using numpy.average on the first axis.
    """
    if weights is None:
        weights = [1. / len(values)] * len(values)
    if not isinstance(values, numpy.ndarray):
        values = numpy.array(values)
    return numpy.average(values, axis=0, weights=weights)


def std_curve(values, weights=None):
    if weights is None:
        weights = [1. / len(values)] * len(values)
    m = mean_curve(values, weights)
    res = numpy.sqrt(numpy.einsum('i,i...', weights, (m - values) ** 2))
    return res

cw_dt = numpy.dtype([('c', float), ('w', float)])


# NB: for equal weights and sorted values the quantile is computed as
# numpy.interp(q, [1/N, 2/N, ..., N/N], values)
def quantile_curve(quantile, curves, weights=None):
    """
    Compute the weighted quantile aggregate of an array or list of arrays

    :param quantile:
        Quantile value to calculate. Should be in the range [0.0, 1.0].
    :param curves:
        R arrays
    :param weights:
        R weights with sum 1, or None
    :returns:
        A numpy array representing the quantile of the underlying arrays

    >>> arr = numpy.array([.15, .25, .3, .4, .5, .6, .75, .8, .9])
    >>> quantile_curve(.8, arr)
    array(0.76)
    >>> quantile_curve(.85, numpy.array([.15, .15, .15]))  # constant array
    array(0.15)
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
        cw = numpy.zeros(R, cw_dt)  # (curve, weight)
        cw['c'] = curves[(slice(None), ) + idx]
        cw['w'] = weights
        cw.sort(order='c')
        # get the quantile from the interpolated CDF
        result[idx] = numpy.interp(quantile, cw['w'].cumsum(), cw['c'])
    return result


# NB: this will be obsolete in numpy 2+
def weighted_quantiles(qs, values, weights):
    """
    Compute weighted quantiles
    """
    vw = numpy.zeros(len(values), cw_dt)  # (value, weight)
    vw['c'] = values
    vw['w'] = weights
    vw.sort(order='c')
    return numpy.interp(qs, vw['w'].cumsum() / vw['w'].sum(), vw['c'])


def max_curve(values, weights=None):
    """
    Compute the maximum curve by taking the upper limits of the values;
    the weights are ignored and present only for API compatibility.
    The values can be arrays and then the maximum is taken pointwise:

    >>> max_curve([numpy.array([.3, .2]), numpy.array([.1, .4])])
    array([0.3, 0.4])
    """
    return numpy.max(values, axis=0)


def compute_pmap_stats(pmaps, stats, weights, imtls):
    """
    :param pmaps:
        a list of R probability maps
    :param stats:
        a sequence of S statistic functions
    :param weights:
        a list of ImtWeights
    :param imtls:
        a DictArray of intensity measure types
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
    sids = numpy.array(sorted(sids), numpy.uint32)
    nstats = len(stats)
    curves = numpy.zeros((len(pmaps), len(sids), L), numpy.float64)
    for i, pmap in enumerate(pmaps):
        for j, sid in enumerate(sids):
            if sid in pmap:
                curves[i, j] = pmap[sid].array[:, 0]
    out = p0.__class__.build(L, nstats, sids)
    for imt in imtls:
        slc = imtls(imt)
        w = [weight[imt] if hasattr(weight, 'dic') else weight
             for weight in weights]
        if sum(w) == 0:  # expect no data for this IMT
            continue
        for i, array in enumerate(compute_stats(curves[:, :, slc], stats, w)):
            for j, sid in numpy.ndenumerate(sids):
                out[sid].array[slc, i] = array[j]
    return out


def calc_stats(df, kfields, stats, weights):
    """
    :param df: a pandas DataFrame with a column rlz_id
    :param kfields: fields used in the group by
    :param stats: a dictionary stat_name->stat_func
    :param weights: an array of weights for each realization
    :returns: a DataFrame with the statistics
    """
    acc = AccumDict(accum=[])
    vfields = [f for f in df.columns if f not in kfields and f != 'rlz_id']
    # in aggrisk kfields=['agg_id', 'loss_type']
    # in aggcurves kfields=['agg_id', 'return_period', 'loss_type']
    for key, group in df.groupby(kfields):
        for name, func in stats.items():
            for k, kf in zip(key, kfields):
                acc[kf].append(k)
            for vf in vfields:
                values = numpy.zeros_like(weights)  # shape R
                values[group.rlz_id] = getattr(group, vf).to_numpy()
                v = func(values, weights)
                acc[vf].append(v)
            acc['stat'].append(name)
    return pandas.DataFrame(acc)


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
    array([([2.5, 3.5], 4.5)], dtype=[('a', '<f8', (2,)), ('b', '<f8')])
    """
    # NB: we are extending the calculation of statistics to the case of an
    # arraylist containing some scalars
    for arr in arraylist:
        if isinstance(arr, numpy.ndarray):
            dtype = arr.dtype
            shape = arr.shape
            break
    else:
        raise ValueError('No array found in the arraylist %s' % arraylist)
    # promote scalars to arrays of the given dtype and shape
    for i, arr in enumerate(arraylist):
        if numpy.isscalar(arr):
            arraylist[i] = numpy.ones(shape, dtype) * arr
    if dtype.names:  # composite array
        new = numpy.zeros(shape, dtype)
        for name in dtype.names:
            new[name] = f([arr[name] for arr in arraylist], *extra, **kw)
        return new
    else:  # simple array
        return f(arraylist, *extra, **kw)


def set_rlzs_stats(dstore, name, **attrs):
    """
    :param dstore: a DataStore object
    :param name: dataset name of kind <prefix>-rlzs
    """
    arrayNR = dstore[name][()]
    R = arrayNR.shape[1]
    pairs = list(attrs.items())
    pairs.insert(1, ('rlz', numpy.arange(R)))
    dstore.set_shape_descr(name, **dict(pairs))
    if R > 1:
        stats = dstore['oqparam'].hazard_stats()
        if not stats:
            return
        statnames, statfuncs = zip(*stats.items())
        weights = dstore['weights'][()]
        name = name.replace('-rlzs', '-stats')
        dstore[name] = compute_stats2(arrayNR, statfuncs, weights)
        pairs = list(attrs.items())
        pairs.insert(1, ('stat', statnames))
        dstore.set_shape_descr(name, **dict(pairs))


def combine_probs(values_by_grp, cmakers, rlz):
    """
    :param values_by_grp: C arrays of shape (D1, D2..., G)
    :param cmakers: C ContextMakers with G gsims each
    :param rlz: a realization index
    :returns: array of shape (D1, D2, ...)
    """
    probs = []
    for values, cmaker in zip(values_by_grp, cmakers):
        assert values.shape[-1] == len(cmaker.gsims)
        for g, rlzs in enumerate(cmaker.gsims.values()):
            if rlz in rlzs:
                probs.append(values[..., g])
    return agg_probs(*probs)


def average_df(dframes, weights=None):
    """
    Compute weighted average of DataFrames with the same index and columns.

    >>> df1 = pandas.DataFrame(dict(value=[1, 1, 1]), [1, 2, 3])
    >>> df2 = pandas.DataFrame(dict(value=[2, 2, 2]), [1, 2, 3])
    >>> average_df([df1, df2], [.4, .6])
       value
    1    1.6
    2    1.6
    3    1.6
    """
    d0 = dframes[0]
    n = len(dframes)
    if n == 1:
        return d0
    elif weights is None:
        weights = numpy.ones(n)
    elif len(weights) != n:
        raise ValueError('There are %d weights for %d dataframes!' %
                         (len(weights), n))
    data = numpy.average([df.to_numpy() for df in dframes],
                         weights=weights, axis=0)  # shape (E, C)
    return pandas.DataFrame({
        col: data[:, c] for c, col in enumerate(d0.columns)}, d0.index)
