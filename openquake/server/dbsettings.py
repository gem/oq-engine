PLATFORM_DATABASES = {
    'platform': {
        'HOST': 'localhost',
        'NAME': "oqplatform",
        'USER': 'oqplatform',
        'PASSWORD': 'openquake',
        'PORT': 5432
    }
}


# Load more settings from a file called local_settings.py if it exists
try:
    from local_settings import *
except ImportError:
    pass
