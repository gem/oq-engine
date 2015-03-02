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

import textwrap
from openquake.commonlib import sap, readinput
from openquake.commonlib.calculators import base


def info(smlt, name=None):
    """
    Give information about the given name. For the moment, only the
    names of the available calculators are recognized.
    """
    if name in base.calculators:
        print textwrap.dedent(base.calculators[name].__doc__.strip())
    elif name:
        print "No info for '%s'" % name
    if smlt:
        oqparam = readinput.get_oqparam(smlt)
        csm = readinput.get_csm_fast(oqparam)
        print csm.info
        print csm.get_rlzs_assoc()


parser = sap.Parser(info)
parser.opt('smlt', 'source model composition info')
parser.arg('name', 'calculator name', choices=base.calculators)
