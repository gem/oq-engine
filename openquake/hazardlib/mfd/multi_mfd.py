# The Hazard Library
# Copyright (C) 2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.mfd.multi_mfd` defines a composite
MFD used for MultiPoint sources.
"""
import numpy
from openquake.hazardlib.mfd.base import BaseMFD
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.mfd.youngs_coppersmith_1985 import (
    YoungsCoppersmith1985MFD)
from openquake.hazardlib.mfd.arbitrary_mfd import ArbitraryMFD

U16 = numpy.uint16
F32 = numpy.float32

ASSOC = {
    'arbitraryMFD': (
        ArbitraryMFD, 'magnitudes', 'occurRates'),
    'incrementalMFD': (
        EvenlyDiscretizedMFD, 'min_mag', 'bin_width', 'occurRates'),
    'truncGutenbergRichterMFD': (
        TruncatedGRMFD, 'min_mag', 'max_mag', 'bin_width', 'a_val', 'b_val'),
    'YoungsCoppersmithMFD': (
        YoungsCoppersmith1985MFD, 'min_mag', 'max_mag', 'a_val', 'b_val',
        'char_mag', 'char_rate', 'bin_width')}

ALIAS = dict(min_mag='minMag', max_mag='maxMag',
             a_val='aValue', b_val='bValue', bin_width='binWidth',
             char_mag='characteristicMag', char_rate='characteristicRate')


def _reshape(kwargs, lengths):
    # reshape occurRates and magnitudes as lists of lists
    for field in kwargs:
        if field in ('occurRates', 'magnitudes'):
            assert len(kwargs[field]) == sum(lengths), (
                len(kwargs[field]), sum(lengths))
            ivalues = iter(kwargs[field])
            kwargs[field] = [[next(ivalues) for _ in range(length)]
                             for length in lengths]


class MultiMFD(BaseMFD):
    """
    A MultiMFD is defined as a sequence of regular MFDs of the same kind.

    :param kind: a string defining the underlying MFD ('arbitraryMFD', ...)
    :param width_of_mfd_bin: used in the truncated Gutenberg-Richter MFD
    """
    MODIFICATIONS = set()

    @classmethod
    def from_node(cls, node, width_of_mfd_bin=None):
        kind = node['kind']
        kwargs = {}  # a dictionary name -> array of n elements
        for field in ASSOC[kind][1:]:
            if field == 'bin_width':
                kwargs[field] = width_of_mfd_bin
            else:
                kwargs[field] = ~getattr(node, field)
        if 'occurRates' in ASSOC[kind][1:]:
            lengths = ~getattr(node, 'lengths')
            _reshape(kwargs, lengths)
        return cls(kind, width_of_mfd_bin, **kwargs)

    def __init__(self, kind, width_of_mfd_bin=None, **kwargs):
        self.kind = kind
        self.width_of_mfd_bin = width_of_mfd_bin
        self.mfd_class = ASSOC[kind][0]
        self.n = len(kwargs.get('min_mag') or kwargs['lengths'])
        self.kwargs = kwargs

    def __iter__(self):
        """
        Yield the underlying MFDs instances
        """
        for i in range(self.n):
            args = []
            for f in ASSOC[self.kind][1:]:
                if f == 'bin_width':  # f has a scalar value
                    args.append(self.kwargs[f])
                else:  # f has a vector value
                    args.append(self.kwargs[f][i])
            yield self.mfd_class(*args)

    def __len__(self):
        return self.n

    def get_min_max_mag(self):
        """
        :returns: minumum and maximum magnitudes from the underlying MFDs
        """
        m1s, m2s = [], []
        for mfd in self:
            m1, m2 = mfd.get_min_max_mag()
            m1s.append(m1)
            m2s.append(m2)
        return min(m1s), max(m2s)

    def check_constraints(self):
        pass

    def get_annual_occurrence_rates(self):
        """
        Yields the occurrence rates of the underlying MFDs in order
        """
        for mfd in self:
            for rates in mfd.get_annual_occurrence_rates():
                yield rates
