#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import time
import os.path
from openquake.baselib import sap
from openquake.baselib.general import safeprint
from openquake.server.manage import db
from openquake.engine.export.core import zipfiles


@sap.Script
def dump(archive, user=None):
    """
    Dump the openquake database and all the complete calculations into a zip
    file. In a multiuser installation must be run as administrator.
    """
    t0 = time.time()
    assert archive.endswith('.zip'), archive
    getfnames = 'select ds_calc_dir || ".hdf5" from job where ?A'
    param = dict(status='complete')
    if user:
        param['user_name'] = user
    fnames = [f for f, in db(getfnames, param) if os.path.exists(f)]
    fnames.append(db.path)
    zipfiles(fnames, archive, safeprint)
    executing = db('select id, description from job where status="executing"')
    dt = time.time() - t0
    safeprint('Archived %d files into %s in %d seconds'
              % (len(fnames), archive, dt))
    if executing:
        safeprint('WARNING: there were calculations executing during the dump')
        safeprint('They have been not copied; please check the correctness of'
                  ' the db.sqlite3 file.')
        for job_id, descr in executing:
            safeprint('%d %s' % (job_id, descr))

dump.arg('archive', 'path to the zip file where to dump the calculations')
dump.arg('user', 'if missing, dump all calculations')
