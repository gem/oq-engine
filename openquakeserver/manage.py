#!/usr/bin/env python
from django.core.management import execute_manager
import imp
try:
    imp.find_module('settings')  # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.exit("""Error: Can't find the file 'settings.py' in the directory
        containing %r. It appears you've customized things.\nYou'll have to
        run django-admin.py, passing it your settings module.\n""" % __file__)

import settings

from engine import executor

if __name__ == "__main__":
    with executor:
        execute_manager(settings)
        from django.db import connection
        connection.close()
