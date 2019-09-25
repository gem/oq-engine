# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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

import os
import socket
import getpass

from openquake.baselib import config, datastore

try:
    from openquakeplatform.settings import STANDALONE, STANDALONE_APPS
except ImportError:
    STANDALONE = False
    STANDALONE_APPS = ()

INSTALLED_APPS = ('openquake.server.db',)

OQSERVER_ROOT = os.path.dirname(__file__)

DEBUG = True
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'openquake.server.utils.oq_server_context_processor',
            ],
        },
    },
]

STATIC_URL = '/static/'

MEDIA_ROOT = '%(mediaroot)s'
STATIC_ROOT = '%(staticroot)s'

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(OQSERVER_ROOT, 'static'),
]

DATABASE = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.expanduser(config.dbserver.file),
    'USER': getpass.getuser(),
    'HOST': config.dbserver.host,
    'PORT': config.dbserver.port,
}
DATABASES = {'default': DATABASE}

ALLOWED_HOSTS = ['*']

AUTHENTICATION_BACKENDS = ()

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Rome'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'f_6=^^_0%ygcpgmemxcp0p^xq%47yqe%u9pu!ad*2ym^zt+xq$'

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

LOCKDOWN = False
ACL_ON = False

# Add additional paths (as regular expressions) that don't require
# authentication.
AUTH_EXEMPT_URLS = ()

ROOT_URLCONF = 'openquake.server.urls'

INSTALLED_APPS += (
    'django.contrib.staticfiles',
    'openquake.server',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'openquake.server': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 1

# A server name can be specified to customize the WebUI in case of
# multiple installations of the Engine are available. This helps avoiding
# confusion between different installations when the WebUI is used
SERVER_NAME = socket.gethostname()

# Expose the WebUI interface, otherwise only the REST API will be available
WEBUI = True

# OpenQuake Standalone tools (IPT, Taxtweb, Taxonomy Glossary)
if STANDALONE and WEBUI:
    INSTALLED_APPS += (
        'openquakeplatform',
    )

    INSTALLED_APPS += STANDALONE_APPS

    FILE_PATH_FIELD_DIRECTORY = datastore.get_datadir()

    CONTEXT_PROCESSORS = TEMPLATES[0]['OPTIONS']['context_processors']
    CONTEXT_PROCESSORS.insert(0, 'django.template.context_processors.request')
    CONTEXT_PROCESSORS.append('openquakeplatform.utils.oq_context_processor')

try:
    # Try to load a local_settings.py from the current folder; this is useful
    # when packages are used. A custom local_settings.py can be placed in
    # /usr/share/openquake/engine, avoiding changes inside the python package
    from local_settings import *
except ImportError:
    # If no local_settings.py is availble in the current folder let's try to
    # load it from openquake/server/local_settings.py
    try:
        from openquake.server.local_settings import *
    except ImportError:
        # If a local_setting.py does not exist
        # settings in this file only will be used
        pass

if LOCKDOWN:

    ACL_ON = True

    AUTHENTICATION_BACKENDS += (
        'django.contrib.auth.backends.ModelBackend',
        # 'dpam.backends.PAMBackend',
    )

    MIDDLEWARE += (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'openquake.server.middleware.LoginRequiredMiddleware',
    )

    INSTALLED_APPS += (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.messages',
        'django.contrib.sessions',
        'django.contrib.admin',
        )

    # Official documentation suggests to override the entire TEMPLATES
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.static',
                    'django.template.context_processors.tz',
                    'django.contrib.messages.context_processors.messages',
                    'openquake.server.utils.oq_server_context_processor',
                ],
            },
        },
    ]

    LOGIN_REDIRECT_URL = '/engine'

    LOGIN_EXEMPT_URLS = ('/accounts/ajax_login/', )
