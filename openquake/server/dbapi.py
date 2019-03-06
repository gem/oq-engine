# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
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
"""\
One of the worst thing about Python is the `DB API 2.0`_
specification, which is unusable except for building frameworks. It
should have been a stepping stone for an usable DB API 3.0 that never
happened. So, instead of a good low level API, we had a proliferation
of Object Relational Mappers making our lives a lot harder. Fortunately,
there has always been good Pythonistas in the anti-ORM camp.

This module is heavily inspired by the dbapiext_ module by
Martin Blais, which is part of the antiorm_ package. The main (only)
difference is that I am using the question mark (?) for the placeholders
instead of the percent sign (%) to avoid confusions with other usages
of the %s, in particular in LIKE queries and in expressions like
`strftime('%s', time)` used in SQLite.

In less than 200 lines of code there is enough support
to build dynamic SQL queries and to make an ORM unneeded, since
we do not need database independence.

.. _DB API 2.0: https://www.python.org/dev/peps/pep-0249
.. _dbapiext: http://furius.ca/pubcode/pub/antiorm/lib/python/dbapiext.py.html
.. _antiorm: https://bitbucket.org/blais/antiorm

dbiapi tutorial
--------------------------

The only thing you must to know is the `Db` class, which is lazy wrapper
over a database connection. You instantiate it by passing a connection
function and its arguments:

>>> import sqlite3
>>> db = Db(sqlite3.connect, ':memory:')

Now you have an interface to your database, the `db` object. This object
is lazy, i.e. the connection is not yet instantiated, but it will be
when you will access its `.conn` attribute. This attribute is automatically
accessed when you call the interface to run a query, for instance to create
an empty table:

>>> curs = db('CREATE TABLE job ('
...     'id INTEGER PRIMARY KEY AUTOINCREMENT, value INTEGER)')

You can populate the table by using the `.insert` method:

>>> db.insert('job', ['value'], [(42,), (43,)]) # doctest: +ELLIPSIS
<sqlite3.Cursor object at ...>

Notice that this method returns a standard DB API 2.0 cursor and
you have access to all of its features: for instance here you could extract
the lastrowid.

Then you can run SELECT queries:

>>> rows = db('SELECT * FROM job')

The dbapi provides a `Row` class which is used to hold the results of
SELECT queries and is working as one would expect:

>>> rows
[<Row(id=1, value=42)>, <Row(id=2, value=43)>]
>>> tuple(rows[0])
(1, 42)
>>> rows[0].id
1
>>> rows[0].value
42
>>> rows[0]._fields
['id', 'value']

The queries can have different kind of `?` parameters:

- `?s` is for interpolated string parameters:

  >>> db('SELECT * FROM ?s', 'job')  # ?s is replaced by 'job'
  [<Row(id=1, value=42)>, <Row(id=2, value=43)>]

- `?x` is for escaped parameters (to avoid SQL injection):

  >>> db('SELECT * FROM job WHERE id=?x', 1)  # ?x is replaced by 1
  [<Row(id=1, value=42)>]

- `?s` and `?x` are for scalar parameters; `?S` and `?X` are for sequences:

  >>> db('INSERT INTO job (?S) VALUES (?X)', ['id', 'value'], (3, 44)) # doctest: +ELLIPSIS
  <sqlite3.Cursor object at ...>

You can see how the interpolation works by calling the `expand` method
that returns the interpolated template (alternatively, there is a
`debug=True` flag when calling `db` that prints the same info). In this case

>>> db.expand('INSERT INTO job (?S) VALUES (?X)', ['id', 'value'], [3, 44])
'INSERT INTO job (id, value) VALUES (?, ?)'

As you see, `?S` parameters work by replacing a list of strings with a comma
separated string, where `?X` parameters are replaced by a comma separated
sequence of question marks, i.e. the low level placeholder for SQLite.
The interpolation performs a regular search and replace,
so if you have a `?-` string in your template that must not be escaped,
you can run into issues. This is an error:

>>> match("SELECT * FROM job WHERE id=?x AND description='Lots of ?s'", 1)
Traceback (most recent call last):
   ...
ValueError: Incorrect number of ?-parameters in SELECT * FROM job WHERE id=?x AND description='Lots of ?s', expected 1

This is correct:

>>> match("SELECT * FROM job WHERE id=?x AND description=?x", 1, 'Lots of ?s')
('SELECT * FROM job WHERE id=? AND description=?', (1, 'Lots of ?s'))

There are three other `?` parameters:

- `?D` is for dictionaries and it is used mostly in UPDATE queries:

  >>> match('UPDATE mytable SET ?D WHERE id=?x', dict(value=33, other=5), 1)
  ('UPDATE mytable SET other=?, value=? WHERE id=?', (5, 33, 1))

- `?A` is for dictionaries and it is used in AND queries:

  >>> match('SELECT * FROM job WHERE ?A', dict(value=33, id=5))
  ('SELECT * FROM job WHERE id=? AND value=?', (5, 33))

- `?O` is for dictionaries and it is used in OR queries:

  >>> match('SELECT * FROM job WHERE ?O', dict(value=33, id=5))
  ('SELECT * FROM job WHERE id=? OR value=?', (5, 33))

The dictionary parameters are ordered per field name, just to make
the templates reproducible. `?A` and `?O` are smart enough to
treat specially `None` parameters, that are turned into `NULL`:

  >>> match('SELECT * FROM job WHERE ?A', dict(value=None, id=5))
  ('SELECT * FROM job WHERE id=? AND value IS NULL', (5,))

The `?` parameters are matched positionally; it is also possible to
pass to the `db` object a few keyword arguments to tune the standard
behavior. In particular, if you know that a query must return a
single row you can do the following:

>>> db('SELECT * FROM job WHERE id=?x', 1, one=True)
<Row(id=1, value=42)>

Without the `one=True` the query would have returned a list with a single
element. If you know that the query must return a scalar you can do the
following:

>>> db('SELECT value FROM job WHERE id=?x', 1, scalar=True)
42

If a query that should return a scalar returns something else, or if a
query that should return a row returns a different number of rows,
appropriate errors are raised:

>>> db('SELECT * FROM job WHERE id=?x', 1, scalar=True) # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
   ...
TooManyColumns: 2, expected 1

>>> db('SELECT * FROM job', None, one=True) # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
   ...
TooManyRows: 3, expected 1

If a row is expected but not found, a NotFound exception is raised:

>>> db('SELECT * FROM job WHERE id=?x', None, one=True) # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
   ...
NotFound

"""
import re
import threading
import collections


