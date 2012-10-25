# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""
Utility functions of general interest.
"""

import cPickle


def singleton(cls):
    """This class decorator facilitates the definition of singletons."""
    instances = {}

    def getinstance(*args, **kwargs):
        """
        Return an instance from the cache if present, create one otherwise.
        """
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance


# Memoize taken from the Python Cookbook that handles also unhashable types
class MemoizeMutable:
    """ This decorator enables method/function caching in memory """
    def __init__(self, fun):
        self.fun = fun
        self.memo = {}

    def __call__(self, *args, **kwds):
        key = cPickle.dumps(args, 1) + cPickle.dumps(kwds, 1)
        if not key in self.memo:
            self.memo[key] = self.fun(*args, **kwds)

        return self.memo[key]


def str2bool(value):
    """Convert a string representation of a boolean value to a bool."""
    return value.lower() in ("true", "yes", "t", "1")


def block_splitter(data, block_size):
    """
    Given a sequence of objects and a ``block_size``, generate slices from the
    list. Each slice has a maximum size of ``block_size``.

    If ``block_size`` is greater than the length of ``data``, this simply
    yields the entire list.

    :param data:
        Any iterable sequence of data (including lists, iterators, and
        generators).
    :param int block_size:
        Maximum size for each slice. Must be greater than 0.
    :raises:
        :exc:`ValueError` of the ``block_size`` is <= 0.
    """
    if block_size <= 0:
        raise ValueError(
            'Invalid block size: %s. Value must be greater than 0.'
            % block_size)

    block_buffer = []
    for d in data:
        block_buffer.append(d)
        if len(block_buffer) == block_size:
            yield block_buffer
            block_buffer = []
    if len(block_buffer) > 0:
        yield block_buffer
