# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2020 GEM Foundation
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
import re
import logging
import operator
import collections
import numpy
from openquake.commonlib.logictree import get_effective_rlzs

MAX_INT = 2 ** 31 - 1
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
weight = operator.attrgetter('weight')


class LtRealization(object):
    """
    Composite realization build on top of a source model realization and
    a GSIM realization.
    """
    def __init__(self, ordinal, sm_lt_path, gsim_rlz, weight):
        self.ordinal = ordinal
        self.sm_lt_path = tuple(sm_lt_path)
        self.gsim_rlz = gsim_rlz
        self.weight = weight

    def __repr__(self):
        return '<%d,%s,w=%s>' % (self.ordinal, self.pid, self.weight)

    @property
    def gsim_lt_path(self):
        return self.gsim_rlz.lt_path

    @property
    def pid(self):
        """An unique identifier for effective realizations"""
        return '_'.join(self.sm_lt_path) + '~' + self.gsim_rlz.pid

    def __lt__(self, other):
        return self.ordinal < other.ordinal

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __ne__(self, other):
        return repr(self) != repr(other)

    def __hash__(self):
        return hash(repr(self))