class NotFound(Exception):
    """Raised when a scalar query has not output"""


class TooManyRows(Exception):
    """Raised when a scalar query produces more than one row"""


class TooManyColumns(Exception):
    """Raised when a scalar query has more than one column"""


class _Replacer(object):
    # helper class for the match function below
    rx = re.compile(r'\?S|\?X|\?D|\?A|\?O|\?s|\?x')
    ph = '?'

    def __init__(self, all_args):
        self.all_args = list(all_args)
        self.xargs = []
        self.sargs = []

    def __call__(self, mo):
        arg = self.all_args[0]  # can raise an IndexError
        del self.all_args[0]
        placeholder = mo.group()
        if placeholder == '?X':
            self.xargs.extend(arg)
            return ', '.join([self.ph] * len(arg))
        elif placeholder == '?S':
            self.sargs.extend(arg)
            return ', '.join(['{}'] * len(arg))
        elif placeholder == '?D':
            keys, values = zip(*sorted(arg.items()))
            self.sargs.extend(keys)
            self.xargs.extend(values)
            return ', '.join(['{}=' + self.ph] * len(arg))
        elif placeholder == '?A':
            return self.join(' AND ', arg) or '1'
        elif placeholder == '?O':
            return self.join(' OR ', arg) or '1'
        elif placeholder == '?x':
            self.xargs.append(arg)
            return self.ph
        elif placeholder == '?s':
            self.sargs.append(arg)
            return '{}'

    def join(self, sep, arg):
        ls = []
        for name in sorted(arg):
            self.sargs.append(name)
            value = arg[name]
            if value is None:
                ls.append('{} IS NULL')
            else:
                self.xargs.append(value)
                ls.append('{}=' + self.ph)
        return sep.join(ls)

    def match(self, m_templ):
        templ = self.rx.sub(self, m_templ)
        return templ.format(*self.sargs), tuple(self.xargs)


