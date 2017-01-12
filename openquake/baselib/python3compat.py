# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2017 GEM Foundation

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

"""
Compatibility layer for Python 2 and 3. Mostly copied from six and future,
but reduced to the subset of utilities needed by GEM. This is done to
avoid an external dependency.
"""
from __future__ import print_function
import os
import sys
import math
import importlib
import subprocess

PY3 = sys.version_info[0] >= 3
PY2 = sys.version_info[0] == 2


def encode(val):
    """
    Encode a string assuming the encoding is UTF-8.

    :param: a unicode or bytes object
    :returns: bytes
    """
    if isinstance(val, unicode):
        return val.encode('utf-8')
    else:
        # assume it was an already encoded object
        return val


def decode(val):
    """
    Decode an object assuming the encoding is UTF-8.

    :param: a unicode or bytes object
    :returns: a unicode object
    """
    if isinstance(val, unicode):
        # it was an already decoded unicode object
        return val
    else:
        # assume it is an encoded bytes object
        return val.decode('utf-8')

if PY2:
    import cPickle as pickle
    import ConfigParser as configparser
    from itertools import izip

    range = xrange
    round = round
    unicode = unicode

    def zip(arg, *args):
        for a in args:
            assert len(a) == len(arg), (len(a), len(arg))
        return izip(arg, *args)

    # taken from six
    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")

    exec('''
def raise_(tp, value=None, tb=None):
    raise tp, value, tb
''')

else:  # Python 3
    import pickle
    import builtins
    import configparser
    exec_ = eval('exec')

    range = range
    unicode = str

    def zip(arg, *args):
        for a in args:
            assert len(a) == len(arg), (len(a), len(arg))
        return builtins.zip(arg, *args)

    def round(x, d=0):
        p = 10 ** d
        return float(math.floor((x * p) + math.copysign(0.5, x))) / p

    def raise_(tp, value=None, tb=None):
        """
        A function that matches the Python 2.x ``raise`` statement. This
        allows re-raising exceptions with the cls value and traceback on
        Python 2 and 3.
        """
        if value is not None and isinstance(tp, Exception):
            raise TypeError("instance exception may not have a separate value")
        if value is not None:
            exc = tp(value)
        else:
            exc = tp
        if exc.__traceback__ is not tb:
            raise exc.with_traceback(tb)
        raise exc


# copied from http://lucumr.pocoo.org/2013/5/21/porting-to-python-3-redux/
def with_metaclass(meta, *bases):
    """
    Returns an instance of meta inheriting from the given bases.
    To be used to replace the __metaclass__ syntax.
    """
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(mcl, name, this_bases, d):
            if this_bases is None:
                return type.__new__(mcl, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})


def check_syntax(pkg):
    """
    Recursively check all modules in the given package for compatibility with
    Python 3 syntax. No imports are performed.

    :param pkg: a Python package
    """
    ok, err = 0, 0
    for cwd, dirs, files in os.walk(pkg.__path__[0]):
        for f in files:
            if f.endswith('.py'):
                fname = os.path.join(cwd, f)
                errno = subprocess.call(['python3', '-m', 'py_compile', fname])
                if errno:
                    err += 1
                else:
                    ok += 1
    print('Checked %d ok, %d wrong modules' % (ok, err))


if __name__ == '__main__':
    check_syntax(importlib.import_module(sys.argv[1]))
