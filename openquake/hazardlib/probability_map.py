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
import collections
import numpy

F64 = numpy.float64


# return a dict imt -> slice and the total number of levels
def _slicedict_n(imt_dt):
    n = 0
    slicedic = {}
    for imt in imt_dt.names:
        shp = imt_dt[imt].shape
        n1 = n + shp[0] if shp else 1
        slicedic[imt] = slice(n, n1)
        n = n1
    return slicedic, n


class Imtls(collections.Mapping):
    """
    A small wrapper over an ordered dictionary of intensity measure types
    and levels.

    >>> Imtls({'PGA': [0.01, 0.02, 0.04], 'PGV': [0.1, 0.2]})
    <Imtls
    PGA: [ 0.01  0.02  0.04]
    PGV: [ 0.1  0.2]>
    """
    def __init__(self, imtls):
        self.imt_dt = dt = numpy.dtype(
            [(imt, F64, len(imls) if hasattr(imls, '__len__') else 1)
             for imt, imls in sorted(imtls.items())])
        self.slicedic, num_levels = _slicedict_n(dt)
        self.array = numpy.zeros(num_levels, F64)
        for imt, imls in imtls.items():
            self[imt] = imls

    def __getitem__(self, imt):
        return self.array[self.slicedic[imt]]

    def __setitem__(self, imt, array):
        self.array[self.slicedic[imt]] = array

    def __iter__(self):
        for imt in self.imt_dt.names:
            yield imt

    def __len__(self):
        return len(self.imt_dt.names)

    def __repr__(self):
        data = ['%s: %s' % (imt, self[imt]) for imt in self]
        return '<Imtls\n%s>' % '\n'.join(data)


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


class ProbabilityMap(dict):
    """
    A dictionary site_id -> ProbabilityCurve. It defines the complement
    operator `~`, performing the complement on each curve, the addition
    operator `+`. performing the

    ~p = 1 - p

    and the inclusive or on the underlying curves:

    m = m1 + m2 = {sid: m1[sid] | m2[sid] for sid in all_sids}

    Such operators are implemented efficiently at the numpy level, by
    dispatching on the underlying array. Moreover there is a classmethod
    .build(num_levels, num_gsims, sids, initvalue) to build initialized
    instances of ProbabilityMap.
    """
    @classmethod
    def build(cls, num_levels, num_gsims, sids, initvalue=0.):
        """
        :param num_levels: the total number of intensity measure levels
        :param num_gsims: the number of GSIMs
        :param sids: a set of site indices
        :param initvalue: the initial value of the probability (default 0)
        """
        dic = cls()
        for sid in sids:
            array = numpy.empty((num_levels, num_gsims), F64)
            array.fill(initvalue)
            dic[sid] = ProbabilityCurve(array)
        return dic

    def extract(self, gsim_idx):
        """
        Extracts a component of the underlying ProbabilityCurves,
        specified by the index `gsim_idx`.
        """
        out = self.__class__()
        for sid in self:
            curve = self[sid]
            array = curve.array[:, gsim_idx].reshape(-1, 1)
            out[sid] = ProbabilityCurve(array)
        return out

    def __add__(self, other):
        sids = set(self) | set(other)
        dic = self.__class__()
        for sid in sids:
            curve = self.get(sid, 0) | other.get(sid, 0)
            if curve:  # this check is very important for performance
                dic[sid] = curve
        return dic

    # faster than ___add__
    def __iadd__(self, other):
        for sid in self:
            self[sid] = self[sid] | other.get(sid, 0)
        for sid in set(other) - set(self):
            self[sid] = other[sid]
        return self

    def __mul__(self, other):
        sids = set(self) | set(other)
        return self.__class__((sid, self.get(sid, 1) * other.get(sid, 1))
                              for sid in sids)

    def __invert__(self):
        return self.__class__((sid, ~self[sid]) for sid in self)

    def __toh5__(self):
        # converts to an array of shape (num_sids, num_levels, num_gsims)
        size = len(self)
        sids = numpy.array(sorted(self), numpy.uint32)
        if size:
            shape = (size,) + self[sids[0]].array.shape
            array = numpy.zeros(shape)
            for i, sid in numpy.ndenumerate(sids):
                array[i] = self[sid].array
        else:
            array = numpy.zeros(0)
        return array, dict(sids=sids)

    def __fromh5__(self, array, attrs):
        # rebuild the map from sids and probs arrays
        for sid, prob in zip(attrs['sids'], array):
            self[sid] = ProbabilityCurve(prob)