def match(m_templ, *m_args):
    """
    :param m_templ: a meta template string
    :param m_args: all arguments
    :returns: template, args

    Here is an example of usage:

    >>> match('SELECT * FROM job WHERE id=?x', 1)
    ('SELECT * FROM job WHERE id=?', (1,))
    """
    # strip commented lines
    m_templ = '\n'.join(line for line in m_templ.splitlines()
                        if not line.lstrip().startswith('--'))
    if not m_args:
        return m_templ, ()
    try:
        return _Replacer(m_args).match(m_templ)
    except IndexError:
        raise ValueError('Incorrect number of ?-parameters in %s, expected %s'
                         % (m_templ, len(m_args)))


class Db(object):
    """
    A wrapper over a DB API 2 connection. See the tutorial.
    """
    def __init__(self, connect, *args, **kw):
        self.connect = connect
        self.args = args
        self.kw = kw
        self.local = threading.local()

    @classmethod
    def expand(cls, m_templ, *m_args):
        """
        Performs partial interpolation of the template. Used for debugging.
        """
        return match(m_templ, *m_args)[0]

    @property
    def conn(self):
        try:
            return self.local.conn
        except AttributeError:
            self.local.conn = self.connect(*self.args, **self.kw)
            #  honor ON DELETE CASCADE
            self.local.conn.execute('PRAGMA foreign_keys = ON')
            return self.local.conn

    @property
    def path(self):
        """Path to the underlying sqlite file"""
        return self.args[0]

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        if etype:
            self.conn.rollback()
        else:
            self.conn.commit()

    def __call__(self, m_templ, *m_args, **kw):
        cursor = self.conn.cursor()
        templ, args = match(m_templ, *m_args)
        if kw.get('debug'):
            print(templ)
            print('args = %s' % repr(args))
        try:
            if args:
                cursor.execute(templ, args)
            else:
                cursor.execute(templ)
        except Exception as exc:
            raise exc.__class__('%s: %s %s' % (exc, templ, args))
        if templ.lstrip().lower().startswith(('select', 'pragma')):
            rows = cursor.fetchall()
            if kw.get('scalar'):  # scalar query
                if not rows:
                    raise NotFound
                elif len(rows) > 1:
                    raise TooManyRows('%s, expected 1' % len(rows))
                elif len(rows[0]) > 1:
                    raise TooManyColumns('%s, expected 1' % len(rows[0]))
                return rows[0][0]
            elif kw.get('one'):  # query returning a single row
                if not rows:
                    raise NotFound(args)
                elif len(rows) > 1:
                    raise TooManyRows('%s, expected 1' % len(rows))
            elif cursor.description is None:
                return cursor

            colnames = [r[0] for r in cursor.description]
            if kw.get('one'):
                return Row(colnames, rows[0])
            else:
                return Table(colnames, rows)
        else:
            return cursor

    def insert(self, table, columns, rows):
        """
        Insert several rows with executemany. Return a cursor.
        """
        cursor = self.conn.cursor()
        if len(rows):
            templ, _args = match('INSERT INTO ?s (?S) VALUES (?X)',
                                 table, columns, rows[0])
            cursor.executemany(templ, rows)
        return cursor

    def close(self):
        """
        Close the main thread connection and refresh the threadlocal object
        """
        self.conn.close()
        self.local = threading.local()


class Table(list):
    """Just a list of Rows with an attribute _fields"""
    def __init__(self, fields, rows):
        self._fields = fields
        for row in rows:
            self.append(Row(fields, row))


# we cannot use a namedtuple here because one would get a PicklingError:
# Can't pickle <class 'openquake.server.dbapi.Row'>: attribute lookup
# openquake.server.dbapi.Row failed
class Row(collections.Sequence):
    """
    A pickleable row, working both as a tuple and an object:

    >>> row = Row(['id', 'value'], (1, 2))
    >>> tuple(row)
    (1, 2)
    >>> assert row[0] == row.id and row[1] == row.value

    :param fields: a sequence of field names
    :param values: a sequence of values (one per field)
    """
    def __init__(self, fields, values):
        if len(values) != len(fields):
            raise ValueError('Got %d values, expected %d' %
                             (len(values), len(fields)))
        self._fields = fields
        self._values = values
        for f, v in zip(fields, values):
            setattr(self, f, v)

    def __getitem__(self, i):
        return self._values[i]

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        items = ['%s=%s' % (f, getattr(self, f)) for f in self._fields]
        return '<Row(%s)>' % ', '.join(items)
