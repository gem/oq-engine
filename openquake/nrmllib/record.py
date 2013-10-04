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
import re
import abc
import inspect
import itertools
import operator
import collections


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


class Unique(object):
    def __init__(self, *indices):
        assert len(set(indices)) == len(indices), 'Duplicates in %s!' % indices
        self.indices = list(indices)  # set by MetaRecord
        self.name = 'unique'  # set by MetaRecord

    def __get__(self, rec, recordtype):
        if rec is None:  # called from the record class
            return self
        return tuple(rec[f] for f in self.indices)


class Field(object):
    _counter = itertools.count()

    def __init__(self, converter, key=False, name='noname', default=''):
        self.converter = converter
        self.key = key
        self.name = name
        self.default = default
        self.ordinal = self._counter.next()

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class MetaRecord(abc.ABCMeta):
    def __new__(mcl, name, bases, dic):
        fields = []
        for base in bases:
            fields.extend(getattr(base, 'fields', []))
        for n, v in dic.iteritems():
            if isinstance(v, Field):
                v.name = n
                fields.append(v)
        fields.sort(key=operator.attrgetter('ordinal'))
        fieldnames = [f.name for f in fields]
        name2index = dict((n, i) for i, n in enumerate(fieldnames))
        keyindices = [name2index[f.name] for f in fields if f.key] or [0]

        # unique constraints
        for n, v in dic.iteritems():
            if isinstance(v, Unique):
                for i, index in enumerate(v.indices):
                    if isinstance(index, str):
                        v.name = n
                        v.indices[i] = name2index[index]

        if '__init__' not in dic:
            dic['__init__'] = mcl.mkinit(fieldnames)
        if 'name2index' not in dic:
            dic['name2index'] = name2index
        if 'fields' not in dic:
            dic['fields'] = fields
        if 'ntuple' not in dic:
            dic['ntuple'] = collections.namedtuple(name, fieldnames)
        if 'pkey' not in dic:
            dic['pkey'] = Unique(*keyindices)
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
        """To override for post-initialization operations"""

    def is_valid(self):
        """True is all columns are valid"""
        return all(self.check_valid())

    def check_valid(self):
        """Returns a namedtuple of booleans, one for each column"""
        status = {}
        for col, field in zip(self.row, self.fields):
            try:
                field.converter(col)
            except ValueError:
                status[field.name] = False
            else:
                status[field.name] = True
        return self.ntuple(**status)

    def cast(self):
        """Cast the record into a namedtuple by casting all of the columns"""
        return self.ntuple._make(
            field.converter(col) for col, field in zip(self.row, self.fields))

    def __getitem__(self, i):
        """Return the column 'i', where 'i' can be an integer or a string"""
        if isinstance(i, str):
            i = self.name2index[i]
        return self.row[i]

    def __setitem__(self, i, value):
        """
        Set the column 'i', where 'i' can be an integer or a name.
        If the value is invalid, raise a ValueError.
        """
        if isinstance(i, str):
            i = self.name2index[i]
        self.fields[i].converter(value)
        self.row[i] = value

    def __delitem__(self, i):
        """Delete the column 'i', where 'i' can be an integer or a string"""
        if isinstance(i, str):
            i = self.name2index[i]
        del self.row[i]

    def __len__(self):
        """The number of columns in the record"""
        return len(self.fields)

    def __str__(self):
        """A CSV representation of the record"""
        return ','.join(self.row)


class Table(collections.MutableSequence):
    """
    In-memory table storing a sequence of record objects.
    Primary key and unique constraints are checked at insertion time.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, recordtype, records):
        self.recordtype = recordtype
        self.unique = []
        for n, v in inspect.getmembers(
                recordtype, lambda v: isinstance(v, Unique)):
            setattr(self, '%s_dict' % v.name, {})
            self.unique.append(v)
        self.records = []
        for rec in records:
            self.append(rec)

    def to_nodedict(self):
        return collections.OrderedDict(
            (rec.pkey, rec.to_node()) for rec in self)

    def __getitem__(self, i):
        return self.records[i]

    def __setitem__(self, i, record):
        self.records[i] = record

    def __delitem__(self, i):
        for descr in self.unique:
            key = descr.__get__(self.records[i], self.recordtype)
            del getattr(self, '%s_dict' % descr.name)[key]
        del self.records[i]

    def __len__(self):
        return len(self.records)

    def insert(self, position, rec):
        for descr in self.unique:
            dic = getattr(self, '%s_dict' % descr.name)
            key = descr.__get__(rec, self.recordtype)
            try:
                rec = dic[key]
            except KeyError:  # not inserted yet
                dic[key] = rec
            else:
                msg = []
                for k, i in zip(key, descr.indices):
                    msg.append('%s=%s' % (rec.fields[i].name, k))
                raise KeyError('%s:%d:Duplicate record:%s' %
                               (self.recordtype.__name__, position,
                                ','.join(msg)))
        self.records.append(rec)

    def getrecord(self, *pkey):
        return self.pkey_dict[pkey]

    def is_valid(self):
        return all(rec.is_valid() for rec in self)

    def __str__(self):
        return '\n'.join(map(str, self))

    def __eq__(self, other):
        assert len(self) == len(other)
        return all(x == y for x, y in zip(self, other))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name, self.recordtype.__name__)
