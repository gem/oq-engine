#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

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
from openquake.commonlib import sap, nrml


def tidy(fname):
    """
    Give information. You can pass the name of an available calculator,
    a job.ini file, or a zip archive with the input files.
    """
    with open(fname + '.bak', 'w') as f:
        f.write(open(fname).read())
    node = nrml.read(fname)[0]
    with open(fname, 'w') as f:
        nrml.write([node], f)
    print('Reformatted %s, original left in %s.bak' % (fname, fname))

parser = sap.Parser(tidy)
parser.arg('fname', 'NRML file name')
