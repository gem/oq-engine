# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2019 GEM Foundation

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

import os
import ast
import csv
import inspect
import logging
import tempfile
import importlib
import itertools
from numbers import Number
from urllib.parse import quote_plus, unquote_plus
import collections
import toml
import numpy
import h5py
from openquake.baselib import InvalidFile
from openquake.baselib.python3compat import encode, decode

vbytes = h5py.special_dtype(vlen=bytes)
vstr = h5py.special_dtype(vlen=str)
vuint8 = h5py.special_dtype(vlen=numpy.uint8)
vuint16 = h5py.special_dtype(vlen=numpy.uint16)
vuint32 = h5py.special_dtype(vlen=numpy.uint32)
vfloat32 = h5py.special_dtype(vlen=numpy.float32)
vfloat64 = h5py.special_dtype(vlen=numpy.float64)


def maybe_encode(value):
    """
    If value is a sequence of strings, encode it
    """
    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], str):
            return encode(value)
    return value


def create(hdf5, name, dtype, shape=(None,), compression=None,
           fillvalue=0, attrs=None):
    """
    :param hdf5: a h5py.File object
    :param name: an hdf5 key string
    :param dtype: dtype of the dataset (usually composite)
    :param shape: shape of the dataset (can be extendable)
    :param compression: None or 'gzip' are recommended
    :param attrs: dictionary of attributes of the dataset
    :returns: a HDF5 dataset
    """
    if shape[0] is None:  # extendable dataset
        dset = hdf5.create_dataset(
            name, (0,) + shape[1:], dtype, chunks=True, maxshape=shape,
            compression=compression)
    else:  # fixed-shape dataset
        dset = hdf5.create_dataset(name, shape, dtype, fillvalue=fillvalue,
                                   compression=compression)
    if attrs:
        for k, v in attrs.items():
            dset.attrs[k] = maybe_encode(v)
    return dset


def preshape(obj):
    """
    :returns: the shape of obj, except the last dimension
    """
    if hasattr(obj, 'shape'):  # array
        return obj.shape[:-1]
    return ()


def extend(dset, array, **attrs):
    """
    Extend an extensible dataset with an array of a compatible dtype.

    :param dset: an h5py dataset
    :param array: an array of length L
    :returns: the total length of the dataset (i.e. initial length + L)
    """
    length = len(dset)
    if len(array) == 0:
        return length
    newlength = length + len(array)
    if array.dtype.name == 'object':  # vlen array
        shape = (newlength,) + preshape(array[0])
    else:
        shape = (newlength,) + array.shape[1:]
    dset.resize(shape)
    dset[length:newlength] = array
    for key, val in attrs.items():
        dset.attrs[key] = val
    return newlength


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


def cls2dotname(cls):
    """
    The full Python name (i.e. `pkg.subpkg.mod.cls`) of a class
    """
    return '%s.%s' % (cls.__module__, cls.__name__)


def dotname2cls(dotname):
    """
    The class associated to the given dotname (i.e. `pkg.subpkg.mod.cls`)
    """
    modname, clsname = dotname.rsplit('.', 1)
    return getattr(importlib.import_module(modname), clsname)


def get_nbytes(dset):
    """
    If the dataset has an attribute 'nbytes', return it. Otherwise get the size
    of the underlying array. Returns None if the dataset is actually a group.
    """
    if 'nbytes' in dset.attrs:
        # look if the dataset has an attribute nbytes
        return dset.attrs['nbytes']
    elif hasattr(dset, 'dtype'):
        # else extract nbytes from the underlying array
        return dset.size * numpy.zeros(1, dset.dtype).nbytes


class ByteCounter(object):
    """
    A visitor used to measure the dimensions of a HDF5 dataset or group.
    Use it as ByteCounter.get_nbytes(dset_or_group).
    """
    @classmethod
    def get_nbytes(cls, dset):
        nbytes = get_nbytes(dset)
        if nbytes is not None:
            return nbytes
        # else dip in the tree
        self = cls()
        dset.visititems(self)
        return self.nbytes

    def __init__(self, nbytes=0):
        self.nbytes = nbytes

    def __call__(self, name, dset_or_group):
        nbytes = get_nbytes(dset_or_group)
        if nbytes:
            self.nbytes += nbytes


