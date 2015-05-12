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

from openquake.commonlib import sap, datastore
from openquake.commonlib.export import export as export_


def export(calc_id, datastore_key, format='csv'):
    """
    Export an output from the datastore.
    """
    dstore = datastore.DataStore(calc_id)
    for fmt in format.split(','):
        fnames = export_((datastore_key, fmt), dstore)
        print 'Exported %s' % fnames


parser = sap.Parser(export)
parser.arg('calc_id', 'number of the calculation', type=int)
parser.arg('datastore_key', 'datastore key')
parser.arg('format', 'export formats (comma separated)')
