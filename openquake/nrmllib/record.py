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
A module to define records extracted from UTF8-encoded CSV files.
Client code should subclass the record class and define the
record fields as follows:

from openquake.nrmllib import record

class Location(record.Record):
    id = record.Field(int, key=True)
    lon = record.Field(float)
    lat = record.Field(float)
    unique = Unique('lon', 'lat')

The argument of the Field constructor is a converter, i.e. a callable
taking in input a UTF8-encoded string and returning a Python object
or raising a ValueError if the string is invalid.
"""

import abc
import inspect
import itertools
import operator
import collections


class Unique(object):
    """
    Descriptor used to describe unique constraints on a record type.
    In the example of a Location record, loc.unique returns the tuple
    (lon, lat), as UTF8-encoded strings.
    """
    def __init__(self, *indexes):
        assert len(set(indexes)) == len(indexes), 'Duplicates in %s!' % indexes
        self.indexes = list(indexes)  # set by MetaRecord
        self.name = 'unique'  # set by MetaRecord

    def __get__(self, rec, recordtype):
        if rec is None:  # called from the record class
            return self
        return tuple(rec[f] for f in self.indexes)


class Field(object):
    """
    Descriptor use to describe record fields.
    In the example of a Location record, loc.lon and loc.lat return
    longitude and latitude respectively, as floats.
    """
    _counter = itertools.count()

    def __init__(self, converter, key=False, name='noname', default=''):
        self.converter = converter
        self.key = key
        self.name = name
        self.default = default
        self.ordinal = self._counter.next()
        self.index = 0  # set by MetaRecord

    def __get__(self, rec, rectype):
        if rec is None:  # sorting function
            return lambda rec: rec.converter(rec[self.index])
        return rec.converter(rec[self.index])

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class MetaRecord(abc.ABCMeta):
    """
    Metaclass for record types. The metaclass is in charge of
    processing the Field objects at class definition time. In particular
    it sets their .name and .index attributes. It also processes the
    Unique constraints, by setting their .name and .indexes attributes.
    It defines on the record subclasses the ``__init__`` method, the
    ``pkey`` property and the attributes ``name2index``, ``fields``,
    ``ntuple``. Moreover it defines the metaclass method
    ``__len__`` and the metaclass property ``fieldnames``.
    """
    def __new__(mcl, name, bases, dic):
        fields = []
        for base in bases:
            fields.extend(getattr(base, 'fields', []))
        for n, v in dic.iteritems():
            if isinstance(v, Field):
                v.name = n
                fields.append(v)
        fields.sort(key=operator.attrgetter('ordinal'))
        fieldnames = []
        name2index = {}
        keyindexes = []
        for i, f in enumerate(fields):
            fieldnames.append(f.name)
            name2index[f.name] = f.index = i
            if f.key:
                keyindexes.append(i)
        keyindexes = keyindexes or [0]

        # unique constraints
        for n, v in dic.iteritems():
            if isinstance(v, Unique):
                for i, index in enumerate(v.indexes):
                    if isinstance(index, str):
                        v.name = n
                        v.indexes[i] = name2index[index]

        if '__init__' not in dic:
            dic['__init__'] = mcl.mkinit(fieldnames)
        if 'name2index' not in dic:
            dic['name2index'] = name2index
        if 'fields' not in dic:
            dic['fields'] = fields
        if 'ntuple' not in dic:
            dic['ntuple'] = collections.namedtuple(name, fieldnames)
        if 'pkey' not in dic:
            dic['pkey'] = Unique(*keyindexes)
        return super(MetaRecord, mcl).__new__(mcl, name, bases, dic)

    @staticmethod
    def mkinit(fieldnames):
        """Build the __init__ method for record subclasses"""
        fields = ', '.join(fieldnames)
        defaults = ', '.join("%s=''" % f for f in fieldnames)
        templ = '''def __init__(self, %s):
        self.row = [%s]
        self.init()''' % (defaults, fields)
        dic = {}
        exec(templ, dic)
        return dic['__init__']

    @property
    def fieldnames(cls):
        """Returns the names of the fields defined in cls"""
        return [f.name for f in cls.fields]

    def __len__(cls):
        """Returns the number of fields defined in cls"""
        return len(cls.fields)


class Record(collections.Sequence):
    """
    The abstract base class for the record subclasses. It defines
    a number of methods, including an ``init`` method called by
    the ``__init__`` method and overridable for post-initialization
    operations. The ``__init__`` method defines a .row attribute
    with the contents of the record, stored as a UTF8-encoded string list.
    Records implements the Sequence interface and have a .cast()
    method, a .check_valid() method and a .is_valid() method.
    """
    __metaclass__ = MetaRecord

    def init(self):
        """To override for post-initialization operations"""

    def is_valid(self):
        """True if all fields are valid"""
        return all(self.check_valid())

    def check_valid(self):
        """Returns a namedtuple of booleans, one for each fields"""
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
        """Cast the record into a namedtuple by casting all of the field"""
        return self.ntuple._make(
            field.converter(col) for col, field in zip(self.row, self.fields))

    def to_node(self):
        """Implement this if you want to convert records into Node objects"""
        raise NotImplementedError

    def __getitem__(self, i):
        """Return the field 'i', where 'i' can be an integer or a field name"""
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

    def __eq__(self, other):
        """
        A record is equal to another sequence if they have the same
        length and content.
        """
        assert len(self) == len(other)
        return all(x == y for x, y in zip(self, other))

    def __ne__(self, other):
        """
        A record is different from another sequence if their lenghts
        are different or if the contents are different.
        """
        if len(self) != len(other):
            return True
        return not self == other

    def __len__(self):
        """The number of columns in the record"""
        return len(self.fields)

    def __str__(self):
        """A CSV representation of the record"""
        return ','.join(self.row)


class Table(collections.MutableSequence):
    """
    In-memory table storing a sequence of record objects.
    Primary key and unique constraints are checked at insertion time,
    by looking at the dictionaries <constraint-name>_dict.
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
        # i must be an integer, not a range
        for descr in self.unique:
            key = descr.__get__(self.records[i], self.recordtype)
            del getattr(self, '%s_dict' % descr.name)[key]
        del self.records[i]

    def __len__(self):
        return len(self.records)

    def insert(self, position, rec):
        """
        Insert a record in the table, at the given position index.
        This is called by the .append method, with position equal
        to the record length. Trying to insert a duplicated record
        (in terms of the unique constraints, including the primary
        key) raises a KeyError.
        """
        for descr in self.unique:
            dic = getattr(self, '%s_dict' % descr.name)
            key = descr.__get__(rec, self.recordtype)
            try:
                rec = dic[key]
            except KeyError:  # not inserted yet
                dic[key] = rec
            else:
                msg = []
                for k, i in zip(key, descr.indexes):
                    msg.append('%s=%s' % (rec.fields[i].name, k))
                raise KeyError('%s:%d:Duplicate record:%s' %
                               (self.recordtype.__name__, position,
                                ','.join(msg)))
        self.records.append(rec)

    def getrecord(self, *pkey):
        """
        Extract the record specified by the given primary key.
        Raise a KeyError if the record is missing from the table.
        """
        return self.pkey_dict[pkey]

    def is_valid(self):
        """True if all the records in the table are valid"""
        return all(rec.is_valid() for rec in self)

    def __str__(self):
        """CSV representation of the whole table"""
        return '\n'.join(map(str, self))

    def __eq__(self, other):
        """
        A table is equal to another sequence if they have the same
        length and content.
        """
        assert len(self) == len(other)
        return all(x == y for x, y in zip(self, other))

    def __ne__(self, other):
        """
        A table is different from another sequence if their lenghts
        are different or if the contents are different.
        """
        if len(self) != len(other):
            return True
        return not self == other

    def __repr__(self):
        """String representation of table displaying the record type name"""
        return '<%s %s>' % (self.__class__.__name, self.recordtype.__name__)
