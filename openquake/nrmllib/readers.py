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
"""
A library of Reader classes to read flat data from .csv + .json files
"""

import os
import csv
import itertools
import warnings
import cStringIO
from openquake.nrmllib import InvalidFile
from openquake.nrmllib.node import node_from_xml


def _make_readers(cls, container, fnames):
    """
    Given a list of filenames, instantiates several readers and yields
    them in groups. Raise a warning for invalid files.
    """
    def getprefix(f):
        return f.rsplit('.', 1)[0]
    fnames = sorted(f for f in fnames if f.endswith(('.csv', '.json')))
    readers = []
    for name, group in itertools.groupby(fnames, getprefix):
        gr = list(group)
        if len(gr) == 2:  # pair (.json, .csv)
            try:
                readers.append(cls(container, name))
            except Exception as e:
                # the reader could not be instantiated, due to an invalid file
                warnings.warn(str(e))

    def getgroupname(reader):
        """Extract the groupname for readers named <groupname>__<subname>"""
        return reader.name.rsplit('__', 1)[0]
    for name, readergroup in itertools.groupby(readers, getgroupname):
        yield name, list(readergroup)


class Reader(object):
    """
    Base class of all Readers.
    """
    def __init__(self, container, name):
        self.container = container
        self.name = name
        self.fieldnames = None  # set in read_fieldnames
        with self.openjson() as j:
            self.load_metadata(j)
        with self.opencsv() as c:
            self.check_fieldnames(c)

    def load_metadata(self, fileobj):
        try:
            self.metadata = node_from_xml(fileobj)
        except Exception as e:
            raise InvalidFile('%s:%s' % (fileobj.name, e))
        try:
            self.read_fieldnames()
        except Exception as e:
            raise InvalidFile('%s: could not extract fieldnames: %s' %
                              (fileobj.name, e))

    def read_fieldnames(self):
        from openquake.nrmllib import convert  # avoid cyclic imports
        getfields = getattr(convert, '%s_fieldnames' %
                            self.metadata.tag.lower())
        self.fieldnames = getfields(self.metadata)

    def check_fieldnames(self, fileobj):
        try:
            fieldnames = csv.DictReader(fileobj).fieldnames
        except ValueError:
            raise InvalidFile(self.name + '.csv')
        if fieldnames is None or any(
                f1.lower() != f2.lower()
                for f1, f2 in zip(fieldnames, self.fieldnames)):
            raise ValueError(
                'According to %s.json the field names should be '
                '%s, but the header in %s.csv says %s' % (
                    self.name, self.fieldnames,
                    self.name, fieldnames))

    def __getitem__(self, index):
        with self.opencsv() as f:
            reader = csv.DictReader(f)
            reader.fieldnames  # read the fieldnames from the header
            if isinstance(index, int):
                # skip the first lines
                for i in xrange(index):
                    next(f)
                return next(reader)
            else:  # slice object
                # skip the first lines
                for i in xrange(index.start):
                    next(f)
                rows = []
                for i in xrange(index.stop - index.start):
                    rows.append(next(reader))
                return rows

    def __iter__(self):
        with self.opencsv() as f:
            for row in csv.DictReader(f):
                yield row

    def __len__(self):
        return sum(1 for line in self.opencsv()) - 1  # skip header

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class FileReader(Reader):
    """
    Read from a couple of files .json and .csv
    """
    @classmethod
    def getall(cls, directory, fnames=None):
        if fnames is None:
            fnames = os.listdir(directory)
        return _make_readers(cls, directory, fnames)

    def opencsv(self):
        return open(os.path.join(self.container, self.name + '.csv'))

    def openjson(self):
        return open(os.path.join(self.container, self.name + '.json'))


class ZipReader(Reader):
    """
    Read from .zip archives/
    """
    @classmethod
    def getall(cls, archive, fnames=None):
        if fnames is None:
            fnames = [i.filename for i in archive.infolist()]
        return _make_readers(cls, archive, fnames)

    def opencsv(self):
        return self.container.open(self.name + '.csv')

    def openjson(self):
        return self.container.open(self.name + '.json')


class FileObject(object):
    """A named cStringIO for reading"""
    def __init__(self, name, bytestring):
        self.name = name
        self.io = cStringIO.StringIO(bytestring)

    def __iter__(self):
        return iter(self.io)

    def readline(self):
        return self.io.readline()

    def read(self, n=-1):
        return self.io.read(n)

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        pass


class StringReader(Reader):
    """
    Read data from the given strings, not from the file system.
    Assume the strings are UTF-8 encoded. The intended usage is
    for unittests.
    """
    def __init__(self, name, json_str, csv_str):
        self.name = name
        self.json_str = json_str
        self.csv_str = csv_str
        Reader.__init__(self, None, name)

    def opencsv(self):
        return FileObject(self.name + '.csv', self.csv_str)

    def openjson(self):
        return FileObject(self.name + '.json', self.json_str)


class RowReader(Reader):
    def __init__(self, name, metadata, rows):
        self.name = name
        self.metadata = metadata
        self.read_fieldnames()
        self.rows = rows

    def __iter__(self):
        for row in self.rows:
            yield dict(zip(self.fieldnames, row))
