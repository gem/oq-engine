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

"""
An extremely simple log viewer, suitable for debugging
"""

import time
import json
try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen
from openquake.baselib import sap


@sap.Script
def viewlog(calc_id, host='localhost', port=8000):
    """
    Extract the log of the given calculation ID from the WebUI
    """
    base_url = 'http://%s:%s/v1/calc/' % (host, port)
    start = 0
    psize = 10  # page size
    try:
        while True:
            url = base_url + '%d/log/%d:%d' % (calc_id, start, start + psize)
            rows = json.load(urlopen(url))
            for row in rows:
                print(' '.join(row))
            start += len(rows)
            time.sleep(1)
    except:
        pass

if __name__ == '__main__':
    viewlog.arg('calc_id', 'calculation ID', type=int)
    viewlog.arg('host', 'hostname of the engine server')
    viewlog.arg('port', 'port of the engine server')
    viewlog.callfunc()
