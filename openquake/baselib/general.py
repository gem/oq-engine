# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2014-2025 GEM Foundation
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
import os
import sys
import zlib
import copy
import math
import time
import pickle
import socket
import random
import atexit
import zipfile
import logging
import builtins
import operator
import warnings
import tempfile
import importlib
import itertools
import subprocess
import collections
import multiprocessing
from importlib.metadata import version, PackageNotFoundError
from contextlib import contextmanager
from collections.abc import Mapping, Container, Sequence, MutableSequence
import numpy
import pandas
from decorator import decorator
from openquake.baselib import __version__, config
from openquake.baselib.python3compat import decode

U8 = numpy.uint8
U16 = numpy.uint16
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16
BASE183 = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmno"
           "pqrstuvwxyz{|}!#$%&'()*+-/0123456789:;<=>?@¡¢"
           "£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑ"
           "ÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ")
BASE33489 = []  # built in 0.003 seconds
for a, b in itertools.product(BASE183, BASE183):
    BASE33489.append(a + b)
mp = multiprocessing.get_context('spawn')


class Cache(dict):
    miss = 0
    tot = 0

    @property
    def hit(self):
        return self.tot - self.miss

    @property
    def speedup(self):
        return self.tot / self.miss

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self.miss += 1

    def __getitem__(self, key):
        self.tot += 1
        return dict.__getitem__(self, key)

    def getsize(self):
        """
        :returns: the size in bytes of the cache values
        """
        return sum(getsizeof(val) for val in self.values())

    def __str__(self):
        templ = '<Cache hit=%d, miss=%d, speedup=%.1f, size=%s>'
        return templ % (self.hit, self.miss, self.speedup,
                        humansize(self.getsize()))


def duplicated(items):
    """
    :returns: the list of duplicated keys, possibly empty
    """
    counter = collections.Counter(items)
    return [key for key, counts in counter.items() if counts > 1]


def cached_property(method):
    """
    :param method: a method without arguments except self
    :returns: a cached property
    """
    name = method.__name__

    def newmethod(self):
        try:
            val = self.__dict__[name]
        except KeyError:
            t0 = time.time()
            val = method(self)
            cached_property.dt[name] = time.time() - t0
            self.__dict__[name] = val
        return val
    newmethod.__name__ = method.__name__
    newmethod.__doc__ = method.__doc__
    return property(newmethod)


cached_property.dt = {}  # dictionary of times


def nokey(item):
    """
    Dummy function to apply to items without a key
    """
    return 'Unspecified'


class WeightedSequence(MutableSequence):
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
            a :class:`openquake.baselib.general.WeightedSequence` instance
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

    def insert(self, i, item_weight):
        """
        Insert an item with the given weight in the sequence
        """
        item, weight = item_weight
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


def ceil(x):
    """
    Converts the result of math.ceil into an integer
    """
    return int(math.ceil(x))


def block_splitter(items, max_weight, weight=lambda item: 1, key=nokey,
                   sort=False):
    """
    :param items: an iterator over items
    :param max_weight: the max weight to split on
    :param weight: a function returning the weigth of a given item
    :param key: a function returning the kind of a given item
    :param sort: if True, sort the items by reverse weight before splitting

    Group together items of the same kind until the total weight exceeds the
    `max_weight` and yield `WeightedSequence` instances. Items
    with weight zero are ignored.

    For instance

     >>> items = 'ABCDE'
     >>> list(block_splitter(items, 3))
     [<WeightedSequence ['A', 'B', 'C'], weight=3>, <WeightedSequence ['D', 'E'], weight=2>]

    The default weight is 1 for all items. Here is an example leveraning on the
    key to group together results:

    >>> items = ['A1', 'C2', 'D2', 'E2']
    >>> list(block_splitter(items, 2, key=operator.itemgetter(1)))
    [<WeightedSequence ['A1'], weight=1>, <WeightedSequence ['C2', 'D2'], weight=2>, <WeightedSequence ['E2'], weight=1>]
    """
    if max_weight <= 0:
        raise ValueError('max_weight=%s' % max_weight)
    ws = WeightedSequence([])
    prev_key = 'Unspecified'
    for item in sorted(items, key=weight, reverse=True) if sort else items:
        w = weight(item)
        k = key(item)
        if w < 0:  # error
            raise ValueError('The item %r got a negative weight %s!' %
                             (item, w))
        elif ws.weight + w > max_weight or k != prev_key:
            new_ws = WeightedSequence([(item, w)])
            if ws:
                yield ws
            ws = new_ws
        elif w > 0:  # ignore items with 0 weight
            ws.append((item, w))
        prev_key = k
    if ws:
        yield ws


def split_in_slices(number, num_slices):
    """
    :param number: a positive number to split in slices
    :param num_slices: the number of slices to return (at most)
    :returns: a list of slices

    >>> split_in_slices(4, 2)
    [slice(0, 2, None), slice(2, 4, None)]
    >>> split_in_slices(5, 1)
    [slice(0, 5, None)]
    >>> split_in_slices(5, 2)
    [slice(0, 3, None), slice(3, 5, None)]
    >>> split_in_slices(2, 4)
    [slice(0, 1, None), slice(1, 2, None)]
    """
    assert number > 0, number
    assert num_slices > 0, num_slices
    blocksize = int(math.ceil(number / num_slices))
    slices = []
    start = 0
    while True:
        stop = min(start + blocksize, number)
        slices.append(slice(start, stop))
        if stop == number:
            break
        start += blocksize
    return slices


def gen_slices(start, stop, blocksize):
    """
    Yields slices of lenght at most block_size.

    >>> list(gen_slices(1, 6, 2))
    [slice(1, 3, None), slice(3, 5, None), slice(5, 6, None)]
    """
    blocksize = int(blocksize)
    assert start <= stop, (start, stop)
    assert blocksize > 0, blocksize
    while True:
        yield slice(start, min(start + blocksize, stop))
        start += blocksize
        if start >= stop:
            break


