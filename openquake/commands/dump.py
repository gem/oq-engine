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
from openquake.server.manage import db
from openquake.engine.export.core import zipfiles


@sap.Script
def dump(archive):
    """
    Dump the openquake database and all the complete calculations into a zip
    file. In a multiuser installation must be run as administrator.
    """
    t0 = time.time()
    assert archive.endswith('.zip'), archive
    query = 'select ds_calc_dir || ".hdf5" from job where status="complete"'
    fnames = [fname for fname, in db(query) if os.path.exists(fname)]
    fnames.append(db.path)
    zipfiles(fnames, archive, print)
    dt = time.time() - t0
    print('Archived %d files into %s in %d seconds'
          % (len(fnames), archive, dt))

dump.arg('archive', 'path to a zip file')
