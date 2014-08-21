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


"""Django settings for OpenQuake."""

from openquake.engine.utils import config


# DEBUG = True
DB_SECTION = config.get_section('database')


def _db_cfg(db_name):
    """
    Helper method to create db config items for the various roles and schemas.

    :param db_name: The name of the database configuration. Configurations for
        this name will be loaded from the site specific config file. If an item
        doesn't exist in the config file, a default value will be used instead.

    :returns: Configuration dict, structured like so::
        {'ENGINE': 'django.db.backends.postgresql_psycopg2',
         'NAME': 'openquake2',
         'USER': 'openquake',
         'PASSWORD': 'secret',
         'HOST': 'localhost',
         'PORT': '5432',
        }


    """

    return dict(
        ENGINE='django.contrib.gis.db.backends.postgis',
        NAME=DB_SECTION.get('name', 'openquake'),
        USER=DB_SECTION.get('%s_user' % db_name, 'openquake'),
        PASSWORD=DB_SECTION.get('%s_password' % db_name, ''),
        HOST=DB_SECTION.get('host', ''),
        PORT=DB_SECTION.get('port', '5432'),
    )


_DB_NAMES = (
    'admin',
    'job_init',
)

DATABASES = dict((db, _db_cfg(db)) for db in _DB_NAMES)

DEFAULT_USER = 'admin'
# We need a 'default' database to make Django happy:
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': DB_SECTION.get('name', 'openquake'),
    'USER': DB_SECTION.get('%s_user' % DEFAULT_USER, 'oq_admin'),
    'PASSWORD': DB_SECTION.get('%s_password' % DEFAULT_USER, 'openquake'),
    'HOST': '',
    'PORT': '5432',
}

DATABASE_ROUTERS = ['openquake.engine.db.routers.OQRouter']

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

USE_I18N = False
USE_L10N = False

try:
    from local_settings import *
except ImportError:
    pass
