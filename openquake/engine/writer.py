# Copyright (c) 2010-2013, GEM Foundation.
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

from django.db import transaction
from django.db import connections
from django.db import router
from django.contrib.gis.db import models as gis_models

LOGGER = logging.getLogger('serializer')


# pylint: disable=W0212
class BulkInserter(object):
    """Handle bulk object insertion"""

    def __init__(self, dj_model, max_cache_size=None):
        """
        Create a new bulk inserter for a Django model class

        :param dj_model:
            Django model class
        :param int max_cache_size:
            The number of entries to cache before flushing/inserting. This
            helps to limit memory consumption for large sets of inserts.

            The default value is `None`, which means there is no maximum.
        """
        self.table = dj_model
        self.max_cache_size = max_cache_size
        self.fields = None
        self.values = []
        self.count = 0

    def add_entry(self, **kwargs):
        """
        Add a new entry to be inserted

        The first time the method is called the field list is stored;
        subsequent add_entry() calls must provide the same set of
        keyword arguments.

        Handles PostGIS/GeoDjango types.
        """
        if not self.fields:
            self.fields = kwargs.keys()
        assert set(self.fields) == set(kwargs.keys())
        for k in self.fields:
            self.values.append(kwargs[k])
        self.count += 1

        # If we have hit the `max_cache_size` is set,
        if self.max_cache_size is not None:
            # check if we have hit the maximum insert the current batch.
            if len(self.values) >= self.max_cache_size:
                self.flush()

    def flush(self):
        """Inserts the entries in the database using a bulk insert query"""
        if not self.values:
            return

        alias = router.db_for_write(self.table)
        cursor = connections[alias].cursor()
        value_args = []

        field_map = dict()
        for f in self.table._meta.fields:
            field_map[f.column] = f

        for f in self.fields:
            col = field_map[f]
            if isinstance(col, gis_models.GeometryField):
                value_args.append('GeomFromText(%%s, %d)' % col.srid)
            else:
                value_args.append('%s')

        sql = "INSERT INTO \"%s\" (%s) VALUES " % (
            self.table._meta.db_table, ", ".join(self.fields)) + \
            ", ".join(["(" + ", ".join(value_args) + ")"] * self.count)
        cursor.execute(sql, self.values)
        transaction.set_dirty(using=alias)

        self.fields = None
        self.values = []
        self.count = 0
