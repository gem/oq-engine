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


class MultiMFD(BaseMFD):
    """
    A MultiMFD is defined as a sequence of regular MFDs of the same kind.

    :param kind: a string defining the underlying MFD
    :param size: the size of the MFD for ArbitraryMFD and EvenlyDiscretizedMFD,
                 otherwise 0
    :param width_of_mfd_bin: used in the truncated Gutenberg-Richter MFD
    :param all_args: a list of arguments
    """
    MODIFICATIONS = set()

    def __init__(self, kind, size, all_args, width_of_mfd_bin=None):
        self.kind = kind
        self.size = size
        self.width_of_mfd_bin = width_of_mfd_bin
        n = len(all_args[0])
        if kind == 'arbitraryMFD':
            self.mfd_class = ArbitraryMFD
            self.array = numpy.zeros(n, [('magnitudes', (F32, size)),
                                         ('occurRates', (F32, size))])

        elif kind == 'incrementalMFD':
            self.mfd_class = EvenlyDiscretizedMFD
            self.array = numpy.zeros(n, [('min_mag', F32),
                                         ('bin_width', F32),
                                         ('occurRates', (F32, size))])
        elif kind == 'truncGutenbergRichterMFD':
            self.mfd_class = TruncatedGRMFD
            self.array = numpy.zeros(n, [('min_mag', F32),
                                         ('max_mag', F32),
                                         ('bin_width', F32),
                                         ('a_val', F32),
                                         ('b_val', F32)])
        elif kind == 'YoungsCoppersmithMFD':
            self.mfd_class = YoungsCoppersmith1985MFD
            self.array = numpy.zeros(n, [('min_mag', F32),
                                         ('max_mag', F32),
                                         ('a_val', F32),
                                         ('b_val', F32),
                                         ('char_mag', F32),
                                         ('char_rate', F32),
                                         ('bin_width', F32)])
        else:
            raise NameError('Unknown MFD: %s' % kind)
        for i, args in enumerate(all_args):
            self.array[i] = args

    def __iter__(self):
        for args in self.array:
            yield self.mfd_class(*args)

    def get_min_max_mag(self):
        return None, None

    def check_constraints(self):
        pass

    def get_annual_occurrence_rates(self):
        for mfd in self:
            for rates in mfd.get_annual_occurrence_rates():
                yield rates
