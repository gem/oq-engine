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
from __future__ import print_function
import os
import logging

from openquake.baselib import general, performance
from openquake.commonlib import sap, datastore
from openquake.commonlib.export import export as export_


# the export is tested in the demos
def export(calc_id, datastore_key, format='csv', export_dir='.'):
    """
    Export an output from the datastore.
    """
    logging.basicConfig(level=logging.INFO)
    dstore = datastore.DataStore(calc_id)
    dstore.export_dir = export_dir
    with performance.Monitor('export', measuremem=True) as mon:
        for fmt in format.split(','):
            fnames = export_((datastore_key, fmt), dstore)
            nbytes = sum(os.path.getsize(f) for f in fnames)
            print('Exported %s in %s' % (general.humansize(nbytes), fnames))
    if mon.duration > 1:
        print(mon)


parser = sap.Parser(export)
parser.arg('calc_id', 'number of the calculation', type=int)
parser.arg('datastore_key', 'datastore key')
parser.arg('format', 'export formats (comma separated)')
parser.arg('export_dir', 'export directory')
