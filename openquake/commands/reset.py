# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
import shutil
import getpass
from openquake.baselib import sap
from openquake.commonlib import datastore, config
from openquake.engine import logs
from openquake.engine.utils import confirm
from openquake.server import dbserver


@sap.Script
def reset(yes):
    """
    Remove all the datastores and the database of the current user
    """
    if config.flag_set('dbserver', 'multi_user'):
        sys.exit('Please ask your sysadmin to reset the database')

    ok = yes or confirm('Do you really want to destroy the database and all '
                        'datastores? (y/n) ')
    if not ok:
        return

    if dbserver.get_status() == 'running':
        logs.dbcmd('stop')
        print('dbserver stopped')

    dbpath = config.get('dbserver', 'file')
    datadir = os.path.join(os.path.realpath(datastore.DATADIR),
                           getpass.getuser())
    if os.path.exists(datadir):
        shutil.rmtree(datadir)  # datastore of the current user
    print('Removed %s' % datadir)
    try:
        os.remove(dbpath)  # database of the current user
        print('Removed %s' % dbpath)
    except OSError:
        print('You have no permission to remove %s' % dbpath)

reset.flg('yes', 'confirmation')