class Group(collections.abc.Mapping):
    """
    A mock for a h5py group object
    """
    def __init__(self, items, attrs):
        self.dic = {quote_plus(k): v for k, v in items}
        self.attrs = attrs

    def __getitem__(self, key):
        return self.dic[key]

    def __setitem__(self, key, value):
        self.dic[key] = value

    def __iter__(self):
        yield from self.dic

    def __len__(self):
        return len(self.dic)


class File(h5py.File):
    """
    Subclass of :class:`h5py.File` able to store and retrieve objects
    conforming to the HDF5 protocol used by the OpenQuake software.
    It works recursively also for dictionaries of the form name->obj.

    >>> f = File('/tmp/x.h5', 'w')
    >>> f['dic'] = dict(a=dict(x=1, y=2), b=3)
    >>> dic = f['dic']
    >>> dic['a']['x'][()]
    1
    >>> dic['b'][()]
    3
    >>> f.close()
    """
    def __init__(self, name, mode=None, driver=None, libver='latest',
                 userblock_size=None, swmr=True, rdcc_nslots=None,
                 rdcc_nbytes=None, rdcc_w0=None, track_order=None,
                 **kwds):
        super().__init__(name, mode, driver, libver,
                         userblock_size, swmr, rdcc_nslots,
                         rdcc_nbytes, rdcc_w0, track_order, **kwds)

    @classmethod
    def temporary(cls):
        """
        Returns a temporary hdf5 file, open for writing.
        The temporary name is stored in the .path attribute.
        It is the user responsability to remove the file when closed.
        """
        fh, path = tempfile.mkstemp(suffix='.hdf5')
        os.close(fh)
        self = cls(path, 'w')
        self.path = path
        return self

    def save_vlen(self, key, data):  # used in SourceWriterTestCase
        """
        Save a sequence of variable-length arrays

        :param key: name of the dataset
        :param data: data to store as a list of arrays
        """
        shape = (None,) + data[0].shape[:-1]
        try:
            dset = self[key]
        except KeyError:
            vdt = h5py.special_dtype(vlen=data[0].dtype)
            dset = create(self, key, vdt, shape, fillvalue=None)
        length = len(dset)
        dset.resize((length + len(data),) + shape[1:])
        dset[length:length + len(data)] = data

    def save_attrs(self, path, attrs, **kw):
        items = list(attrs.items()) + list(kw.items())
        if items:
            a = super().__getitem__(path).attrs
            for k, v in sorted(items):
                try:
                    a[k] = maybe_encode(v)
                except Exception as exc:
                    raise TypeError(
                        'Could not store attribute %s=%s: %s' % (k, v, exc))

    def __setitem__(self, path, obj):
        cls = obj.__class__
        if hasattr(obj, '__toh5__'):
            obj, attrs = obj.__toh5__()
            pyclass = cls2dotname(cls)
        else:
            pyclass = ''
        if isinstance(obj, (dict, Group)) and obj:
            for k, v in obj.items():
                # NB: there was a line sorted(obj.items()) here
                # it was removed because it caused the absurd issue
                # https://github.com/gem/oq-engine/issues/4761
                # for an exposure with more than 65536 assets
                if isinstance(k, tuple):  # multikey
                    k = '-'.join(k)
                key = '%s/%s' % (path, quote_plus(k))
                self[key] = v
            if isinstance(obj, Group):
                self.save_attrs(
                    path, obj.attrs, __pyclass__=cls2dotname(Group))
        elif (isinstance(obj, numpy.ndarray) and obj.shape and
              len(obj) and isinstance(obj[0], str)):
            self.create_dataset(path, obj.shape, vstr)[:] = obj
        elif (isinstance(obj, numpy.ndarray) and not obj.shape and
              obj.dtype.name.startswith('bytes')):
            self._set(path, numpy.void(bytes(obj)))
        elif isinstance(obj, list) and len(obj) and isinstance(
                obj[0], numpy.ndarray):
            self.save_vlen(path, obj)
        elif isinstance(obj, bytes):
            self._set(path, numpy.void(obj))
        else:
            self._set(path, obj)
        if pyclass:
            self.flush()  # make sure it is fully saved
            self.save_attrs(path, attrs, __pyclass__=pyclass)

    def _set(self, path, obj):
        try:
            super().__setitem__(path, obj)
        except Exception as exc:
            raise exc.__class__('Could not set %s=%r' % (path, obj))

    def __getitem__(self, path):
        h5obj = super().__getitem__(path)
        h5attrs = h5obj.attrs
        if '__pyclass__' in h5attrs:
            cls = dotname2cls(h5attrs['__pyclass__'])
            obj = cls.__new__(cls)
            if hasattr(h5obj, 'items'):  # is group
                h5obj = {unquote_plus(k): self['%s/%s' % (path, k)]
                         for k, v in h5obj.items()}
            elif hasattr(h5obj, 'shape'):
                h5obj = h5obj[()]
            if hasattr(obj, '__fromh5__'):
                obj.__fromh5__(h5obj, h5attrs)
            else:  # Group object
                obj.dic = h5obj
                obj.attrs = h5attrs
            return obj
        else:
            return h5obj

    def __getstate__(self):
        # make the file pickleable
        return {'_id': 0}

    def getitem(self, name):
        """
        Return a dataset by using h5py.File.__getitem__
        """
        return h5py.File.__getitem__(self, name)


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