def split_in_blocks(sequence, hint, weight=lambda item: 1, key=nokey):
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
     [<WeightedSequence ['A'], weight=1>, <WeightedSequence ['B'], weight=1>, <WeightedSequence ['C'], weight=1>, <WeightedSequence ['D'], weight=1>, <WeightedSequence ['E'], weight=1>]
    """
    if isinstance(sequence, pandas.DataFrame):
        num_elements = len(sequence)
        out = numpy.array_split(
            sequence, num_elements if num_elements < hint else hint)
        return out
    elif isinstance(sequence, int):
        return split_in_slices(sequence, hint)
    elif hint in (0, 1) and key is nokey:  # do not split
        return [sequence]
    elif hint in (0, 1):  # split by key
        blocks = []
        for k, group in groupby(sequence, key).items():
            blocks.append(group)
        return blocks
    items = sorted(sequence, key=lambda item: (key(item), weight(item)))
    assert hint > 0, hint
    assert len(items) > 0, len(items)
    total_weight = float(sum(weight(item) for item in items))
    return block_splitter(items, total_weight / hint, weight, key)


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
    if isinstance(a, (str, bytes, int)):
        # another shortcut
        assert a == b, (a, b)
        return
    if hasattr(a, 'keys'):  # dict-like objects
        assert a.keys() == b.keys(), set(a).symmetric_difference(set(b))
        for x in a:
            if x != '__geom__':
                assert_close(a[x], b[x], rtol, atol, x)
        return
    if hasattr(a, '__dict__'):  # objects with an attribute dictionary
        assert_close(vars(a), vars(b), rtol, atol, context=a)
        return
    if hasattr(a, '__iter__'):  # iterable objects
        xs, ys = list(a), list(b)
        assert len(xs) == len(ys), ('Lists of different lenghts: %d != %d'
                                    % (len(xs), len(ys)))
        for x, y in zip(xs, ys):
            assert_close(x, y, rtol, atol, x)
        return
    if a == b:  # last attempt to avoid raising the exception
        return
    ctx = '' if context is None else 'in context ' + repr(context)
    raise AssertionError('%r != %r %s' % (a, b, ctx))


_tmp_paths = []


def gettemp(content=None, dir=None, prefix="tmp", suffix="tmp", remove=True):
    """Create temporary file with the given content.

    Please note: the temporary file can be deleted by the caller or not.

    :param string content: the content to write to the temporary file.
    :param string dir: directory where the file should be created
    :param string prefix: file name prefix
    :param string suffix: file name suffix
    :param bool remove:
        True by default, meaning the file will be automatically removed
        at the exit of the program
    :returns:
        a string with the path to the temporary file
    """
    if dir is not None:
        if not os.path.exists(dir):
            os.makedirs(dir)
    fh, path = tempfile.mkstemp(dir=dir or config.directory.custom_tmp or None,
                                prefix=prefix, suffix=suffix)
    if remove:
        _tmp_paths.append(path)
    with os.fdopen(fh, "wb") as fh:
        if content:
            if hasattr(content, 'encode'):
                content = content.encode('utf8')
            fh.write(content)
    return path


@atexit.register
def removetmp():
    """
    Remove the temporary files created by gettemp
    """
    for path in _tmp_paths:
        if os.path.exists(path):  # not removed yet
            try:
                os.remove(path)
            except PermissionError:
                pass


def check_extension(fnames):
    """
    Make sure all file names have the same extension
    """
    if not fnames:
        return
    _, extension = os.path.splitext(fnames[0])
    for fname in fnames[1:]:
        _, ext = os.path.splitext(fname)
        if ext != extension:
            raise NameError(f'{fname} does not end with {ext}')


def engine_version():
    """
    :returns: __version__ + `<short git hash>` if Git repository found
    """
    # we assume that the .git folder is two levels above any package
    # i.e. openquake/engine/../../.git
    git_path = os.path.join(os.path.dirname(__file__), '..', '..', '.git')

    # macOS complains if we try to execute git and it's not available.
    # Code will run, but a pop-up offering to install bloatware (Xcode)
    # is raised. This is annoying in end-users installations, so we check
    # if .git exists before trying to execute the git executable
    gh = ''
    if os.path.isdir(git_path):
        try:
            with open(os.devnull, 'w') as devnull:
                gh = subprocess.check_output(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    stderr=devnull, cwd=os.path.dirname(git_path)).strip()
            gh = "-git" + decode(gh) if gh else ''
        except Exception:
            pass
            # trapping everything on purpose; git may not be installed or it
            # may not work properly

    return __version__ + gh


def extract_dependencies(lines):
    for line in lines:
        longname = line.split('/')[-1]  # i.e. urllib3-2.1.0-py3-none-any.whl
        try:
            pkg, version, _other = longname.split('-', 2)
        except ValueError:  # for instance a comment
            continue
        if pkg in ('fonttools', 'protobuf', 'pyreadline3', 'python_dateutil',
                   'python_pam', 'django_cors_headers',
                   'django_cookie_consent'):
            # not importable
            continue
        if pkg in ('alpha_shapes', 'django_pam', 'pbr', 'iniconfig',
                   'importlib_metadata', 'zipp'):
            # missing __version__
            continue
        elif pkg == 'pyzmq':
            pkg = 'zmq'
        elif pkg == 'Pillow':
            pkg = 'PIL'
        elif pkg == 'GDAL':
            pkg = 'osgeo.gdal'
        elif pkg == 'Django':
            pkg = 'django'
        elif pkg == 'pyshp':
            pkg = 'shapefile'
        elif pkg == 'django_appconf':
            pkg = 'appconf'
        yield pkg, version


def check_dependencies():
    """
    Print a warning if we forgot to update the dependencies.
    Works only for development installations.
    """
    import openquake
    if 'site-packages' in openquake.__path__[0]:
        return  # do nothing for non-devel installations
    pyver = '%d%d' % (sys.version_info[0], sys.version_info[1])
    system = sys.platform
    if system == 'linux':
        system = 'linux64'
    elif system == 'win32':
        system = 'win64'
    elif system == 'darwin':
        system = 'macos_arm64'
    else:
        # unsupported OS, do not check dependencies
        return
    reqfile = 'requirements-py%s-%s.txt' % (pyver, system)
    repodir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    with open(os.path.join(repodir, reqfile)) as f:
        lines = f.readlines()
    for pkg, expected in extract_dependencies(lines):
        try:
            installed_version = version(pkg)
        except PackageNotFoundError:
            # handling cases such as "No package metadata was found for zmq"
            # (in other cases, e.g. timezonefinder, __version__ is not defined)
            installed_version = __import__(pkg).__version__
        if installed_version != expected:
            logging.warning('%s is at version %s but the requirements say %s' %
                            (pkg, installed_version, expected))


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
        print(exc.cmd[-1], file=sys.stderr)
        raise
    if out:
        out = out.rstrip(b'\x1b[?1034h')
        # this is absurd, but it happens: just importing a module can
        # produce escape sequences in stdout, see for instance
        # https://bugs.python.org/issue19884
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
            if f.endswith('.py') and not f.startswith('__init__'):
                # convert PKGPATH/subpackage/module.py -> subpackage.module
                # works at any level of nesting
                modname = (module_or_package + cwd[n:].replace(os.sep, '.') +
                           '.' + os.path.basename(f[:-3]))
                importlib.import_module(modname)
    return set(sys.modules) - already_imported


def assert_independent(package, *packages):
    """
    :param package: Python name of a module/package
    :param packages: Python names of modules/packages

    Make sure the `package` does not depend from the `packages`.
    """
    assert packages, 'At least one package must be specified'
    import_package = 'from openquake.baselib.general import import_all\n' \
                     'print(import_all("%s"))' % package
    imported_modules = run_in_process(import_package)
    for mod in imported_modules:
        for pkg in packages:
            if mod.startswith(pkg):
                raise CodeDependencyError('%s depends on %s' % (package, pkg))


class CallableDict(dict):
    r"""
    A callable object built on top of a dictionary of functions, used
    as a smart registry or as a poor man generic function dispatching
    on the first argument. It is typically used to implement converters.
    Here is an example:

    >>> format_attrs = CallableDict()  # dict of functions (fmt, obj) -> str

    >>> @format_attrs.add('csv')  # implementation for csv
    ... def format_attrs_csv(fmt, obj):
    ...     items = sorted(vars(obj).items())
    ...     return '\n'.join('%s,%s' % item for item in items)

    >>> @format_attrs.add('json')  # implementation for json
    ... def format_attrs_json(fmt, obj):
    ...     return json.dumps(vars(obj))

    `format_attrs(fmt, obj)` calls the correct underlying function
    depending on the `fmt` key. If the format is unknown a `KeyError` is
    raised. It is also possible to set a `keymissing` function to specify
    what to return if the key is missing.

    For a more practical example see the implementation of the exporters
    in openquake.calculators.export
    """
    def __init__(self, keyfunc=lambda key: key, keymissing=None):
        super().__init__()
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
            return self.keymissing
        raise KeyError(key)


class pack(dict):
    """
    Compact a dictionary of lists into a dictionary of arrays.
    If attrs are given, consider those keys as attributes. For instance,

    >>> p = pack(dict(x=[1], a=[0]), ['a'])
    >>> p
    {'x': array([1])}
    >>> p.a
    array([0])
    """
    def __init__(self, dic, attrs=()):
        for k, v in dic.items():
            arr = numpy.array(v)
            if k in attrs:
                setattr(self, k, arr)
            else:
                self[k] = arr


class AccumDict(dict):
    """
    An accumulating dictionary, useful to accumulate variables::

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

    The multiplication has been defined:

     >>> prob1 = AccumDict(dict(a=0.4, b=0.5))
     >>> prob2 = AccumDict(dict(b=0.5))
     >>> prob1 * prob2
     {'a': 0.4, 'b': 0.25}
     >>> prob1 * 1.2
     {'a': 0.48, 'b': 0.6}
     >>> 1.2 * prob1
     {'a': 0.48, 'b': 0.6}

    And even the power:

    >>> prob2 ** 2
    {'b': 0.25}

    It is very common to use an AccumDict of accumulators; here is an
    example using the empty list as accumulator:

    >>> acc = AccumDict(accum=[])
    >>> acc['a'] += [1]
    >>> acc['b'] += [2]
    >>> sorted(acc.items())
    [('a', [1]), ('b', [2])]

    The implementation is smart enough to make (deep) copies of the
    accumulator, therefore each key has a different accumulator, which
    initially is the empty list (in this case).
    """
    def __init__(self, dic=None, accum=None, keys=()):
        for key in keys:
            self[key] = copy.deepcopy(accum)
        if dic:
            self.update(dic)
        self.accum = accum

    def __iadd__(self, other):
        if hasattr(other, 'items'):
            for k, v in other.items():
                if k not in self:
                    self[k] = v
                elif isinstance(v, list):
                    # specialized for speed
                    self[k].extend(v)
                else:
                    self[k] += v
        else:  # add other to all elements
            for k in self:
                self[k] += other
        return self

    def __add__(self, other):
        new = self.__class__(self)
        new += other
        return new

    __radd__ = __add__

    def __isub__(self, other):
        if hasattr(other, 'items'):
            for k, v in other.items():
                try:
                    self[k] -= self[k]
                except KeyError:
                    self[k] = v
        else:  # subtract other to all elements
            for k in self:
                self[k] -= other
        return self

    def __sub__(self, other):
        new = self.__class__(self)
        new -= other
        return new

    def __rsub__(self, other):
        return - self.__sub__(other)

    def __neg__(self):
        return self.__class__({k: -v for k, v in self.items()})

    def __invert__(self):
        return self.__class__({k: ~v for k, v in self.items()})

    def __imul__(self, other):
        if hasattr(other, 'items'):
            for k, v in other.items():
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

    def __pow__(self, n):
        new = self.__class__(self)
        for key in new:
            new[key] **= n
        return new

    def __truediv__(self, other):
        return self * (1. / other)

    def __missing__(self, key):
        if self.accum is None:
            # no accumulator, accessing a missing key is an error
            raise KeyError(key)
        val = self[key] = copy.deepcopy(self.accum)
        return val

    def apply(self, func, *extras):
        """
        >> a = AccumDict({'a': 1,  'b': 2})
        >> a.apply(lambda x, y: 2 * x + y, 1)
        {'a': 3, 'b': 5}
        """
        return self.__class__({key: func(value, *extras)
                               for key, value in self.items()})


def copyobj(obj, **kwargs):
    """
    :returns: a shallow copy of obj with some changed attributes
    """
    new = copy.copy(obj)
    for k, v in kwargs.items():
        setattr(new, k, v)
    return new


class DictArray(Mapping):
    """
    A small wrapper over a dictionary of arrays with the same lenghts.
    """
    def __init__(self, imtls):
        levels = imtls[next(iter(imtls))]
        self.M = len(imtls)
        self.L1 = len(levels)
        self.size = self.M * self.L1
        items = imtls.items()
        self.dt = numpy.dtype([(str(imt), F64, (self.L1,))
                               for imt, imls in items])
        self.array = numpy.zeros((self.M, self.L1), F64)
        self.slicedic = {}
        n = 0
        self.mdic = {}
        for m, (imt, imls) in enumerate(items):
            if len(imls) != self.L1:
                raise ValueError('imt=%s has %d levels, expected %d' %
                                 (imt, len(imls), self.L1))
            self.slicedic[imt] = slice(n, n + self.L1)
            self.mdic[imt] = m
            self.array[m] = imls
            n += self.L1

    def __call__(self, imt):
        return self.slicedic[imt]

    def __getitem__(self, imt):
        return self.array[self.mdic[imt]]

    def __setitem__(self, imt, array):
        self.array[self.mdic[imt]] = array

    def __iter__(self):
        for imt in self.dt.names:
            yield imt

    def __len__(self):
        return len(self.dt.names)

    def __eq__(self, other):
        arr = self.array == other.array
        if isinstance(arr, bool):
            return arr
        return arr.all()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        data = ['%s: %s' % (imt, self[imt]) for imt in self]
        return '<%s\n%s>' % (self.__class__.__name__, '\n'.join(data))


def groupby(objects, key, reducegroup=list):
    """
    :param objects: a sequence of objects with a key value
    :param key: the key function to extract the key value
    :param reducegroup: the function to apply to each group
    :returns: a dict {key value: map(reducegroup, group)}

    >>> groupby(['A1', 'A2', 'B1', 'B2', 'B3'], lambda x: x[0],
    ...         lambda group: ''.join(x[1] for x in group))
    {'A': '12', 'B': '123'}
    """
    kgroups = itertools.groupby(sorted(objects, key=key), key)
    return {k: reducegroup(group) for k, group in kgroups}


def groupby2(records, kfield, vfield):
    """
    :param records: a sequence of records with positional or named fields
    :param kfield: the index/name/tuple specifying the field to use as a key
    :param vfield: the index/name/tuple specifying the field to use as a value
    :returns: an list of pairs of the form (key, [value, ...]).

    >>> groupby2(['A1', 'A2', 'B1', 'B2', 'B3'], 0, 1)
    [('A', ['1', '2']), ('B', ['1', '2', '3'])]

    Here is an example where the keyfield is a tuple of integers:

    >>> groupby2(['A11', 'A12', 'B11', 'B21'], (0, 1), 2)
    [(('A', '1'), ['1', '2']), (('B', '1'), ['1']), (('B', '2'), ['1'])]
    """
    if isinstance(kfield, tuple):
        kgetter = operator.itemgetter(*kfield)
    else:
        kgetter = operator.itemgetter(kfield)
    if isinstance(vfield, tuple):
        vgetter = operator.itemgetter(*vfield)
    else:
        vgetter = operator.itemgetter(vfield)
    dic = groupby(records, kgetter, lambda rows: [vgetter(r) for r in rows])
    return list(dic.items())  # Python3 compatible


def get_bins(values, nbins, key=None, minval=None, maxval=None):
    """
    :param values: an array of N floats (or arrays)
    :returns: an array of N bin indices plus an array of B bins
    """
    assert len(values)
    if key is not None:
        values = numpy.array([key(val) for val in values])
    if minval is None:
        minval = values.min()
    if maxval is None:
        maxval = values.max()
    if minval == maxval:
        bins = [minval] * nbins
    else:
        bins = numpy.arange(minval, maxval, (maxval-minval) / nbins)
    return numpy.searchsorted(bins, values, side='right'), bins


def groupby_grid(xs, ys, deltax, deltay):
    """
    :param xs: an array of P abscissas
    :param ys: an array of P ordinates
    :param deltax: grid spacing on the x-axis
    :param deltay: grid spacing on the y-axis
    :returns:
        dictionary centroid -> indices (of the points around each centroid)
    """
    lx, ly = len(xs), len(ys)
    assert lx == ly, (lx, ly)
    assert lx > 1, lx
    assert deltax > 0, deltax
    assert deltay > 0, deltay
    xmin = xs.min()
    xmax = xs.max()
    ymin = ys.min()
    ymax = ys.max()
    nx = numpy.ceil((xmax - xmin) / deltax)
    ny = numpy.ceil((ymax - ymin) / deltay)
    assert nx > 0, nx
    assert ny > 0, ny
    xbins = get_bins(xs, nx, None, xmin, xmax)[0]
    ybins = get_bins(ys, ny, None, ymin, ymax)[0]
    acc = AccumDict(accum=[])
    for k, ij in enumerate(zip(xbins, ybins)):
        acc[ij].append(k)
    dic = {}
    for ks in acc.values():
        ks = numpy.array(ks)
        dic[xs[ks].mean(), ys[ks].mean()] = ks
    return dic


def groupby_bin(values, nbins, key=None, minval=None, maxval=None):
    """
    >>> values = numpy.arange(10)
    >>> for group in groupby_bin(values, 3):
    ...     print(group)
    [0, 1, 2]
    [3, 4, 5]
    [6, 7, 8, 9]
    """
    if len(values) == 0:  # do nothing
        return values
    idxs = get_bins(values, nbins, key, minval, maxval)[0]
    acc = AccumDict(accum=[])
    for idx, val in zip(idxs, values):
        if isinstance(idx, numpy.ndarray):
            idx = tuple(idx)  # make it hashable
        acc[idx].append(val)
    return acc.values()


def _reducerecords(group):
    records = list(group)
    return numpy.array(records, records[0].dtype)


def group_array(array, *kfields):
    """
    Convert an array into a dict kfields -> array
    """
    return groupby(array, operator.itemgetter(*kfields), _reducerecords)


def multi_index(shape, axis=None):
    """
    :param shape: a shape of lenght L
    :param axis: None or an integer in the range 0 .. L -1
    :yields:
        tuples of indices with a slice(None) at the axis position (if any)

    >>> for slc in multi_index((2, 3), 0): print(slc)
    (slice(None, None, None), 0, 0)
    (slice(None, None, None), 0, 1)
    (slice(None, None, None), 0, 2)
    (slice(None, None, None), 1, 0)
    (slice(None, None, None), 1, 1)
    (slice(None, None, None), 1, 2)
    """
    ranges = (range(s) for s in shape)
    if axis is None:
        yield from itertools.product(*ranges)
    for tup in itertools.product(*ranges):
        lst = list(tup)
        lst.insert(axis, slice(None))
        yield tuple(lst)


# NB: the fast_agg functions are usually faster than pandas
def fast_agg(indices, values=None, axis=0, factor=None, M=None):
    """
    :param indices: N indices in the range 0 ... M - 1 with M < N
    :param values: N values (can be arrays)
    :param factor: if given, a multiplicate factor (or weight) for the values
    :param M: maximum index; if None, use max(indices) + 1
    :returns: M aggregated values (can be arrays)

    >>> values = numpy.array([[.1, .11], [.2, .22], [.3, .33], [.4, .44]])
    >>> fast_agg([0, 1, 1, 0], values)
    array([[0.5 , 0.55],
           [0.5 , 0.55]])
    """
    if values is None:
        values = numpy.ones_like(indices)
    N = len(values)
    if len(indices) != N:
        raise ValueError('There are %d values but %d indices' %
                         (N, len(indices)))
    shp = values.shape[1:]
    if M is None:
        M = max(indices) + 1
    if not shp:
        return numpy.bincount(
            indices, values if factor is None else values * factor, M)
    lst = list(shp)
    lst.insert(axis, M)
    res = numpy.zeros(lst, values.dtype)
    for mi in multi_index(shp, axis):
        vals = values[mi] if factor is None else values[mi] * factor
        res[mi] = numpy.bincount(indices, vals, M)
    return res


# NB: the fast_agg functions are usually faster than pandas
def fast_agg2(tags, values=None, axis=0):
    """
    :param tags: N non-unique tags out of M
    :param values: N values (can be arrays)
    :returns: (M unique tags, M aggregated values)

    >>> values = numpy.array([[.1, .11], [.2, .22], [.3, .33], [.4, .44]])
    >>> fast_agg2(['A', 'B', 'B', 'A'], values)
    (array(['A', 'B'], dtype='<U1'), array([[0.5 , 0.55],
           [0.5 , 0.55]]))

    It can also be used to count the number of tags:

    >>> fast_agg2(['A', 'B', 'B', 'A', 'A'])
    (array(['A', 'B'], dtype='<U1'), array([3., 2.]))
    """
    uniq, indices = numpy.unique(tags, return_inverse=True)
    return uniq, fast_agg(indices, values, axis)


# NB: the fast_agg functions are usually faster than pandas
def fast_agg3(structured_array, kfield, vfields=None, factor=None):
    """
    Aggregate a structured array with a key field (the kfield)
    and some value fields (the vfields). If vfields is not passed,
    use all fields except the kfield.

    >>> data = numpy.array([(1, 2.4), (1, 1.6), (2, 2.5)],
    ...                    [('aid', U16), ('val', F32)])
    >>> fast_agg3(data, 'aid')
    array([(1, 4. ), (2, 2.5)], dtype=[('aid', '<u2'), ('val', '<f4')])
    """
    allnames = structured_array.dtype.names
    if vfields is None:
        vfields = [name for name in allnames if name != kfield]
    assert kfield in allnames, kfield
    for vfield in vfields:
        assert vfield in allnames, vfield
    tags = structured_array[kfield]
    uniq, indices = numpy.unique(tags, return_inverse=True)
    dic = {}
    dtlist = [(kfield, structured_array.dtype[kfield])]
    for name in vfields:
        dic[name] = fast_agg(indices, structured_array[name], factor=factor)
        dtlist.append((name, structured_array.dtype[name]))
    res = numpy.zeros(len(uniq), dtlist)
    res[kfield] = uniq
    for name in dic:
        res[name] = dic[name]
    return res


def idxs_by_tag(tags):
    """
    >>> idxs_by_tag([2, 1, 1, 2])
    {2: array([0, 3], dtype=uint32), 1: array([1, 2], dtype=uint32)}
    """
    dic = AccumDict(accum=[])
    for i, tag in enumerate(tags):
        dic[tag].append(i)
    return {tag: numpy.uint32(dic[tag]) for tag in dic}


def count(groupiter):
    return sum(1 for row in groupiter)


def countby(array, *kfields):
    """
    :returns: a dict kfields -> number of records with that key
    """
    return groupby(array, operator.itemgetter(*kfields), count)


def get_array(array, **kw):
    """
    Extract a subarray by filtering on the given keyword arguments
    """
    for name, value in kw.items():
        array = array[array[name] == value]
    return array


def not_equal(array_or_none1, array_or_none2):
    """
    Compare two arrays that can also be None or have diffent shapes
    and returns a boolean.

    >>> a1 = numpy.array([1])
    >>> a2 = numpy.array([2])
    >>> a3 = numpy.array([2, 3])
    >>> not_equal(a1, a2)
    True
    >>> not_equal(a1, a3)
    True
    >>> not_equal(a1, None)
    True
    """
    if array_or_none1 is None and array_or_none2 is None:
        return False
    elif array_or_none1 is None and array_or_none2 is not None:
        return True
    elif array_or_none1 is not None and array_or_none2 is None:
        return True
    if array_or_none1.shape != array_or_none2.shape:
        return True
    return (array_or_none1 != array_or_none2).any()


def all_equals(inputs):
    """
    :param inputs: a list of arrays or strings
    :returns: True if all values are equal, False otherwise
    """
    inp0 = inputs[0]
    for inp in inputs[1:]:
        try:
            diff = inp != inp0
        except ValueError:  # Lengths must match to compare
            return False
        if isinstance(diff, numpy.ndarray):
            if diff.any():
                return False
        elif diff:
            return False
    return True


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


# the builtin DeprecationWarning has been silenced in Python 2.7
class DeprecationWarning(UserWarning):
    """
    Raised the first time a deprecated function is called
    """


@decorator
def deprecated(func, msg='', *args, **kw):
    """
    A family of decorators to mark deprecated functions.

    :param msg:
        the message to print the first time the
        deprecated function is used.

    Here is an example of usage:

    >>> @deprecated(msg='Use new_function instead')
    ... def old_function():
    ...     'Do something'

    Notice that if the function is called several time, the deprecation
    warning will be displayed only the first time.
    """
    msg = '%s.%s has been deprecated. %s' % (
        func.__module__, func.__name__, msg)
    if not hasattr(func, 'called'):
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
        func.called = 0
    func.called += 1
    return func(*args, **kw)


def random_filter(objects, reduction_factor, seed=42):
    """
    Given a list of objects, returns a sublist by extracting randomly
    some elements. The reduction factor (< 1) tells how small is the extracted
    list compared to the original list.
    """
    assert 0 < reduction_factor <= 1, reduction_factor
    if reduction_factor == 1:  # do not reduce
        return objects
    rnd = random.Random(seed)
    if isinstance(objects, pandas.DataFrame):
        df = pandas.DataFrame({
            col: random_filter(objects[col], reduction_factor, seed)
            for col in objects.columns})
        return df
    out = []
    for obj in objects:
        if rnd.random() <= reduction_factor:
            out.append(obj)
    return out


def random_choice(array, num_samples, offset=0, seed=42):
    """
    Extract num_samples from an array. It has the fundamental property
    of splittability, i.e. if the seed is the same and `||` means
    array concatenation:

    choice(a, N) = choice(a, n, 0) || choice(a, N-n, n)

    This property makes `random_choice` suitable to be parallelized,
    while `random.choice` is not. It as also absurdly fast.
    """
    rng = numpy.random.default_rng(seed)
    rng.bit_generator.advance(offset)
    N = len(array)
    cumsum = numpy.repeat(1./N, N).cumsum()
    choices = numpy.searchsorted(cumsum, rng.random(num_samples))
    return array[choices]


def random_histogram(counts, nbins_or_binweights, seed):
    """
    Distribute a total number of counts over a set of bins. If the
    weights of the bins are equal you can just pass the number of the
    bins and a faster algorithm will be used. Otherwise pass the weights.
    Here are a few examples:

    >>> list(random_histogram(1, 2, seed=42))
    [0, 1]
    >>> list(random_histogram(100, 5, seed=42))
    [22, 17, 21, 26, 14]
    >>> list(random_histogram(10000, 5, seed=42))
    [2034, 2000, 2014, 1998, 1954]
    >>> list(random_histogram(1000, [.3, .3, .4], seed=42))
    [308, 295, 397]
    """
    rng = numpy.random.default_rng(seed)
    try:
        nbins = len(nbins_or_binweights)
    except TypeError:  # 'int' has no len()
        nbins = nbins_or_binweights
        weights = numpy.repeat(1./nbins, nbins)
    else:
        weights = numpy.array(nbins_or_binweights)
        weights /= weights.sum()  # normalize to 1
    bins = numpy.searchsorted(weights.cumsum(), rng.random(counts))
    return numpy.bincount(bins, minlength=len(weights))


def safeprint(*args, **kwargs):
    """
    Convert and print characters using the proper encoding
    """
    new_args = []
    # when stdout is redirected to a file, python 2 uses ascii for the writer;
    # python 3 uses what is configured in the system (i.e. 'utf-8')
    # if sys.stdout is replaced by a StringIO instance, Python 2 does not
    # have an attribute 'encoding', and we assume ascii in that case
    str_encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
    for s in args:
        new_args.append(s.encode('utf-8').decode(str_encoding, 'ignore'))

    return print(*new_args, **kwargs)


def socket_ready(hostport):
    """
    :param hostport: a pair (host, port) or a string (tcp://)host:port
    :returns: True if the socket is ready and False otherwise
    """
    if hasattr(hostport, 'startswith'):
        # string representation of the hostport combination
        if hostport.startswith('tcp://'):
            hostport = hostport[6:]  # strip tcp://
        host, port = hostport.split(':')
        hostport = (host, int(port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        exc = sock.connect_ex(hostport)
    finally:
        sock.close()
    return False if exc else True


port_candidates = list(range(1920, 2000))


def _get_free_port():
    # extracts a free port in the range 1920:2000 and raises a RuntimeError if
    # there are no free ports. NB: the port is free when extracted, but another
    # process may take it immediately, so this function is not safe against
    # race conditions. Moreover, once a port is taken, it is taken forever and
    # never considered free again, even if it is. These restrictions as
    # acceptable for usage in the tests, but only in that case.
    while port_candidates:
        port = random.choice(port_candidates)
        port_candidates.remove(port)
        if not socket_ready(('127.0.0.1', port)):  # no server listening
            return port  # the port is free
    raise RuntimeError('No free ports in the range 1920:2000')


def zipfiles(fnames, archive, mode='w', log=lambda msg: None, cleanup=False):
    """
    Build a zip archive from the given file names.

    :param fnames: list of path names
    :param archive: path of the archive or BytesIO object
    """
    prefix = len(os.path.commonprefix([os.path.dirname(f) for f in fnames]))
    with zipfile.ZipFile(
            archive, mode, zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for f in fnames:
            log('Archiving %s' % f)
            z.write(f, f[prefix:])
            if cleanup:  # remove the zipped file
                os.remove(f)
    return archive


def detach_process():
    """
    Detach the current process from the controlling terminal by using a
    double fork. Can be used only on platforms with fork (no Windows).
    """
    # see https://pagure.io/python-daemon/blob/master/f/daemon/daemon.py and
    # https://stackoverflow.com/questions/45911705/why-use-os-setsid-in-python
    def fork_then_exit_parent():
        pid = os.fork()
        if pid:  # in parent
            os._exit(0)
    fork_then_exit_parent()
    os.setsid()
    fork_then_exit_parent()


def shortlist(lst):
    """
    >>> shortlist([1, 2, 3, 4, 5, 6, 7, 8])
    '[1, 2, 3, ..., 6, 7, 8]'
    """
    if len(lst) <= 7:
        return str(lst)
    return str(lst[:3] + ['...'] + lst[-3:]).replace("'", "")


def println(msg):
    """
    Convenience function to print messages on a single line in the terminal
    """
    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stdout.write('\x08' * len(msg))
    sys.stdout.flush()


def debug(line):
    """
    Append a debug line to the file /tmp/debug.txt
    """
    tmp = tempfile.gettempdir()
    with open(os.path.join(tmp, 'debug.txt'), 'a', encoding='utf8') as f:
        f.write(line + '\n')


builtins.debug = debug


def warn(msg, *args):
    """
    Print a warning on stderr
    """
    if not args:
        sys.stderr.write('WARNING: ' + msg)
    else:
        sys.stderr.write('WARNING: ' + msg % args)


def getsizeof(o, ids=None):
    '''
    Find the memory footprint of a Python object recursively, see
    https://code.tutsplus.com/tutorials/understand-how-much-memory-your-python-objects-use--cms-25609
    :param o: the object
    :returns: the size in bytes
    '''
    ids = ids or set()
    if id(o) in ids:
        return 0

    if hasattr(o, 'nbytes'):
        return o.nbytes
    elif hasattr(o, 'array'):
        return o.array.nbytes

    nbytes = sys.getsizeof(o)
    ids.add(id(o))

    if isinstance(o, Mapping):
        return nbytes + sum(getsizeof(k, ids) + getsizeof(v, ids)
                            for k, v in o.items())
    elif isinstance(o, Container):
        return nbytes + sum(getsizeof(x, ids) for x in o)

    return nbytes


def get_duplicates(array, *fields):
    """
    :returns: a dictionary {key: num_dupl} for duplicate records
    """
    uniq = numpy.unique(array[list(fields)])
    if len(uniq) == len(array):  # no duplicates
        return {}
    return {k: len(g) for k, g in group_array(array, *fields).items()
            if len(g) > 1}


def add_columns(a, b, on, cols=None):
    """
    >>> a_dt = [('aid', numpy.int64), ('eid', numpy.int64), ('loss', float)]
    >>> b_dt = [('ordinal', numpy.int64), ('custom_site_id', numpy.int64)]
    >>> a = numpy.array([(1, 0, 2.4), (2, 0, 2.2),
    ...                  (1, 1, 2.1), (2, 1, 2.3)], a_dt)
    >>> b = numpy.array([(0, 20126), (1, 20127), (2, 20128)], b_dt)
    >>> add_columns(a, b, 'aid', ['custom_site_id'])
    array([(1, 0, 2.4, 20127), (2, 0, 2.2, 20128), (1, 1, 2.1, 20127),
           (2, 1, 2.3, 20128)],
          dtype=[('aid', '<i8'), ('eid', '<i8'), ('loss', '<f8'), ('custom_site_id', '<i8')])
    """
    if cols is None:
        cols = b.dtype.names
    dtlist = []
    for name in a.dtype.names:
        dtlist.append((name, a.dtype[name]))
    for name in cols:
        dtlist.append((name, b.dtype[name]))
    new = numpy.zeros(len(a), dtlist)
    for name in a.dtype.names:
        new[name] = a[name]
    idxs = a[on]
    for name in cols:
        new[name] = b[name][idxs]
    return new


def categorize(values, nchars=2):
    """
    Takes an array with duplicate values and categorize it, i.e. replace
    the values with codes of length nchars in BASE183. With nchars=2 33856
    unique values can be encoded, if there are more nchars must be increased
    otherwise a ValueError will be raised.

    :param values: an array of V non-unique values
    :param nchars: number of characters in BASE183 for each code
    :returns: an array of V non-unique codes

    >>> categorize([1,2,2,3,4,1,1,2]) # 8 values, 4 unique ones
    array([b'AA', b'AB', b'AB', b'AC', b'AD', b'AA', b'AA', b'AB'],
          dtype='|S2')
    """
    uvalues = numpy.unique(values)
    mvalues = 184 ** nchars  # maximum number of unique values
    if len(uvalues) > mvalues:
        raise ValueError(
            f'There are too many unique values ({len(uvalues)} > {mvalues})')
    prod = itertools.product(*[BASE183] * nchars)
    dic = {uvalue: ''.join(chars) for uvalue, chars in zip(uvalues, prod)}
    return numpy.array([dic[v] for v in values], (numpy.bytes_, nchars))


def get_nbytes_msg(sizedict, size=8):
    """
    :param sizedict: mapping name -> num_dimensions
    :returns: (size of the array in bytes, descriptive message)

    >>> get_nbytes_msg(dict(nsites=2, nbins=5))
    (80, '(nsites=2) * (nbins=5) * 8 bytes = 80 B')
    """
    nbytes = numpy.prod(list(sizedict.values())) * size
    prod = ' * '.join('({}={:_d})'.format(k, int(v))
                      for k, v in sizedict.items())
    return nbytes, '%s * %d bytes = %s' % (prod, size, humansize(nbytes))


def gen_subclasses(cls):
    """
    :returns: the subclasses of `cls`, ordered by name
    """
    for subclass in sorted(cls.__subclasses__(), key=lambda cls: cls.__name__):
        yield subclass
        yield from gen_subclasses(subclass)


def pprod(p, axis=None):
    """
    Probability product 1 - prod(1-p)
    """
    return 1. - numpy.prod(1. - p, axis)


def agg_probs(*probs):
    """
    Aggregate probabilities with the usual formula 1 - (1 - P1) ... (1 - Pn)
    """
    acc = 1. - probs[0]
    for prob in probs[1:]:
        acc *= 1. - prob
    return 1. - acc


class Param:
    """
    Container class for a set of parameters with defaults

    >>> p = Param(a=1, b=2)
    >>> p.a = 3
    >>> p.a, p.b
    (3, 2)
    >>> p.c = 4
    Traceback (most recent call last):
      ...
    AttributeError: Unknown parameter c
    """
    def __init__(self, **defaults):
        for k, v in defaults.items():
            self.__dict__[k] = v

    def __setattr__(self, name, value):
        if name in self.__dict__:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError('Unknown parameter %s' % name)


class RecordBuilder(object):
    """
    Builder for numpy records or arrays.

    >>> rb = RecordBuilder(a=numpy.int64(0), b=1., c="2")
    >>> rb.dtype
    dtype([('a', '<i8'), ('b', '<f8'), ('c', 'S1')])
    >>> rb()
    (0, 1., b'2')
    """
    def __init__(self, **defaults):
        self.names = []
        self.values = []
        dtypes = []
        for name, value in defaults.items():
            self.names.append(name)
            self.values.append(value)
            if isinstance(value, (str, bytes)):
                tp = (numpy.bytes_, len(value) or 1)
            elif isinstance(value, numpy.ndarray):
                tp = (value.dtype, len(value))
            else:
                tp = type(value)
            dtypes.append(tp)
        self.dtype = numpy.dtype([(n, d) for n, d in zip(self.names, dtypes)])

    def zeros(self, shape):
        return numpy.zeros(shape, self.dtype).view(numpy.recarray)

    def dictarray(self, shape):
        return {n: numpy.ones(shape, self.dtype[n]) for n in self.names}

    def __call__(self, *args, **kw):
        rec = numpy.zeros(1, self.dtype)[0]
        for i, name in enumerate(self.names):
            if name in kw:
                rec[name] = kw[name]  # takes precedence
                continue
            try:
                rec[name] = args[i]
            except IndexError:
                rec[name] = self.values[i]
        return rec


def rmsdiff(a, b):
    """
    :param a: an array of shape (N, ...)
    :param b: an array with the same shape of a
    :returns: an array of shape (N,) with the root mean squares of a-b
    """
    assert a.shape == b.shape
    axis = tuple(range(1, len(a.shape)))
    rms = numpy.sqrt(((a - b)**2).mean(axis=axis))
    return rms


def sqrscale(x_min, x_max, n):
    """
    :param x_min: minumum value
    :param x_max: maximum value
    :param n: number of steps
    :returns: an array of n values from x_min to x_max in a quadratic scale
    """
    if not (isinstance(n, int) and n > 0):
        raise ValueError('n must be a positive integer, got %s' % n)
    if x_min < 0:
        raise ValueError('x_min must be positive, got %s' % x_min)
    if x_max <= x_min:
        raise ValueError('x_max (%s) must be bigger than x_min (%s)' %
                         (x_max, x_min))
    delta = numpy.sqrt(x_max - x_min) / (n - 1)
    return x_min + (delta * numpy.arange(n))**2


# NB: this is present in contextlib in Python 3.11, but
# we still support Python 3.9, so it cannot be removed yet
@contextmanager
def chdir(path):
    """
    Context manager to temporarily change the CWD
    """
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


def smart_concat(arrays):
    """
    Concatenated structured arrays by considering only the common fields
    """
    if len(arrays) == 0:
        return ()
    common = set(arrays[0].dtype.names)
    for array in arrays[1:]:
        common &= set(array.dtype.names)
    assert common, 'There are no common field names'
    common = sorted(common)
    dt = arrays[0][common].dtype
    return numpy.concatenate([arr[common] for arr in arrays], dtype=dt)


def around(vec, value, delta):
    """
    :param vec: a numpy vector or pandas column
    :param value: a float value
    :param delta: a positive float
    :returns: array of booleans for the range [value-delta, value+delta]
    """
    return (vec <= value + delta) & (vec >= value - delta)


def sum_records(array):
    """
    :returns: the sums of the composite array
    """
    res = numpy.zeros(1, array.dtype)
    for name in array.dtype.names:
        res[name] = array[name].sum(axis=0)
    return res


def compose_arrays(**kwarrays):
    """
    Compose multiple 1D and 2D arrays into a single composite array.
    For instance

    >>> mag = numpy.array([5.5, 5.6])
    >>> mea = numpy.array([[-4.5, -4.6], [-4.45, -4.55]])
    >>> compose_arrays(mag=mag, mea=mea)
    array([(5.5, -4.5 , -4.6 ), (5.6, -4.45, -4.55)],
          dtype=[('mag', '<f8'), ('mea0', '<f8'), ('mea1', '<f8')])
    """
    dic = {}
    dtlist = []
    nrows = set()
    for key, array in kwarrays.items():
        shape = array.shape
        nrows.add(shape[0])
        if len(shape) >= 2:
            for k in range(shape[1]):
                dic[f'{key}{k}'] = array[:, k]
                dtlist.append((f'{key}{k}', (array.dtype, shape[2:])))
        else:
            dic[key] = array
            dtlist.append((key, array.dtype))
    [R] = nrows  # all arrays must have the same number of rows
    array = numpy.empty(R, dtlist)
    for key, _ in dtlist:
        array[key] = dic[key]
    return array


# #################### COMPRESSION/DECOMPRESSION ##################### #

# Compressing the task outputs makes everything slower, so you should NOT
# do that, except in one case. The case if when you have a lot of workers
# (say 320) sending a lot of data (say 320 GB) to a master node which is
# not able to keep up. Then the zmq queue fills all of the avalaible RAM
# until the master node blows up. With compression you can reduce the queue
# size a lot (say one order of magnitude).
# Therefore by losing a bit of speed (say 3%) you can convert a failing
# calculation into a successful one.

def compress(obj):
    """
    gzip a Python object
    """
    # level=1: compress the least, but fast, good choice for us
    return zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL), level=1)


def decompress(cbytes):
    """
    gunzip compressed bytes into a Python object
    """
    return pickle.loads(zlib.decompress(cbytes))

# ########################### dumpa/loada ############################## #

# the functions below as useful to avoid data transfer, to be used as

# smap.share(arr=dumpa(big_object))

# and then in the workers

# with monitor.shared['arr'] as arr:
#      big_object = loada(arr)


def dumpa(obj):
    """
    Dump a Python object as an array of uint8:

    >>> dumpa(23)
    array([128,   5,  75,  23,  46], dtype=uint8)
    """
    buf = memoryview(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL))
    return numpy.ndarray(len(buf), dtype=numpy.uint8, buffer=buf)


def loada(arr):
    """
    Convert an array of uint8 into a Python object:

    >>> loada(numpy.array([128, 5, 75, 23, 46], numpy.uint8))
    23
    """
    return pickle.loads(bytes(arr))


class Deduplicate(Sequence):
    """
    Deduplicate lists containing duplicated objects
    """
    def __init__(self, objects, check_one=False):
        pickles = [pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
                   for obj in objects]
        uni, self.inv = numpy.unique(pickles, return_inverse=True)
        self.uni = [pickle.loads(pik) for pik in uni]
        if check_one:
            assert len(self.uni) == 1, self.uni

    def __getitem__(self, i):
        return self.uni[self.inv[i]]

    def __repr__(self):
        name = self[0].__class__.__name__
        return '<Deduplicated %s %d/%d>' % (name, len(self.uni), len(self.inv))

    def __len__(self):
        return len(self.inv)
