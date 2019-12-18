# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import io
import os
import re
import gzip
import getpass
import itertools
import collections
import numpy
import h5py
import pandas

from openquake.baselib import hdf5, config, performance


CALC_REGEX = r'(calc|cache)_(\d+)\.hdf5'


def get_datadir():
    """
    Extracts the path of the directory where the openquake data are stored
    from the environment ($OQ_DATADIR) or from the shared_dir in the
    configuration file.
    """
    datadir = os.environ.get('OQ_DATADIR')
    if not datadir:
        shared_dir = config.directory.shared_dir
        if shared_dir:
            datadir = os.path.join(shared_dir, getpass.getuser(), 'oqdata')
        else:  # use the home of the user
            datadir = os.path.join(os.path.expanduser('~'), 'oqdata')
    return datadir


def get_calc_ids(datadir=None):
    """
    Extract the available calculation IDs from the datadir, in order.
    """
    datadir = datadir or get_datadir()
    if not os.path.exists(datadir):
        return []
    calc_ids = set()
    for f in os.listdir(datadir):
        mo = re.match(CALC_REGEX, f)
        if mo:
            calc_ids.add(int(mo.group(2)))
    return sorted(calc_ids)


def get_last_calc_id(datadir=None):
    """
    Extract the latest calculation ID from the given directory.
    If none is found, return 0.
    """
    datadir = datadir or get_datadir()
    calcs = get_calc_ids(datadir)
    if not calcs:
        return 0
    return calcs[-1]


def hdf5new(datadir=None):
    """
    Return a new `hdf5.File by` instance with name determined by the last
    calculation in the datadir (plus one). Set the .path attribute to the
    generated filename.
    """
    datadir = datadir or get_datadir()
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    calc_id = get_last_calc_id(datadir) + 1
    fname = os.path.join(datadir, 'calc_%d.hdf5' % calc_id)
    new = hdf5.File(fname, 'w')
    new.path = fname
    performance.init_performance(new)
    return new


def extract_calc_id_datadir(filename, datadir=None):
    """
    Extract the calculation ID from the given filename or integer:

    >>> extract_calc_id_datadir('/mnt/ssd/oqdata/calc_25.hdf5')
    (25, '/mnt/ssd/oqdata')
    >>> extract_calc_id_datadir('/mnt/ssd/oqdata/wrong_name.hdf5')
    Traceback (most recent call last):
       ...
    ValueError: Cannot extract calc_id from /mnt/ssd/oqdata/wrong_name.hdf5
    """
    datadir = datadir or get_datadir()
    try:
        calc_id = int(filename)
    except ValueError:
        filename = os.path.abspath(filename)
        datadir = os.path.dirname(filename)
        mo = re.match(CALC_REGEX, os.path.basename(filename))
        if mo is None:
            raise ValueError('Cannot extract calc_id from %s' % filename)
        calc_id = int(mo.group(2))
    return calc_id, datadir


def read(calc_id, mode='r', datadir=None):
    """
    :param calc_id: calculation ID or filename
    :param mode: 'r' or 'w'
    :param datadir: the directory where to look
    :returns: the corresponding DataStore instance

    Read the datastore, if it exists and it is accessible.
    """
    datadir = datadir or get_datadir()
    dstore = DataStore(calc_id, datadir, mode=mode)
    try:
        hc_id = dstore['oqparam'].hazard_calculation_id
    except KeyError:  # no oqparam
        hc_id = None
    if hc_id:
        dstore.parent = read(hc_id, datadir=os.path.dirname(dstore.filename))
    return dstore


def dset2df(dset):
    """
    Converts an HDF5 dataset with an attribute shape_descr into a Pandas
    dataframe.
    """
    shape_descr = [v.decode('utf-8') for v in dset.attrs['shape_descr']]
    out = []
    tags = []
    idxs = []
    dtlist = []
    for i, field in enumerate(shape_descr):
        values = dset.attrs[field]
        dtlist.append((field[:-1], values[0].dtype))
        tags.append(values)
        idxs.append(range(len(values)))
    dtlist.append(('value', dset.dtype))
    for idx, values in zip(itertools.product(*idxs),
                           itertools.product(*tags)):
        out.append(values + (dset[idx],))
    return pandas.DataFrame(numpy.array(out, dtlist))


