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
"""
Associate assets to the vs30 grid coming from the USGS.
Here is an example of usage:

$ oq prepare_site_model Exposure/Exposure_Res_Ecuador.csv \
                        Vs30/usgs_vs30_data/Ecuador.csv 10
"""
import numpy
from openquake.baselib import sap, performance
from openquake.hazardlib import site
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.utils import assoc
from openquake.commonlib.writers import write_csv
from openquake.commonlib.util import compose_arrays


F32 = numpy.float32
vs30_dt = numpy.dtype([('lon', F32), ('lat', F32), ('vs30', F32)])


def read_vs30(fname):
    data = [tuple(line.split(','))
            for line in open(fname, 'U', encoding='utf-8-sig')]
    return numpy.array(data, vs30_dt)


def read_exposure(fname):
    lons, lats = [], []
    f = open(fname, 'U', encoding='utf-8-sig')
    next(f)
    with f:
        for line in f:
            _id, lon, lat = line.split(',')[:3]
            lons.append(lon)
            lats.append(lat)
    return Mesh(numpy.array(lons, F32), numpy.array(lats, F32))


@sap.Script
def prepare_site_model(exposure_csv, vs30_csv, grid_spacing):
    """
    Prepare a site_model.csv file from an exposure, a vs30 csv file
    and a grid spacing which can be 0 (meaning no grid).
    """
    with performance.Monitor(measuremem=True) as mon:
        mesh = read_exposure(exposure_csv)
        if grid_spacing:
            grid = mesh.get_convex_hull().discretize(grid_spacing)
            lons, lats = grid.lons, grid.lats
        else:
            lons, lats = mesh.lons, mesh.lats
        sitecol = site.SiteCollection.from_points(lons, lats)
        vs30 = read_vs30(vs30_csv)
        sitecol, vs30, _discarded = assoc(
            vs30, sitecol, grid_spacing * 1.414, 'filter')
        sids = numpy.arange(len(vs30), dtype=numpy.uint32)
        sites = compose_arrays(sids, vs30, 'site_id')
        write_csv('sites.csv', sites)
    print(sitecol)
    print('Saved %d rows in sites.csv' % len(vs30))
    print(mon)


prepare_site_model.arg('exposure_csv', 'exposure')
prepare_site_model.arg('vs30_csv', 'USGS file')
prepare_site_model.arg('grid_spacing', 'grid spacing in km (or 0)', type=float)
