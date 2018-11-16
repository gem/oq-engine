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
import sys
from openquake.risklib.countries import code2country

# example: utils/addcol.py Exposure_Res_Venezuela.csv country=VEN


def main(fname, namevalue):
    name, value = namevalue.split('=')
    if name == 'country':
        assert value in code2country, value
    header, *lines = open(fname).readlines()
    out = [header.rstrip() + ',' + name]
    for line in lines:
        out.append(line.rstrip() + ',' + value)
    with open(fname, 'w') as f:
        for line in out:
            f.write(line + '\n')


if __name__ == '__main__':
    main(*sys.argv[1:])
