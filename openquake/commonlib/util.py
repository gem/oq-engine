# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
from openquake.baselib import config, datastore
from openquake.commonlib import logs

F32 = numpy.float32


def read(calc_id, username=None):
    """
    :param calc_id: a calculation ID
    :param username: if given, restrict the search to the user's calculations
    :returns: the associated DataStore instance
    """
    if isinstance(calc_id, str) or calc_id < 0 and not username:
        # get the last calculation in the datastore of the current user
        return datastore.read(calc_id)
    job = logs.dbcmd('get_job', calc_id, username)
    if job:
        return datastore.read(job.ds_calc_dir + '.hdf5')
    else:
        # calc_id can be present in the datastore and not in the database:
        # this happens if the calculation was run with `oq run`
        return datastore.read(calc_id)


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
    :param arrays: a sequence of R arrays
    :param ref: the reference array
    :returns: a dictionary with keys rlz, value, and dist
    """
    dist = numpy.zeros(len(arrays))
    logref = log(ref, cutoff)
    for rlz, array in enumerate(arrays):
        diff = log(array, cutoff) - logref
        dist[rlz] = numpy.sqrt((diff * diff).sum())
    rlz = dist.argmin()
    closest = dict(rlz=rlz, value=arrays[rlz], dist=dist[rlz])
    return closest


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
    :returns: an array of records (asset_ref, tag1, ..., tagN, lon, lat)
    """
    assetcol = dstore['assetcol']
    tagnames = sorted(assetcol.tagnames)
    tag = {t: getattr(assetcol.tagcol, t) for t in tagnames}
    dtlist = [('asset_ref', (bytes, 100))]
    for tagname in tagnames:
        dtlist.append((tagname, (bytes, 100)))
    dtlist.extend([('lon', F32), ('lat', F32)])
    asset_data = []
    for aref, a in zip(assetcol.asset_refs, assetcol.array):
        tup = tuple(b'"%s"' % tag[t][a[t]].encode('utf-8') for t in tagnames)
        asset_data.append((aref,) + tup + (a['lon'], a['lat']))
    return numpy.array(asset_data, dtlist)


def shared_dir_on():
    """
    :returns: True if a shared_dir has been set in openquake.cfg, else False
    """
    return config.directory.shared_dir
