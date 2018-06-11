# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
from openquake.baselib import sap, config
from openquake.commonlib import logs
from openquake.engine.utils import confirm
from openquake.server import dbserver
from openquake.commands.purge import purge_all


@sap.Script
def reset(yes):
    """
    Remove all the datastores and the database of the current user
    """
    ok = yes or confirm('Do you really want to destroy all your data? (y/n) ')
    if not ok:
        return

    status = dbserver.get_status()
    dbpath = os.path.realpath(os.path.expanduser(config.dbserver.file))

    if not os.path.isfile(dbpath):
        sys.exit('%s does not exist' % dbpath)
    elif status == 'running':
        purge_all()  # datastore of the current user
    if os.access(dbpath, os.W_OK):
        # stop the dbserver
        pid = logs.dbcmd('getpid')
        os.kill(pid, signal.SIGTERM)
        time.sleep(.5)  # give time to stop
        assert dbserver.get_status() == 'not-running'
        print('dbserver stopped')
        os.remove(dbpath)
        print('Removed %s' % dbpath)
    else:
        sys.exit('You cannot remove %s' % dbpath)


reset.flg('yes', 'confirmation')
