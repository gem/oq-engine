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
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from openquake.baselib.python3compat import zip
from openquake.hazardlib.stats import mean_quantiles
import numpy

F64 = numpy.float64
BYTES_PER_FLOAT = 8


class ProbabilityCurve(object):
    """
    This class is a small wrapper over an array of PoEs associated to
    a set of intensity measure types and levels. It provides a few operators,
    including the complement operator `~`

    ~p = 1 - p

    and the inclusive or operator `|`

    p = p1 | p2 = ~(~p1 * ~p2)

    Such operators are implemented efficiently at the numpy level, by
    dispatching on the underlying array.

    Here is an example of use:

    >>> poe = ProbabilityCurve(numpy.array([0.1, 0.2, 0.3, 0, 0]))
    >>> ~(poe | poe) * .5
    <ProbabilityCurve
    [ 0.405  0.32   0.245  0.5    0.5  ]>
    """
    def __init__(self, array):
        self.array = array

    def __or__(self, other):
        if other == 0:
            return self
        else:
            return self.__class__(1. - (1. - self.array) * (1. - other.array))
    __ror__ = __or__

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.array * other.array)
        elif other == 1:
            return self
        else:
            return self.__class__(self.array * other)
    __rmul__ = __mul__

    def __invert__(self):
        return self.__class__(1. - self.array)

    def __nonzero__(self):
        return bool(self.array.any())

    def __repr__(self):
        return '<ProbabilityCurve\n%s>' % self.array

    # used when exporting to HDF5
    def convert(self, imtls, idx=0):
        """
        Convert a probability curve into a record of dtype `imtls.imt_dt`.

        :param imtls: DictArray instance
        :param idx: extract the data corresponding to the given inner index
        """
        curve = numpy.zeros(1, imtls.imt_dt)
        for imt in imtls:
            curve[imt] = self.array[imtls.slicedic[imt], idx]
        return curve[0]


class ProbabilityMap(dict):
    """
    A dictionary site_id -> ProbabilityCurve. It defines the complement
    operator `~`, performing the complement on each curve

    ~p = 1 - p

    and the "inclusive or" operator `|`:

    m = m1 | m2 = {sid: m1[sid] | m2[sid] for sid in all_sids}

    Such operators are implemented efficiently at the numpy level, by
    dispatching on the underlying array. Moreover there is a classmethod
    .build(L, I, sids, initvalue) to build initialized instances of
    :class:`ProbabilityMap`. The map can be represented as 3D array of shape
    (shape_x, shape_y, shape_z) = (N, L, I), where N is the number of site IDs,
    L the total number of hazard levels and I the number of GSIMs.
    """
    @classmethod
    def build(cls, shape_y, shape_z, sids, initvalue=0.):
        """
        :param shape_y: the total number of intensity measure levels
        :param shape_z: the number of inner levels
        :param sids: a set of site indices
        :param initvalue: the initial value of the probability (default 0)
        :returns: a ProbabilityMap dictionary
        """
        dic = cls(shape_y, shape_z)
        for sid in sids:
            dic.setdefault(sid, initvalue)
        return dic

    def __init__(self, shape_y, shape_z):
        self.shape_y = shape_y
        self.shape_z = shape_z

    def setdefault(self, sid, value):
        """
        Works like `dict.setdefault`: if the `sid` key is missing, it fills
        it with an array and returns it.

        :param sid: site ID
        :param value: value used to fill the returned array
        """
        try:
            return self[sid]
        except KeyError:
            array = numpy.empty((self.shape_y, self.shape_z), F64)
            array.fill(value)
            pc = ProbabilityCurve(array)
            self[sid] = pc
            return pc

    @property
    def sids(self):
        """The ordered keys of the map as a numpy.uint32 array"""
        return numpy.array(sorted(self), numpy.uint32)

    @property
    def array(self):
        """
        The underlying array of shape (N, L, I)
        """
        return numpy.array([self[sid].array for sid in sorted(self)])

    @property
    def nbytes(self):
        """The size of the underlying array"""
        N, L, I = get_shape([self])
        return BYTES_PER_FLOAT * N * L * I

    # used when exporting to HDF5
    def convert(self, imtls, nsites=None, idx=0):
        """
        Convert a probability map into a composite array of length `nsites`
        and dtype `imtls.imt_dt`.

        :param imtls: DictArray instance
        :param nsites: the total number of sites (or None)
        :param idx: extract the data corresponding to the given inner index
        """
        if nsites is None:
            nsites = len(self)
        curves = numpy.zeros(nsites, imtls.imt_dt)
        for imt in curves.dtype.names:
            curves_by_imt = curves[imt]
            for sid in self:
                curves_by_imt[sid] = self[sid].array[imtls.slicedic[imt], idx]
        return curves

    def filter(self, sids):
        """
        Extracs a submap of self for the given sids.
        """
        dic = self.__class__(self.shape_y, self.shape_z)
        for sid in sids:
            try:
                dic[sid] = self[sid]
            except KeyError:
                pass
        return dic

    def extract(self, inner_idx):
        """
        Extracts a component of the underlying ProbabilityCurves,
        specified by the index `inner_idx`.
        """
        out = self.__class__(self.shape_y, 1)
        for sid in self:
            curve = self[sid]
            array = curve.array[:, inner_idx].reshape(-1, 1)
            out[sid] = ProbabilityCurve(array)
        return out

    def __ior__(self, other):
        self_sids = set(self)
        other_sids = set(other)
        for sid in self_sids & other_sids:
            self[sid] = self[sid] | other[sid]
        for sid in other_sids - self_sids:
            self[sid] = other[sid]
        return self

    def __or__(self, other):
        new = self.__class__(self.shape_y, self.shape_z)
        new |= other
        return new

    __ror__ = __or__

    def __mul__(self, other):
        sids = set(self) | set(other)
        new = self.__class__(self.shape_y, self.shape_z)
        for sid in sids:
            new[sid] = self.get(sid, 1) * other.get(sid, 1)
        return new

    def __invert__(self):
        new = self.__class__(self.shape_y, self.shape_z)
        for sid in self:
            if (self[sid].array != 1.).any():
                new[sid] = ~self[sid]  # store only nonzero probabilities
        return new

    def __toh5__(self):
        # converts to an array of shape (num_sids, shape_y, shape_z)
        size = len(self)
        sids = self.sids
        shape = (size, self.shape_y, self.shape_z)
        array = numpy.zeros(shape, F64)
        for i, sid in numpy.ndenumerate(sids):
            array[i] = self[sid].array
        return array, dict(sids=sids)

    def __fromh5__(self, array, attrs):
        # rebuild the map from sids and probs arrays
        self.shape_y = array.shape[1]
        self.shape_z = array.shape[2]
        for sid, prob in zip(attrs['sids'], array):
            self[sid] = ProbabilityCurve(prob)


