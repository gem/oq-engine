# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016 GEM Foundation
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

import re
import shlex
import threading
import collections


class NotFound(Exception):
    """Raised when a scalar query has not output"""


class TooManyRows(Exception):
    """Raised when a scalar query produces more than one row"""


class TooManyColumns(Exception):
    """Raised when a scalar query has more than one columns"""


class _Replacer(object):
    # helper for match
    rx = re.compile(r'\$T|\$S|\$D|\$A|\$O|\$t|\$s')
    ph = '?'

    def __init__(self, all_args):
        self.all_args = list(all_args)
        self.xargs = []
        self.targs = []

    def __call__(self, mo):
        arg = self.all_args[0]
        del self.all_args[0]
        placeholder = mo.group()
        if placeholder == '$S':
            self.xargs.extend(arg)
            return ', '.join([self.ph] * len(arg))
        elif placeholder == '$T':
            self.targs.extend(arg)
            return ', '.join(['{}'] * len(arg))
        elif placeholder == '$D':
            self.targs.extend(arg.keys())
            self.xargs.extend(arg.values())
            return ', '.join(['{}=' + self.ph] * len(arg))
        elif placeholder == '$A':
            self.targs.extend(arg.keys())
            self.xargs.extend(arg.values())
            return self.join(' AND ', arg)
        elif placeholder == '$O':
            self.targs.extend(arg.keys())
            self.xargs.extend(arg.values())
            return self.join(' OR ', arg)
        elif placeholder == '$s':
            self.xargs.append(arg)
            return self.ph
        elif placeholder == '$t':
            self.targs.append(arg)
            return '{}'

    def join(self, sep, args):
        ls = []
        for arg in args:
            ls.append('{} IS NULL' if arg is None else '{}=' + self.ph)
        return sep.join(ls)


def match(m_templ, *m_args):
    """
    :param m_templ: a meta template string
    :param m_args: all arguments
    :returns: template, args

    Here is an example of usage:

    >>> match('SELECT * FROM job WHERE id=$s', 1)
    ('SELECT * FROM job WHERE id=?', (1,))
    """
    if not m_args:
        return m_templ, ()
    repl = _Replacer(m_args)
    lst = []
    for token in shlex.split(m_templ, comments='#', posix=False):
        if not token.startswith('\'"'):
            lst.append(repl.rx.sub(repl, token))
    templ = ' '.join(lst)
    return templ.format(*repl.targs), tuple(repl.xargs)


class Db(object):
    """
    A wrapper over a DB API 2 connection
    """
    def __init__(self, connect, *args, **kw):
        self.connect = connect
        self.args = args
        self.kw = kw
        self.local = threading.local()

    @property
    def conn(self):
        try:
            return self.local.conn
        except AttributeError:
            self.local.conn = self.connect(*self.args, **self.kw)
            return self.local.conn

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
            print(templ, args)
        try:
            if args:
                cursor.execute(templ, args)
            else:
                cursor.execute(templ)
        except Exception as exc:
            raise exc.__class__('%s: %s %s' % (exc, templ, args))
        if templ.lower().startswith('select'):
            rows = cursor.fetchall()

            if kw.get('scalar'):  # scalar query
                if not rows:
                    raise NotFound
                elif len(rows) > 1:
                    raise TooManyRows(len(rows))
                elif len(rows[0]) > 1:
                    raise TooManyColumns(len(rows[0]))
                return rows[0][0]
            elif kw.get('one'):  # query returning a single row
                if not rows:
                    raise NotFound
                elif len(rows) > 1:
                    raise TooManyRows(len(rows))

            colnames = [r[0] for r in cursor.description]
            row = Row(colnames)
            if kw.get('one'):
                return row._new(rows[0])
            elif kw.get('header'):
                return [row] + [row._new(r) for r in rows]
            else:
                return [row._new(r) for r in rows]
        else:
            return cursor

    def insert(self, table, columns, rows):
        cursor = self.conn.cursor()
        if len(rows):
            templ, _args = match('INSERT INTO $t ($T) VALUES ($S)',
                                 table, columns, rows[0])
            cursor.executemany(templ, rows)
        return cursor


# we cannot use a namedtuple here because one would get aPicklingError:
# Can't pickle <class 'openquake.server.dbapi.Row'>: attribute lookup
# openquake.server.dbapi.Row failed
class Row(collections.Sequence):
    """
    A pickleable row. Here is an example of usage:

    >>> row = Row('id value'.split())
    >>> row._new((1, 42))
    <Row(id=1, value=42)>
    >>> row._fields
    ['id', 'value']
    """
    def __init__(self, fields):
        self._fields = self._tup = fields
        for f in fields:
            setattr(self, f, f)

    def _new(self, values):
        if len(values) != len(self._tup):
            raise ValueError('Got %d fields, expected %d' %
                             (len(values), len(self._tup)))
        new = self.__new__(self.__class__)
        new._fields = self._fields
        new._tup = values
        for f, v in zip(self._fields, values):
            setattr(new, f, v)
        return new

    def __getitem__(self, i):
        return self._tup[i]

    def __len__(self):
        return len(self._tup)

    def __repr__(self):
        items = ['%s=%s' % (f, getattr(self, f)) for f in self._fields]
        return '<Row(%s)>' % ', '.join(items)
