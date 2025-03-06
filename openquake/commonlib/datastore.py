# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import collections
import numpy
import h5py

from openquake.baselib import hdf5, performance, general
from openquake.commonlib.logs import get_datadir, CALC_REGEX, dbcmd, init


def extract_calc_id_datadir(filename):
    """
    Extract the calculation ID from the given filename or integer:

    >>> id, datadir = extract_calc_id_datadir('/mnt/ssd/oqdata/calc_25.hdf5')
    >>> id
    25
    >>> path_items = os.path.normpath(datadir).split(os.sep)[1:]
    >>> print(path_items)
    ['mnt', 'ssd', 'oqdata']

    >>> wrong_name = '/mnt/ssd/oqdata/wrong_name.hdf5'
    >>> try:
    ...     extract_calc_id_datadir(wrong_name)
    ... except ValueError as exc:
    ...     assert 'Cannot extract calc_id from' in str(exc)
    ...     assert 'wrong_name.hdf5' in str(exc)
    """
    filename = os.path.abspath(filename)
    datadir = os.path.dirname(filename)
    mo = re.match(CALC_REGEX, os.path.basename(filename))
    if mo is None:
        raise ValueError('Cannot extract calc_id from %s' % filename)
    calc_id = int(mo.group(2))
    return calc_id, datadir


def _read(calc_id: int, datadir, mode, haz_id=None):
    # low level function to read a datastore file
    ddir = datadir or get_datadir()
    ppath = None
    # look in the db
    job = dbcmd('get_job', calc_id)
    if job:
        jid = job.id
        path = job.ds_calc_dir + '.hdf5'
        hc_id = job.hazard_calculation_id
        if not hc_id and haz_id:
            dbcmd('update_job', jid, {'hazard_calculation_id': haz_id})
            hc_id = haz_id
        if hc_id and hc_id != jid:
            hc = dbcmd('get_job', hc_id)
            if hc:
                ppath = hc.ds_calc_dir + '.hdf5'
            else:
                ppath = os.path.join(ddir, 'calc_%d.hdf5' % hc_id)
    else:  # when using oq run there is no job in the db
        path = os.path.join(ddir, 'calc_%s.hdf5' % calc_id)
    return DataStore(path, ppath, mode)


def read(calc_id, mode='r', datadir=None, parentdir=None, read_parent=True):
    """
    :param calc_id: calculation ID or filename
    :param mode: 'r' or 'w'
    :param datadir: the directory where to look
    :param parentdir: the datadir of the parent calculation
    :param read_parent: read the parent calculation if it is there
    :returns: the corresponding DataStore instance

    Read the datastore, if it exists and it is accessible.
    """
    if isinstance(calc_id, str):  # pathname
        dstore = DataStore(calc_id, mode=mode)
    else:
        dstore = _read(calc_id, datadir, mode)
    try:
        hc_id = dstore['oqparam'].hazard_calculation_id
    except KeyError:  # no oqparam
        hc_id = None
    if read_parent and hc_id:
        dstore.parent = _read(hc_id, datadir, mode='r')
        dstore.ppath = dstore.parent.filename
    return dstore.open(mode)


def new(calc_id, oqparam, datadir=None, mode=None):
    """
    :param calc_id:
        if integer > 0 look in the database and then on the filesystem
        if integer < 0 look at the old calculations in the filesystem
    :param oqparam:
        OqParam instance with the validated parameters of the calculation
    :returns:
        a DataStore instance associated to the given calc_id
    """
    dstore = _read(calc_id, mode, datadir)
    if 'oqparam' not in dstore:
        dstore['oqparam'] = oqparam
    if oqparam.hazard_calculation_id:
        dstore.ppath = read(calc_id, 'r', datadir).ppath
    return dstore


def create_job_dstore(description='custom calculation', parent=(), ini=None):
    """
    :returns: <DataStore> and <LogContext> associated to the calculation
    """
    if ini is not None:
        dic = ini
    else:
        dic = dict(description=description, calculation_mode='custom')
    log = init(dic)
    dstore = new(log.calc_id, log.get_oqparam(validate=False))
    dstore.parent = parent
    return log, dstore


def read_hc_id(hdf5):
    """
    Getting the hazard_calculation_id, if any
    """
    try:
        oq = hdf5['oqparam']
    except KeyError:  # oqparam not saved yet
        return
    except OSError:  # file open by another process with oqparam not flushed
        return
    return oq.hazard_calculation_id