def get_shape(pmaps):
    """
    :param pmaps: a set of homogenous ProbabilityMaps
    :returns: the common shape (N, L, I)
    """
    for pmap in pmaps:
        if pmap:
            sid = next(iter(pmap))
            break
    else:
        raise ValueError('All probability maps where empty!')
    return (len(pmap),) + pmap[sid].array.shape


class PmapStats(object):
    """
    A class to perform statistics on ProbabilityMaps.

    :param weights: a list of weights
    :param quantiles: a list of floats in the range 0..1

    Here is an example:

    >>> pm1 = ProbabilityMap.build(3, 1, sids=[0, 1],
    ...                            initvalue=1.0)
    >>> pm2 = ProbabilityMap.build(3, 1, sids=[0],
    ...                            initvalue=0.8)
    >>> PmapStats(quantiles=[]).compute(sids=[0, 1], pmaps=[pm1, pm2])
    [('mean', {0: <ProbabilityCurve
    [[ 0.9]
     [ 0.9]
     [ 0.9]]>, 1: <ProbabilityCurve
    [[ 0.5]
     [ 0.5]
     [ 0.5]]>})]
    """
    def __init__(self, quantiles, weights=None):
        self.quantiles = quantiles
        self.weights = weights

    # the tests are in the engine
    def compute_pmap(self, sids, pmaps):
        """
        :params sids: array of N site IDs
        :param pmaps: array of R simple ProbabilityMaps
        :returns: a ProbabilityMap with arrays of size (num_levels, num_stats)
        """
        if len(pmaps) == 0:
            raise ValueError('No probability maps!')
        elif len(pmaps) == 1:  # the mean is the only pmap
            assert not self.quantiles, self.quantiles
            return pmaps[0]
        elif sum(len(pmap) for pmap in pmaps) == 0:  # all empty pmaps
            raise ValueError('All empty probability maps!')
        N, L, I = get_shape(pmaps)
        nstats = len(self.quantiles) + 1
        stats = ProbabilityMap.build(L, nstats, sids)
        curves_by_rlz = numpy.zeros((len(pmaps), len(sids), L), numpy.float64)
        for i, pmap in enumerate(pmaps):
            for j, sid in enumerate(sids):
                if sid in pmap:
                    curves_by_rlz[i][j] = pmap[sid].array[:, 0]
        mq = mean_quantiles(curves_by_rlz, self.quantiles, self.weights)
        for i, array in enumerate(mq):
            for j, sid in numpy.ndenumerate(sids):
                stats[sid].array[:, i] = array[j]
        return stats

    def compute(self, sids, pmaps):
        """
        :params sids:
            array of N site IDs
        :param pmaps:
            array of R simple ProbabilityMaps
        :returns:
            a list of pairs [('mean', ...), ('quantile-XXX', ...), ...]
        """
        stats = self.compute_pmap(sids, pmaps)
        names = ['mean'] + ['quantile-%s' % q for q in self.quantiles]
        return [(name, stats.extract(i)) for i, name in enumerate(names)]
