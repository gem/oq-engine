# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
The OpenQuake supervising facilities consist of :mod:`job supervisor
<openquake.engine.supervising.supervisor>` which always runs paired with actual
``bin/openquake`` process.
"""

import os
import errno


def is_pid_running(pid):
    """
    Check if a process is still running.

    :param pid: the process id
    :type pid: int

    :return: True if the process is running, False otherwise
    """
    # NB: Process ids are not globally unique, so existance of process with
    # given pid doesn't guarantee that the job/supervisor/whatever is alive.
    try:
        os.kill(pid, 0)
    except OSError as e:
        return e.errno != errno.ESRCH
    else:
        return True
