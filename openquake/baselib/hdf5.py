# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2015-2021 GEM Foundation

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
import tempfile
import warnings
import importlib
import itertools
from urllib.parse import quote_plus, unquote_plus
import collections
import json
import toml
import pandas
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

FLOAT = (float, numpy.float32, numpy.float64)
INT = (int, numpy.int32, numpy.uint32, numpy.int64, numpy.uint64)


def maybe_encode(value):
    """
    If value is a sequence of strings, encode it
    """
    if isinstance(value, bytes):
        return numpy.void(value)
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
    def __init__(self, name, mode='r', driver=None, libver='latest',
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
        elif isinstance(obj, numpy.ndarray) and obj.shape:
            d = self.create_dataset(path, obj.shape, obj.dtype, fillvalue=None)
            d[:] = obj
        elif (isinstance(obj, numpy.ndarray) and
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


def dumps(dic):
    """
    Dump in json
    """
    new = {}
    for k, v in dic.items():
        if k.startswith('_') or v is None:
            pass
        elif isinstance(v, (list, tuple)) and v:
            if isinstance(v[0], INT):
                new[k] = [int(x) for x in v]
            elif isinstance(v[0], FLOAT):
                new[k] = [float(x) for x in v]
            else:
                new[k] = json.dumps(v)
        elif isinstance(v, FLOAT):
            new[k] = float(v)
        elif isinstance(v, INT):
            new[k] = int(v)
        elif hasattr(v, 'tolist'):
            lst = v.tolist()
            if lst and isinstance(lst[0], bytes):
                new[k] = json.dumps(decode_array(v))
            else:
                new[k] = json.dumps(lst)
        elif hasattr(v, '__dict__'):
            new[k] = {cls2dotname(v.__class__): dumps(vars(v))}
        elif isinstance(v, dict):
            new[k] = dumps(v)
        elif isinstance(v, str):
            new[k] = '"%s"' % v
        else:
            new[k] = v
    return "{%s}" % ','.join('\n"%s": %s' % it for it in new.items())


def set_shape_descr(hdf5file, dsetname, kw):
    """
    Set shape attributes on a dataset (and possibly other attributes)
    """
    dset = hdf5file[dsetname]
    S = len(dset.shape)
    if len(kw) < S:
        raise ValueError('The dataset %s has %d dimensions but you passed %d'
                         ' axis' % (dsetname, S, len(kw)))
    keys = list(kw)
    fields, extra = keys[:S], keys[S:]
    dic = dict(shape_descr=fields)
    for f in fields:
        dic[f] = kw[f]
    dset.attrs['json'] = dumps(dic)
    for e in extra:
        dset.attrs[e] = kw[e]


def get_shape_descr(json_string):
    """
    :param json_string:
        JSON string containing the shape_descr
    :returns:
        a dictionary field -> values extracted from the shape_descr
    """
    dic = json.loads(json_string)
    for field in dic['shape_descr']:
        val = dic[field]
        if isinstance(val, INT):
            dic[field] = range(val)
    return dic


class ArrayWrapper(object):
    """
    A pickleable and serializable wrapper over an array, HDF5 dataset or group

    :param array: an array (or the empty tuple)
    :param attrs: metadata of the array (or dictionary of arrays)
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
            if 'json' in attrs:
                attrs.update(get_shape_descr(attrs.pop('json')))
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

    def __setitem__(self, idx, val):
        if isinstance(idx, str) and idx in self.__dict__:
            setattr(self, idx, val)
        else:
            self.array[idx] = val

    def __toh5__(self):
        arr = getattr(self, 'array', ())
        if len(arr):
            return arr, self.to_dict()
        return self.to_dict(), {}

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
        dic = {}
        for k, v in vars(self).items():
            if k.startswith('_'):
                continue
            elif k == 'json':
                dic.update(json.loads(bytes(v)))
            else:
                dic[k] = v
        return toml.dumps(dic)

    def to_dframe(self):
        """
        Convert an ArrayWrapper with shape (D1, ..., DN) and attributes
        T1, ..., TN which are list of tags of lenghts D1, ... DN into
        a DataFrame with rows (tag1, ... tagN, extra1, ... extraM) of maximum
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
        >>> pprint(aw.to_dframe())
          taxonomy occupancy   value
        0       RC       RES  2000.0
        1       RC       IND  5000.0
        2     WOOD       RES   500.0
        """
        if hasattr(self, 'array'):
            names = self.array.dtype.names
            if names:  # wrapper over a structured array
                return pandas.DataFrame({n: self[n] for n in names})

        if hasattr(self, 'json'):
            vars(self).update(json.loads(self.json))
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
            if isinstance(val, numpy.ndarray):
                if val.sum():
                    out.append(values + tuple(val))
            elif val:  # is a scalar
                out.append(values + (val,))
        return pandas.DataFrame(out, columns=fields)

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


def parse_comment(comment):
    """
    Parse a comment of the form
    `investigation_time=50.0, imt="PGA", ...`
    and returns it as pairs of strings:

    >>> parse_comment('''path=['b1'], time=50.0, imt="PGA"''')
    [('path', ['b1']), ('time', 50.0), ('imt', 'PGA')]
    """
    if comment[0] == '"' and comment[-1] == '"':
        comment = comment[1:-1]
    try:
        dic = toml.loads('{%s}' % comment.replace('""', '"'))
    except toml.TomlDecodeError as err:
        raise ValueError('%s in %s' % (err, comment))
    return list(dic.items())


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
            if None in dtypedict:
                dt = dtypedict[None]
            else:
                raise KeyError('Missing dtype for field %r' % name)
        lst.append((name, vstr if dt is str else dt))
    return numpy.dtype(lst)


def _read_csv(fileobj, compositedt):
    itemsize = [0] * len(compositedt)
    dt = []
    for i, name in enumerate(compositedt.names):
        dt.append(compositedt[name])
        if compositedt[name].kind == 'S':  # limit of the length of byte-fields
            itemsize[i] = compositedt[name].itemsize
    rows = []
    for lineno, row in enumerate(csv.reader(fileobj), 3):
        cols = []
        for i, col in enumerate(row):
            if itemsize[i] and len(col) > itemsize[i]:
                raise ValueError(
                    'line %d: %s=%r has length %d > %d' %
                    (lineno, compositedt.names[i], col, len(col), itemsize[i]))
            if dt[i].kind == 'b':  # boolean
                cols.append(int(col))
            else:
                cols.append(col)
        rows.append(tuple(cols))
    return numpy.array(rows, compositedt)


# NB: it would be nice to use numpy.loadtxt(
#  f, build_dt(dtypedict, header), delimiter=sep, ndmin=1, comments=None)
# however numpy does not support quoting, and "foo,bar" would be split :-(
def read_csv(fname, dtypedict={None: float}, renamedict={}, sep=',',
             index=None):
    """
    :param fname: a CSV file with an header and float fields
    :param dtypedict: a dictionary fieldname -> dtype, None -> default
    :param renamedict: aliases for the fields to rename
    :param sep: separator (default comma)
    :param index: if not None, returns a pandas DataFrame
    :returns: an ArrayWrapper, unless there is an index
    """
    attrs = {}
    with open(fname, encoding='utf-8-sig') as f:
        while True:
            first = next(f)
            if first.startswith('#'):
                attrs = dict(parse_comment(first.strip('#,\n ')))
                continue
            break
        header = first.strip().split(sep)
        if isinstance(dtypedict, dict):
            dt = build_dt(dtypedict, header)
        else:
            # in test_recompute dt is already a composite dtype
            dt = dtypedict
        try:
            arr = _read_csv(f, dt)
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
    if index:
        df = pandas.DataFrame.from_records(arr, index)
        vars(df).update(attrs)
        return df
    return ArrayWrapper(arr, attrs)


def _fix_array(arr, key):
    """
    :param arr: array or array-like object
    :param key: string associated to the error (appear in the error message)

    If `arr` is a numpy array with dtype object containing strings, convert
    it into a numpy array containing bytes, unless it has more than 2
    dimensions or contains non-strings (these are errors). Return `arr`
    unchanged in the other cases.
    """
    if arr is None:
        return ()
    if not isinstance(arr, numpy.ndarray):
        return arr
    if arr.dtype.names:
        # for extract_assets d[0] is the pair
        # ('id', ('|S50', {'h5py_encoding': 'ascii'}))
        # this is a horrible workaround for the h5py 2.10.0 issue
        # https://github.com/numpy/numpy/issues/14142
        dtlist = []
        for i, n in enumerate(arr.dtype.names):
            if isinstance(arr.dtype.descr[i][1], tuple):
                dtlist.append((n, str(arr.dtype[n])))
            else:
                dtlist.append((n, arr.dtype[n]))
        arr.dtype = dtlist
    return arr


def save_npz(obj, path):
    """
    :param obj: object to serialize
    :param path: an .npz pathname
    """
    a = {}
    for key, val in vars(obj).items():
        if key.startswith('_'):
            continue
        elif isinstance(val, str):
            # without this oq extract would fail
            a[key] = val.encode('utf-8')
        else:
            a[key] = _fix_array(val, key)
    # turn into an error https://github.com/numpy/numpy/issues/14142
    with warnings.catch_warnings():
        warnings.filterwarnings("error", category=UserWarning)
        numpy.savez_compressed(path, **a)

# #################### obj <-> json ##################### #


def obj_to_json(obj):
    """
    :param obj: a Python object with a .__dict__
    :returns: a JSON string
    """
    return dumps({cls2dotname(obj.__class__): vars(obj)})


def json_to_obj(js):
    """
    :param js: a JSON string with the form {"cls": {"arg1": ...}}
    :returns: an instance cls(arg1, ...)
    """
    [(dotname, attrs)] = json.loads(js).items()
    cls = dotname2cls(dotname)
    obj = cls.__new__(cls)
    vars(obj).update(attrs)
    return obj
