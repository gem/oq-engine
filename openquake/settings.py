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


""" Django settings for openquake project.  """

#ADD THIS
import os
GEOGRAPHIC_ADMIN_DIR = os.path.dirname(__file__)

# http://docs.djangoproject.com/en/dev/topics/testing/#id1
# Your user must be a postgrest superuser
# Avoid specifying your password with: ~/.pgpass
# http://www.postgresql.org/docs/8.3/interactive/libpq-pgpass.html
TEST_RUNNER = 'django.contrib.gis.tests.run_gis_tests'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Aurea Moemke', 'aurea.moemke@sed.ethz.ch'),
)

MANAGERS = ADMINS

SPATIALITE_LIBRARY_PATH = '/Library/Frameworks/SQLite3.framework/SQLite3'
# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'openquake.db'  # Or path to database file if using sqlite3.
DATABASE_USER = ''              # Not used with sqlite3.
DATABASE_PASSWORD = ''          # Not used with sqlite3.
DATABASE_HOST = ''              # Set to empty string for localhost.
DATABASE_PORT = ''              # Set to empty string for default.

# Not used at this point but you'll need it here if you
# want to enable a google maps baselayer within your
# OpenLayers maps
GOOGLE_MAPS_API_KEY = 'abcdefg'

GIS_DATA_DIR = os.path.join(GEOGRAPHIC_ADMIN_DIR, '../tests/data')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(GEOGRAPHIC_ADMIN_DIR, '../media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '!!0h0h*84l#&e*ki(t1f#)8h0wnj9!#r=w!3wxqy$e7o$3=@b&'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(GEOGRAPHIC_ADMIN_DIR, '../templates'),
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.databrowse',
    'django.contrib.gis',
)

LOSS_CURVES_OUTPUT_FILE = 'loss-curves-jobber.xml'

KVS_PORT = 6379
KVS_HOST = "localhost"

SOURCEGEOM_SHP = 'seismicsources/data/sourcegeometrycatalog.shp'
WORLD_SHP = 'world/data/TM_WORLD_BORDERS-0.3.shp'

TEST_KVS_DB = 3

AMQP_HOST = "localhost"
AMQP_PORT = 5672
AMQP_USER = "guest"
AMQP_PASSWORD = "guest"
AMQP_VHOST = "/"

LOG4J_STDOUT_SETTINGS = {
    'log4j.rootLogger': '%(level)s, stdout',

    'log4j.appender.stdout': 'org.apache.log4j.ConsoleAppender',
    'log4j.appender.stdout.follow': 'true',
    'log4j.appender.stdout.layout': 'org.apache.log4j.PatternLayout',
    'log4j.appender.stdout.layout.ConversionPattern':
        '%d %-5p [%c] - Job %X{job_id} - %m%n',
}
