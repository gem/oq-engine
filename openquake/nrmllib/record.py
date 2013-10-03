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
A module to manage record extracted from CSV files, i.e. with fields
which are UTF-8 encoded strings.
"""

import os
import re
import csv
import abc
import zipfile
import cStringIO
import itertools
import operator
import collections
from abc import ABCMeta, abstractmethod
from openquake.nrmllib import InvalidFile


NAME = re.compile(r'[a-zA-Z_]\w*')


class Choice(object):
    def __init__(self, *choices):
        self.choices = choices

    def __call__(self, value):
        if not value in self.choices:
            raise ValueError('%r is not a valid choice in %s' % (
                             value, self.choices))


def namelist(text):
    names = text.split()
    if not names:
        raise ValueError('Got an empty name list')
    for name in names:
        if NAME.match(name) is None:
            raise ValueError('%r is not a valid name' % name)
    return names


class Field(object):
    _counter = itertools.count()

    def __init__(self, converter, key=False, name='noname', default=''):
        self.converter = converter
        self.key = key
        self.name = name
        self.default = default
        self.ordinal = self._counter.next()


def extractfields(dic):
    fields = []
    for n, v in dic.iteritems():
        if isinstance(v, Field):
            v.name = n
            fields.append(v)
    return sorted(fields, key=operator.attrgetter('ordinal'))


class MetaRecord(abc.ABCMeta):
    def __new__(mcl, name, bases, dic):
        fields = sum((extractfields(vars(base)) for base in bases), [])
        fields.extend(extractfields(dic))
        fieldnames = [f.name for f in fields]
        name2index = dict((n, i) for i, n in enumerate(fieldnames))
        keyindices = [name2index[f.name] for f in fields if f.key] or [0]
        if '__init__' not in dic:
            dic['__init__'] = mcl.mkinit(fieldnames)
        if 'name2index' not in dic:
            dic['name2index'] = name2index
        if 'fields' not in dic:
            dic['fields'] = fields
        if 'ntuple' not in dic:
            dic['ntuple'] = collections.namedtuple(name, fieldnames)
        if 'keygetter' not in dic:
            dic['keygetter'] = operator.itemgetter(*keyindices)
        return super(MetaRecord, mcl).__new__(mcl, name, bases, dic)

    @staticmethod
    def mkinit(fieldnames):
        fields = ', '.join(fieldnames)
        defaults = ', '.join("%s=''" % f for f in fieldnames)
        templ = '''def __init__(self, %s):
        self.row = [%s]
        self.init()''' % (defaults, fields)
        dic = {}
        exec(templ, dic)
        return dic['__init__']

    def keyfunc(cls, fieldname):
        """
        Returns the function to use in sorting; assume there are no
        invalid records.
        """
        index = cls.name2index[fieldname]
        converter = cls.fields[index].converter
        return lambda self: converter(self[index])

    @property
    def fieldnames(cls):
        return [f.name for f in cls.fields]


class Record(collections.Sequence):
    """
    Assume the inner data are UTF-8 encoded strings
    """
    __metaclass__ = MetaRecord

    def init(self):
        pass

    def keytuple(self):
        return self.__class__.keygetter(self)

    def is_valid(self):
        return all(self.check_valid())

    def check_valid(self):
        status = {}
        for col, field in zip(self.row, self.fields):
            try:
                field.converter(col)
            except ValueError:
                status[field.name] = False
            else:
                status[field.name] = True
        return self.ntuple(**status)

    def convert(self):
        return self.ntuple(
            field.converter(col) for col, field in zip(self.row, self.fields))

    def __getitem__(self, i):
        if isinstance(i, str):
            i = self.name2index[i]
        return self.row[i]

    def __setitem__(self, i, value):
        if isinstance(i, str):
            i = self.name2index[i]
        self.fields[i].converter(value)
        self.row[i] = value

    def __delitem__(self, i):
        if isinstance(i, str):
            i = self.name2index[i]
        del self.row[i]

    def __len__(self):
        return len(self.fields)

    def __str__(self):
        return ','.join(self.row)


class Table(collections.MutableSequence):
    """
    In-memory table with a method is_valid
    """
    __metaclass__ = abc.ABCMeta

    @classmethod
    def create(cls, recordtype, csvstr):
        name = '__' + recordtype.__name__ + '.csv'
        archive = MemArchive((name, csvstr))
        reclist = list(CSVManager('', archive).read(recordtype))
        return cls(recordtype, reclist)

    def __init__(self, recordtype, records):
        self.recordtype = recordtype
        self.key2index = {}
        self.records = []
        self.index = 0
        for rec in records:
            self.append(rec)

    def to_nodedict(self):
        return collections.OrderedDict(
            (rec.keytuple(), rec.to_node()) for rec in self)

    def __getitem__(self, i):
        return self.records[i]

    def __setitem__(self, i, record):
        self.records[i] = record

    def __delitem__(self, i):
        del self.key2index[self[i].keytuple()]
        del self.records[i]

    def __len__(self):
        return len(self.records)

    def insert(self, position, rec):
        key = rec.keytuple()
        if key in self.key2index:
            raise KeyError('Duplicate key: %s' % str(key))
        self.records.append(rec)
        self.key2index[key] = self.index
        self.index += 1

    def getrecord(self, *key):
        return self[self.key2index[key]]

    def is_valid(self):
        is_valid = all(rec.is_valid() for rec in self)
        if not is_valid:
            return False
        # check unique keys for instance
        keyset = set()
        for i, rec in enumerate(self.records):
            key = rec.getkey()
            if key in keyset:
                return False
                raise KeyError('At row %s: %s is duplicated' %
                               (i, key))
            else:
                keyset.add(key)
        return True

    def __str__(self):
        return '\n'.join(map(str, self))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name, self.recordtype.__name__)


class FileObject(object):
    """
    A named reusable cStringIO for reading, useful for the tests
    """
    def __init__(self, name, bytestring):
        self.name = name
        self.bytestring = bytestring
        self.io = cStringIO.StringIO(bytestring)

    def close(self):
        self.io = cStringIO.StringIO(self.bytestring)

    def __iter__(self):
        return self

    def next(self):
        return self.io.next()

    def readline(self):
        return self.io.readline()

    def read(self, n=-1):
        return self.io.read(n)

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
        try:
            return self.dic[name]
        except KeyError:
            raise NotInArchive(name)

    def extract_filenames(self, prefix=''):
        return [f for f in self.dic if f.startswith(prefix)]


class CSVManager(object):
    def __init__(self, prefix, archive):
        self.prefix = prefix
        self.archive = archive
        self.rt2reader = {}
        self.rt2writer = {}
        self.rt2file = {}

    def get_all(self, recordmodule):
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
            recordtype = getattr(recordmodule, recordcsv[:-4], None)
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