class ArrayWrapper(object):
    """
    A pickleable and serializable wrapper over an array, HDF5 dataset or group
    """
    @classmethod
    def from_(cls, obj, extra='value'):
        if isinstance(obj, cls):  # it is already an ArrayWrapper
            return obj
        elif inspect.isgenerator(obj):
            array, attrs = (), dict(obj)
        elif hasattr(obj, '__toh5__'):
            return obj
        elif hasattr(obj, 'attrs'):  # is a dataset
            array, attrs = obj[()], dict(obj.attrs)
            shape_descr = attrs.get('shape_descr', [])
            for descr in map(decode, shape_descr):
                attrs[descr] = list(attrs[descr])
        else:  # assume obj is an array
            array, attrs = obj, {}
        return cls(array, attrs, (extra,))

    def __init__(self, array, attrs, extra=('value',)):
        vars(self).update(attrs)
        self._extra = tuple(extra)
        if len(array):
            self.array = array

    def __iter__(self):
        if hasattr(self, 'array'):
            return iter(self.array)
        else:
            return iter(vars(self).items())

    def __len__(self):
        if hasattr(self, 'array'):
            return len(self.array)
        else:
            return len(vars(self))

    def __getitem__(self, idx):
        if isinstance(idx, str) and idx in self.__dict__:
            return getattr(self, idx)
        return self.array[idx]

    def __toh5__(self):
        arr = getattr(self, 'array', ())
        return arr, self.to_dict()

    def __fromh5__(self, array, attrs):
        self.__init__(array, attrs)

    def __repr__(self):
        if hasattr(self, 'shape_descr'):
            assert len(self.shape) == len(self.shape_descr), (
                self.shape_descr, self.shape)
            lst = ['%s=%d' % (descr, size)
                   for descr, size in zip(self.shape_descr, self.shape)]
            return '<%s(%s)>' % (self.__class__.__name__, ', '.join(lst))
        return '<%s%s>' % (self.__class__.__name__, self.shape)

    @property
    def dtype(self):
        """dtype of the underlying array"""
        return self.array.dtype

    @property
    def shape(self):
        """shape of the underlying array"""
        return self.array.shape if hasattr(self, 'array') else ()

    def toml(self):
        """
        :returns: a TOML string representation of the ArrayWrapper
        """
        if self.shape:
            return toml.dumps(self.array)
        dic = {k: v for k, v in vars(self).items()
               if not k.startswith('_')}
        return toml.dumps(dic)

    def save(self, path, **extra):
        """
        :param path: an .hdf5 pathname
        :param extra: extra attributes to be saved in the file
        """
        with File(path, 'w') as f:
            for key, val in vars(self).items():
                assert val is not None, key  # sanity check
                try:
                    f[key] = maybe_encode(val)
                except ValueError as err:
                    if 'Object header message is too large' in str(err):
                        logging.error(str(err))
            for k, v in extra.items():
                f.attrs[k] = maybe_encode(v)

    def sum_all(self, *tags):
        """
        Reduce the underlying array by summing on the given dimensions
        """
        tag2idx = {tag: i for i, tag in enumerate(self.shape_descr)}
        array = self.array.sum(axis=tuple(tag2idx[tag] for tag in tags))
        attrs = vars(self).copy()
        attrs['shape_descr'] = [tag for tag in self.shape_descr
                                if tag not in tags]
        return self.__class__(array, attrs)

    def to_table(self):
        """
        Convert an ArrayWrapper with shape (D1, ..., DN) and attributes
        T1, ..., TN which are list of tags of lenghts D1, ... DN into
        a table with rows (tag1, ... tagN, extra1, ... extraM) of maximum
        length D1 * ... * DN. Zero values are discarded.

        >>> from pprint import pprint
        >>> dic = dict(shape_descr=['taxonomy', 'occupancy'],
        ...            taxonomy=['RC', 'WOOD'],
        ...            occupancy=['RES', 'IND', 'COM'])
        >>> arr = numpy.zeros((2, 3))
        >>> arr[0, 0] = 2000
        >>> arr[0, 1] = 5000
        >>> arr[1, 0] = 500
        >>> aw = ArrayWrapper(arr, dic)
        >>> pprint(aw.to_table())
        [('taxonomy', 'occupancy', 'value'),
         ('RC', 'RES', 2000.0),
         ('RC', 'IND', 5000.0),
         ('WOOD', 'RES', 500.0)]
        >>> pprint(aw.sum_all('taxonomy').to_table())
        [('occupancy', 'value'), ('RES', 2500.0), ('IND', 5000.0)]
        >>> pprint(aw.sum_all('occupancy').to_table())
        [('taxonomy', 'value'), ('RC', 7000.0), ('WOOD', 500.0)]
        """
        shape = self.shape
        tup = len(self._extra) > 1
        if tup:
            if shape[-1] != len(self._extra):
                raise ValueError(
                    'There are %d extra-fields but %d dimensions in %s' %
                    (len(self._extra), shape[-1], self))
        shape_descr = tuple(decode(d) for d in self.shape_descr)
        fields = shape_descr + self._extra
        out = []
        tags = []
        idxs = []
        for i, tagname in enumerate(shape_descr):
            values = getattr(self, tagname)
            if len(values) != shape[i]:
                raise ValueError(
                    'The tag %s with %d values is inconsistent with %s'
                    % (tagname, len(values), self))
            tags.append(decode_array(values))
            idxs.append(range(len(values)))
        for idx, values in zip(itertools.product(*idxs),
                               itertools.product(*tags)):
            val = self.array[idx]
            if tup:
                if val.sum():
                    out.append(values + tuple(val))
            elif val:
                out.append(values + (val,))
        return [fields] + out

    def to_dict(self):
        """
        Convert the public attributes into a dictionary
        """
        return {k: v for k, v in vars(self).items()
                if k != 'array' and not k.startswith('_')}


