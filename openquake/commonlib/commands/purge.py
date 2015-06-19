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
from openquake.commonlib import sap, datastore
import shutil


def purge(calc_id):
    """
    Remove the given calculation. If calc_id is 0, remove all calculations.
    """
    if not calc_id:
        shutil.rmtree(datastore.DATADIR)
        print('Removed %s' % datastore.DATADIR)
    else:
        calc_dir = datastore.DataStore(calc_id).calc_dir
        shutil.rmtree(calc_dir)
        print('Removed %s' % calc_dir)


parser = sap.Parser(purge)
parser.arg('calc_id', 'calculation ID', type=int)
