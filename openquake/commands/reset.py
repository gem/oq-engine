# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
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
from openquake.baselib import sap
from openquake.commonlib import datastore, config
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

    if config.flag_set('dbserver', 'multi_user'):
        purge_all()  # remove data of the current user only
        return

    # else: fast way of removing everything

    if dbserver.get_status() == 'running':
        logs.dbcmd('stop')
        print('dbserver stopped')

    dbpath = os.path.realpath(
        os.path.expanduser(config.get('dbserver', 'file')))
    try:
        os.remove(dbpath)  # database of the current user
        print('Removed %s' % dbpath)
    except OSError as exc:
        print(exc, file=sys.stderr)
    datadir = os.path.realpath(datastore.DATADIR)
    if os.path.exists(datadir):
        shutil.rmtree(datadir)  # datastore of the current user
    print('Removed %s' % datadir)

reset.flg('yes', 'confirmation')
