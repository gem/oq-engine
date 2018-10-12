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
import logging
import numpy
from openquake.baselib import sap, performance, datastore
from openquake.hazardlib import site
from openquake.hazardlib.geo.utils import assoc
from openquake.risklib.asset import Exposure
from openquake.commonlib.writers import write_csv
from openquake.commonlib.util import compose_arrays


F32 = numpy.float32
SQRT2 = 1.414
vs30_dt = numpy.dtype([('lon', F32), ('lat', F32), ('vs30', F32)])


def read_vs30(fnames):
    data = []
    for fname in fnames:
        for line in open(fname, 'U', encoding='utf-8-sig'):
            data.append(tuple(line.split(',')))
    return numpy.array(data, vs30_dt)


@sap.Script
def prepare_site_model(exposure_xml, vs30_csv, grid_spacing=0,
                       site_param_distance=5, output='sites.csv'):
    """
    Prepare a site_model.csv file from an exposure xml file, a vs30 csv file
    and a grid spacing which can be 0 (meaning no grid). Sites far away from
    the vs30 records are discarded and you can see them with the command
    `oq plot_assets`. It is up to you decide if you need to fix your exposure
    or if it is right to ignore the discarded sites.
    """
    logging.basicConfig(level=logging.INFO)
    hdf5 = datastore.hdf5new()
    with performance.Monitor(hdf5.path, hdf5, measuremem=True) as mon:
        mesh, assets_by_site = Exposure.read(
            exposure_xml, check_dupl=False).get_mesh_assets_by_site()
        mon.hdf5['assetcol'] = assetcol = site.SiteCollection.from_points(
            mesh.lons, mesh.lats, req_site_params={'vs30'})
        if grid_spacing:
            grid = mesh.get_convex_hull().discretize(grid_spacing)
            haz_sitecol = site.SiteCollection.from_points(
                grid.lons, grid.lats, req_site_params={'vs30'})
            logging.info('Reducing exposure grid with %d locations to %d sites'
                         ' with assets', len(haz_sitecol), len(assets_by_site))
            haz_sitecol, assets_by, _discarded = assoc(
                assets_by_site, haz_sitecol, grid_spacing * SQRT2, 'filter')
            haz_sitecol.make_complete()
        else:
            haz_sitecol = assetcol
        vs30orig = read_vs30(vs30_csv.split(','))
        logging.info('Associating %d hazard sites to %d site parameters',
                     len(haz_sitecol), len(vs30orig))
        sitecol, vs30, discarded = assoc(
            vs30orig, haz_sitecol,
            grid_spacing * SQRT2 or site_param_distance, 'filter')
        sitecol.array['vs30'] = vs30['vs30']
        mon.hdf5['sitecol'] = sitecol
        if discarded:
            mon.hdf5['discarded'] = numpy.array(discarded)
        sids = numpy.arange(len(vs30), dtype=numpy.uint32)
        sites = compose_arrays(sids, vs30, 'site_id')
        write_csv(output, sites)
    if discarded:
        logging.info('Discarded %d sites with assets [use oq plot_assets]',
                     len(discarded))
    logging.info('Saved %d rows in %s' % (len(sitecol), output))
    logging.info(mon)
    return sitecol


prepare_site_model.arg('exposure_xml', 'exposure in XML format')
prepare_site_model.arg('vs30_csv', 'USGS file lon,lat,vs30 with no header')
prepare_site_model.opt('grid_spacing', 'grid spacing in km (or 0)', type=float)
prepare_site_model.opt('site_param_distance',
                       'sites over this distance are discarded', type=float)
prepare_site_model.opt('output', 'output file')
