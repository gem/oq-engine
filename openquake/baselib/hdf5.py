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

import os
import sys
import ast
import operator
import tempfile
import importlib
import itertools
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
            dset.attrs[k] = v
    return dset


def extend(dset, array):
    """
    Extend an extensible dataset with an array of a compatible dtype.

    :param dset: an h5py dataset
    :param array: an array of length L
    :returns: the total length of the dataset (i.e. initial length + L)
    """
    length = len(dset)
    newlength = length + len(array)
    dset.resize((newlength,) + array.shape[1:])
    dset[length:newlength] = array
    return newlength


def extend3(hdf5path, key, array, **attrs):
    """
    Extend an HDF5 file dataset with the given array
    """
    with h5py.File(hdf5path) as h5:
        try:
            dset = h5[key]
        except KeyError:
            dset = create(h5, key, array.dtype,
                          shape=(None,) + array.shape[1:])
        length = extend(dset, array)
        for key, val in attrs.items():
            dset.attrs[key] = val
        h5.flush()
    return length


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
    elif hasattr(dset, 'value'):
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

    def __setitem__(self, path, obj):
        cls = obj.__class__
        if hasattr(obj, '__toh5__'):
            obj, attrs = obj.__toh5__()
            pyclass = cls2dotname(cls)
        else:
            pyclass = ''
        if isinstance(obj, dict):
            for k, v in sorted(obj.items()):
                key = '%s/%s' % (path, quote_plus(k))
                self[key] = v
        else:
            super(File, self).__setitem__(path, obj)
        if pyclass:
            self.flush()  # make sure it is fully saved
            a = super(File, self).__getitem__(path).attrs
            a['__pyclass__'] = pyclass
            for k, v in sorted(attrs.items()):
                a[k] = v

    def __getitem__(self, path):
        h5obj = super(File, self).__getitem__(path)
        h5attrs = h5obj.attrs
        if '__pyclass__' in h5attrs:
            # NB: the `decode` below is needed for Python 3
            cls = dotname2cls(decode(h5attrs['__pyclass__']))
            obj = cls.__new__(cls)
            if hasattr(h5obj, 'items'):  # is group
                h5obj = {unquote_plus(k): self['%s/%s' % (path, k)]
                         for k, v in h5obj.items()}
            elif hasattr(h5obj, 'value'):
                h5obj = h5obj.value
            obj.__fromh5__(h5obj, h5attrs)
            return obj
        else:
            return h5obj

    def set_nbytes(self, key, nbytes=None):
        """
        Set the `nbytes` attribute on the HDF5 object identified by `key`.
        """
        obj = super(File, self).__getitem__(key)
        if nbytes is not None:  # size set from outside
            obj.attrs['nbytes'] = nbytes
        else:  # recursively determine the size of the datagroup
            obj.attrs['nbytes'] = nbytes = ByteCounter.get_nbytes(obj)
        return nbytes

    def save(self, nodedict, root=''):
        """
        Save a node dictionary in the .hdf5 file, starting from the root
        dataset. A common application is to convert XML files into .hdf5
        files, see the usage in :mod:`openquake.commands.to_hdf5`.

        :param nodedict:
            a dictionary with keys 'tag', 'attrib', 'text', 'nodes'
        """
        setitem = super(File, self).__setitem__
        getitem = super(File, self).__getitem__
        tag = nodedict['tag']
        text = nodedict.get('text', None)
        if hasattr(text, 'strip'):
            text = text.strip()
        attrib = nodedict.get('attrib', {})
        path = '/'.join([root, tag])
        nodes = nodedict.get('nodes', [])
        if text not in ('', None):  # text=0 is stored
            try:
                setitem(path, text)
            except Exception as exc:
                sys.stderr.write('%s: %s\n' % (path, exc))
                raise
        elif attrib and not nodes:
            setitem(path, numpy.nan)
        for subdict in _resolve_duplicates(nodes):
            self.save(subdict, path)
        if attrib:
            dset = getitem(path)
            for k, v in attrib.items():
                dset.attrs[k] = v


def _resolve_duplicates(dicts):
    # when node dictionaries with duplicated tags are passed (for instance
    # [{'tag': 'SourceGroup', ...}, {'tag': 'SourceGroup', ...}])
    # add an incremental number to the tag, preceded by a semicolon:
    # [{'tag': 'SourceGroup;1', ...}, {'tag': 'SourceGroup;2', ...}])
    # in this way the dictionaries can be saved in HDF5 format without
    # name conflicts and by respecting the ordering
    for tag, grp in itertools.groupby(dicts, operator.itemgetter('tag')):
        group = list(grp)
        if len(group) > 1:  # there are duplicate tags
            for i, dic in enumerate(group, 1):
                dic['tag'] += ';%d' % i
    return dicts


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
