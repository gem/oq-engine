# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source.rupture import BaseRupture


def new_ctx(cmaker, n, mag=6., rake=0., lons=(), lats=()):
    """
    Build a context array starting from a fake rupture and site collection
    """
    if len(lons) or len(lats):
        assert len(lons) == len(lats) == n
    else:
        lons = lats = np.zeros(n)
    lon, lat = lons[0], lats[0]
    hyp = Point(lon, lat + 0.5)
    trc = Line([Point(lon, lat), Point(lon, lat + 1.)])
    sfc = SimpleFaultSurface.from_fault_data(
        fault_trace=trc, upper_seismogenic_depth=0,
        lower_seismogenic_depth=15, dip=90., mesh_spacing=10.)
    rup = BaseRupture(mag, rake, '*', hyp, sfc)
    rup.rup_id = 1
    sitecol = SiteCollection([Site(Point(*ll)) for ll in zip(lons, lats)])
    rctxs = cmaker.gen_contexts([[[rup], sitecol]], src_id=0)
    return cmaker.recarray(list(rctxs))
