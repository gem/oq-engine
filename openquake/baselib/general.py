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
from __future__ import division
import os
import sys
import imp
import math
import tempfile
import importlib
import itertools
import subprocess
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
            `openquake.baselib.general.WeightedSequence` instances
        :returns:
            a `openquake.baselib.general.WeightedSequence` instance
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

    def __lt__(self, other):
        """
        Ensure ordering by weight
        """
        return self.weight < other.weight

    def __eq__(self, other):
        """
        Compare for equality the items contained in self
        """
        return all(x == y for x, y in zip(self, other))

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


def block_splitter(items, max_weight, weight=lambda item: 1,
                   kind=lambda item: 'Unspecified'):
    """
    :param items: an iterator over items
    :param max_weight: the max weight to split on
    :param weight: a function returning the weigth of a given item
    :param kind: a function returning the kind of a given item

    Group together items of the same kind until the total weight exceeds the
    `max_weight` and yield `WeightedSequence` instances. Items
    with weight zero are ignored.

    For instance

     >>> items = 'ABCDE'
     >>> list(block_splitter(items, 3))
     [<WeightedSequence ['A', 'B', 'C'], weight=3>, <WeightedSequence ['D', 'E'], weight=2>]

    The default weight is 1 for all items.
    """
    if max_weight <= 0:
        raise ValueError('max_weight=%s' % max_weight)
    ws = WeightedSequence([])
    prev_kind = 'Unspecified'
    for item in items:
        w = weight(item)
        k = kind(item)
        if w < 0:  # error
            raise ValueError('The item %r got a negative weight %s!' %
                             (item, w))
        elif w == 0:  # ignore items with 0 weight
            pass
        elif ws.weight + w > max_weight or k != prev_kind:
            new_ws = WeightedSequence([(item, w)])
            if ws:
                yield ws
            ws = new_ws
        else:
            ws.append((item, w))
        prev_kind = k
    if ws:
        yield ws


def split_in_blocks(sequence, hint, weight=lambda item: 1,
                    key=lambda item: 'Unspecified'):
    """
    Split the `sequence` in a number of WeightedSequences close to `hint`.

    :param sequence: a finite sequence of items
    :param hint: an integer suggesting the number of subsequences to generate
    :param weight: a function returning the weigth of a given item
    :param key: a function returning the key of a given item

    The WeightedSequences are of homogeneous key and they try to be
    balanced in weight. For instance

     >>> items = 'ABCDE'
     >>> list(split_in_blocks(items, 3))
     [<WeightedSequence ['A', 'B'], weight=2>, <WeightedSequence ['C', 'D'], weight=2>, <WeightedSequence ['E'], weight=1>]

    """
    assert hint > 0, hint
    items = list(sequence)
    total_weight = float(sum(weight(item) for item in items))
    return block_splitter(items, math.ceil(total_weight / hint), weight, key)


