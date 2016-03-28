# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2016 GEM Foundation

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

import ast
import collections
import numpy


class Hdf5Dataset(object):
    """
    Little wrapper around an (extendable) HDF5 dataset. Extendable datasets
    are useful for logging information incrementally into an HDF5 file.
    """
    @classmethod
    def create(cls, hdf5, name, dtype, shape=None, compression=None):
        """
        :param hdf5: a h5py.File object
        :param name: an hdf5 key string
        :param dtype: dtype of the dataset (usually composite)
        :param shape: shape of the dataset (if None, the dataset is extendable)
        :param compression: None or 'gzip' are recommended
        """
        if shape is None:  # extendable dataset
            dset = hdf5.create_dataset(
                name, (0,), dtype, chunks=True, maxshape=(None,))
        else:  # fixed-shape dataset
            dset = hdf5.create_dataset(name, shape, dtype)
        return cls(dset)

    def __init__(self, dset):
        self.dset = dset
        self.file = dset.file
        self.name = dset.name
        self.dtype = dset.dtype
        self.attrs = dset.attrs
        self.length = len(dset)

    def extend(self, array):
        """
        Extend the dataset with the given array, which must have
        the expected dtype. This method will give an error if used
        with a fixed-shape dataset.
        """
        newlength = self.length + len(array)
        self.dset.resize((newlength,))
        self.dset[self.length:newlength] = array
        self.length = newlength

    def append(self, tup):
        """
        Append a compatible tuple of data to the underlying dataset
        """
        self.extend(numpy.array([tup], self.dtype))

KEYLEN = 50
VALUELEN = 200
info_dt = numpy.dtype([('key', (bytes, KEYLEN)), ('value', (bytes, VALUELEN))])


def check_len(key, value):
    """
    Check the lengths of `key` and `value` and raise a ValueError if they
    are too long. Otherwise, returns the pair (key, value).
    """
    if len(key) > KEYLEN:
        raise ValueError(
            'An instance of Serializable cannot have '
            'public attributes longer than %d chars; '
            '%r has %d chars' % (KEYLEN, key, len(key)))
    rep = repr(value)
    if len(rep) > VALUELEN:
        raise ValueError(
            'Attribute %r too long: %d > %d' % (key, len(rep), VALUELEN))
    return key, rep


class LiteralAttrs(object):
    """
    A mixin class to serialize attributes to HDF5. It treats specially
    dictionaries. It works at a single level of nesting.

    >>> class Ser(LiteralAttrs):
    ...     def __init__(self, a, b):
    ...         self.a = a
    ...         self.b = b
    >>> ser = Ser(1, dict(x='xxx', y='yyy'))
    >>> arr, attrs = ser.__toh5__()
    >>> print arr
    [('a', '1') ('b.x', "'xxx'") ('b.y', "'yyy'")]
    >>> s = object.__new__(Ser)
    >>> s.__fromh5__(arr, attrs)
    >>> s.a
    1
    >>> s.b['x']
    'xxx'
    """
    def __toh5__(self):
        attrnames = sorted(a for a in vars(self) if not a.startswith('_'))
        lst = []
        for attr in attrnames:
            value = getattr(self, attr)
            if isinstance(value, dict):
                for k, v in sorted(value.items()):
                    key = '%s.%s' % (attr, k)
                    lst.append(check_len(key, v))
            else:
                lst.append(check_len(attr, value))
        return numpy.array(lst, info_dt), {}

    def __fromh5__(self, array, attrs):
        dd = collections.defaultdict(dict)
        for (name, literal) in array:
            if '.' in name:
                k1, k2 = name.split('.')
                dd[k1][k2] = ast.literal_eval(literal)
            else:
                dd[name] = ast.literal_eval(literal)
        vars(self).update(dd)
