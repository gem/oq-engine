import os
import re
import sys
import uuid
import warnings
from contextlib import contextmanager

import psycopg2


# user password host port database
def dissect(uri):
    # rfc1738 URL
    m = re.compile(r'''
            (?:
                (?P<user>[^:/]*)
                (?::(?P<password>[^/]*))?
            @)?
            (?:
                (?P<host>[^/:]*)
                (?::(?P<port>[^/]*))?
            )?
            (?:/(?P<database>.*))?
            ''', re.X).match(uri)
    assert m, "Not an URL '%s'" % uri
    return m.groupdict()


def abspath(name, pkg):
    name = os.path.normpath(name)
    if name == os.path.abspath(name):
        return name
    if pkg is None:
        raise ValueError(
            '%r is a relative name, you must specify '
            'the package where the file lives' % name)
    return os.path.abspath(os.path.join(pkg.__path__[0], name))


def create_from_filename(filename, pkg=None):
    fname = abspath(filename, pkg)

    def create(conn):
        sql = open(fname).read()
        try:
            conn.executescript(sql)
        except:
            sys.stderr.write('Error executing %s\n' % filename)
            raise
    return create


def create_from_filenames(filenames, pkg=None):
    fnames = [abspath(f, pkg) for f in filenames]

    def create(conn):
        for fname in fnames:
            create_from_filename(fname)(conn)
    return create


class Resource(object):
    """
    A resource is an object with methods 'open/close' and an attribute
    'opened' which can be used as a context manager. The '__enter__'
    method calls 'open', whereas the '__exit__' method calls 'close'.
    If you override them, remember that the 'open' method should set the
    attribute opened to True and return self whereas the 'closed'  method
    should reset the attribute to False and return None.
    """
    opened = False

    def open(self):
        self.opened = True
        return self

    def close(self):
        self.opened = False

    def __enter__(self):
        return self.open() if not self.opened else self

    def __exit__(self, etype, evalue, tb):
        if self.opened:
            self.close()

############################### Connection #################################


class Connection(Resource):
    def __init__(self, uristr, autocommit=False):
        self.uridict = dissect(uristr)
        self.autocommit = autocommit
        self._debugstream = None

    def open(self):
        import pdb; pdb.set_trace()
        self.dbapi = psycopg2.connect(**self.uridict)
        self.dbapi.autocommit = self.autocommit
        self.opened = True
        return self

    def close(self):
        try:
            self.dbapi.close()
        except:  # already closed or not opened
            pass
        self.opened = False

    def cursor(self):
        return self.dbapi.cursor()

    def executescript(self, sqlcode):
        self.dbapi.cursor().execute(sqlcode)

    def executemany(self, templ, paramlist):
        if not isinstance(templ, basestring):  # common case
            raise TypeError('%r is not a string!' % templ)
        paramlist = map(tuple, paramlist)
        debug = self._debugstream
        if debug:
            debug.write('executing {}\n'.format(templ))
            if paramlist:
                trunc = '(truncated)' if len(paramlist) > 10 else ''
                debug.write(
                    'with paramlist {}{}\n'.format(paramlist[:10], trunc))

        curs = self.cursor()
        if not paramlist:
            curs.execute(templ)
        elif len(paramlist) == 1:
            curs.execute(templ, paramlist[0])
        else:
            curs.executemany(templ, paramlist)

        return curs

    def execute(self, templ, args=()):
        return self.executemany(templ, [args] if args else [])

    def all(self, templ, args=()):
        curs = self.execute(templ, args)
        try:
            return curs.fetchall()
        finally:
            curs.close()

    def one(self, templ, args=()):
        """Raises a ValueError if there are no rows or multiple rows"""
        rows = self.all(templ, args)
        nrows = len(rows)
        if nrows == 0:
            return
        elif nrows > 1:
            raise ValueError('Got more than one row')
        return rows[0]

    def scalar(self, templ, args=()):
        row = self.one(templ, args)
        if row is None:
            raise ValueError('Got nothing')
        elif len(row) > 1:
            raise ValueError('Expected a scalar value, got {}'.format(row))
        return row[0]

    def commit(self):
        etype, exc, tb = sys.exc_info()  # the original error
        try:
            self.dbapi.commit()
        except:  # for instance there is no connection to the server
            self.close()  # close the dead connection
            # re-raise the original exception, not an useless cannot rollback
            raise etype, exc, tb

    def rollback(self):
        if self.autocommit:
            warnings.warn(
                'Tried to rollback a transaction in autocommit mode',
                stacklevel=4)
        etype, exc, tb = sys.exc_info()  # the original error
        try:
            self.dbapi.rollback()
        except:  # for instance there is no connection to the server
            self.close()  # close the dead connection
            # re-raise the original exception, not an useless cannot rollback
            raise etype, exc, tb

    def opencopy(self, dbapi=None):
        new = self.__class__(self.uridict, self.autocommit, **self.extras)
        vars(new).update(vars(self))
        if dbapi:
            new.dbapi = dbapi
            new.opened = True
            return new
        return new.open()

    @contextmanager
    def begin(self, rollback=False):
        'Transaction context manager'
        try:
            yield
        except:
            self.rollback()
            raise
        else:
            if rollback:  # useful in tests
                self.rollback()
            else:
                self.commit()

    @contextmanager
    def begin_nested(self):
        'Subtransaction context manager'
        savepoint = 'savepoint_' + str(uuid.uuid1()).replace('-', '_')
        self.execute('SAVEPOINT %s' % savepoint)
        try:
            yield
        except:
            self.execute('ROLLBACK TO SAVEPOINT %s' % savepoint)
            raise
        else:
            self.execute('RELEASE SAVEPOINT %s' % savepoint)

    def debug(self, debugstream=sys.stderr):
        self._debugstream = debugstream

    def __repr__(self):
        s = '<{clsname} {user}:@{host}/{database}; opened: {opened}>'
        return s.format(clsname=self.__class__.__name__,
                        opened=self.opened, **self.uridict)

    def __hash__(self):
        return hash(repr(self))