# the implementation here is unbelievably ugly; it is a remnant of the
# past and soon or later will be removed (MS)
def deep_eq(a, b, decimal=7, exclude=None):
    """Deep compare two objects for equality by traversing __dict__ and
    __slots__.

    Caution: This function will exhaust generators.

    :param decimal:
        Desired precision (digits after the decimal point) for numerical
        comparisons.

    :param exclude:
        A list of attributes that will be excluded when traversing objects

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
    elif isinstance(a, numpy.ndarray):
        assert numpy.array_equal(a, b), '%s and %s are different' % (a, b)
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
            if slot not in exclude:
                _deep_eq(getattr(a, slot), getattr(b, slot), decimal)
    else:
        # Objects must be primitives

        # Are they numbers?
        if isinstance(a, (int, long, float, complex)):
            numpy.testing.assert_almost_equal(a, b, decimal=decimal)
        else:
            assert a == b, "%s != %s" % (a, b)


def writetmp(content=None, dir=None, prefix="tmp", suffix="tmp"):
    """Create temporary file with the given content.

    Please note: the temporary file must be deleted by the caller.

    :param string content: the content to write to the temporary file.
    :param string dir: directory where the file should be created
    :param string prefix: file name prefix
    :param string suffix: file name suffix
    :returns: a string with the path to the temporary file
    """
    if dir is not None:
        if not os.path.exists(dir):
            os.makedirs(dir)
    fh, path = tempfile.mkstemp(dir=dir, prefix=prefix, suffix=suffix)
    if content:
        fh = os.fdopen(fh, "w")
        fh.write(content)
        fh.close()
    return path


def run_in_process(code, *args):
    """
    Run in an external process the given Python code and return the
    output as a Python object. If there are arguments, then code is
    taken as a template and traditional string interpolation is performed.

    :param code: string or template describing Python code
    :param args: arguments to be used for interpolation
    :returns: the output of the process, as a Python object
    """
    if args:
        code %= args
    try:
        out = subprocess.check_output([sys.executable, '-c', code])
    except subprocess.CalledProcessError as exc:
        print >> sys.stderr, exc.cmd[-1]
        raise
    if out:
        return eval(out, {}, {})


class CodeDependencyError(Exception):
    pass


def import_all(module_or_package):
    """
    If `module_or_package` is a module, just import it; if it is a package,
    recursively imports all the modules it contains. Returns the names of
    the modules that were imported as a set. The set can be empty if
    the modules were already in sys.modules.
    """
    already_imported = set(sys.modules)
    mod_or_pkg = importlib.import_module(module_or_package)
    if not hasattr(mod_or_pkg, '__path__'):  # is a simple module
        return set(sys.modules) - already_imported
    # else import all modules contained in the package
    [pkg_path] = mod_or_pkg.__path__
    n = len(pkg_path)
    for cwd, dirs, files in os.walk(pkg_path):
        if all(os.path.basename(f) != '__init__.py' for f in files):
            # the current working directory is not a subpackage
            continue
        for f in files:
            if f.endswith('.py'):
                # convert PKGPATH/subpackage/module.py -> subpackage.module
                # works at any level of nesting
                modname = (module_or_package + cwd[n:].replace('/', '.') +
                           '.' + os.path.basename(f[:-3]))
                try:
                    importlib.import_module(modname)
                except Exception as exc:
                    print >> sys.stderr, 'Could not import %s: %s: %s' % (
                        modname, exc.__class__.__name__, exc)
    return set(sys.modules) - already_imported


def assert_independent(package, *packages):
    """
    :param package: Python name of a module/package
    :param packages: Python names of modules/packages

    Make sure the `package` does not depend from the `packages`.
    For instance

    >>> assert_independent('openquake.hazardlib',
    ...                    'openquake.risklib', 'openquake.commonlib')
    >>> assert_independent('openquake.risklib.tests', 'openquake.risklib')
    Traceback (most recent call last):
    ...
    CodeDependencyError: openquake.risklib.tests depends on openquake.risklib
    """
    assert packages, 'At least one package must be specified'
    import_package = 'from openquake.baselib.general import import_all\n' \
                     'print import_all("%s")' % package
    imported_modules = run_in_process(import_package)
    for mod in imported_modules:
        for pkg in packages:
            if mod.startswith(pkg):
                raise CodeDependencyError('%s depends on %s' % (package, pkg))


def search_module(module, syspath=sys.path):
    """
    Given a module name (possibly with dots) returns the corresponding
    filepath, or None, if the module cannot be found.

    :param module: (dotted) name of the Python module to look for
    :param syspath: a list of directories to search (default sys.path)
    """
    lst = module.split(".")
    pkg, submodule = lst[0], ".".join(lst[1:])
    try:
        fileobj, filepath, descr = imp.find_module(pkg, syspath)
    except ImportError:
        return
    if submodule:  # recursive search
        return search_module(submodule, [filepath])
    return filepath


class CallableDict(collections.OrderedDict):
    """
    A callable object built on top of a dictionary of functions,
    dispatching on the first argument according to the given keyfunc.
    The default keyfunc is the identity function, i.e. the first
    argument is assumed to be the key.
    """
    def __init__(self, keyfunc=lambda key: key):
        super(CallableDict, self).__init__()
        self.keyfunc = keyfunc

    def add(self, *keys):
        """
        Return a decorator registering a new implementation for the
        CallableDict for the given keys.
        """
        def decorator(func):
            for key in keys:
                self[key] = func
            return func
        return decorator

    def __call__(self, obj, *args, **kw):
        key = self.keyfunc(obj)
        if key not in self:
            raise KeyError(
                'There is nothing registered for %s' % repr(key))
        return self[key](obj, *args, **kw)


class AccumDict(dict):
    """
    An accumulating dictionary, useful to accumulate variables.

    >>> acc = AccumDict()
    >>> acc += {'a': 1}
    >>> acc += {'a': 1, 'b': 1}
    >>> acc
    {'a': 2, 'b': 1}
    >>> {'a': 1} + acc
    {'a': 3, 'b': 1}
    >>> acc + 1
    {'a': 3, 'b': 2}
    >>> 1 - acc
    {'a': -1, 'b': 0}
    >>> acc - 1
    {'a': 1, 'b': 0}

    Also the multiplication has been defined:

    >>> prob1 = AccumDict(a=0.4, b=0.5)
    >>> prob2 = AccumDict(b=0.5)
    >>> prob1 * prob2
    {'a': 0.4, 'b': 0.25}
    >>> prob1 * 1.2
    {'a': 0.48, 'b': 0.6}
    >>> 1.2 * prob1
    {'a': 0.48, 'b': 0.6}
    """

    def __iadd__(self, other):
        if hasattr(other, 'iteritems'):
            for k, v in other.iteritems():
                try:
                    self[k] = self[k] + v
                except KeyError:
                    self[k] = v
        else:  # add other to all elements
            for k in self:
                self[k] = self[k] + other
        return self

    def __add__(self, other):
        new = self.__class__(self)
        new += other
        return new

    __radd__ = __add__

    def __isub__(self, other):
        if hasattr(other, 'iteritems'):
            for k, v in other.iteritems():
                try:
                    self[k] = self[k] - v
                except KeyError:
                    self[k] = v
        else:  # subtract other to all elements
            for k in self:
                self[k] = self[k] - other
        return self

    def __sub__(self, other):
        new = self.__class__(self)
        new -= other
        return new

    def __rsub__(self, other):
        return - self.__sub__(other)

    def __neg__(self):
        return self.__class__({k: -v for k, v in self.iteritems()})

    def __imul__(self, other):
        if hasattr(other, 'iteritems'):
            for k, v in other.iteritems():
                try:
                    self[k] = self[k] * v
                except KeyError:
                    self[k] = v
        else:  # add other to all elements
            for k in self:
                self[k] = self[k] * other
        return self

    def __mul__(self, other):
        new = self.__class__(self)
        new *= other
        return new

    __rmul__ = __mul__

    def __truediv__(self, other):
        return self * (1. / other)

    def apply(self, func, *extras):
        """
        >>> a = AccumDict({'a': 1,  'b': 2})
        >>> a.apply(lambda x, y: 2 * x + y, 1)
        {'a': 3, 'b': 5}
        """
        return self.__class__({key: func(value, *extras)
                               for key, value in self.iteritems()})


class ArrayDict(collections.Mapping):
    """
    A class wrapping an array-valued dictionary. ArrayDict instances
    work as fixed-lenght mappings, but they also get some methods from
    numpy arrays. In particular, the arithmetic operators are supported.
    Notice that the arrays may have different lenghts for different keys.
    You should use this class when you have fixed keys and you want to
    store the data in a compact way.
    Here are a few examples of usage:

    >>> z = ArrayDict.zeros(dict(x=1, y=2), extradims=(5,))
    >>> z
    <ArrayDict x:1, y:2>
    >>> z.shape
    (3, 5)
    >>> a = ArrayDict(dict(x=[0], y=[2, 3]))
    >>> a.nbytes
    24
    >>> a['x'] = [1]
    >>> a['z'] = [2]
    Traceback (most recent call last):
     ...
    KeyError: 'z'
    >>> a.from_array(numpy.array([1, 2, 3, 4]))
    Traceback (most recent call last):
     ...
    ValueError: Wrong array size: expected 3, got 4

    >>> b = ArrayDict(dict(x=[3], y=[4, 5]))
    >>> print a
    [1 2 3]
    >>> print b
    [3 4 5]
    >>> print a + b
    [4 6 8]
    >>> print a - b
    [-2 -2 -2]
    >>> print a * b
    [ 3  8 15]
    >>> print a / b
    [ 0.33333333  0.5         0.6       ]
    >>> print -a
    [-1 -2 -3]
    >>> print a ** 2
    [1 4 9]
    >>> print a.apply(numpy.sqrt)
    [ 1.          1.41421356  1.73205081]
    """
    @classmethod
    def zeros(cls, sizedic, extradims=()):
        """
        :sizedic: a dictionary key -> size of array slice
        :extradims: an optional tuple of integers with extra dimensions
        :returns: an ArrayDict full of zeros
        """
        self = cls.__new__(cls)
        self.slicedic = {}
        start = 0
        for k in sorted(sizedic):
            self.slicedic[k] = slice(start, start + sizedic[k])
            start += sizedic[k]
        self.array = numpy.zeros((start,) + extradims)
        return self

    def __init__(self, dic):
        self.array = numpy.concatenate([dic[k] for k in sorted(dic)])
        self.slicedic = {}
        start = 0
        for k in sorted(dic):
            size = len(dic[k])
            self.slicedic[k] = slice(start, start + size)
            start += size

    @property
    def shape(self):
        """The shape of the underlying array"""
        return self.array.shape

    @property
    def size(self):
        """The size (number of elements) of the underlying array"""
        return self.array.size

    @property
    def nbytes(self):
        """The size in bytes of the underlying array"""
        return self.array.nbytes

    def copy(self):
        """
        Return a copy of the DictArray.

        >>> z = ArrayDict.zeros(dict(x=1))
        >>> w = z.copy()  # make a copy
        >>> w['x'] = [2]  # change the copy
        >>> print w - z   # w and z are different
        [ 2.]
        """
        return self.from_array(numpy.array(self.array))

    def mean(self):
        """The mean of the underlying array"""
        return self.array.mean()

    def from_array(self, array):
        """
        :param array: an array with the right length
        :returns: a new ArrayDict with the same .slicedic as self
        """
        n = sum(len(v) for v in self.itervalues())
        if len(array) != n:
            raise ValueError('Wrong array size: expected %d, got %d' %
                             (n, len(array)))
        new = self.__new__(self.__class__)
        new.array = array
        new.slicedic = self.slicedic
        return new

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.array[self.slicedic[key]]
        else:
            return self.array[key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.array[self.slicedic[key]] = value
        else:
            self.array[key] = value

    def __iter__(self):
        for k in sorted(self.slicedic):
            yield k

    def __len__(self):
        return len(self.array)

    def __add__(self, other):
        return self.from_array(self.array + getattr(other, 'array', other))

    __radd__ = __add__

    def __sub__(self, other):
        return self.from_array(self.array - getattr(other, 'array', other))

    def __rsub__(self, other):
        return - self.__sub__(other)

    def __neg__(self):
        return self.from_array(-self.array)

    def __mul__(self, other):
        return self.from_array(self.array * getattr(other, 'array', other))

    __rmul__ = __mul__

    def __truediv__(self, other):
        return self.from_array(self.array / getattr(other, 'array', other))

    def __pow__(self, other):
        return self.from_array(self.array.__pow__(other))

    def __gt__(self, other):
        return self.array > other

    def __lt__(self, other):
        return self.array < other

    def __ge__(self, other):
        return self.array >= other

    def __le__(self, other):
        return self.array <= other

    def apply(self, func, *extras):
        return self.from_array(func(self.array, *extras))

    def __repr__(self):
        sizes = ['%s:%s' % (k, s.stop - s.start)
                 for k, s in sorted(self.slicedic.iteritems())]
        return '<%s %s>' % (self.__class__.__name__, ', '.join(sizes))

    def __str__(self):
        return str(self.array)


def groupby(objects, key, reducegroup=list):
    """
    :param objects: a sequence of objects with a key value
    :param key: the key function to extract the key value
    :param reducegroup: the function to apply to each group
    :returns: an OrderedDict {key value: map(reducegroup, group)}

    >>> groupby(['A1', 'A2', 'B1', 'B2', 'B3'], lambda x: x[0],
    ...         lambda group: ''.join(x[1] for x in group))
    OrderedDict([('A', '12'), ('B', '123')])
    """
    kgroups = itertools.groupby(sorted(objects, key=key), key)
    return collections.OrderedDict((k, reducegroup(group))
                                   for k, group in kgroups)
