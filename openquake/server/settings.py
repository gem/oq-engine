import os

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
from openquake.engine import settings as oqe_settings

OQSERVER_ROOT = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'django.contrib.messages.context_processors.messages',
    'openquake.server.utils.oq_server_context_processor',
)

MANAGERS = ADMINS

STATIC_URL = '/static/'

MEDIA_ROOT = '%(mediaroot)s'
STATIC_ROOT = '%(staticroot)s'

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(OQSERVER_ROOT, 'static'),
]


DATABASES = oqe_settings.DATABASES

DATABASE_ROUTERS = ['openquake.server.routers.AuthRouter',
                    'openquake.engine.db.routers.OQRouter', ]

AUTH_DATABASES = {
    'auth_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__),
                             'engineserver.sqlite3'),
    }
}

DATABASES.update(AUTH_DATABASES)

ALLOWED_HOSTS = ['*']

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # 'dpam.backends.PAMBackend',
)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Zurich'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'f_6=^^_0%ygcpgmemxcp0p^xq%47yqe%u9pu!ad*2ym^zt+xq$'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

LOCKDOWN = False

# Add additional paths (as regular expressions) that don't require
# authentication.
AUTH_EXEMPT_URLS = ()

ROOT_URLCONF = 'openquake.server.urls'

INSTALLED_APPS = ('django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.messages',
                  'django.contrib.sessions',
                  'django.contrib.staticfiles',
                  'django.contrib.admin',
                  'openquake.server',)

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
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'openquake.server': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 1

try:
    from local_settings import *
except ImportError:
    raise ImportError

if LOCKDOWN:
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
        ('openquake.server.middleware.LoginRequiredMiddleware',)
