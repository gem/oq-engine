# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
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

import math
import collections

import numpy


class WeightedSequence(collections.MutableSequence):
    """
    A wrapper over a sequence of weighted items with a total weight attribute.
    Adding items automatically increases the weight.
    """
    @classmethod
    def merge(cls, ws_list):
        """
        Merge a set of WeightedSequence objects.

        :param ws_list:
            a sequence of :class:
            `openquake.commonlib.general.WeightedSequence` instances
        :returns:
            a `openquake.commonlib.general.WeightedSequence` instance
        """
        return sum(ws_list, cls())

    def __init__(self, seq=()):
        """
        param seq: a finite sequence of pairs (item, weight)
        """
        self._seq = []
        self.weight = 0
        self.extend(seq)

    def __getitem__(self, sliceobj):
        """
        Return an item or a slice
        """
        return self._seq[sliceobj]

    def __setitem__(self, i, v):
        """
        Modify the sequence
        """
        self._seq[i] = v

    def __delitem__(self, sliceobj):
        """
        Remove an item from the sequence
        """
        del self._seq[sliceobj]

    def __len__(self):
        """
        The length of the sequence
        """
        return len(self._seq)

    def __add__(self, other):
        """
        Add two weighted sequences and return a new WeightedSequence
        with weight equal to the sum of the weights.
        """
        new = self.__class__()
        new._seq.extend(self._seq)
        new._seq.extend(other._seq)
        new.weight = self.weight + other.weight
        return new

    def insert(self, i, (item, weight)):
        """
        Insert an item with the given weight in the sequence
        """
        self._seq.insert(i, item)
        self.weight += weight

    def __cmp__(self, other):
        """
        Ensure ordering by reverse weight
        """
        return -cmp(self.weight, other.weight)

    def __repr__(self):
        """
        String representation of the sequence, including the weight
        """
        return '<%s %s, weight=%s>' % (self.__class__.__name__,
                                       self._seq, self.weight)


def distinct(keys):
    """
    Return the distinct keys in order.
    """
    known = set()
    outlist = []
    for key in keys:
        if key not in known:
            outlist.append(key)
        known.add(key)
    return outlist


def str2bool(value):
    """Convert a string representation of a boolean value to a bool."""
    return value.lower() in ("true", "yes", "t", "1")


def ceil(a, b):
    """
    Divide a / b and return the biggest integer close to the quotient.

    :param a:
        a number
    :param b:
        a positive number
    :returns:
        the biggest integer close to the quotient
    """
    assert b > 0, b
    return int(math.ceil(float(a) / b))


def split_on_max_weight(item_weight_pairs, max_weight):
    """
    :param item_weight_pairs: an iterator of pairs (item, weight)
    :param max_weight: the max weight to split on

    Group together the pairs until the total weight exceeds the
    `max_weight` and yield `WeightedSequence` instances. Items
    with weight zero are ignored.

    For instance

     >>> pairs = [('A', 1), ('B', 2), ('C', 0), ('D', 4), ('E', 1)]
     >>> list(split_on_max_weight(pairs, 3))
     [<WeightedSequence ['A', 'B'], weight=3>, <WeightedSequence ['D'], weight=4>, <WeightedSequence ['E'], weight=1>]
    """
    ws = WeightedSequence([])
    for item, weight in item_weight_pairs:
        if weight < 0:  # error
            raise ValueError('The item %r got a negative weight %s!' %
                             (item, weight))
        elif weight == 0:  # ignore items with 0 weight
            pass
        elif ws.weight + weight > max_weight:
            new_ws = WeightedSequence([(item, weight)])
            if ws:
                yield ws
            ws = new_ws
        else:
            ws.append((item, weight))
    if ws:
        yield ws


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


def deep_eq(a, b, decimal=7, exclude=None):
    """Deep compare two objects for equality by traversing __dict__ and
    __slots__.

    Caution: This function will exhaust generators.

    :param decimal:
        Desired precision (digits after the decimal point) for numerical
        comparisons.

    :param exclude: a list of attributes that will be excluded when
    traversing objects

    :returns:
        Return `True` or `False` (to indicate if objects are equal) and a `str`
        message. If the two objects are equal, the message is empty. If the two
        objects are not equal, the message indicates which part of the
        comparison failed.
    """
    exclude = exclude or []

    try:
        _deep_eq(a, b, decimal=decimal, exclude=exclude)
    except AssertionError, err:
        return False, err.message
    return True, ''


def _deep_eq(a, b, decimal, exclude=None):
    """Do the actual deep comparison. If the two items up for comparison are
    not equal, a :exception:`AssertionError` is raised (to
    :function:`deep_eq`).
    """

    exclude = exclude or []

    def _test_dict(a, b):
        """Compare `dict` types recursively."""
        assert len(a) == len(b), (
            "Dicts %(a)s and %(b)s do not have the same length."
            " Actual lengths: %(len_a)s and %(len_b)s") % dict(
            a=a, b=b, len_a=len(a), len_b=len(b))

        for key in a:
            if not key in exclude:
                _deep_eq(a[key], b[key], decimal)

    def _test_seq(a, b):
        """Compare `list` or `tuple` types recursively."""
        assert len(a) == len(b), (
            "Sequences %(a)s and %(b)s do not have the same length."
            " Actual lengths: %(len_a)s and %(len_b)s") % \
            dict(a=a, b=b, len_a=len(a), len_b=len(b))

        for i, item in enumerate(a):
            _deep_eq(item, b[i], decimal)

    # lists or tuples
    if isinstance(a, (list, tuple)):
        _test_seq(a, b)
    # dicts
    elif isinstance(a, dict):
        _test_dict(a, b)
    # objects with a __dict__
    elif hasattr(a, '__dict__'):
        assert a.__class__ == b.__class__, (
            "%s and %s are different classes") % (a.__class__, b.__class__)
        _test_dict(a.__dict__, b.__dict__)
    # iterables (not strings)
    elif isinstance(a, collections.Iterable) and not isinstance(a, str):
        # If there's a generator or another type of iterable, treat it as a
        # `list`. NOTE: Generators will be exhausted if you do this.
        _test_seq(list(a), list(b))
    # objects with __slots__
    elif hasattr(a, '__slots__'):
        assert a.__class__ == b.__class__, (
            "%s and %s are different classes") % (a.__class__, b.__class__)
        assert a.__slots__ == b.__slots__, (
            "slots %s and %s are not the same") % (a.__slots__, b.__slots__)
        for slot in a.__slots__:
            if not slot in exclude:
                _deep_eq(getattr(a, slot), getattr(b, slot), decimal)
    else:
        # Objects must be primitives

        # Are they numbers?
        if isinstance(a, (int, long, float, complex)):
            numpy.testing.assert_almost_equal(a, b, decimal=decimal)
        else:
            assert a == b, "%s != %s" % (a, b)
