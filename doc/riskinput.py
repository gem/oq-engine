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

"""
This is an example of script which is useful if you want to play with
the RiskInput objects. You can enable the pdb and see what is inside
the objects.
"""
from __future__ import print_function

import sys
from openquake.commonlib import readinput
from openquake.calculators.calc import calc_gmfs

if __name__ == '__main__':
    job_ini = sys.argv[1:]
    o = readinput.get_oqparam(job_ini)
    exposure = readinput.get_exposure(o)
    sitecol, assets_by_site = readinput.get_sitecol_assets(o, exposure)
    risk_model = readinput.get_risk_model(o)
    gmfs_by_imt = calc_gmfs(o, sitecol)

    for imt in gmfs_by_imt:
        ri = risk_model.build_input(imt, gmfs_by_imt[imt], assets_by_site)
        print(ri)
        #for out in risk_model.gen_outputs([ri]):
        #    print out
        # import pdb; pdb.set_trace()
