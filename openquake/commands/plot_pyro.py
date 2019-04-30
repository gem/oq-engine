# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import numpy
from openquake.baselib import sap
from openquake.commonlib import util


@sap.script
def plot_pyro(calc_id=-1):
    """
    Plot the pyroclastic cloud and the assets
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    dstore = util.read(calc_id)
    sitecol = dstore['sitecol']
    asset_risk = dstore['asset_risk'].value
    pyro, = numpy.where(dstore['multi_peril']['PYRO'] == 1)
    lons = sitecol.lons[pyro]
    lats = sitecol.lats[pyro]
    p.scatter(lons, lats, marker='o', color='red')

    building_pyro, = numpy.where(asset_risk['building-PYRO'] == 1)
    lons = sitecol.lons[building_pyro]
    lats = sitecol.lats[building_pyro]
    p.scatter(lons, lats, marker='.', color='green')
    p.show()


plot_pyro.arg('calc_id', 'a computation id', type=int)
