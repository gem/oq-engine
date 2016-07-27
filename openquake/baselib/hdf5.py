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
import importlib
try:  # with Python 3
    from urllib.parse import quote_plus, unquote_plus
except ImportError:  # with Python 2
    from urllib import quote_plus, unquote_plus
import collections
import numpy
import h5py
from openquake.baselib.python3compat import pickle, decode

vbytes = h5py.special_dtype(vlen=bytes)
vstr = h5py.special_dtype(vlen=str)


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


def extend(dset, array):
    """
    Extend an extensible dataset with an array of a compatible dtype
    """
    length = len(dset)
    newlength = length + len(array)
    dset.resize((newlength,))
    dset[length:newlength] = array


class LiteralAttrs(object):
    """
    A class to serialize a set of parameters in HDF5 format. The goal is to
    store simple parameters as an HDF5 table in a readable way. Each
    parameter can be retrieved as an attribute, given its name. The
    implementation treats specially dictionary attributes, by storing
    them as `attrname.keyname` strings, see the example below:

    >>> class Ser(LiteralAttrs):
    ...     def __init__(self, a, b):
    ...         self.a = a
    ...         self.b = b
    >>> ser = Ser(1, dict(x='xxx', y='yyy'))
    >>> arr, attrs = ser.__toh5__()
    >>> for k, v in arr:
    ...     print('%s=%s' % (k, v))
    a=1
    b.x='xxx'
    b.y='yyy'
    >>> s = object.__new__(Ser)
    >>> s.__fromh5__(arr, attrs)
    >>> s.a
    1
    >>> s.b['x']
    'xxx'

    The implementation is not recursive, i.e. there will be at most
    one dot in the serialized names (in the example here `a`, `b.x`, `b.y`).

    """
    def __toh5__(self):
        info_dt = numpy.dtype([('par_name', vbytes), ('par_value', vbytes)])
        attrnames = sorted(a for a in vars(self) if not a.startswith('_'))
        lst = []
        for attr in attrnames:
            value = getattr(self, attr)
            if isinstance(value, dict):
                for k, v in sorted(value.items()):
                    key = '%s.%s' % (attr, k)
                    lst.append((key, repr(v)))
            else:
                lst.append((attr, repr(value)))
        return numpy.array(lst, info_dt), {}

    def __fromh5__(self, array, attrs):
        dd = collections.defaultdict(dict)
        for (name_, literal_) in array:
            name = decode(name_)
            literal = decode(literal_)
            if '.' in name:
                k1, k2 = name.split('.', 1)
                dd[k1][k2] = ast.literal_eval(literal)
            else:
                dd[name] = ast.literal_eval(literal)
        vars(self).update(dd)

    def __repr__(self):
        names = sorted(n for n in vars(self) if not n.startswith('_'))
        nameval = ', '.join('%s=%r' % (n, getattr(self, n)) for n in names)
        return '<%s %s>' % (self.__class__.__name__, nameval)


# the implementation below stores a dataset per each object; it would be nicer
# to store an array, however I am not able to do that with the current version
# of h5py; the best I could do is to store an array of variable length ASCII
# strings, but then I would have to use the ASCII format of pickle, which is
# the least efficient. The current solution looks like a decent compromise.
class PickleableSequence(collections.Sequence):
    """
    An immutable sequence of pickleable objects that can be serialized
    in HDF5 format. Here is an example, using the LiteralAttrs class defined
    in this module, but any pickleable class would do:

    >>> seq = PickleableSequence([LiteralAttrs(), LiteralAttrs()])
    >>> with File('/tmp/x.h5', 'w') as f:
    ...     f['data'] = seq
    >>> with File('/tmp/x.h5') as f:
    ...     f['data']
    (<LiteralAttrs >, <LiteralAttrs >)
    """
    def __init__(self, objects):
        self._objects = tuple(objects)

    def __getitem__(self, i):
        return self._objects[i]

    def __len__(self):
        return len(self._objects)

    def __repr__(self):
        return repr(self._objects)

    def __toh5__(self):
        dic = {}
        nbytes = 0
        for i, obj in enumerate(self._objects):
            pik = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
            dic['%06d' % i] = numpy.array(pik)
            nbytes += len(pik)
        return dic, dict(nbytes=nbytes)

    def __fromh5__(self, dic, attrs):
        self._objects = tuple(pickle.loads(dic[k].value) for k in sorted(dic))
        vars(self).update(attrs)


class File(h5py.File):
    """
    Subclass of :class:`h5py.File` able to store and retrieve objects
    conforming to the HDF5 protocol used by the OpenQuake software.
    It works recursively also for dictionaries of the form name->obj.

    >>> f = File('/tmp/x.h5', 'w')
    >>> f['dic'] = dict(a=dict(x=1, y=2), b=3)
    >>> dic = f['dic']
    >>> dic['a']['x'].value
    1
    >>> dic['b'].value
    3
    >>> f.close()
    """
    def __setitem__(self, path, obj):
        cls = obj.__class__
        if hasattr(obj, '__toh5__'):
            obj, attrs = obj.__toh5__()
            pyclass = '%s.%s' % (cls.__module__, cls.__name__)
        else:
            pyclass = ''
        if isinstance(obj, dict):
            for k, v in sorted(obj.items()):
                key = '%s/%s' % (path, quote_plus(k))
                self[key] = v
        else:
            super(File, self).__setitem__(path, obj)
        a = super(File, self).__getitem__(path).attrs
        if pyclass:
            a['__pyclass__'] = pyclass
            for k, v in sorted(attrs.items()):
                a[k] = v

    def __getitem__(self, path):
        h5obj = super(File, self).__getitem__(path)
        h5attrs = h5obj.attrs
        if '__pyclass__' in h5attrs:
            # NB: the `decode` below is needed for Python 3
            modname, clsname = decode(h5attrs['__pyclass__']).rsplit('.', 1)
            cls = getattr(importlib.import_module(modname), clsname)
            obj = cls.__new__(cls)
            if not hasattr(h5obj, 'shape'):  # is group
                h5obj = {unquote_plus(k): self['%s/%s' % (path, k)]
                         for k, v in h5obj.items()}
            obj.__fromh5__(h5obj, h5attrs)
            return obj
        else:
            return h5obj


def array_of_vstr(lst):
    """
    :param lst: a list of strings or bytes
    :returns: an array of variable length ASCII strings
    """
    ls = []
    for el in lst:
        try:
            ls.append(el.encode('utf-8'))
        except AttributeError:
            ls.append(el)
    return numpy.array(ls, vstr)
