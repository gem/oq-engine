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

OQDIR = os.environ.get('OQ_DIRECTORY', os.path.expanduser('~/oqlite'))


def get_last_calc_id(oqdir=OQDIR):
    """
    Extract the latest calculation ID from the given directory.
    If none is found, return 0.
    """
    calcs = [f for f in os.listdir(OQDIR) if re.match('calc_\d+', f)]
    if not calcs:
        return 0
    calc_ids = [int(calc[5:]) for calc in calcs]
    return max(calc_ids)


def key2str(key):
    """
    Convert the key (a string or a tuple of strings) into a dash-separated
    ASCII string.
    """
    if isinstance(key, basestring):
        if '-' in key:
            raise KeyError('The key %s is invalid since it contains a dash'
                           % key)
        return str(key)
    return '-'.join(key)


def str2key(keystr):
    """
    Convert a key string into a tuple of strings, by splitting on dashes
    """
    return tuple(keystr.split('-'))


class DataStore(collections.MutableMapping):
    """
    DataStore class to store the inputs/outputs of each calculation on the
    filesystem. It works like a mapping; composite keys ending with
    "h5" are associated to .hdf5 files; other keys are associated
    to .pik files containing pickled objects.

    NB: the calc_dir is created only at the first attempt to write on it,
    so there is potentially a race condition. It is up to the client code
    to ensure that two calculations are not writing on the same directory.

    Here is a minimal example of usage:

    >>> ds = DataStore()
    >>> ds['example'] = 'hello world'
    >>> ds.items()
    [(('example',), 'hello world')]
    >>> ds.remove()

    It is also possible to store callables with two arguments (key, datastore).
    They will be automatically invoked when the key is accessed:
    """
    def __init__(self, calc_id=None, oqdir=OQDIR):
        if not os.path.exists(oqdir):
            os.makedirs(oqdir)
        self.calc_id = calc_id or (get_last_calc_id(oqdir) + 1)
        self.calc_dir = os.path.join(oqdir, 'calc_%s' % self.calc_id)

    def path(self, key):
        """
        Return the full path name associated to the given key
        """
        if key[-1] == 'h5':
            return os.path.join(self.calc_dir, key2str(key)[:-3] + '.hdf5')
        return os.path.join(self.calc_dir, key2str(key) + '.pik')

    def remove(self):
        """Remove the datastore from the file system"""
        shutil.rmtree(self.calc_dir)

    def __getitem__(self, key):
        if key[-1] == 'h5':
            h5f = h5py.File(self.path(key), 'r')
            value = h5f['dset'][:]
            h5f.close()
            return value
        with open(self.path(key)) as df:
            value = cPickle.load(df)
            if callable(value):
                return value(key, self)
            return value

    def __setitem__(self, key, value):
        if not os.path.exists(self.calc_dir):
            os.mkdir(self.calc_dir)
        if key[-1] == 'h5':
            if not isinstance(value, numpy.ndarray):
                raise ValueError('%r is not a numpy array' % value)
            h5f = h5py.File(self.path(key), 'w', libver='latest')
            dset = h5f.create_dataset('dset', data=value)
            h5f.close()
            return dset
        with open(self.path(key), 'w') as df:
            return cPickle.dump(value, df, cPickle.HIGHEST_PROTOCOL)

    def __delitem__(self, key):
        os.remove(self.path(key))

    def __iter__(self):
        for f in sorted(os.listdir(self.calc_dir)):
            if f.endswith('.pik'):
                yield str2key(f[:-4])
            elif f.endswith('.hdf5'):
                yield str2key(f[:-5]) + ('h5',)

    def __len__(self):
        return sum(1 for f in os.listdir(self.calc_dir)
                   if f.endswith(('.pik', '.hdf5')))

    def __repr__(self):
        return '<%s %d>' % (self.__class__.__name__, self.calc_id)
