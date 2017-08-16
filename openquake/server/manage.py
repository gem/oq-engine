#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
from __future__ import print_function
import os
import sys
import sqlite3
from django.core.management import execute_from_command_line
from openquake.server.settings import DATABASE
from openquake.server import executor, dbserver
from openquake.server.db import actions
from openquake.server.dbapi import Db
from openquake.commonlib import logs

db = Db(sqlite3.connect, DATABASE['NAME'], isolation_level=None,
        detect_types=sqlite3.PARSE_DECLTYPES, timeout=20)
# NB: I am increasing the timeout from 5 to 20 seconds to see if the random
# OperationalError: "database is locked" disappear in the WebUI tests


# bypass the DbServer and run the action directly
def dbcmd(action, *args):
    """
    A dispatcher to the database server.

    :param action: database action to perform
    :param args: arguments
    """
    return getattr(actions, action)(db, *args)


# the code here is run in development mode; for instance
# $ python manage.py runserver 0.0.0.0:8800
if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "openquake.server.settings")

    if 'runserver' in sys.argv:
        if '--nothreading' in sys.argv:
            logs.dbcmd = dbcmd  # turn this on when debugging
        # check if we are talking to the right server
        err = dbserver.check_foreign()
        if err:
            sys.exit(err)
        logs.dbcmd('upgrade_db')  # make sure the DB exists
        logs.dbcmd('reset_is_running')  # reset the flag is_running

    with executor:
        execute_from_command_line(sys.argv)
