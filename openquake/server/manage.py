#!/usr/bin/env python
import os
import sys
import imp
import subprocess
from django.core.management import execute_manager
try:
    imp.find_module('settings')  # Assumed to be in the same directory.
except ImportError:
    sys.exit("""Error: Can't find the file 'settings.py' in the directory
        containing %r. It appears you've customized things.\nYou'll have to
        run django-admin.py, passing it your settings module.\n""" % __file__)
import settings
from openquake.server import executor

CELERYD = [sys.executable, '-m', 'celery.bin.celeryd', '-l', 'INFO', '--purge',
           '--logfile', '/tmp/celery.log']


# the code here is run in development mode
if __name__ == "__main__":
    # the django autoreloader sets the variable RUN_MAIN; at the beginning
    # it is None, and only at that moment celery must be run
    run_celery = settings.RUN_CELERY and os.environ.get("RUN_MAIN") is None
    if run_celery:
        cel = subprocess.Popen(CELERYD)
        print 'Starting celery, logging on /tmp/celery.log'
    try:
        with executor:
            execute_manager(settings)
    finally:
        if run_celery:
            print '\nKilling celery'
            cel.kill()
