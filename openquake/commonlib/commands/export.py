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

import shutil
from openquake.commonlib import sap, datastore
from openquake.commonlib.export import ds_export


def export(calc_id, output_key, format='csv'):
    """
    Export an output from the datastore.
    """
    dstore = datastore.DataStore(calc_id)
    for fmt in format.split(','):
        ekey = tuple(output_key.split('-') + [fmt])
        epath = dstore.export_path(ekey)
        if ekey[-1] == ekey[-2]:
            # the export format is the same as the inner format
            shutil.copy(dstore.path(ekey[:-1]), epath)
        else:
            ds_export(ekey, dstore)
        print 'Exported %s' % epath


parser = sap.Parser(export)
parser.arg('calc_id', 'number of the calculation', type=int)
parser.arg('output_key', 'output key (dash separated)')
parser.arg('format', 'export formats (comma separated)')
