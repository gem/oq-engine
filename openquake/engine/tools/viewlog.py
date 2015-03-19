#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
An extremely simple log viewer, suitable for debugging
"""

import time
import json
import urllib
from openquake.commonlib import sap


def main(calc_id, host='localhost', port=8000):
    base_url = 'http://%s:%s/v1/calc/' % (host, port)
    start = 0
    psize = 10  # page size
    try:
        while True:
            url = base_url + '%d/log/%d:%d' % (calc_id, start, start + psize)
            rows = json.load(urllib.urlopen(url))
            for row in rows:
                print ' '.join(row)
            start += len(rows)
            time.sleep(1)
    except:
        pass

if __name__ == '__main__':
    parser = sap.Parser(main)
    parser.arg('calc_id', 'calculation ID', type=int)
    parser.arg('host', 'hostname of the engine server')
    parser.arg('port', 'port of the engine server')
    parser.callfunc()
