#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

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
import csv
import inspect
import zipfile
import StringIO
import itertools
import collections
from abc import ABCMeta, abstractmethod

from openquake.nrmllib.record import Table
from openquake.nrmllib.node import node_to_nrml, node_from_nrml
from openquake.nrmllib import InvalidFile, records, converter


class FileObject(object):
    """
    A named reusable StringIO for reading and writing, useful for the tests
    """
    def __init__(self, name, bytestring):
        self.name = name
        self.bytestring = bytestring
        self.io = StringIO.StringIO(bytestring)

    def close(self):
        self.io = StringIO.StringIO(self.io.getvalue())

    def __iter__(self):
        return self

    def next(self):
        return self.io.next()

    def readline(self):
        return self.io.readline()

    def read(self, n=-1):
        return self.io.read(n)

    def write(self, data):
        self.io.write(data)

    def flush(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        self.close()


class FakeWriter(object):
    def __init__(self, archive, name):
        self.archive = archive
        self.name = name

    def write(self, data):
        print 'Writing', self.name, data
        self.archive.writestr(self.name, data)

    def flush(self):
        pass

    def close(self):
        pass


class NotInArchive(Exception):
    pass


class ArchiveABC(object):
    __metaclass__ = ABCMeta

    opened = []

    def open(self, name, mode='r'):
        #opened = set(f.name for f in self.opened)
        #if name in opened:
        #    raise RuntimeError(
        #        'Trying to open a file already opened: %r' % name)
        f = self._open(name, mode)
        self.opened.add(f)
        return f

    @abstractmethod
    def _open(self, name, mode):
        pass

    @abstractmethod
    def extract_filenames(self, prefix=''):
        pass

    def close(self):
        for f in self.opened:
            f.close()

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.extract_filenames())


class ZipArchive(ArchiveABC):
    def __init__(self, zipname, mode='r'):
        self.zip = zipfile.ZipFile(zipname, mode)
        self.opened = set()

    def _open(self, name, mode):
        if mode in ('w', 'w+', 'r+'):
            f = FakeWriter(self.zip, name)
        else:
            f = self.zip.open(name, mode)
        return f

    def extract_filenames(self, prefix=''):
        return set(i.filename for i in self.zip.infolist()
                   if i.filename.startswith(prefix))


class DirArchive(ArchiveABC):
    def __init__(self, dirname, mode='r'):
        self.dirname = dirname
        self.mode = mode
        if mode in ('w', 'w+', 'r+') and not os.path.exists(dirname):
            os.mkdir(dirname)
        self.opened = set()

    def _open(self, name, mode):
        return open(os.path.join(self.dirname, name), mode)

    def extract_filenames(self, prefix=''):
        return [f for f in os.listdir(self.dirname) if f.startswith(prefix)]


class MemArchive(ArchiveABC):
    def __init__(self, items, mode='r'):
        self.dic = {}
        for name, csvstr in items:
            self.add(name, csvstr)
        self.opened = set()

    def add(self, name, csvstr):
        self.dic[name] = FileObject(name, csvstr)

    def _open(self, name, mode='r'):
        if mode in ('w', 'w+', 'r+'):
            self.dic[name] = f = FileObject(name, '')
            return f
        try:
            return self.dic[name]
        except KeyError:
            raise NotInArchive(name)

    def extract_filenames(self, prefix=''):
        return [f for f in self.dic if f.startswith(prefix)]


def create_table(recordtype, csvstr):
    name = '__' + recordtype.__name__ + '.csv'
    archive = MemArchive((name, csvstr))
    reclist = list(CSVManager('', archive).read(recordtype))
    return Table(recordtype, reclist)