class DataStore(collections.abc.MutableMapping):
    """
    DataStore class to store the inputs/outputs of a calculation on the
    filesystem.

    Here is a minimal example of usage:

    >>> ds = DataStore()
    >>> ds['example'] = 42
    >>> print(ds['example'][()])
    42
    >>> ds.clear()

    When reading the items, the DataStore will return a generator. The
    items will be ordered lexicographically according to their name.

    There is a serialization protocol to store objects in the datastore.
    An object is serializable if it has a method `__toh5__` returning
    an array and a dictionary, and a method `__fromh5__` taking an array
    and a dictionary and populating the object.
    For an example of use see :class:`openquake.hazardlib.site.SiteCollection`.
    """
    def __init__(self, calc_id=None, datadir=None, params=(), mode=None):
        datadir = datadir or get_datadir()
        if isinstance(calc_id, str):  # passed a real path
            self.filename = calc_id
            self.calc_id, datadir = extract_calc_id_datadir(calc_id, datadir)
        else:
            if calc_id is None:  # use a new datastore
                self.calc_id = get_last_calc_id(datadir) + 1
            elif calc_id < 0:  # use an old datastore
                calc_ids = get_calc_ids(datadir)
                try:
                    self.calc_id = calc_ids[calc_id]
                except IndexError:
                    raise IndexError(
                        'There are %d old calculations, cannot '
                        'retrieve the %s' % (len(calc_ids), calc_id))
            else:  # use the given datastore
                self.calc_id = calc_id
            self.filename = os.path.join(
                datadir, 'calc_%s.hdf5' % self.calc_id)
        self.tempname = self.filename[:-5] + '_tmp.hdf5'
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        self.params = params
        self.parent = ()  # can be set later
        self.datadir = datadir
        self.mode = mode or ('r+' if os.path.exists(self.filename) else 'w')
        if self.mode == 'r' and not os.path.exists(self.filename):
            raise IOError('File not found: %s' % self.filename)
        self.hdf5 = ()  # so that `key in self.hdf5` is valid
        self.open(self.mode)

    def open(self, mode):
        """
        Open the underlying .hdf5 file and the parent, if any
        """
        if self.hdf5 == ():  # not already open
            try:
                self.hdf5 = hdf5.File(self.filename, mode)
            except OSError as exc:
                raise OSError('%s in %s' % (exc, self.filename))

    @property
    def export_dir(self):
        """
        Return the underlying export directory
        """
        edir = getattr(self, '_export_dir', None) or self['oqparam'].export_dir
        return edir

    @export_dir.setter
    def export_dir(self, value):
        """
        Set the export directory
        """
        self._export_dir = value

    def getitem(self, name):
        """
        Return a dataset by using h5py.File.__getitem__
        """
        return h5py.File.__getitem__(self.hdf5, name)

    def swmr_on(self):
        """
        Enable the SWMR mode on the underlying HDF5 file
        """
        self.close()  # flush everything
        self.open('a')
        try:
            self.hdf5.swmr_mode = True
        except ValueError:  # already set
            pass

    def set_attrs(self, key, **kw):
        """
        Set the HDF5 attributes of the given key
        """
        self.hdf5.save_attrs(key, kw)

    def get_attr(self, key, name, default=None):
        """
        :param key: dataset path
        :param name: name of the attribute
        :param default: value to return if the attribute is missing
        """
        try:
            obj = h5py.File.__getitem__(self.hdf5, key)
        except KeyError:
            if self.parent != ():
                return self.parent.get_attr(key, name, default)
            else:
                raise
        try:
            return obj.attrs[name]
        except KeyError:
            if default is None:
                raise
            return default

    def get_attrs(self, key):
        """
        :param key: dataset path
        :returns: dictionary of attributes for that path
        """
        try:
            dset = h5py.File.__getitem__(self.hdf5, key)
        except KeyError:
            if self.parent != ():
                dset = h5py.File.__getitem__(self.parent.hdf5, key)
            else:
                raise
        return dict(dset.attrs)

    def create_dset(self, key, dtype, shape=(None,), compression=None,
                    fillvalue=0, attrs=None):
        """
        Create a one-dimensional HDF5 dataset.

        :param key: name of the dataset
        :param dtype: dtype of the dataset (usually composite)
        :param shape: shape of the dataset, possibly extendable
        :param compression: the kind of HDF5 compression to use
        :param attrs: dictionary of attributes of the dataset
        :returns: a HDF5 dataset
        """
        return hdf5.create(
            self.hdf5, key, dtype, shape, compression, fillvalue, attrs)

    def save(self, key, kw):
        """
        Update the object associated to `key` with the `kw` dictionary;
        works for LiteralAttrs objects and automatically flushes.
        """
        if key not in self:
            obj = hdf5.LiteralAttrs()
        else:
            obj = self[key]
        vars(obj).update(kw)
        self[key] = obj
        self.flush()

    def export_path(self, relname, export_dir=None):
        """
        Return the path of the exported file by adding the export_dir in
        front, the calculation ID at the end.

        :param relname: relative file name
        :param export_dir: export directory (if None use .export_dir)
        """
        # removing inner slashed to avoid creating intermediate directories
        name, ext = relname.replace('/', '-').rsplit('.', 1)
        newname = '%s_%s.%s' % (name, self.calc_id, ext)
        if export_dir is None:
            export_dir = self.export_dir
        return os.path.join(export_dir, newname)

    def build_fname(self, prefix, postfix, fmt, export_dir=None):
        """
        Build a file name from a realization, by using prefix and extension.

        :param prefix: the prefix to use
        :param postfix: the postfix to use (can be a realization object)
        :param fmt: the extension ('csv', 'xml', etc)
        :param export_dir: export directory (if None use .export_dir)
        :returns: relative pathname including the extension
        """
        if hasattr(postfix, 'sm_lt_path'):  # is a realization
            fname = '%s-rlz-%03d.%s' % (prefix, postfix.ordinal, fmt)
        else:
            fname = prefix + ('-%s' % postfix if postfix else '') + '.' + fmt
        return self.export_path(fname, export_dir)

    def flush(self):
        """Flush the underlying hdf5 file"""
        if self.parent != ():
            self.parent.flush()
        if self.hdf5:  # is open
            self.hdf5.flush()

    def close(self):
        """Close the underlying hdf5 file"""
        if self.parent != ():
            self.parent.flush()
            self.parent.close()
        if self.hdf5:  # is open
            self.hdf5.flush()
            self.hdf5.close()
            self.hdf5 = ()

    def clear(self):
        """Remove the datastore from the file system"""
        self.close()
        os.remove(self.filename)

    def getsize(self, key=None):
        """
        Return the size in byte of the output associated to the given key.
        If no key is given, returns the total size of all files.
        """
        if key is None:
            return os.path.getsize(self.filename)
        return hdf5.ByteCounter.get_nbytes(
            h5py.File.__getitem__(self.hdf5, key))

    def get(self, key, default):
        """
        :returns: the value associated to the datastore key, or the default
        """
        try:
            return self[key]
        except KeyError:
            return default

    def store_files(self, fnames, where='input/'):
        """
        :param fnames: a set of full pathnames
        """
        prefix = len(os.path.commonprefix(fnames))
        for fname in fnames:
            data = gzip.compress(open(fname, 'rb').read())
            self[where + fname[prefix:]] = numpy.void(data)

    def retrieve_files(self, prefix='input'):
        """
        :yields: pairs (relative path, data)
        """
        for k, v in self[prefix].items():
            if hasattr(v, 'items'):
                yield from self.retrieve_files(prefix + '/' + k)
            else:
                yield k, gzip.decompress(bytes(numpy.asarray(v[()])))

    def get_file(self, key):
        """
        :returns: a BytesIO object
        """
        data = bytes(numpy.asarray(self[key][()]))
        return io.BytesIO(gzip.decompress(data))

    def read_df(self, key, index=None):
        """
        :param key: name of the structured dataset
        :param index: if given, name of the "primary key" field
        :returns: pandas DataFrame associated to the dataset
        """
        dset = self.getitem(key)
        if 'shape_descr' in dset.attrs:
            return dset2df(dset)
        dtlist = []
        for name in dset.dtype.names:
            dt = dset.dtype[name]
            if dt.shape:  # vector field
                templ = name + '_%d' * len(dt.shape)
                for i, _ in numpy.ndenumerate(numpy.zeros(dt.shape)):
                    dtlist.append((templ % i, dt.base))
            else:  # scalar field
                dtlist.append((name, dt))
        data = numpy.zeros(len(dset), dtlist)
        for name in dset.dtype.names:
            arr = dset[name]
            dt = dset.dtype[name]
            if dt.shape:  # vector field
                templ = name + '_%d' * len(dt.shape)
                for i, _ in numpy.ndenumerate(numpy.zeros(dt.shape)):
                    data[templ % i] = arr[(slice(None),) + i]
            else:  # scalar field
                data[name] = arr
        return pandas.DataFrame.from_records(data, index=index)

    @property
    def metadata(self):
        """
        :returns: datastore metadata version, date, checksum as a dictionary
        """
        a = self.hdf5.attrs
        return dict(generated_by='OpenQuake engine %s' % a['engine_version'],
                    start_date=a['date'], checksum=a['checksum32'])

    def __getitem__(self, key):
        if self.hdf5 == ():  # the datastore is closed
            raise ValueError('Cannot find %s in %s' % (key, self))
        try:
            val = self.hdf5[key]
        except KeyError:
            if self.parent != ():
                self.parent.open('r')
                try:
                    val = self.parent[key]
                except KeyError:
                    raise KeyError(
                        'No %r found in %s and ancestors' % (key, self))
            else:
                raise KeyError('No %r found in %s' % (key, self))
        return val

    def __setitem__(self, key, val):
        if key in self.hdf5:
            # there is a bug in the current version of HDF5 for composite
            # arrays: is impossible to save twice the same key; so we remove
            # the key first, then it is possible to save it again
            del self[key]
        try:
            self.hdf5[key] = val
        except RuntimeError as exc:
            raise RuntimeError('Could not save %s: %s in %s' %
                               (key, exc, self.filename))

    def __delitem__(self, key):
        del self.hdf5[key]

    def __enter__(self):
        self.was_close = self.hdf5 == ()
        if self.was_close:
            self.open(self.mode)
        return self

    def __exit__(self, etype, exc, tb):
        if self.was_close:  # and has been opened in __enter__, close it
            self.close()
        del self.was_close

    def __getstate__(self):
        # make the datastore pickleable
        return dict(mode='r',
                    parent=self.parent,
                    calc_id=self.calc_id,
                    hdf5=(),
                    filename=self.filename)

    def __iter__(self):
        if not self.hdf5:
            raise RuntimeError('%s is closed' % self)
        for path in sorted(self.hdf5):
            yield path

    def __contains__(self, key):
        return key in self.hdf5 or self.parent and key in self.parent.hdf5

    def __len__(self):
        if self.hdf5 == ():  # closed
            return 1
        return sum(1 for f in self.hdf5)

    def __hash__(self):
        return self.calc_id

    def __repr__(self):
        status = 'open' if self.hdf5 else 'closed'
        return '<%s %s %s>' % (self.__class__.__name__, self.filename, status)
