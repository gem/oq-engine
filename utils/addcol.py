#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

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
from openquake.baselib import sap
from openquake.risklib.countries import code2country

# example: utils/addcol.py country=VEN Exposure_Res_Venezuela.csv


@sap.Script
def addcol(namevalue, fnames):
    name, value = namevalue.split('=')
    if name == 'country':
        assert value in code2country, value
    for fname in fnames:
        header, *lines = open(fname).readlines()
        out = [header.rstrip() + ',' + name]
        for line in lines:
            out.append(line.rstrip() + ',' + value)
        with open(fname, 'w') as f:
            for line in out:
                f.write(line + '\n')
        print('Added %s to %s' % (namevalue, fname))


addcol.arg('namevalue', 'string of the form column_name=column_value')
addcol.arg('fnames', 'CSV files to update', nargs='+')

if __name__ == '__main__':
    addcol.callfunc()
