# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

import sys
import os
import socket
import getpass
import tempfile
import logging

from openquake.baselib import config
from openquake.commonlib import datastore

try:
    from openquakeplatform.settings import STANDALONE, STANDALONE_APPS
except ImportError:
    STANDALONE = False
    STANDALONE_APPS = ()

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
WEBUI_USER = 'openquake'

TEST = 'test' in sys.argv or any('pytest' in arg for arg in sys.argv)

INSTALLED_APPS = ('openquake.server.db',)

OQSERVER_ROOT = os.path.dirname(__file__)

DEBUG = True
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

WEBUI_PATHPREFIX = os.getenv('WEBUI_PATHPREFIX', '')
USE_X_FORWARDED_HOST = os.getenv('USE_X_FORWARDED_HOST', False)

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
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# USE_TZ = True is the default for Django >= 5.0. From Django documentation:
# "
# When support for time zones is enabled, Django stores datetime information
# in UTC in the database, uses time-zone-aware datetime objects internally,
# and translates them to the end user’s time zone in templates and forms.
# This is handy if your users live in more than one time zone and you want
# to display datetime information according to each user’s wall clock.
# Even if your website is available in only one time zone, it’s still good
# practice to store data in UTC in your database. The main reason is daylight
# saving time (DST). Many countries have a system of DST, where clocks are
# moved forward in spring and backward in autumn. If you’re working in local
# time, you’re likely to encounter errors twice a year, when the transitions
# happen.
# "
USE_TZ = True

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
    # NOTE: the following can be useful for debugging
    # 'openquake.server.middleware.PrintHeadersMiddleware',
)

# Authentication is not enabled by default
LOCKDOWN = False
# Forbid users to see other users outputs by default
ACL_ON = True

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

SUPPRESS_PERMISSION_DENIED_WARNINGS = False

FILE_UPLOAD_MAX_MEMORY_SIZE = 1
FILE_UPLOAD_TEMP_DIR = config.directory.custom_tmp or tempfile.gettempdir()

# A server name can be specified to customize the WebUI in case of
# multiple installations of the Engine are available. This helps avoiding
# confusion between different installations when the WebUI is used
SERVER_NAME = socket.gethostname()

APPLICATION_MODES = [
    'PUBLIC', 'RESTRICTED', 'AELO', 'ARISTOTLE', 'READ_ONLY', 'TOOLS_ONLY']

APPLICATION_MODE = 'PUBLIC'

ARISTOTLE_DEFAULT_USGS_ID = 'us7000n7n8'  # loadable and convertible rupture
# ARISTOTLE_DEFAULT_USGS_ID = 'us6000jllz'  # loadable but with conversion err

EXTERNAL_TOOLS = os.environ.get('EXTERNAL_TOOLS', False) == 'True'

# If False, a warning is displayed in case a newer version of the engine has
# been released
DISABLE_VERSION_WARNING = False

# Set to True if using NGINX or some other reverse proxy
# Externally visible url and port number is different from Django visible
# values
USE_REVERSE_PROXY = False

# Expose the WebUI interface, otherwise only the REST API will be available
WEBUI = True

MAX_AELO_SITE_NAME_LEN = 256

GOOGLE_ANALYTICS_TOKEN = None

CONTEXT_PROCESSORS = TEMPLATES[0]['OPTIONS']['context_processors']

# OpenQuake Standalone tools (IPT, Taxtweb, Taxonomy Glossary)
if STANDALONE and WEBUI:
    INSTALLED_APPS += (
        'openquakeplatform', 'corsheaders',
    )

    INSTALLED_APPS += STANDALONE_APPS

    # cors-headers configuration
    corsheader_middleware = 'corsheaders.middleware.CorsMiddleware'
    if corsheader_middleware not in MIDDLEWARE:
        MIDDLEWARE += (corsheader_middleware,)
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_URLS_REGEX = r'^/taxtweb/explanation/.*$'

    FILE_PATH_FIELD_DIRECTORY = datastore.get_datadir()

    CONTEXT_PROCESSORS.insert(0, 'django.template.context_processors.request')
    CONTEXT_PROCESSORS.append('openquakeplatform.utils.oq_context_processor')

try:
    # Try to load a local_settings.py from the current folder; this is useful
    # when packages are used. A custom local_settings.py can be placed in
    # /usr/share/openquake/engine, avoiding changes inside the python package
    from local_settings import *  # noqa
except ImportError:
    # If no local_settings.py is availble in the current folder let's try to
    # load it from openquake/server/local_settings.py
    try:
        from openquake.server.local_settings import *  # noqa
    except ImportError:
        # If a local_setting.py does not exist
        # settings in this file only will be used
        pass

