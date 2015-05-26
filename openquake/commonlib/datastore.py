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
import shutil
import cPickle
import collections

import numpy

try:
    import h5py
except ImportError:
    class mock_h5py(object):
        def __getattr__(self, name):
            raise ImportError('Could not import h5py.%s' % name)
    h5py = mock_h5py()

from openquake.commonlib.writers import write_csv


DATADIR = os.environ.get('OQ_DATADIR', os.path.expanduser('~/oqdata'))


class ByteCounter(object):
    """
    A visitor used to measure the dimensions of a HDF5 dataset or group.
    Build an instance of it, pass it to the .visititems method, and then
    read the value of the .nbytes attribute.
    """
    def __init__(self, nbytes=0):
        self.nbytes = nbytes

    def __call__(self, name, dset_or_group):
        try:
            value = dset_or_group.value
        except AttributeError:
            pass  # .value is only defined for datasets, not groups
        else:
            self.nbytes += value.nbytes


def get_last_calc_id(datadir=DATADIR):
    """
    Extract the latest calculation ID from the given directory.
    If none is found, return 0.
    """
    calcs = [f for f in os.listdir(DATADIR) if re.match('calc_\d+', f)]
    if not calcs:
        return 0
    calc_ids = [int(calc[5:]) for calc in calcs]  # strip calc_
    return max(calc_ids)


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
    [('example', 'hello world')]
    >>> ds.clear()

    It is also possible to store callables taking in input the datastore.
    They will be automatically invoked when the key is accessed.

    It possible to store numpy arrays in HDF5 format, if the library h5py is
    installed and if the last field of the key is 'h5'. It is also possible
    to store items of the form (name, value) where name is a string and value
    is an array, and the last field of the key is 'hdf5'. When reading the
    items, the DataStore will return a generator. The items will be ordered
    lexicographically according to their name.
    """
    def __init__(self, calc_id=None, datadir=DATADIR, parent=None):
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        if calc_id is None:  # use a new datastore
            self.calc_id = get_last_calc_id(datadir) + 1
        elif calc_id == -1:  # use the last datastore
            self.calc_id = get_last_calc_id(datadir)
        else:  # use the given datastore
            self.calc_id = calc_id
        self.parent = parent  # parent datastore (if any)
        self.calc_dir = os.path.join(datadir, 'calc_%s' % self.calc_id)
        if not os.path.exists(self.calc_dir):
            os.mkdir(self.calc_dir)
        self.export_dir = '.'
        self.hdf5path = os.path.join(self.calc_dir, 'output.hdf5')
        mode = 'r+' if os.path.exists(self.hdf5path) else 'w'
        self.hdf5 = h5py.File(self.hdf5path, mode, libver='latest')

    def path(self, key):
        """
        Return the full path name associated to the given key
        """
        if key.startswith('/'):
            return key
        return os.path.join(self.calc_dir, key + '.pik')

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
            piksize = sum(self.getsize(key) for key in self
                          if not key.startswith('/'))
            return piksize + os.path.getsize(self.hdf5path)
        elif key.startswith('/'):
            dset = self.hdf5[key]
            if hasattr(dset, 'value'):
                return dset.value.nbytes
            bc = ByteCounter()
            dset.visititems(bc)
            return bc.nbytes
        return os.path.getsize(self.path(key))

    def get(self, key, default):
        """
        :returns: the value associated to the datastore key, or the default
        """
        try:
            return self[key]
        except (KeyError, IOError):
            return default

    def __getitem__(self, key):
        if key.startswith('/'):
            try:
                return self.hdf5[key]
            except KeyError:
                if self.parent:
                    return self.parent.hdf5[key]
                else:
                    raise
        path = self.path(key)
        if not os.path.exists(path) and self.parent:
            path = self.parent.path(key)
        with open(path) as df:
            value = cPickle.load(df)
            if callable(value):
                return value(self)
            return value

    def __setitem__(self, key, value):
        if key.startswith('/'):
            if not isinstance(value, numpy.ndarray):
                raise ValueError('not an array: %r' % value)
            try:
                self.hdf5[key] = value
            except RuntimeError as exc:
                raise RuntimeError('Could not save %s: %s in %s' %
                                   (key, exc, self.hdf5path))
        else:
            with open(self.path(key), 'w') as df:
                return cPickle.dump(value, df, cPickle.HIGHEST_PROTOCOL)

    def __delitem__(self, key):
        if key.startswith('/'):
            del self.hdf5[key]
        else:
            os.remove(self.path(key))

    def __iter__(self):
        for f in sorted(os.listdir(self.calc_dir)):
            if f.endswith('.pik'):
                yield f[:-4]
        for path in sorted(self.hdf5):
            yield '/' + path

    def __contains__(self, key):
        return key in set(self)

    def __len__(self):
        return sum(1 for f in self)

    def __repr__(self):
        return '<%s %d>' % (self.__class__.__name__, self.calc_id)


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
    privatekey = '_' + key[1:] if key[0] == '/' else '_' + key

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
