#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import ast
import shutil
import logging
from openquake.baselib.python3compat import pickle
import collections

import numpy
try:
    import h5py
except ImportError:
    # there is no need of h5py in the workers
    class mock_h5py(object):
        def __getattr__(self, name):
            raise ImportError('Could not import h5py.%s' % name)
    h5py = mock_h5py()

from openquake.baselib.general import CallableDict
from openquake.commonlib.writers import write_csv


# a dictionary of views datastore -> array
view = CallableDict()

DATADIR = os.environ.get('OQ_DATADIR', os.path.expanduser('~/oqdata'))


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
        return dset.value.nbytes


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


def get_calc_ids(datadir=DATADIR):
    """
    Extract the available calculation IDs from the datadir, in order.
    """
    if not os.path.exists(datadir):
        return []
    calc_ids = []
    for f in os.listdir(DATADIR):
        mo = re.match('calc_(\d+)', f)
        if mo:
            calc_ids.append(int(mo.group(1)))
    return sorted(calc_ids)


def get_last_calc_id(datadir):
    """
    Extract the latest calculation ID from the given directory.
    If none is found, return 0.
    """
    calcs = get_calc_ids(datadir)
    if not calcs:
        return 0
    return calcs[-1]


class Hdf5Dataset(object):
    """
    Little wrapper around a one-dimensional HDF5 dataset.

    :param hdf5: a h5py.File object
    :param key: an hdf5 key string
    :param dtype: dtype of the dataset (usually composite)
    :param shape: shape of the dataset (if None, the dataset is extendable)
    """
    def __init__(self, hdf5, key, dtype, shape):
        self.hdf5 = hdf5
        self.key = key
        self.dtype = dtype
        if shape is None:  # extendable dataset
            self.dset = self.hdf5.create_dataset(
                key, (0,), dtype, chunks=True, maxshape=(None,))
            self.size = 0
            self.dset.attrs['nbytes'] = 0
        else:  # fixed-shape dataset
            if isinstance(shape, tuple):
                n = numpy.prod(shape)
            else:  # integer shape
                n = shape
                shape = (n,)
            self.dset = self.hdf5.create_dataset(key, shape, dtype)
            self.size = n
            self.dset.attrs['nbytes'] = n * numpy.zeros(1, dtype).nbytes
        self.attrs = self.dset.attrs

    def extend(self, array):
        """
        Extend the dataset with the given array, which must have
        the expected dtype. This method will give an error if used
        with a fixed-shape dataset.
        """
        newsize = self.size + len(array)
        self.dset.resize((newsize,))
        self.dset[self.size:newsize] = array
        self.size = newsize
        self.dset.attrs['nbytes'] += array.nbytes


