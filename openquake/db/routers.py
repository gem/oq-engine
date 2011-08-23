# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


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
    SCHEMA_RE = re.compile(r'^(\w+)"')

    @classmethod
    def _schema_from_model(cls, model):
        '''
        Get the db schema name from a given model.

        :param model: a Django model object

        :returns: schema name, or None if no schema is defined
        '''
        match = cls.SCHEMA_RE.match(
            model._meta.db_table)  # pylint: disable=W0212
        if match:
            return match.group(1)
        else:
            return None

    def db_for_read(self, model, **_hints):
        '''
        Get the name of the correct db configuration to use for read operations
        on the given model.
        '''
        schema = self._schema_from_model(model)

        if schema in ('admin', 'oqmif'):
            # The db name for these is the same as the schema
            return schema
        else:
            # For everything else, the db name we want to use is
            # 'schema_read'.
            return '%s_read' % schema

    def db_for_write(self, model, **_hints):
        '''
        Get the name of the correct db configuration to use for write
        operations on the given model.
        '''
        schema = self._schema_from_model(model)

        if schema in ('admin', 'oqmif'):
            # The db name for these is the same as the schema
            return schema
        else:
            # For everything else, the db name we want to use is
            # 'schema_write'.
            return '%s_write' % schema

    def allow_relation(self, _obj1, _obj2, **_hints):  # pylint: disable=R0201
        '''
        Determine if relations between two model objects should be allowed.

        For now, this always returns True.
        '''
        return True
