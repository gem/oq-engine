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

ALIAS = dict(min_mag='minMag', max_max='maxMag', bin_width='binWidth')


class MultiMFD(BaseMFD):
    """
    A MultiMFD is defined as a sequence of regular MFDs of the same kind.

    :param kind: a string defining the underlying MFD ('arbitraryMFD', ...)
    :param size: the size of the MFD for ArbitraryMFD and EvenlyDiscretizedMFD,
                 otherwise 1
    :param all_args: the list of arguments of the underlying MFDs
    :param width_of_mfd_bin: used in the truncated Gutenberg-Richter MFD
    """
    MODIFICATIONS = set()

    def __init__(self, kind, size, all_args, width_of_mfd_bin=None):
        self.kind = kind
        self.size = size
        self.width_of_mfd_bin = width_of_mfd_bin
        n = len(all_args)
        self.mfd_class = ASSOC[kind][0]
        dtlist = []
        for field in ASSOC[kind][1:]:
            dt = (F32, size) if field in ('magnitudes', 'occurRates') else F32
            dtlist.append((field, dt))
        self.array = numpy.zeros(n, dtlist)
        for i, args in enumerate(all_args):
            self.array[i] = args

    def __iter__(self):
        for args in self.array:
            yield self.mfd_class(*args)

    def __len__(self):
        return len(self.array)

    def get_min_max_mag(self):
        return None, None

    def check_constraints(self):
        pass

    def get_annual_occurrence_rates(self):
        for mfd in self:
            for rates in mfd.get_annual_occurrence_rates():
                yield rates
