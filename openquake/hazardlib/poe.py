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
import collections
import numpy

F64 = numpy.float64


# returns a dict imt -> slice
def slicedict(imt_dt):
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
    and levels
    """
    def __init__(self, imtls):
        self.imt_dt = dt = numpy.dtype(
            [(imt, F64, len(imls) if hasattr(imls, '__len__') else 1)
             for imt, imls in sorted(imtls.items())])
        self.slicedic, num_levels = slicedict(dt)
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
        data = ['%s: %s' % (imt, self.array[imt]) for imt in self]
        return '<Imtls\n%s>' % '\n'.join(data)


class ProbabilityCurve(object):
    """
    This class is a small wrapper over an array of PoEs associated to
    a set of intensity measure types and levels. It provides a few
    class methods to manage a dictionary of curves keyed by an integer
    (the site index) and defines a few operators, including the complement
    operator `~`

    ~p = 1 - p

    and the inclusive or operator `|`

    p = p1 | p2 = ~(~p1 * ~p2)

    Such operators are implemented efficiently at the numpy level, by
    dispatching on the underlying array.

    Here is an example of use:

    >>> imtls = Imtls({'PGA': [0.01, 0.02, 0.04], 'PGV': [0.1, 0.2]})
    >>> poe = ProbabilityCurve(imtls.slicedic, numpy.zeros(5, F64))
    >>> poe['PGA'] = [0.1, 0.2, 0.3]
    >>> ~(poe | poe) * .5
    <ProbabilityCurve
    PGA: [ 0.405  0.32   0.245]
    PGV: [ 0.5  0.5]>
    """
    def __init__(self, slicedic, array):
        self.slicedic = slicedic
        self.array = array

    def __setitem__(self, imt, array):
        self.array[self.slicedic[imt]] = array

    def __getitem__(self, imt):
        return self.array[self.slicedic[imt]]

    def __or__(self, other):
        if other == 0:
            return self
        else:
            return self.__class__(
                self.slicedic, 1. - (1. - self.array) * (1. - other.array))
    __ror__ = __or__

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.slicedic, self.array * other.array)
        elif other == 1:
            return self
        else:
            return self.__class__(self.slicedic, self.array * other)
    __rmul__ = __mul__

    def __invert__(self):
        return self.__class__(self.slicedic, 1. - self.array)

    def __nonzero__(self):
        return bool(self.array.sum())

    def __repr__(self):
        data = ['%s: %s' % (imt, self[imt]) for imt in sorted(self.slicedic)]
        return '<ProbabilityCurve\n%s>' % '\n'.join(data)


class ProbabilityMap(dict):
    """
    >>> imtls = Imtls(dict(PGA=[1, 2, 3], PGV=[4, 5]))
    >>> curves1 = ProbabilityMap.build(imtls, 1, [0, 1], initvalue=.1)
    >>> curves2 = ProbabilityMap.build(imtls, 1, [1, 2], initvalue=.1)
    >>> dic = curves1 + curves2
    >>> dic[0]
    <ProbabilityCurve
    PGA: [[ 0.1]
     [ 0.1]
     [ 0.1]]
    PGV: [[ 0.1]
     [ 0.1]]>
    >>> dic[1]
    <ProbabilityCurve
    PGA: [[ 0.19]
     [ 0.19]
     [ 0.19]]
    PGV: [[ 0.19]
     [ 0.19]]>
    >>> dic[2]
    <ProbabilityCurve
    PGA: [[ 0.1]
     [ 0.1]
     [ 0.1]]
    PGV: [[ 0.1]
     [ 0.1]]>
    """

    @classmethod
    def build(cls, imtls, num_gsims, sids, initvalue=0.):
        """
        :param imtls: an :class:`openquake.hazardlib.imt.Imtls` instance
        :param num_gsims: the number of GSIMs
        :param sids: a set of site indices
        :param initvalue: the initial value of the probability (default 0)
        """
        dic = cls()
        for sid in sids:
            array = numpy.empty((len(imtls.array), num_gsims), F64)
            array.fill(initvalue)
            dic[sid] = ProbabilityCurve(imtls.slicedic, array)
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
            out[sid] = ProbabilityCurve(curve.slicedic, array)
        return out

    def __add__(self, other):
        sids = set(self) | set(other)
        dic = self.__class__()
        for sid in sids:
            curve = self.get(sid, 0) | other.get(sid, 0)
            if curve:
                dic[sid] = curve
        return dic

    def __mul__(self, other):
        sids = set(self) | set(other)
        return self.__class__((sid, self.get(sid, 1) * other.get(sid, 1))
                              for sid in sids)

    def __invert__(self):
        return self.__class__((sid, ~self[sid]) for sid in self)