def decode_array(values):
    """
    Decode the values which are bytestrings.
    """
    out = []
    for val in values:
        try:
            out.append(val.decode('utf8'))
        except AttributeError:
            out.append(val)
    return out


def extract(dset, *d_slices):
    """
    :param dset: a D-dimensional dataset or array
    :param d_slices: D slice objects (or similar)
    :returns: a reduced D-dimensional array

    >>> a = numpy.array([[1, 2, 3], [4, 5, 6]])  # shape (2, 3)
    >>> extract(a, slice(None), 1)
    array([[2],
           [5]])
    >>> extract(a, [0, 1], slice(1, 3))
    array([[2, 3],
           [5, 6]])
    """
    shp = list(dset.shape)
    if len(shp) != len(d_slices):
        raise ValueError('Array with %d dimensions but %d slices' %
                         (len(shp), len(d_slices)))
    sizes = []
    slices = []
    for i, slc in enumerate(d_slices):
        if slc == slice(None):
            size = shp[i]
            slices.append([slice(None)])
        elif hasattr(slc, 'start'):
            size = slc.stop - slc.start
            slices.append([slice(slc.start, slc.stop, 0)])
        elif isinstance(slc, list):
            size = len(slc)
            slices.append([slice(s, s + 1, j) for j, s in enumerate(slc)])
        elif isinstance(slc, Number):
            size = 1
            slices.append([slice(slc, slc + 1, 0)])
        else:
            size = shp[i]
            slices.append([slc])
        sizes.append(size)
    array = numpy.zeros(sizes, dset.dtype)
    for tup in itertools.product(*slices):
        aidx = tuple(s if s.step is None
                     else slice(s.step, s.step + s.stop - s.start)
                     for s in tup)
        sel = tuple(s if s.step is None else slice(s.start, s.stop)
                    for s in tup)
        array[aidx] = dset[sel]
    return array


