# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (C) 2017-2019 GEM Foundation

# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import time
import getpass
import os.path
import zipfile
import sqlite3
import requests
from openquake.baselib import sap
from openquake.baselib.general import safeprint
from openquake.server.dbapi import Db


@sap.script
def restore(archive, oqdata):
    """
    Build a new oqdata directory from the data contained in the zip archive
    """
    if os.path.exists(oqdata):
        sys.exit('%s exists already' % oqdata)
    if '://' in archive:
        # get the zip archive from an URL
        resp = requests.get(archive)
        _, archive = archive.rsplit('/', 1)
        with open(archive, 'wb') as f:
            f.write(resp.content)
    if not os.path.exists(archive):
        sys.exit('%s does not exist' % archive)
    t0 = time.time()
    oqdata = os.path.abspath(oqdata)
    assert archive.endswith('.zip'), archive
    os.mkdir(oqdata)
    zipfile.ZipFile(archive).extractall(oqdata)
    dbpath = os.path.join(oqdata, 'db.sqlite3')
    db = Db(sqlite3.connect, dbpath, isolation_level=None,
            detect_types=sqlite3.PARSE_DECLTYPES)
    n = 0
    for fname in os.listdir(oqdata):
        mo = re.match('calc_(\d+)\.hdf5', fname)
        if mo:
            job_id = int(mo.group(1))
            fullname = os.path.join(oqdata, fname)[:-5]  # strip .hdf5
            db("UPDATE job SET user_name=?x, ds_calc_dir=?x WHERE id=?x",
               getpass.getuser(), fullname, job_id)
            safeprint('Restoring ' + fname)
            n += 1
    dt = time.time() - t0
    safeprint('Extracted %d calculations into %s in %d seconds'
              % (n, oqdata, dt))


restore.arg('archive', 'path to a zip file')
restore.arg('oqdata', 'path to an oqdata directory')
