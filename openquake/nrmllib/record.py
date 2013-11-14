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
    id = record.Field(int)
    lon = record.Field(float)
    lat = record.Field(float)
    pkey = Unique('id')
    unique = Unique('lon', 'lat')

The argument of the Field constructor is a callable taking in input a
UTF8-encoded string and returning a Python object or raising a
ValueError if the string is invalid.
"""

import abc
import inspect
import itertools
import operator
import collections


class InvalidRecord(Exception):
    """
    Exception raised when casting a record fails. It provides the attributes
    .record (the failing record) and .errorlist which is a list of pair
    (fieldname, errormessage), where fieldname is the name of the column
    that could not be casted and errormessage is the relative error message.
    """

    def __init__(self, record, errorlist):
        self.fname = None
        self.rowno = 0
        self.record = record
        self.errorlist = errorlist

    def __str__(self):
        where = self.fname or self.record.__class__.__name__
        msg = []
        for field, errmsg in self.errorlist:
            colno = self.record._name2index[field]
            msg.append('%s[%s]: %d,%d: %s' %
                       (where, field, self.rowno, colno, errmsg))
        return '\n'.join(msg)


class ForeignKeyError(Exception):
    pass


class Unique(object):
    """
    Descriptor used to describe unique constraints on a record type.
    In the example of a Location record

    class Location(record.Record):
        id = record.Field(int)
        lon = record.Field(float)
        lat = record.Field(float)
        pkey = Unique('id')
        unique = Unique('lon', 'lat')

    loc.unique_fields returns the tuple (lon, lat), as UTF8-encoded strings.
    """
    def __init__(self, *names):
        assert len(set(names)) == len(names), 'Duplicates in %s!' % names
        self.names = names
        self.recordtype = None
        self.dict = None

    def __get__(self, rec, recordtype):
        if rec is None:  # called from the record class
            unique = Unique(*self.names)
            unique.recordtype = recordtype
            unique.dict = {}
            return unique
        return tuple(rec[f] for f in self.names)

    def __repr__(self):
        return '<Unique%s>' % str(self.names)


class ForeignKey(object):
    """
    Descriptor used to describe unique constraints on a record type.
    """
    def __init__(self, unique, *names):
        self.unique = unique
        self.names = names
        self.recordtype = None

    def __get__(self, rec, recordtype):
        if rec is None:  # called from the record class
            fkey = ForeignKey(self.unique, *self.names)
            fkey.recordtype = recordtype
            return fkey
        return tuple(rec[f] for f in self.names)

    def __repr__(self):
        return '<ForeignKey%s>' % str(self.names)


class Field(object):
    """
    Descriptor used to describe record fields. A Field instance has

    - a cast function which is able to convert a UTF-8 string into a Python
      object;
    - a name attribute with the name of the field
    - a default attribute with the default string value of the field
    - an ordinal attribute keeping track of the order of definition
    """
    _counter = itertools.count()

    def __init__(self, cast, name='noname', default=''):
        self.cast = cast
        self.name = name
        self.default = default
        self.ordinal = self._counter.next()

    def __get__(self, rec, rectype):
        if rec is None:
            return lambda rec: rec[self.name].cast()
        return rec[self.name].cast()

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class MetaRecord(abc.ABCMeta):
    """
    Metaclass for record types. The metaclass is in charge of
    processing the Field objects at class definition time. In particular
    it sets their .name attribute.
    It defines on the record subclasses the ``__init__`` method
    and the attributes ``_name2index``, ``fields``,
    ``_ntuple``. Moreover it defines the metaclass method
    ``__len__`` and the metaclass property ``fieldnames``.
    """
    _counter = itertools.count()
    _reserved_names = set('fields fieldnames _name2index _ntuple _ordinal')

    def __new__(mcl, name, bases, dic):
        for nam in dic:
            if nam in mcl._reserved_names:
                raise NameError('Cannot instantiate %s because the name %s'
                                ' is reserved' % (name, nam))
        fields = []
        for base in bases:
            fields.extend(getattr(base, 'fields', []))
        for n, v in dic.iteritems():
            if isinstance(v, Field):
                v.name = n
                fields.append(v)
        fields.sort(key=operator.attrgetter('ordinal'))
        fieldnames = []
        _name2index = {}
        for i, f in enumerate(fields):
            fieldnames.append(f.name)
            _name2index[f.name] = i

        # normal an user should not define the following fields in
        # a client class, since they are defined by the metaclass
        # a savvy user however can provide her own implementations
        # and they will have the precedence against the default ones
        if '__init__' not in dic:
            dic['__init__'] = mcl.mkinit(fieldnames)
        if '_name2index' not in dic:
            dic['_name2index'] = _name2index
        if 'fields' not in dic:
            dic['fields'] = fields
        if '_ntuple' not in dic:
            dic['_ntuple'] = collections.namedtuple(name, fieldnames)
        dic['_ordinal'] = mcl._counter.next()
        cls = super(MetaRecord, mcl).__new__(mcl, name, bases, dic)
        if name != 'Record':
            cls.pkey  # raise an AttributeError if pkey is not defined
        return cls

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

    def get_items(cls, descriptor_cls):
        """
        Return the instances of descriptor_cls defined in cls as pairs
        (name, descriptor)
        """
        return inspect.getmembers(cls, lambda m: isinstance(m, descriptor_cls))

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
    convertername = 'Converter'

    def init(self):
        """To override for post-initialization operations"""

    def is_valid(self, i=None):
        """
        `i` can be an integer, a field name, or None: if `i` is None,
        check all the fields; if `i` is a file name convert it into an integer
        by looking at the _name2index dictionary and check the corresponding
        field.
        """
        if i is None:
            return all(self.is_valid(i) for i in range(len(self)))
        if isinstance(i, str):
            i = self._name2index[i]
        try:
            self.fields[i].cast(self[i])
        except ValueError:
            return False
        return True

    def cast(self):
        """Return a casted (namedtuple, InvalidRecord) pair"""
        cols = []
        errs = []
        for col, field in zip(self.row, self.fields):
            try:
                cols.append(field.cast(col))
            except ValueError as e:
                errs.append((field.name, str(e)))
        if errs:
            return None, InvalidRecord(self, errs)
        else:
            return self._ntuple._make(cols), None

    def to_tuple(self):
        """
        Cast the record to a namedtuple with the right types or raise
        an InvalidRecord exception.
        """
        tup, exc = self.cast()
        if exc:
            raise exc
        return tup

    def to_node(self):
        """Implement this if you want to convert records into Node objects"""
        raise NotImplementedError

    def __getitem__(self, i):
        """Return the field 'i', where 'i' can be an integer or a field name"""
        if isinstance(i, str):
            i = self._name2index[i]
        return self.row[i]

    def __setitem__(self, i, value):
        """
        Set the column 'i', where 'i' can be an integer or a field name.
        If the value is invalid, raise a ValueError.
        """
        if isinstance(i, str):
            i = self._name2index[i]
        self.fields[i].cast(value)
        self.row[i] = value

    def __delitem__(self, i):
        """
        Delete the column 'i', where 'i' can be an integer or a field name
        """
        if isinstance(i, str):
            i = self._name2index[i]
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


def nodedict(records):
    """
    Convert a sequence of records into an OrderedDict
    rec.pkey -> rec.to_node()
    """
    return collections.OrderedDict(
        (rec.pkey, rec.to_node()) for rec in records)


def find_invalid(recorditer):
    """
    Yield the InvalidRecord exceptions found in the record iterator.
    To find the first record only call

      find_invalid(records).next()
    """
    for rowno, rec in enumerate(recorditer):
        row, exc = rec.cast()
        if exc:
            exc.rowno = rowno
            yield exc


class Table(collections.MutableSequence):
    """
    In-memory table storing a sequence of record objects.
    Unique constraints are checked at insertion time.
    """
    def __init__(self, recordtype, records):
        self.recordtype = recordtype
        self._unique_fields = []
        self._records = []
        for n, v in recordtype.get_items(Unique):
            self._unique_fields.append(v)
        for rec in records:
            self.append(rec)

    def __getitem__(self, i):
        """Return the i-th record"""
        return self._records[i]

    def __setitem__(self, i, record):
        """Set the i-th record"""
        self._records[i] = record

    def __delitem__(self, i):
        """Delete the i-th record"""
        # i must be an integer, not a range
        for descr in self._unique_fields:
            key = descr.__get__(self._records[i], self.recordtype)
            del descr.dict[key]
        del self._records[i]

    def __len__(self):
        """The number of records stored in the table"""
        return len(self._records)

    def insert(self, position, rec):
        """
        Insert a record in the table, at the given position index.
        This is called by the .append method, with position equal
        to the record length. Trying to insert a duplicated record
        (in terms of unique constraints, including the primary
        key) raises a KeyError.
        """
        for descr in self._unique_fields:
            key = descr.__get__(rec, self.recordtype)
            try:
                rec = descr.dict[key]
            except KeyError:  # not inserted yet
                descr.dict[key] = rec
            else:
                msg = []
                for k, name in zip(key, descr.names):
                    msg.append('%s=%s' % (name, k))
                raise KeyError('%s:%d:Duplicated record:%s' %
                               (self.recordtype.__name__, position,
                                ','.join(msg)))
        self._records.append(rec)

    def getrecord(self, *pkey):
        """
        Extract the record specified by the given primary key.
        Raise a KeyError if the record is missing from the table.
        """
        return self.pkey.dict[pkey]

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
        return '<%s %s>' % (self.__class__.__name__, self.recordtype.__name__)


class TableSet(object):
    """
    A set of tables associated to the same converter
    """
    def __init__(self, converter):
        self.tables = []
        for rt in converter.recordtypes():
            tbl = Table(rt, [])
            self.tables.append(tbl)
            setattr(self, rt.__name__, tbl)

    def insert(self, rec):
        """
        Insert a record in the correct table in the TableSet, by
        checking the ForeignKey constraints, if any.
        """
        rectype = rec.__class__
        for fkname, fkey in rectype.get_items(ForeignKey):
            target = fkey.unique.recordtype.__name__
            udict = getattr(getattr(self, target), '%s_dict' % fkey.unique)
            fkvalues = fkey.__get__(rec, rectype)
            if not fkvalues in udict:
                raise ForeignKeyError(fkvalues)
        tbl = getattr(self, rectype.___name__)
        tbl.insert(rec)
