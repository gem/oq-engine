# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2025 GEM Foundation

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
import math
import builtins
import numpy


def encode(val):
    """
    Encode a string assuming the encoding is UTF-8.

    :param: a unicode or bytes object
    :returns: bytes
    """
    if isinstance(val, (list, tuple, numpy.ndarray)):
        # encode a sequence of strings
        return [encode(v) for v in val]
    elif isinstance(val, str):
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
    if isinstance(val, (list, tuple, numpy.ndarray)):
        return [decode(v) for v in val]
    elif hasattr(val, 'decode'):
        # assume it is an encoded bytes object
        return val.decode('utf-8')
    else:
        return str(val)


def zip(arg, *args):
    for a in args:
        assert len(a) == len(arg), (len(a), len(arg))
    return builtins.zip(arg, *args)


# NB: using numpy.round would be advisable, but it would break
# plenty of tests, including the AELO tests, so it is a no go
def round(x, d=0):
    """
    Python2-compatible round function
    """
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


# the following is used in the SMT module of the OQ-MBTK
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
