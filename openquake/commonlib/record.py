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

# I am reinventing a database here; we should probably just use a database
# (for instance sqlite in memory) and an ORM. I am not happy (MS)
"""
A module to define records extracted from UTF8-encoded CSV files.
Client code should subclass the record class and define the
record fields as follows:

from openquake.commonlib import record

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
        self.name = None  # set by MetaRecord
        self.recordtype = None  # set by MetaRecord

    def __get__(self, rec, recordtype):
        if rec is None:
            return self
        return tuple(rec[f] for f in self.names)

    def __repr__(self):
        return '<Unique%s>' % str((self.recordtype,) + self.names)


class ForeignKey(object):
    """
    Descriptor used to describe unique constraints on a record type.
    """
    def __init__(self, unique, *names):
        self.unique = unique
        self.names = names
        self.name = None  # set by MetaRecord
        self.recordtype = None  # set by MetaRecord

    def __get__(self, rec, recordtype):
        if rec is None:
            return self
        return tuple(rec[f] for f in self.names)

    def __repr__(self):
        return '<ForeignKey%s>' % str((self.recordtype,) + self.names)


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
            return lambda rec: self.cast(rec[self.name])
        return self.cast(rec[self.name])

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
    _reserved_names = set(
        'fields fieldnames _name2index _ntuple _ordinal'.split())

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
        if '_constraints' not in dic:
            dic['_constraints'] = []
        return super(MetaRecord, mcl).__new__(mcl, name, bases, dic)

    def __init__(cls, name, bases, dic):
        if name != 'Record':
            cls.pkey  # raise an AttributeError if pkey is not defined
        for n, v in dic.iteritems():
            # make a bound copy of the unbound Unique and ForeignKey constraint
            if isinstance(v, Unique):
                unique = Unique(*v.names)
                unique.name = n
                unique.recordtype = cls
                setattr(cls, n, unique)
            elif isinstance(v, ForeignKey):
                fkey = ForeignKey(v.unique, *v.names)
                fkey.name = n
                fkey.recordtype = cls
                setattr(cls, n, fkey)

    @staticmethod
    def mkinit(fieldnames):
        """Build the __init__ method for record subclasses"""
        fields = ', '.join(fieldnames)
        defaults = ', '.join("%s=''" % f for f in fieldnames)
        templ = '''def __init__(self, %s):
        self.row = [%s]
        self.init()''' % (defaults, fields)
        dic = {}
        try:
            exec(templ, dic)
        except:
            print 'Could not build __init__ method, error in:', templ
            raise
        return dic['__init__']

    @property
    def fieldnames(cls):
        """Returns the names of the fields defined in cls"""
        return [f.name for f in cls.fields]

    def get_descriptors(cls, descriptor_cls):
        """
        Return the instances of descriptor_cls defined in cls.
        """
        return [v.__get__(None, cls) for v in vars(cls).values()
                if isinstance(v, descriptor_cls)]

    def add_check(cls, constraint):
        cls._constraints.append(constraint)

    def __len__(cls):
        """Returns the number of fields defined in cls"""
        return len(cls.fields)

    def __repr__(cls):
        return '<class %s>' % cls.__name__


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

    @classmethod
    def get_field_index(cls, field_name):
        """
        Return the index associated to the field name. As a special case,
        if field_name is an integer, return it
        """
        if isinstance(field_name, str):
            i = cls._name2index[field_name]
        else:
            i = field_name
        return i

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
            return all(self.is_valid(i) for i in range(len(self))) and all(
                constraint(self) for constraint in self._constraints)
        i = self.get_field_index(i)
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
        i = self.get_field_index(i)
        return self.row[i]

    def __setitem__(self, i, value):
        """
        Set the column 'i', where 'i' can be an integer or a field name.
        If the value is invalid, raise a ValueError.
        """
        i = self.get_field_index(i)
        self.fields[i].cast(value)
        self.row[i] = value

    def __delitem__(self, i):
        """
        Delete the column 'i', where 'i' can be an integer or a field name
        """
        i = self.get_field_index(i)
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


class UniqueData(object):
    """Table-related"""
    def __init__(self, table, unique):
        self.table = table
        self.unique = unique
        self.dict = {}

    @property
    def names(self):
        return self.unique.names


class Table(collections.MutableSequence):
    """
    In-memory table storing a sequence of record objects.
    Unique constraints are checked at insertion time.
    """
    def __init__(self, recordtype, records, ordinal=None):
        self.recordtype = recordtype
        self.ordinal = ordinal  # not None if part of a TableSet
        self._unique_data = dict(
            (u.name, UniqueData(self, u))
            for u in recordtype.get_descriptors(Unique))
        self._records = []
        for rec in records:
            self.append(rec)
        self.attr = {}  # a dictionary that can be populated by extension
        # modules, for instance a GUI could add visualization settings here

    @property
    def name(self):
        return 'table' + self.recordtype.__name__

    def __getitem__(self, i):
        """Return the i-th record"""
        return self._records[i]

    def __setitem__(self, i, new_record):
        """Set the i-th record"""
        # TODO: the fk dictionaries must be updated!
        # TODO: there is no unique check here!
        for name, unique in self._unique_data.iteritems():
            old_key = getattr(self._records[i], name)
            new_key = getattr(new_record, name)
            del unique.dict[old_key]
            unique.dict[new_key] = new_record
        self._records[i] = new_record

    def __delitem__(self, i):
        """Delete the i-th record"""
        # i must be an integer, not a range
        for name, unique in self._unique_data.iteritems():
            key = getattr(self._records[i], name)
            del unique.dict[key]
        del self._records[i]

    def insert(self, position, rec):
        """
        Insert a record in the table, at the given position index.
        This is called by the .append method, with position equal
        to the record length. Trying to insert a duplicated record
        (in terms of unique constraints, including the primary
        key) raises a KeyError.
        """
        for name, unique in self._unique_data.iteritems():
            key = getattr(rec, name)
            try:
                rec = unique.dict[key]
            except KeyError:  # not inserted yet
                unique.dict[key] = rec
            else:
                msg = []
                for k, name in zip(key, unique.names):
                    msg.append('%s=%s' % (name, k))
                raise KeyError('%s:%d:Duplicated record:%s' %
                               (self.recordtype.__name__, position,
                                ','.join(msg)))
        self._records.insert(position, rec)

    def getrecord(self, *pkey):
        """
        Extract the record specified by the given primary key.
        Raise a KeyError if the record is missing from the table.
        """
        return self._unique_data['pkey'].dict[pkey]

    def is_valid(self):
        """True if all the records in the table are valid"""
        return all(rec.is_valid() for rec in self)

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

    def __str__(self):
        """CSV representation of the whole table"""
        return '\n'.join(map(str, self))

    def __repr__(self):
        """String representation of table displaying the record type name"""
        return '<%s %d records>' % (self.recordtype.__name__, len(self))

    def __len__(self):
        """The number of records stored in the table"""
        return len(self._records)


class TableSet(object):
    """
    A set of tables associated to the same converter
    """
    def __init__(self, convertertype, tables=None):
        self.convertertype = convertertype
        self.name = convertertype.__name__
        self.tables = tables or [
            Table(rt, [], ordinal)
            for ordinal, rt in enumerate(convertertype.recordtypes())]
        self.fkdict = {}
        for tbl in self.tables:
            rt = tbl.recordtype
            setattr(self, 'table' + rt.__name__, tbl)
            for fkey in rt.get_descriptors(ForeignKey):
                target = fkey.unique
                target_name = 'table' + target.recordtype.__name__
                target_tbl = getattr(self, target_name)
                self.fkdict[fkey] = target_tbl._unique_data[target.name]

    def __getitem__(self, sliceobj):
        return self.__class__(self.convertertype, self.tables[sliceobj])

    def __iter__(self):
        """
        Returns only the nonempty tables
        """
        for table in self.tables:
            if len(table):
                yield table

    def check_fk(self, rec):
        """
        Check is a record has a companion record in the referenced table.
        """
        for fkey in rec.__class__.get_descriptors(ForeignKey):
            fkvalues = getattr(rec, fkey.name)
            if not fkvalues in self.fkdict[fkey].dict:
                raise ForeignKeyError(
                    'Missing record in table %s corresponding to the keys %s'
                    % (fkey.unique.recordtype.__name__, fkvalues))

    def insert(self, rec):
        """
        Insert a record in the correct table in the TableSet, by
        checking the ForeignKey constraints, if any.
        """
        self.check_fk(rec)
        tbl = getattr(self, 'table' + rec.__class__.__name__)
        tbl.append(rec)

    def insert_all(self, recs):
        """
        Insert a set of records in the right tables;
        may raise a ForeignKeyError.
        """
        for rec in recs:
            self.insert(rec)

    def delete(self, rec):
        """
        Delete a record by cascading on the ForeignKeys
        """
        raise NotImplementedError

    def to_node(self):
        """
        Convert the table set into a node object by using the converter class
        """
        return self.convertertype(self).to_node()

    def __repr__(self):
        return '<%s %s>' % (self.name, self.tables)

    def __len__(self):
        return len(self.tables)