def parse_comment(comment):
    """
    Parse a comment of the form
    `investigation_time=50.0, imt="PGA", ...`
    and returns it as pairs of strings:

    >>> parse_comment('''path=('b1',), time=50.0, imt="PGA"''')
    [('path', ('b1',)), ('time', 50.0), ('imt', 'PGA')]
    """
    names, vals = [], []
    if comment.startswith('"'):
        comment = comment[1:-1]
    pieces = comment.split('=')
    for i, piece in enumerate(pieces):
        if i == 0:  # first line
            names.append(piece.strip())
        elif i == len(pieces) - 1:  # last line
            vals.append(ast.literal_eval(piece))
        else:
            val, name = piece.rsplit(',', 1)
            vals.append(ast.literal_eval(val))
            names.append(name.strip())
    return list(zip(names, vals))


def build_dt(dtypedict, names):
    """
    Build a composite dtype for a list of names and dictionary
    name -> dtype with a None entry corresponding to the default dtype.
    """
    lst = []
    for name in names:
        try:
            dt = dtypedict[name]
        except KeyError:
            dt = dtypedict[None]
        lst.append((name, vstr if dt is str else dt))
    return numpy.dtype(lst)


# NB: it would be nice to use numpy.loadtxt(
#  f, build_dt(dtypedict, header), delimiter=sep, ndmin=1, comments=None)
# however numpy does not support quoting, and "foo,bar" would be split :-(
def read_csv(fname, dtypedict={None: float}, renamedict={}, sep=','):
    """
    :param fname: a CSV file with an header and float fields
    :param dtypedict: a dictionary fieldname -> dtype, None -> default
    :param renamedict: aliases for the fields to rename
    :param sep: separator (default comma)
    :return: a structured array of floats
    """
    attrs = {}
    with open(fname, encoding='utf-8-sig') as f:
        while True:
            first = next(f)
            if first.startswith('#'):
                attrs = dict(parse_comment(first.strip('#,\n')))
                continue
            break
        header = first.strip().split(sep)
        try:
            rows = [tuple(row) for row in csv.reader(f)]
            arr = numpy.array(rows, build_dt(dtypedict, header))
        except KeyError:
            raise KeyError('Missing None -> default in dtypedict')
        except Exception as exc:
            raise InvalidFile('%s: %s' % (fname, exc))
    if renamedict:
        newnames = []
        for name in arr.dtype.names:
            new = renamedict.get(name, name)
            newnames.append(new)
        arr.dtype.names = newnames
    return ArrayWrapper(arr, attrs)
