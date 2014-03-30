# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base classes for the output methods of the various codecs.
"""

import logging
import weakref
import atexit
from cStringIO import StringIO

from django.db import transaction
from django.db import connections
from django.db import router
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.geos.point import Point

LOGGER = logging.getLogger('serializer')


class CacheInserter(object):
    """
    Bulk insert bunches of Django objects by converting them in strings
    and by using COPY FROM.
    """
    instances = weakref.WeakSet()

    @classmethod
    def flushall(cls):
        """
        Flush the caches of all the instances of CacheInserter.
        """
        for instance in cls.instances:
            instance.flush()

    @classmethod
    def saveall(cls, objects, block_size=1000):
        """
        Save a sequence of Django objects in the database in a single
        transaction, by using a COPY FROM. Returns the ids of the inserted
        objects.
        """
        self = cls(objects[0].__class__, block_size)
        curs = connections[self.alias].cursor()
        seq = self.tname.replace('"', '') + '_id_seq'
        with transaction.commit_on_success(using=self.alias):
            reserve_ids = "select nextval('%s') "\
                "from generate_series(1, %d)" % (seq, len(objects))
            curs.execute(reserve_ids)
            ids = [i for (i,) in curs.fetchall()]
            stringio = StringIO()
            for i, obj in zip(ids, objects):
                stringio.write('%d\t%s\n' % (i, self.to_line(obj)))
            stringio.reset()
            curs.copy_from(stringio, self.tname)
            stringio.close()
        return ids

    def __init__(self, dj_model, max_cache_size):
        self.table = dj_model
        self.max_cache_size = max_cache_size
        self.alias = router.db_for_write(dj_model)
        self.tname = '"%s"' % dj_model._meta.db_table
        self._fields = {}
        self.nlines = 0
        self.stringio = StringIO()
        self.instances.add(self)

    @property
    def fields(self):
        """
        Returns the field names as introspected from the db, except the
        id field. The introspection is done only once per table.
        NB: we cannot trust the ordering in the Django model.
        """
        try:
            return self._fields[self.tname]
        except KeyError:
            # introspect the field names from the database
            # by relying on the DB API 2.0
            # NB: we cannot trust the ordering in the Django model
            curs = connections[self.alias].cursor()
            curs.execute('select * from %s where 1=0' % self.tname)
            names = self._fields[self.tname] = [
                r[0] for r in curs.description if r[0] != 'id']
            return names

    def add(self, obj):
        """
        :param obj: a Django model object

        Append an object to the list of objects to save. If the list exceeds
        the max_cache_size, flush it on the database.
        """
        assert isinstance(obj, self.table), 'Expected instance of %s, got %r' \
            % (self.table.__name__, obj)
        line = self.to_line(obj)
        self.stringio.write(line + '\n')
        self.nlines += 1
        if self.nlines >= self.max_cache_size:
            self.flush()

    def flush(self):
        """
        Save the pending objects on the database with a COPY FROM.
        """
        if not self.nlines:
            return

        # save the StringIO object with a COPY FROM
        with transaction.commit_on_success(using=self.alias):
            curs = connections[self.alias].cursor()
            self.stringio.reset()
            curs.copy_from(self.stringio, self.tname, columns=self.fields)
            self.stringio.close()
            self.stringio = StringIO()

        ## TODO: should we add an assert that the number of rows stored
        ## in the db is the expected one? I (MS) have seen a case where
        ## this fails silently (it was for True/False not converted in t/f)

        LOGGER.debug('saved %d rows in %s', self.nlines, self.tname)
        self.nlines = 0

    def to_line(self, obj):
        """
        Convert the fields of a Django object into a line string suitable
        for import via COPY FROM. The encoding is UTF8.
        """
        cols = []
        for f in self.fields:
            col = getattr(obj, f)
            if col is None:
                col = r'\N'
            elif isinstance(col, bool):
                col = 't' if col else 'f'
            elif isinstance(col, Point):
                col = 'SRID=4326;' + col.wkt
            elif isinstance(col, GeometryField):
                col = col.wkt()
            elif isinstance(col, (tuple, list)):
                # for numeric arrays; this is fragile
                col = self.array_to_pgstring(col)
            else:
                col = unicode(col).encode('utf8')
            cols.append(col)
        return '\t'.join(cols)

    @staticmethod
    def array_to_pgstring(a):
        """
        Convert a Python list/array into the Postgres string-representation
        of it.
        """
        ls = []
        for n in a:
            s = str(n)
            if s.endswith('L'):  # strip the trailing "L"
                s = s[:-1]
            ls.append(s)
        return '{%s}' % ','.join(ls)


# just to make sure that flushall is always called
atexit.register(CacheInserter.flushall)
