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
SQRT2 = 1.414
FIVEKM = 5  # asset-site maximum distance in the case of no grid
vs30_dt = numpy.dtype([('lon', F32), ('lat', F32), ('vs30', F32)])


def read_vs30(fnames):
    data = []
    for fname in fnames:
        for line in open(fname, 'U', encoding='utf-8-sig'):
            data.append(tuple(line.split(',')))
    return numpy.array(data, vs30_dt)


def read_exposure(fnames):
    lonlats = set()
    for fname in fnames:
        f = open(fname, 'U', encoding='utf-8-sig')
        next(f)
        with f:
            for line in f:
                _id, lon, lat = line.split(',')[:3]
                lonlats.add((lon, lat))
    lons, lats = zip(*sorted(lonlats))
    return Mesh(numpy.array(lons, F32), numpy.array(lats, F32))


@sap.Script
def prepare_site_model(exposure_csv, vs30_csv, grid_spacing=0,
                       output='sites.csv'):
    """
    Prepare a site_model.csv file from an exposure, a vs30 csv file
    and a grid spacing which can be 0 (meaning no grid).
    """
    with performance.Monitor(measuremem=True) as mon:
        mesh = read_exposure(exposure_csv.split(','))
        if grid_spacing:
            grid = mesh.get_convex_hull().discretize(grid_spacing)
            lons, lats = grid.lons, grid.lats
            mode = 'filter'
        else:
            lons, lats = mesh.lons, mesh.lats
            mode = 'warn'
        sitecol = site.SiteCollection.from_points(
            lons, lats, req_site_params={'vs30'})
        vs30orig = read_vs30(vs30_csv.split(','))
        sitecol, vs30, _discarded = assoc(
            vs30orig, sitecol, grid_spacing * SQRT2 or FIVEKM, mode)
        sitecol.array['vs30'] = vs30['vs30']
        sids = numpy.arange(len(vs30), dtype=numpy.uint32)
        sites = compose_arrays(sids, vs30, 'site_id')
        write_csv(output, sites)
    print(sitecol)
    print('Saved %d rows in %s' % (len(sitecol), output))
    print(mon)
    return sitecol


prepare_site_model.arg('exposure_csv', 'exposure with header')
prepare_site_model.arg('vs30_csv', 'USGS file lon,lat,vs30 with no header')
prepare_site_model.opt('grid_spacing', 'grid spacing in km (or 0)', type=float)
prepare_site_model.opt('output', 'output file')
