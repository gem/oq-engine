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
from openquake.commonlib import sap
from openquake.commonlib.calculators import base


def info(name):
    """
    Give information about the given name. For the moment, only the
    names of the available calculators are recognized.
    """
    if name in base.calculators:
        print textwrap.dedent(base.calculators[name].__doc__.strip())
    else:
        print "No info for '%s'" % name

parser = sap.Parser(info)
parser.arg('name', 'calculator name', choices=base.calculators)
