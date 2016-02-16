# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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

"""
Django settings for OpenQuake.
"""

import os
from openquake.engine.utils import config


# DEBUG = True
DB_NAME = config.get_section('database')['name'].replace(
    '$HOME', os.environ['HOME'])

INSTALLED_APPS = ('openquake.server.db',)


def _db_cfg(db_name):
    return dict(ENGINE='django.db.backends.sqlite3', NAME=DB_NAME)


_DB_NAMES = (
    'job_init',
)

DATABASES = dict((db, _db_cfg(db)) for db in _DB_NAMES)

DEFAULT_USER = 'job_init'
# We need a 'default' database to make Django happy:
DATABASES['default'] = DATABASES[DEFAULT_USER]

DATABASE_ROUTERS = ['openquake.server.db.routers.OQRouter']

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