if SUPPRESS_PERMISSION_DENIED_WARNINGS:
    class SuppressPermissionDeniedWarnings(logging.Filter):
        def filter(self, record):
            if 'Forbidden' in record.getMessage():
                # Avoid warnings like "WARNING Forbidden: /v1/calc/list"
                return False
            return True

    LOGGING['filters'] = {
        'suppress_403_warnings': {
            '()': SuppressPermissionDeniedWarnings,
        },
    }
    LOGGING['handlers']['console']['filters'] = ['suppress_403_warnings']

# NOTE: the OQ_APPLICATION_MODE environment variable, if defined, overrides
# both the default setting and the one specified in the local settings
APPLICATION_MODE = os.environ.get('OQ_APPLICATION_MODE', APPLICATION_MODE)

if APPLICATION_MODE not in ('PUBLIC',):
    # add installed_apps for cookie-consent
    for app in ('django.contrib.auth', 'django.contrib.contenttypes',
                'openquake.server.user_profile', 'cookie_consent',):
        if app not in INSTALLED_APPS:
            INSTALLED_APPS += (app,)

    if 'django.template.context_processors.request' not in CONTEXT_PROCESSORS:
        CONTEXT_PROCESSORS.insert(
            0, 'django.template.context_processors.request')
    COOKIE_CONSENT_NAME = "cookie_consent"
    COOKIE_CONSENT_MAX_AGE = 31536000  # 1 year in seconds
    COOKIE_CONSENT_LOG_ENABLED = False

if TEST and APPLICATION_MODE in ('AELO', 'ARISTOTLE'):
    if APPLICATION_MODE == 'ARISTOTLE':
        from openquake.server.tests.settings.local_settings_impact import *  # noqa
    elif APPLICATION_MODE == 'AELO':
        from openquake.server.tests.settings.local_settings_aelo import *  # noqa
    # FIXME: this is mandatory, but it writes anyway in /tmp/app-messages.
    #        We should redefine it to a different directory for each test,
    #        in order to avoid concurrency issues in case tests run in
    #        parallel
    EMAIL_FILE_PATH = os.path.join(
        config.directory.custom_tmp or tempfile.gettempdir(),
        'app-messages')

if APPLICATION_MODE in ('RESTRICTED', 'AELO', 'ARISTOTLE'):
    LOCKDOWN = True

STATIC_URL = '%s/static/' % WEBUI_PATHPREFIX

if LOCKDOWN:

    # NOTE: the following variables are needed to send pasword reset emails
    #       using the createnormaluser Django command.
    USE_HTTPS = True
    SERVER_PORT = 443

    # do not log to file unless running through the webui
    if getpass.getuser() == WEBUI_USER:
        try:
            log_filename = os.path.join(WEBUI_ACCESS_LOG_DIR,  # NOQA
                                        'webui-access.log')
        except NameError:
            # In case WEBUI_ACCESS_LOG_DIR is not defined, we use the standard
            # handler, without logging to file
            pass
        else:
            LOGGING['formatters']['timestamp'] = {
                'format': (
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            }
            LOGGING['handlers']['file'] = {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'formatter': 'timestamp',
                'filename': log_filename,
                'mode': 'a'
            }
            LOGGING['loggers']['openquake.server.signals'] = {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': False,
            }

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

    for app in ('django.contrib.auth',
                'django.contrib.contenttypes',
                'openquake.server.user_profile',
                'django.contrib.messages',
                'django.contrib.sessions',
                'django.contrib.admin',
                'openquake.server.announcements',):
        if app not in INSTALLED_APPS:
            INSTALLED_APPS += (app,)

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
                    'django.template.context_processors.request',
                    'django.contrib.messages.context_processors.messages',
                    'openquake.server.utils.oq_server_context_processor',
                ],
            },
        },
    ]

    LOGIN_REDIRECT_URL = '%s/engine/' % WEBUI_PATHPREFIX
    LOGOUT_REDIRECT_URL = '%s/accounts/login/' % WEBUI_PATHPREFIX
    LOGIN_EXEMPT_URLS = (
        '%s/accounts/ajax_login/' % WEBUI_PATHPREFIX,
        'reset_password', 'reset/', 'cookies/',
    )
    LOGIN_URL = '%s/accounts/login/' % WEBUI_PATHPREFIX

    AUTH_PASSWORD_VALIDATORS = [
        {'NAME': 'django.contrib.auth.password_validation.'
                 'UserAttributeSimilarityValidator', },
        {'NAME': 'django.contrib.auth.password_validation.'
                 'MinimumLengthValidator', },
        {'NAME': 'django.contrib.auth.password_validation.'
                 'CommonPasswordValidator', },
        {'NAME': 'django.contrib.auth.password_validation.'
                 'NumericPasswordValidator', },
    ]