class CSVManager(object):

    @classmethod
    def getconverters(cls, archive):
        """
        Returns a list of Converter instances, one for each file group
        in the underlying archive. Each converter has its own manager
        with the right prefix.
        """
        converters = {}  # name->converter dictionary
        cc = {}  # name -> converter class dictionary
        for name, value in vars(converter).iteritems():
            if inspect.isclass(value) and issubclass(
                    value, converter.Converter):
                cc[name] = value
        for fname in sorted(archive.extract_filenames()):
            try:
                prefix, recordcsv = fname.split('__')
            except ValueError:
                continue
            if not recordcsv.endswith('.csv'):
                continue
            recordtype = getattr(records, recordcsv[:-4], None)
            if recordtype is None:
                continue
            if not prefix in converters:
                converters[prefix] = cc[recordtype._tag](cls(prefix, archive))
        return converters.values()

    def __init__(self, prefix, archive):
        self.prefix = prefix
        self.archive = archive
        self.rt2reader = {}
        self.rt2writer = {}
        self.rt2file = {}

    def getconverter(self):
        """
        Extract the appropriate converter to convert the files in
        the underlying archive. Raise an error is no converter is
        found (this happens if there are no files following the
        naming conventions).
        """
        converters = self.getconverters(self.archive)
        if not converters:
            raise RuntimeError(
                'Could not determine the right converter '
                'from files %s' % self.archive.extract_filenames())
        elif len(converters) > 2:
            raise RuntimeError(
                'Found %d converters, expected 1' % len(converters))
        return converters[0]

    def convert_to_node(self):
        """
        Convert the CSV files in the archive with the given prefix
        into a Node object
        """
        return self.getconverter().csv_to_node()

    def convert_to_nrml(self, out=None):
        """
        From CSV files with the given prefix to a single .xml file
        """
        conv = self.getconverter()
        with conv.man:
            out = out or conv.man.archive.open(conv.man.prefix + '.xml', 'w')
            node_to_nrml(conv.csv_to_node(), out)
        return out.name

    def convert_from_nrml(self, fname):
        """
        Populate the underlying archive with CSV files extracted from the
        given XML file.
        """
        assert fname.endswith('.xml'), fname
        return self.convert_from_node(node_from_nrml(fname)[0], fname[:-4])

    def convert_from_node(self, node, prefix=''):
        """
        Populate the underlying archive with CSV files extracted from the
        given Node object.
        """
        name = node.tag[0].upper() + node.tag[1:]
        clsname = name[:-5] if name.endswith('Model') else name
        man = self.__class__(prefix, self.archive)
        conv = getattr(converter, clsname)(man)
        with man:
            for rec in conv.node_to_records(node):
                man.write(rec)  # automatically writes the header
        return [f.name for f in man.archive.opened]

    def get_all(self):
        """
        Returns a dictionary of lists, {tag: [recordtype]}
        """
        dd = collections.defaultdict(list)
        for fname in sorted(self.archive.extract_filenames(self.prefix)):
            try:
                name, recordcsv = fname.split('__')
            except ValueError:
                continue
            if not recordcsv.endswith('.csv'):
                continue
            recordtype = getattr(records, recordcsv[:-4], None)
            if recordtype is None:
                continue
            dd[recordtype._tag].append(recordtype)
        return dd

    def read(self, recordtype):
        reader = self.rt2reader.get(recordtype)
        if reader is None:
            fname = '%s__%s.csv' % (self.prefix, recordtype.__name__)
            self.rt2file[recordtype] = f = self.archive.open(fname, 'r')
            self.rt2reader[recordtype] = reader = csv.reader(f)
            header = reader.next()  # skip header
            if header != recordtype.fieldnames:
                raise InvalidFile('%s: line 1: got %s as header, expected %s' %
                                  (fname, header, recordtype.fieldnames))
        for row in reader:
            yield recordtype(*row)

    def groupby(self, keyfields, recordtype):
        keyindices = [recordtype.name2index[k] for k in keyfields]
        return itertools.groupby(
            self.read(recordtype), lambda rec: [rec[i] for i in keyindices])

    def readtable(self, recordtype):
        return Table(recordtype, list(self.read(recordtype)))

    def write(self, record):
        rt = type(record)  # record type
        writer = self.rt2writer.get(rt)
        if writer is None:
            fname = '%s__%s.csv' % (self.prefix, rt.__name__)
            self.rt2file[rt] = f = self.archive.open(fname, 'w')
            self.rt2writer[rt] = writer = csv.writer(f)
            writer.writerow(rt.fieldnames)
        writer.writerow(record)

    def __enter__(self):
        self.rt2reader = {}
        self.rt2writer = {}
        self.rt2file = {}
        self.archive.opened = set()
        return self

    def __exit__(self, etype, exc, tb):
        self.archive.close()
