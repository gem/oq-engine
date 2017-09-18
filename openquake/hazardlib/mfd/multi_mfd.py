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
    for vals in ASSOC.values():
        MODIFICATIONS.update(vals[0].MODIFICATIONS)

    @classmethod
    def from_node(cls, node, width_of_mfd_bin=None):
        kind = node['kind']
        size = node['size']
        kwargs = {}  # a dictionary name -> array of n elements
        for field in ASSOC[kind][1:]:
            try:
                kwargs[field] = ~getattr(node, field)
            except AttributeError:
                if field != 'bin_width':
                    raise
                # missing bindWidth in GR MDFs is ok
        if 'occurRates' in ASSOC[kind][1:]:
            lengths = ~getattr(node, 'lengths')
            if len(lengths) == 1:  # all occurRates are the same
                lengths = [lengths[0]] * size
            _reshape(kwargs, lengths)
        return cls(kind, size, width_of_mfd_bin, **kwargs)

    def __init__(self, kind, size, width_of_mfd_bin=None, **kwargs):
        self.kind = kind
        self.size = size
        self.width_of_mfd_bin = width_of_mfd_bin
        self.mfd_class = ASSOC[kind][0]
        self.kwargs = kwargs
        if 'bin_width' not in kwargs:
            kwargs['bin_width'] = [width_of_mfd_bin]
        for field in kwargs:
            self.check_size(field, kwargs[field])

    def check_size(self, field, values):
        if len(values) not in (1, self.size):
            raise ValueError('%s of size %d, expected 1 or %d' %
                             (field, len(values), self.size))

    def __iter__(self):
        """
        Yield the underlying MFDs instances
        """
        for i in range(self.size):
            args = []
            for f in ASSOC[self.kind][1:]:
                arr = self.kwargs[f]
                if len(arr) == 1:
                    args.append(arr[0])
                else:
                    args.append(arr[i])
            yield self.mfd_class(*args)

    def __len__(self):
        return self.size

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

    def modify(self, modification, parameters):
        """
        Apply a modification to the underlying point sources, with the
        same parameters for all sources
        """
        for src in self:
            src.modify(modification, parameters)
