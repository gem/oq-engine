#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

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

from openquake.commonlib import nrml, readinput, sap


def check(fname, pprint):
    """
    Check the validity of NRML files and .ini files.
    Optionally, displays NRML files in indented format.
    """
    if fname.endswith('.xml'):
        node = nrml.read(fname)
        if pprint:
            print node.to_str()
    elif fname.endswith('.ini'):
        oqparam = readinput.getoqparam(fname)
        if pprint:
            print oqparam


parser = sap.Parser(check)
parser.arg('fname', 'file in NRML format or job.ini file')
parser.flg('pprint', 'display in indented format')
