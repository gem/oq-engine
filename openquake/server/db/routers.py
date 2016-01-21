# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


'''
Database routers for the OpenQuake DB
'''

import re


class OQRouter(object):
    '''
    Helps determine which database credentials to use for read/write operations
    on a given model
    '''

    # Parses the schema name from model's _meta.db_table
    SCHEMA_TABLE_RE = re.compile(r'^(\w+)"\.\"(\w+)')

    @classmethod
    def _schema_table_from_model(cls, model):
        '''
        Get the db schema name from a given model.

        :param model: a Django model object

        :returns: schema name, or None if no schema is defined
        '''
        parts = model._meta.db_table.split('"."')  # pylint: disable=W0212
        if len(parts) == 2:
            return parts
        else:
            return None, parts[0]

    def db_for_read(self, model, **_hints):
        '''
        Get the name of the correct db configuration to use for read operations
        on the given model.
        '''
        return "job_init"

    def db_for_write(self, model, **_hints):
        '''
        Get the name of the correct db configuration to use for write
        operations on the given model.
        '''
        schema, table = self._schema_table_from_model(model)
        if schema == "uiapi" and table == "output":
            return "job_init"
        else:
            return "job_init"

    def allow_relation(self, _obj1, _obj2, **_hints):  # pylint: disable=R0201
        '''
        Determine if relations between two model objects should be allowed.

        For now, this always returns True.
        '''
        return True
