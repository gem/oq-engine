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


"""Django settings for OpenQuake."""

from openquake.utils import config


def _db_cfg(db_name):
    """
    Helper method to create db config items for the various roles and schemas.

    :param db_name: The name of the database configuration. Configurations for
        this name will be loaded from the site specific config file. If an item
        doesn't exist in the config file, a default value will be used instead.

    :returns: Configuration dict, structured like so::
        {'ENGINE': 'django.db.backends.postgresql_psycopg2',
         'NAME': 'openquake',
         'USER': 'openquake',
         'PASSWORD': 'secret',
         'HOST': 'localhost',
         'PORT': '5432',
        }


    """
    db_section = config.get_section('database')

    return dict(
        ENGINE='django.contrib.gis.db.backends.postgis',
        NAME=db_section.get('name', 'openquake'),
        USER=db_section.get('%s_user' % db_name, 'openquake'),
        PASSWORD=db_section.get('%s_password' % db_name, ''),
        HOST=db_section.get('host', ''),
        PORT=db_section.get('port', ''),
    )


_DB_NAMES = (
    'admin',
    'eqcat_read', 'eqcat_write',
    'hzrdi_read', 'hzrdi_write',
    'hzrdr_read', 'hzrdr_write',
    'oqmif',
    'riski_read', 'riski_write',
    'riskr_read', 'riskr_write',
    'uiapi_read', 'uiapi_write',
)
DATABASES = dict((db, _db_cfg(db)) for db in _DB_NAMES)
# We need a 'default' database to make Django happy:
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'openquake',
    'USER': 'openquake',
    'PASSWORD': '',
    'HOST': '',
    'PORT': '',
}

DATABASE_ROUTERS = ['openquake.db.routers.OQRouter']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
TIME_ZONE = 'Europe/Zurich'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'change-me-in-production'
