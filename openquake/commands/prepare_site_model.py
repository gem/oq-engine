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
from openquake.baselib import sap, performance, datastore
from openquake.hazardlib import site
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.utils import assoc
from openquake.risklib.asset import Exposure
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


@sap.Script
def prepare_site_model(exposure_xml, vs30_csv, grid_spacing=0,
                       output='sites.csv'):
    """
    Prepare a site_model.csv file from an exposure xml file, a vs30 csv file
    and a grid spacing which can be 0 (meaning no grid). In case of
    no grid warnings are raised for long distance associations.
    """
    hdf5 = datastore.hdf5new()
    with performance.Monitor(hdf5.path, hdf5, measuremem=True) as mon:
        mesh, assets_by_site = Exposure.read(
            exposure_xml).get_mesh_assets_by_site()
        mon.hdf5['assetcol'] = site.SiteCollection.from_points(
            mesh.lons, mesh.lats)
        if grid_spacing:
            grid = mesh.get_convex_hull().discretize(grid_spacing)
            lons, lats = grid.lons, grid.lats
            mode = 'filter'
        else:
            lons, lats = mesh.lons, mesh.lats
            mode = 'warn'
        haz_sitecol = site.SiteCollection.from_points(
            lons, lats, req_site_params={'vs30'})
        if grid_spacing:
            # reduce the grid to the sites with assets
            haz_sitecol, assets_by, discarded = assoc(
                assets_by_site, haz_sitecol, grid_spacing * SQRT2, 'filter')
            haz_sitecol.make_complete()
        vs30orig = read_vs30(vs30_csv.split(','))
        sitecol, vs30, discarded = assoc(
            vs30orig, haz_sitecol, grid_spacing * SQRT2 or FIVEKM, mode)
        sitecol.array['vs30'] = vs30['vs30']
        mon.hdf5['sitecol'] = sitecol
        if discarded:
            mon.hdf5['discarded'] = numpy.array(discarded)
        sids = numpy.arange(len(vs30), dtype=numpy.uint32)
        sites = compose_arrays(sids, vs30, 'site_id')
        write_csv(output, sites)
    if discarded:
        print('Discarded %d sites with assets [use oq plot_assets]' % len(
            discarded))
    print('Saved %d rows in %s' % (len(sitecol), output))
    print(mon)
    return sitecol


prepare_site_model.arg('exposure_xml', 'exposure with header')
prepare_site_model.arg('vs30_csv', 'USGS file lon,lat,vs30 with no header')
prepare_site_model.opt('grid_spacing', 'grid spacing in km (or 0)', type=float)
prepare_site_model.opt('output', 'output file')
