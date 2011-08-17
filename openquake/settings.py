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


""" Settings for OpenQuake.  """

KVS_PORT = 6379
KVS_HOST = "localhost"

TEST_KVS_DB = 3

AMQP_HOST = "localhost"
AMQP_PORT = 5672
AMQP_USER = "guest"
AMQP_PASSWORD = "guest"
AMQP_VHOST = "/"
AMQP_EXCHANGE = 'oq.signalling'

# Keep the Python and Java formats in sync!
LOGGING_AMQP_FORMAT = '%(asctime)s %(loglevel)-5s %(processName)s' \
    ' [%(name)s] - Job %(job_id)s - %(message)s'
LOG4J_AMQP_FORMAT = '%d %-5p %X{processName} [%c] - Job %X{job_id} - %m'

LOGGING_STDOUT_FORMAT = '%(levelname)-5s %(processName)s' \
    ' [%(name)s] - %(message)s'
LOG4J_STDOUT_FORMAT = '%-5p %X{processName} [%c] - Job %X{job_id} - %m%n'

LOG4J_STDOUT_SETTINGS = {
    'log4j.rootLogger': '%(level)s, stdout',

    'log4j.appender.stdout': 'org.apache.log4j.ConsoleAppender',
    'log4j.appender.stdout.follow': 'true',
    'log4j.appender.stdout.layout': 'org.apache.log4j.PatternLayout',
    'log4j.appender.stdout.layout.ConversionPattern': LOG4J_STDOUT_FORMAT,
}

LOG4J_AMQP_SETTINGS = {
    'log4j.rootLogger': '%(level)s, amqp',

    'log4j.appender.amqp': 'org.gem.log.AMQPAppender',
    'log4j.appender.amqp.host': AMQP_HOST,
    'log4j.appender.amqp.port': str(AMQP_PORT),
    'log4j.appender.amqp.username': AMQP_USER,
    'log4j.appender.amqp.password': AMQP_PASSWORD,
    'log4j.appender.amqp.virtualHost': AMQP_VHOST,
    'log4j.appender.amqp.routingKeyPattern': 'log.%p.%X{job_id}',
    'log4j.appender.amqp.exchange': AMQP_EXCHANGE,
    'log4j.appender.amqp.layout': 'org.apache.log4j.PatternLayout',
    'log4j.appender.amqp.layout.ConversionPattern': LOG4J_AMQP_FORMAT,
}

LOGGING_BACKEND = 'console'


# Django settings for the openquake project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'openquake',
        'USER': 'openquake',
        'PASSWORD': 'secret',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
TIME_ZONE = 'Europe/Zurich'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'change-me-in-production'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'openquake.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