class DataStore(collections.abc.MutableMapping):
    """
    DataStore class to store the inputs/outputs of a calculation on the
    filesystem.

    Here is a minimal example of usage:

    >>> log, dstore = create_job_dstore()
    >>> with dstore, log:
    ...     dstore['example'] = 42
    ...     print(dstore['example'][()])
    42

    When reading the items, the DataStore will return a generator. The
    items will be ordered lexicographically according to their name.

    There is a serialization protocol to store objects in the datastore.
    An object is serializable if it has a method `__toh5__` returning
    an array and a dictionary, and a method `__fromh5__` taking an array
    and a dictionary and populating the object.
    For an example of use see :class:`openquake.hazardlib.site.SiteCollection`.
    """
    calc_id = None  # set at instantiation time
    job = None  # set at instantiation time
    opened = 0
    closed = 0

    def __init__(self, path, ppath=None, mode=None):
        self.filename = path
        self.ppath = ppath
        self.calc_id, datadir = extract_calc_id_datadir(path)
        self.tempname = self.filename[:-5] + '_tmp.hdf5'
        if not os.path.exists(datadir) and mode != 'r':
            os.makedirs(datadir)
        self.parent = ()  # can be set later
        self.datadir = datadir
        self.mode = mode or ('r+' if os.path.exists(self.filename) else 'w')
        if self.mode == 'r' and not os.path.exists(self.filename):
            raise IOError('File not found: %s' % self.filename)
        self.hdf5 = ()  # so that `key in self.hdf5` is valid
        self.open(self.mode)
        if mode != 'r':  # w, a or r+
            performance.init_performance(self.hdf5)

    def open(self, mode):
        """
        Open the underlying .hdf5 file
        """
        if self.hdf5 == ():  # not already open
            try:
                self.hdf5 = hdf5.File(self.filename, mode)
            except OSError as exc:
                raise OSError('%s in %s' % (exc, self.filename))
            hc_id = read_hc_id(self.hdf5)
            if hc_id:
                self.parent = read(hc_id)
        return self

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
        try:
            return h5py.File.__getitem__(self.hdf5, name)
        except KeyError:
            if self.parent != ():
                if not self.parent.hdf5:
                    self.parent.open('r')
                return self.parent.getitem(name)
            else:
                raise

    def swmr_on(self):
        """
        Enable the SWMR mode on the underlying HDF5 file
        """
        self.close()  # flush everything
        self.open('a')
        if self.parent != ():
            self.parent.open('r')
        try:
            self.hdf5.swmr_mode = True
        except (ValueError, RuntimeError):  # already set
            pass

    def set_attrs(self, key, **kw):
        """
        Set the HDF5 attributes of the given key
        """
        self.hdf5.save_attrs(key, kw)

    def set_shape_descr(self, key, **kw):
        """
        Set shape attributes
        """
        hdf5.set_shape_descr(self.hdf5, key, kw)

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
        if isinstance(dtype, numpy.ndarray):
            dset = hdf5.create(
                self.hdf5, key, dtype.dtype, dtype.shape,
                compression, fillvalue, attrs)
            dset[:] = dtype
            return dset
        return hdf5.create(
            self.hdf5, key, dtype, shape, compression, fillvalue, attrs)

    def create_df(self, key, nametypes, compression=None, **kw):
        """
        Create a HDF5 datagroup readable as a pandas DataFrame

        :param key:
            name of the dataset
        :param nametypes:
            list of pairs (name, dtype) or (name, array) or DataFrame
        :param compression:
            the kind of HDF5 compression to use
        :param kw:
            extra attributes to store
        """
        return self.hdf5.create_df(key, nametypes, compression, **kw)

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

    def getsize(self, key='/'):
        """
        Return the size in byte of the output associated to the given key.
        If no key is given, returns the total size of all files.
        """
        if key == '/':
            return os.path.getsize(self.filename)
        try:
            dset = self.getitem(key)
        except KeyError:
            if self.parent != ():
                dset = self.parent.getitem(key)
            else:
                raise
        return hdf5.ByteCounter.get_nbytes(dset)

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
            with open(fname, 'rb') as f:
                data = gzip.compress(f.read())
            self[where + fname[prefix:]] = numpy.void(data)

    def retrieve_files(self, prefix='input'):
        """
        :yields: pairs (relative path, data)
        """
        for k, v in self[prefix].items():
            if hasattr(v, 'items'):
                yield from self.retrieve_files(prefix + '/' + k)
            else:
                yield prefix + '/' + k, gzip.decompress(
                    bytes(numpy.asarray(v[()])))

    def get_file(self, key):
        """
        :returns: a BytesIO object
        """
        data = bytes(numpy.asarray(self[key][()]))
        return io.BytesIO(gzip.decompress(data))

    def read_df(self, key, index=None, sel=(), slc=slice(None)):
        """
        :param key: name of the structured dataset
        :param index: pandas index (or multi-index), possibly None
        :param sel: dictionary used to select subsets of the dataset
        :param slc: slice object to extract a slice of the dataset
        :returns: pandas DataFrame associated to the dataset
        """
        if key in self.hdf5:
            return self.hdf5.read_df(key, index, sel, slc)
        if self.parent:
            return self.parent.read_df(key, index, sel, slc)
        raise KeyError(key)

    def read_unique(self, key, field):
        """
        :param key: key to a dataset containing a structured array
        :param field: a field in the structured array
        :returns: sorted, unique values

        Works with chunks of 1M records
        """
        unique = set()
        dset = self.getitem(key)
        for slc in general.gen_slices(0, len(dset), 10_000_000):
            arr = numpy.unique(dset[slc][field])
            unique.update(arr)
        return sorted(unique)

    def sel(self, key, **kw):
        """
        Select a dataset with shape_descr. For instance
        dstore.sel('hcurves', imt='PGA', sid=2)
        """
        return hdf5.sel(self.getitem(key), kw)

    @property
    def metadata(self):
        """
        :returns: datastore metadata version, date, checksum as a dictionary
        """
        a = self.hdf5.attrs
        if 'aelo_version' in a:
            return dict(generated_by='AELO %s' % a['aelo_version'],
                        start_date=a['date'], checksum=a['checksum32'])
        else:
            return dict(
                generated_by='OpenQuake engine %s' % a['engine_version'],
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
                    filename=self.filename,
                    ppath=self.ppath)

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
