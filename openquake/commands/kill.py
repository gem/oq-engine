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

from openquake.baselib import sap, zeromq
from openquake.commonlib import config


@sap.Script
def kill(calc_id=None):  # NB: calc_id not None is not implemented yet
    """
    Kill a given calculation (defaul all)
    """
    frontend, _backend = config.zmq_urls()
    ncores = sum(tup[-1] for tup in config.get_host_cores())
    with zeromq.Context() as c, c.connect(frontend, zeromq.DEALER) as s:
        for _ in range(ncores):
            s.send_pyobj(['stop', calc_id])

kill.arg('calc_id', 'calculation ID', type=int)
