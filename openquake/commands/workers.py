# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2021 GEM Foundation
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
from openquake.baselib import config, parallel as p

ro_commands = ('status', 'inspect')


def main(cmd):
    """
    start/stop the workers, or return their status
    """
    if (cmd not in ro_commands and config.dbserver.multi_user and
            getpass.getuser() not in 'openquake'):
        sys.exit('oq workers only works in single user mode')
    if p.OQDIST in ('dask', 'celery', 'zmq'):
        print(getattr(p, 'workers_' + cmd)())
    else:
        print('Nothing to do: oq_distribute=%s' % p.OQDIST)


main.cmd = dict(help='command', choices='start stop status wait kill'.split())
