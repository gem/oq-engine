# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2013-2017 GEM Foundation

# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import operator
import numpy


def with_slots(cls):
    """
    Decorator for a class with _slots_. It automatically defines
    the methods __eq__, __ne__, assert_equal.
    """
    def _compare(self, other):
        for slot in self.__class__._slots_:
            attr = operator.attrgetter(slot)
            source = attr(self)
            target = attr(other)
            if isinstance(source, numpy.ndarray):
                eq = numpy.array_equal(source, target)
            else:
                eq = source == target
            yield slot, source, target, eq

    def __eq__(self, other):
        return all(eq for slot, source, target, eq in _compare(self, other))

    def __ne__(self, other):
        return not self.__eq__(other)

    def assert_equal(self, other):
        for slot, source, target, eq in _compare(self, other):
            if not eq:
                raise AssertionError('slot %s: %s is different from %s' %
                                     (slot, source, target))

    cls._slots_  # raise an AttributeError for missing slots
    cls.__eq__ = __eq__
    cls.__ne__ = __ne__
    cls.assert_equal = assert_equal
    return cls
