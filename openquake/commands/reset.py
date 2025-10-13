# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
import time
import signal
import getpass
from openquake.baselib import config
from openquake.commonlib import logs
from openquake.engine.utils import confirm
from openquake.server import dbserver
from openquake.commands.purge import purge_one, purge_all


def main(yes=False):
    """
    Remove all the datastores and the database of the current user
    """
    ok = yes or confirm('Do you really want to destroy all your data? (y/n) ')
    if not ok:
        return

    dbpath = os.path.realpath(os.path.expanduser(config.dbserver.file))
    if not os.path.isfile(dbpath):
        sys.exit('%s does not exist' % dbpath)
    else:
        dbserver.ensure_on()  # start the dbserver in a subprocess
        user = getpass.getuser()
        for calc_id in logs.dbcmd('get_calc_ids', user):
            purge_one(calc_id, user, force=True)
        if os.access(dbpath, os.W_OK):   # single user mode
            purge_all(user)  # calculations in oqdata not in the db
            if config.dbserver.host != '127.0.0.1':
                # stop the dbserver first
                pid = logs.dbcmd('getpid')
                os.kill(pid, signal.SIGTERM)
                time.sleep(.5)  # give time to stop
                assert dbserver.get_status() == 'not-running'
                print('dbserver stopped')
            # remove the database
            os.remove(dbpath)
            print('Removed %s' % dbpath)


main.yes = 'confirmation'
