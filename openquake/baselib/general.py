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


def split_in_blocks_2(long_sequence, short_sequence, hint,
                      weight=lambda item: 1,
                      key=lambda item: 'Unspecified'):
    """
    Split two sequences in blocks. The first sequence has to be longer
    than the second. Yield pairs (block_from_seq_1, block_from_seq_2).

    :param long_sequence: a finite sequence of items of size N
    :param short_sequence: a finite sequence of items of size n <=N
    :param hint: an integer suggesting the number of blocks to generate
    :param weight: a function returning the weigth of a given item
    :param key: a function returning the key of a given item

    A few examples will explain how it works:

    >>> for b1, b2 in split_in_blocks_2(range(10), 'ABC', 3):
    ...      print b1, b2
    [0, 1, 2, 3] ['A']
    [4, 5, 6, 7] ['B']
    [8, 9] ['C']

    >>> for b1, b2 in split_in_blocks_2(range(10), 'ABC', 2):
    ...      print b1, b2
    [0, 1, 2, 3, 4] ['A', 'B']
    [5, 6, 7, 8, 9] ['C']

    If the second sequence is so short that it cannot be splitted in enough
    blocks (i.e. n < hint), then its blocks will be repeated to produce a
    number of blocks equal to the number of blocks of the first sequence:

    >>> for b1, b2 in split_in_blocks_2(range(10), 'ABC', 4):
    ...      print b1, b2
    [0, 1, 2] ['A']
    [3, 4, 5] ['B']
    [6, 7, 8] ['C']
    [9] ['A']
    """
    N, n = len(long_sequence), len(short_sequence)
    assert N >= n
    long_blocks = split_in_blocks(long_sequence, hint, weight, key)
    short_blocks = split_in_blocks(short_sequence, hint)
    for long_, short in zip(long_blocks, itertools.cycle(short_blocks)):
        yield list(long_), list(short)


def assert_close_seq(seq1, seq2, rtol, atol, context=None):
    """
    Compare two sequences of the same length.

    :param seq1: a sequence
    :param seq2: another sequence
    :param rtol: relative tolerance
    :param atol: absolute tolerance
    """
    assert len(seq1) == len(seq2), 'Lists of different lenghts: %d != %d' % (
        len(seq1), len(seq2))
    for x, y in zip(seq1, seq2):
        assert_close(x, y, rtol, atol, context)


def assert_close(a, b, rtol=1e-07, atol=0, context=None):
    """
    Compare for equality up to a given precision two composite objects
    which may contain floats. NB: if the objects are or contain generators,
    they are exhausted.

    :param a: an object
    :param b: another object
    :param rtol: relative tolerance
    :param atol: absolute tolerance
    """
    if isinstance(a, float) or isinstance(a, numpy.ndarray) and a.shape:
        # shortcut
        numpy.testing.assert_allclose(a, b, rtol, atol)
        return
    if a == b:  # another shortcut
        return
    if hasattr(a, '__slots__'):  # record-like objects
        assert_close_seq(a.__slots__, b.__slots__, rtol, atol, a)
        for x, y in zip(a.__slots__, b.__slots__):
            assert_close(getattr(a, x), getattr(b, y), rtol, atol, x)
        return
    if isinstance(a, collections.Mapping):  # dict-like objects
        assert_close_seq(a.keys(), b.keys(), rtol, atol, a)
        assert_close_seq(a.values(), b.values(), rtol, atol, a)
        return
    if hasattr(a, '__iter__'):  # iterable objects
        assert_close_seq(list(a), list(b), rtol, atol, a)
        return
    if hasattr(a, '__dict__'):  # objects with an attribute dictionary
        assert_close(vars(a), vars(b), context=a)
        return
    ctx = '' if context is None else 'in context ' + repr(context)
    raise AssertionError('%r != %r %s' % (a, b, ctx))


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
    r"""
    A callable object built on top of a dictionary of functions, used
    as a smart registry or as a poor man generic function dispatching
    on the first argument. It is typically used to implement converters.
    Here is an example:

    >>> format_attrs = CallableDict()  # dict of functions (fmt, obj) -> str

    >>> @format_attrs.add('csv')  # implementation for csv
    ... def format_attrs_csv(fmt, obj):
    ...     items = sorted(vars(obj).iteritems())
    ...     return '\n'.join('%s,%s' % item for item in items)

    >>> @format_attrs.add('json')  # implementation for json
    ... def format_attrs_json(fmt, obj):
    ...     return json.dumps(vars(obj))

    `format_attrs(fmt, obj)` calls the correct underlying function
    depending on the `fmt` key. If the format is unknown a `KeyError` is
    raised. It is also possible to set a `keymissing` function to specify
    what to return if the key is missing.

    For a more practical example see the implementation of the exporters
    in :module:`openquake.commonlib.export`
    """
    def __init__(self, keyfunc=lambda key: key, keymissing=None):
        super(CallableDict, self).__init__()
        self.keyfunc = keyfunc
        self.keymissing = keymissing

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
        return self[key](obj, *args, **kw)

    def __missing__(self, key):
        if callable(self.keymissing):
            return self.keymissing(key)
        raise KeyError(key)


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


def humansize(nbytes, suffixes=('B', 'KB', 'MB', 'GB', 'TB', 'PB')):
    """
    Return file size in a human-friendly format
    """
    if nbytes == 0:
        return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])
