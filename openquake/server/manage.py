#!/usr/bin/env python3
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
import os
import sys
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"
from django.core.management import execute_from_command_line
from openquake.server import dbserver
from openquake.server.db import actions
from openquake.commonlib import logs


# bypass the DbServer and run the action directly
def fakedbcmd(action, *args):
    """
    A dispatcher to the database server.

    :param action: database action to perform
    :param args: arguments
    """
    return getattr(actions, action)(dbserver.db, *args)


# the code here is run in development mode; for instance
# $ python manage.py runserver 0.0.0.0:8800
if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "openquake.server.settings")

    if 'runserver' in sys.argv:
        if '--nothreading' in sys.argv:
            logs.dbcmd = fakedbcmd  # turn this on when debugging
        # check if we are talking to the right server
        err = dbserver.check_foreign()
        if err:
            sys.exit(err)
        logs.dbcmd('upgrade_db')  # make sure the DB exists

    setproctitle('oq-webui')
    execute_from_command_line(sys.argv)
