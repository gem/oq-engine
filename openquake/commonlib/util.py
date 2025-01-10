# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
from openquake.baselib import config, python3compat
from openquake.commonlib import datastore

F32 = numpy.float32
read = datastore.read


def max_rel_diff(curve_ref, curve, min_value=0.01):
    """
    Compute the maximum relative difference between two curves. Only values
    greather or equal than the min_value are considered.

    >>> curve_ref = [0.01, 0.02, 0.03, 0.05, 1.0]
    >>> curve = [0.011, 0.021, 0.031, 0.051, 1.0]
    >>> round(max_rel_diff(curve_ref, curve), 2)
    0.1
    """
    assert len(curve_ref) == len(curve), (len(curve_ref), len(curve))
    assert len(curve), 'The curves are empty!'
    max_diff = 0
    for c1, c2 in zip(curve_ref, curve):
        if c1 >= min_value:
            max_diff = max(max_diff, abs(c1 - c2) / c1)
    return max_diff


def max_rel_diff_index(curve_ref, curve, min_value=0.01):
    """
    Compute the maximum relative difference between two sets of curves.
    Only values greather or equal than the min_value are considered.
    Return both the maximum difference and its location (array index).

    >>> curve_refs = [[0.01, 0.02, 0.03, 0.05], [0.01, 0.02, 0.04, 0.06]]
    >>> curves = [[0.011, 0.021, 0.031, 0.051], [0.012, 0.022, 0.032, 0.051]]
    >>> max_rel_diff_index(curve_refs, curves)
    (0.2, 1)
    """
    assert len(curve_ref) == len(curve), (len(curve_ref), len(curve))
    assert len(curve), 'The curves are empty!'
    diffs = [max_rel_diff(c1, c2, min_value)
             for c1, c2 in zip(curve_ref, curve)]
    maxdiff = max(diffs)
    maxindex = diffs.index(maxdiff)
    return maxdiff, maxindex


def rmsep(array_ref, array, min_value=0):
    """
    Root Mean Square Error Percentage for two arrays.

    :param array_ref: reference array
    :param array: another array
    :param min_value: compare only the elements larger than min_value
    :returns: the relative distance between the arrays

    >>> curve_ref = numpy.array([[0.01, 0.02, 0.03, 0.05],
    ... [0.01, 0.02, 0.04, 0.06]])
    >>> curve = numpy.array([[0.011, 0.021, 0.031, 0.051],
    ... [0.012, 0.022, 0.032, 0.051]])
    >>> str(round(rmsep(curve_ref, curve, .01), 5))
    '0.11292'
    """
    bigvalues = array_ref > min_value
    reldiffsquare = (1. - array[bigvalues] / array_ref[bigvalues]) ** 2
    return numpy.sqrt(reldiffsquare.mean())


def log(array, cutoff):
    """
    Compute the logarithm of an array with a cutoff on the small values
    """
    arr = numpy.copy(array)
    arr[arr < cutoff] = cutoff
    return numpy.log(arr)


def closest_to_ref(arrays, ref, cutoff=1E-12):
    """
    :param arrays: a sequence of arrays
    :param ref: the reference array
    :returns: a list of indices ordered by closeness

    This function is used to extract the realization closest to the mean in
    disaggregation. For instance, if there are 2 realizations with indices
    0 and 1, the first hazard curve having values

    >>> c0 = numpy.array([.99, .97, .5, .1])

    and the second hazard curve having values

    >>> c1 = numpy.array([.98, .96, .45, .09])

    with weights 0.6 and 0.4 and mean

    >>> mean = numpy.average([c0, c1], axis=0, weights=[0.6, 0.4])

    then calling ``closest_to_ref`` will returns the indices 0 and 1
    respectively:

    >>> closest_to_ref([c0, c1], mean)
    [0, 1]

    This means that the realization 0 is the closest to the mean, as expected,
    since it has a larger weight. You can check that it is indeed true by
    computing the sum of the quadratic deviations:

    >>> ((c0 - mean)**2).sum()
    0.0004480000000000008
    >>> ((c1 - mean)**2).sum()
    0.0010079999999999985

    If the 2 realizations have equal weights the distance from the mean will be
    the same. In that case both the realizations will be okay; the one that
    will be chosen by ``closest_to_ref`` depends on the magic of floating point
    approximation (theoretically identical distances will likely be different
    as numpy.float64 numbers) or on the magic of Python ``list.sort``.
    """
    dist = numpy.zeros(len(arrays))
    logref = log(ref, cutoff)
    pairs = []
    for idx, array in enumerate(arrays):
        diff = log(array, cutoff) - logref
        dist = numpy.sqrt((diff * diff).sum())
        pairs.append((dist, idx))
    pairs.sort()
    return [idx for dist, idx in pairs]


def compose_arrays(a1, a2, firstfield='etag'):
    """
    Compose composite arrays by generating an extended datatype containing
    all the fields. The two arrays must have the same length.
    """
    assert len(a1) == len(a2),  (len(a1), len(a2))
    if a1.dtype.names is None and len(a1.shape) == 1:
        # the first array is not composite, but it is one-dimensional
        a1 = numpy.array(a1, numpy.dtype([(firstfield, a1.dtype)]))

    fields1 = [(f, a1.dtype.fields[f][0]) for f in a1.dtype.names]
    if a2.dtype.names is None:  # the second array is not composite
        assert len(a2.shape) == 2, a2.shape
        width = a2.shape[1]
        fields2 = [('value%d' % i, a2.dtype) for i in range(width)]
        composite = numpy.zeros(a1.shape, numpy.dtype(fields1 + fields2))
        for f1 in dict(fields1):
            composite[f1] = a1[f1]
        for i in range(width):
            composite['value%d' % i] = a2[:, i]
        return composite

    fields2 = [(f, a2.dtype.fields[f][0]) for f in a2.dtype.names]
    composite = numpy.zeros(a1.shape, numpy.dtype(fields1 + fields2))
    for f1 in dict(fields1):
        composite[f1] = a1[f1]
    for f2 in dict(fields2):
        composite[f2] = a2[f2]
    return composite


def get_assets(dstore):
    """
    :param dstore: a datastore with keys 'assetcol'
    :returns: an array of records (id, tag1, ..., tagN, lon, lat)
    """
    assetcol = dstore['assetcol']
    tagnames = sorted(tn for tn in assetcol.tagnames if tn != 'id')
    if 'site_id' in tagnames:  # special case, starts from 1 and not from 0
        assetcol.array['site_id'] += 1
    tag = {t: getattr(assetcol.tagcol, t) for t in tagnames}
    dtlist = [('id', '<S100')]
    for tagname in tagnames:
        dtlist.append((tagname, '<S100'))
    dtlist.extend([('lon', F32), ('lat', F32)])
    asset_data = []
    for a in assetcol.array:
        tup = tuple(python3compat.encode(tag[t][a[t]]) for t in tagnames)
        asset_data.append((a['id'],) + tup + (a['lon'], a['lat']))
    return numpy.array(asset_data, dtlist)


def shared_dir_on():
    """
    :returns: True if a shared_dir has been set in openquake.cfg, else False
    """
    return config.directory.shared_dir
