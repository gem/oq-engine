# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.


import functools
import collections
import itertools
import numpy


class Register(collections.OrderedDict):
    def add(self, tag):
        def dec(obj):
            self[tag] = obj
            return obj
        return dec


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    # b ahead one step; if b is empty do not raise StopIteration
    next(b, None)
    return itertools.izip(a, b)  # if a is empty will return an empty iter


class memoized(object):
    """
    Minimalistic memoizer decorator
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


def _composed(f, g, *args, **kwargs):
    return f(g(*args, **kwargs))


def compose(*a):
    try:
        return functools.partial(_composed, a[0], compose(*a[1:]))
    except IndexError:
        return a[0]


numpy_map = compose(numpy.array, map)
