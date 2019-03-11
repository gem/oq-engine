# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import sys
import getpass
from openquake.baselib import sap, config, workerpool


@sap.script
def workers(cmd):
    """
    start/stop/restart the workers, or return their status
    """
    if config.dbserver.multi_user and getpass.getuser() != 'openquake':
        sys.exit('oq workers only works in single user mode')

    master = workerpool.WorkerMaster(config.dbserver.host,
                                     **config.zworkers)
    print(getattr(master, cmd)())


workers.arg('cmd', 'command', choices='start stop status restart'.split())
