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


def info(name=None, filtersources=False):
    """
    Give information. You can pass the name of an available calculator or
    also a job.ini file.
    """
    if name in base.calculators:
        print textwrap.dedent(base.calculators[name].__doc__.strip())
    elif name.endswith('.ini'):
        oqparam = readinput.get_oqparam(name)
        sitecol = (readinput.get_site_collection(oqparam)
                   if filtersources else None)
        csm = readinput.get_composite_source_model(
            oqparam, sitecol, prefilter=filtersources, in_memory=filtersources)
        assoc = csm.get_rlzs_assoc()
        print assoc.csm_info
        print assoc
    else:
        print "No info for '%s'" % name

parser = sap.Parser(info)
parser.arg('name', 'calculator name or job.ini file')
parser.flg('filtersources', 'flag to enable filtering of the source models')