class DataStore(collections.MutableMapping):
    """
    DataStore class to store the inputs/outputs of each calculation on the
    filesystem. It works like a mapping; composite keys ending with
    "h5" are associated to .hdf5 files; other keys are associated
    to .pik files containing pickled objects.

    NB: the calc_dir is created only at the first attempt to write on it,
    so there is potentially a race condition if the client code does not pass
    an unique calc_id and relies on the DataStore to create it.

    Here is a minimal example of usage:

    >>> ds = DataStore()
    >>> ds['example'] = 'hello world'
    >>> ds.items()
    [(u'example', 'hello world')]
    >>> ds.clear()

    It possible to store numpy arrays in HDF5 format, if the library h5py is
    installed and if the last field of the key is 'h5'. It is also possible
    to store items of the form (name, value) where name is a string and value
    is an array, and the last field of the key is 'hdf5'. When reading the
    items, the DataStore will return a generator. The items will be ordered
    lexicographically according to their name.
    """
    def __init__(self, calc_id=None, datadir=DATADIR, parent=(),
                 export_dir='.', params=()):
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        if calc_id is None:  # use a new datastore
            self.calc_id = get_last_calc_id(datadir) + 1
        elif calc_id < 0:  # use an old datastore
            calc_ids = get_calc_ids(datadir)
            try:
                self.calc_id = calc_ids[calc_id]
            except IndexError:
                raise IndexError('There are %d old calculations, cannot '
                                 'retrieve the %s' % (len(calc_ids), calc_id))
        else:  # use the given datastore
            self.calc_id = calc_id
        self.parent = parent  # parent datastore (if any)
        self.datadir = datadir
        self.calc_dir = os.path.join(datadir, 'calc_%s' % self.calc_id)
        if not os.path.exists(self.calc_dir):
            os.mkdir(self.calc_dir)
        self.export_dir = export_dir
        self.hdf5path = os.path.join(self.calc_dir, 'output.hdf5')
        mode = 'r+' if os.path.exists(self.hdf5path) else 'w'
        self.hdf5 = h5py.File(self.hdf5path, mode, libver='latest')
        self.attrs = self.hdf5.attrs
        for name, value in params:
            self.attrs[name] = value
        if not parent and 'hazard_calculation_id' in self.attrs:
            parent_id = ast.literal_eval(self.attrs['hazard_calculation_id'])
            if parent_id:
                self.parent = self.__class__(parent_id)

    def set_parent(self, parent):
        """
        Give a parent to a datastore and update its .attrs with the parent
        attributes, which are assumed to be literal strings.
        """
        self.parent = parent
        # merge parent attrs into child attrs
        for name, value in self.parent.attrs.items():
            if name not in self.attrs:  # add missing parameter
                self.attrs[name] = value

    def create_dset(self, key, dtype, size=None):
        """
        Create a one-dimensional HDF5 dataset.

        :param key: a string starting with '/'
        :param dtype: dtype of the dataset (usually composite)
        :param size: size of the dataset (if None, the dataset is extendable)
        """
        return Hdf5Dataset(self.hdf5, key, dtype, size)

    def export_path(self, key, fmt):
        """
        Return the name of the exported file.

        :param key: the datastore key
        :param fmt: the export format extension
        """
        if key.startswith('/'):
            key = key[1:]
        return os.path.join(self.export_dir, key + '.' + fmt)

    def export_csv(self, key):
        """
        Generic csv exporter
        """
        return write_csv(self.export_path(key, 'csv'), self[key])

    def close(self):
        """Close the underlying hdf5 file"""
        self.hdf5.close()

    def symlink(self, name):
        """
        Make a symlink to the hdf5 file (except on Windows)

        :param name:
            a file or directory name without extensions; the name of
            the link will be extracted from it by replacing the slashes
            with dashes; the symlink will be created in the .datadir
        """
        if hasattr(os, 'symlink'):  # Unix, Max
            link_name = os.path.join(
                self.datadir, name.strip('/').replace('/', '-')) + '.hdf5'
            try:
                if os.path.exists(link_name):
                    os.remove(link_name)
                os.symlink(self.hdf5path, link_name)
            except OSError as err:
                # this is not an issue
                logging.info('Could not create symlink %s: %s', link_name, err)

    def clear(self):
        """Remove the datastore from the file system"""
        self.close()
        shutil.rmtree(self.calc_dir)

    def getsize(self, key=None):
        """
        Return the size in byte of the output associated to the given key.
        If no key is given, returns the total size of all files.
        """
        if key is None:
            return os.path.getsize(self.hdf5path)
        return ByteCounter.get_nbytes(self.hdf5[key])

    def get(self, key, default):
        """
        :returns: the value associated to the datastore key, or the default
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        try:
            val = self.hdf5[key]
        except KeyError:
            if self.parent:
                try:
                    val = self.parent.hdf5[key]
                except KeyError:
                    raise KeyError(
                        'No %r found in %s' % (key, [self, self.parent]))
            else:
                raise KeyError('No %r found in %s' % (key, self))
        try:
            shape = val.shape
        except AttributeError:  # val is a group
            return val
        if not shape:
            val = pickle.loads(val.value)
        return val

    def __setitem__(self, key, value):
        if (not isinstance(value, numpy.ndarray) or
                value.dtype is numpy.dtype(object)):
            val = numpy.array(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
        else:
            val = value
        if key in self.hdf5:
            # there is a bug in the current version of HDF5 for composite
            # arrays: is impossible to save twice the same key; so we remove
            # the key first, then it is possible to save it again
            del self[key]
        try:
            self.hdf5[key] = val
        except RuntimeError as exc:
            raise RuntimeError('Could not save %s: %s in %s' %
                               (key, exc, self.hdf5path))

    def __delitem__(self, key):
        if (h5py.version.version <= '2.0.1' and not
                hasattr(self.hdf5[key], 'shape')):
            # avoid bug when deleting groups that produces a segmentation fault
            return
        del self.hdf5[key]

    def __iter__(self):
        for path in sorted(self.hdf5):
            yield path

    def __contains__(self, key):
        return key in self.hdf5

    def __len__(self):
        return sum(1 for f in self)

    def __repr__(self):
        return '<%s %d>' % (self.__class__.__name__, self.calc_id)


class Fake(dict):
    """
    A fake datastore as a dict subclass, useful in tests and such
    """
    def __init__(self, attrs, **kwargs):
        self.attrs = {k: repr(v) for k, v in attrs.items()}
        self.update(kwargs)


def persistent_attribute(key):
    """
    Persistent attributes are persisted to the datastore and cached.
    Modifications to mutable objects are not automagically persisted.
    If you have a huge object that does not fit in memory use the datastore
    directory (for instance, open a HDF5 file to create an empty array, then
    populate it). Notice that you can use any dict-like data structure in
    place of the datastore, provided you can set attributes on it.
    Here is an example:

    >>> class Datastore(dict):
    ...     "A fake datastore"

    >>> class Store(object):
    ...     a = persistent_attribute('a')
    ...     def __init__(self, a):
    ...         self.datastore = Datastore()
    ...         self.a = a  # this assegnation will store the attribute

    >>> store = Store([1])
    >>> store.a  # this retrieves the attribute
    [1]
    >>> store.a.append(2)
    >>> store.a = store.a  # remember to store the modified attribute!

    :param key: the name of the attribute to be made persistent
    :returns: a property to be added to a class with a .datastore attribute
    """
    privatekey = '_' + key

    def getter(self):
        # Try to get the value from the privatekey attribute (i.e. from
        # the cache of the datastore); if not possible, get the value
        # from the datastore and set the cache; if not possible, get the
        # value from the parent and set the cache. If the value cannot
        # be retrieved, raise an AttributeError.
        try:
            return getattr(self.datastore, privatekey)
        except AttributeError:
            value = self.datastore[key]
            setattr(self.datastore, privatekey, value)
            return value

    def setter(self, value):
        # Update the datastore and the private key
        self.datastore[key] = value
        setattr(self.datastore, privatekey, value)

    return property(getter, setter)
