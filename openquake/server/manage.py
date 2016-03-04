#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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
import sys
import celery
import subprocess
from django.core.management import execute_from_command_line
from openquake.server import executor
if celery.__version__ < '3.0.0':
    CELERY = [sys.executable, '-m', 'celery.bin.celeryd', '-l', 'INFO',
              '--purge', '--logfile', '/tmp/celery.log']
else:
    CELERY = [sys.executable, '-m', 'celery.bin.celery', 'worker',
              '-l', 'INFO', '--purge', '--logfile', '/tmp/celery.log']


# the code here is run in development mode; for instance
# $ python manage.py runserver 0.0.0.0:8800 celery
if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "openquake.server.settings")
    # notice that the import must be done after the os.environ.setdefault;
    # the issue is that importing openquake.engine sets a wrong
    # DJANGO_SETTINGS_MODULE environment variable, causing the irritating
    # CommandError: You must set settings.ALLOWED_HOSTS if DEBUG is False.

    from openquake.server.db import models
    models.getcursor().execute(
        # cleanup of the flag oq_job.is_running
        'UPDATE job SET is_running=false WHERE is_running')

    # the django autoreloader sets the variable RUN_MAIN; at the beginning
    # it is None, and only at that moment celery must be run
    run_celery = 'celery' in sys.argv and os.environ.get("RUN_MAIN") is None
    if run_celery:
        sys.argv.remove('celery')
        cel = subprocess.Popen(CELERY)
        print 'Starting celery, logging on /tmp/celery.log'
    try:
        with executor:
            execute_from_command_line(sys.argv)
    finally:
        if run_celery:
            print '\nKilling celery'
            cel.kill()
