# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import os

from openquake.baselib import general, performance
from openquake.commonlib import datastore
from openquake.calculators.export import export as export_


# the export is tested in the demos
def main(datastore_key, calc_id: int = -1, *, exports='csv', export_dir='.'):
    """
    Export an output from the datastore. To see the available datastore
    keys, use the command `oq info exports`.
    """
    dstore = datastore.read(calc_id)
    parent_id = dstore['oqparam'].hazard_calculation_id
    if parent_id:
        dstore.parent = datastore.read(parent_id)
    dstore.export_dir = export_dir
    with performance.Monitor('export', measuremem=True) as mon:
        for fmt in exports.split(','):
            fnames = export_((datastore_key, fmt), dstore)
            nbytes = sum(os.path.getsize(f) for f in fnames)
            print('Exported %s in %s' % (general.humansize(nbytes), fnames))
    if mon.duration > 1:
        print(mon)
    dstore.close()


main.datastore_key = 'datastore key'
main.calc_id = 'number of the calculation'
main.exports = 'export formats (comma separated)'
main.export_dir = dict(help='export directory', abbrev='-d')
