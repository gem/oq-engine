# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
import logging
import numpy
from openquake.baselib import sap, performance, datastore
from openquake.hazardlib import site, valid
from openquake.hazardlib.geo.utils import assoc
from openquake.risklib.asset import Exposure
from openquake.commonlib.writers import write_csv

F32 = numpy.float32
SQRT2 = 1.414
vs30_dt = numpy.dtype([('lon', F32), ('lat', F32), ('vs30', F32)])


# TODO: equivalents of calculate_z1pt0 and calculate_z2pt5_ngaw2
# are inside some GSIM implementations, we should avoid duplication
def calculate_z1pt0(vs30):
    '''
    Reads an array of vs30 values (in m/s) and
    returns the depth to the 1.0 km/s velocity horizon (in m)
    Ref: Chiou & Youngs (2014) California model
    :param vs30: the shear wave velocity (in m/s) at a depth of 30m
    '''
    c1 = 571 ** 4.
    c2 = 1360.0 ** 4.
    return numpy.exp((-7.15 / 4.0) * numpy.log((vs30 ** 4. + c1) / (c2 + c1)))


def calculate_z2pt5_ngaw2(vs30):
    '''
    Reads an array of vs30 values (in m/s) and
    returns the depth to the 2.5 km/s velocity horizon (in km)
    Ref: Campbell, K.W. & Bozorgnia, Y., 2014.
    'NGA-West2 ground motion model for the average horizontal components of
    PGA, PGV, and 5pct damped linear acceleration response spectra.'
    Earthquake Spectra, 30(3), pp.1087–1114.

    :param vs30: the shear wave velocity (in m/s) at a depth of 30 m
    '''
    c1 = 7.089
    c2 = -1.144
    z2pt5 = numpy.exp(c1 + numpy.log(vs30) * c2)
    return z2pt5


def read_vs30(fnames):
    """
    :param fnames: a list of CSV files with fields lon,lat,vs30
    :returns: a vs30 array of dtype vs30dt
    """
    data = []
    for fname in fnames:
        for line in open(fname, encoding='utf-8-sig'):
            data.append(tuple(line.split(',')))
    return numpy.array(data, vs30_dt)


@sap.script
def prepare_site_model(exposure_xml, sites_csv, vs30_csv,
                       z1pt0, z2pt5, vs30measured, grid_spacing=0,
                       assoc_distance=5, output='site_model.csv'):
    """
    Prepare a site_model.csv file from exposure xml files/site csv files,
    vs30 csv files and a grid spacing which can be 0 (meaning no grid).
    For each site the closest vs30 parameter is used. The command can also
    generate (on demand) the additional fields z1pt0, z2pt5 and vs30measured
    which may be needed by your hazard model, depending on the required GSIMs.
    """
    hdf5 = datastore.hdf5new()
    req_site_params = {'vs30'}
    fields = ['lon', 'lat', 'vs30']
    if z1pt0:
        req_site_params.add('z1pt0')
        fields.append('z1pt0')
    if z2pt5:
        req_site_params.add('z2pt5')
        fields.append('z2pt5')
    if vs30measured:
        req_site_params.add('vs30measured')
        fields.append('vs30measured')
    with performance.Monitor(hdf5.path, hdf5, measuremem=True) as mon:
        if exposure_xml:
            mesh, assets_by_site = Exposure.read(
                exposure_xml, check_dupl=False).get_mesh_assets_by_site()
            mon.hdf5['assetcol'] = assetcol = site.SiteCollection.from_points(
                mesh.lons, mesh.lats, req_site_params=req_site_params)
            if grid_spacing:
                grid = mesh.get_convex_hull().dilate(
                    grid_spacing).discretize(grid_spacing)
                haz_sitecol = site.SiteCollection.from_points(
                    grid.lons, grid.lats, req_site_params=req_site_params)
                logging.info(
                    'Associating exposure grid with %d locations to %d '
                    'exposure sites', len(haz_sitecol), len(assets_by_site))
                haz_sitecol, assets_by, discarded = assoc(
                    assets_by_site, haz_sitecol,
                    grid_spacing * SQRT2, 'filter')
                if len(discarded):
                    logging.info('Discarded %d sites with assets '
                                 '[use oq plot_assets]', len(discarded))
                    mon.hdf5['discarded'] = numpy.array(discarded)
                haz_sitecol.make_complete()
            else:
                haz_sitecol = assetcol
                discarded = []
        elif sites_csv:
            lons, lats = [], []
            for fname in sites_csv:
                with open(fname) as csv:
                    for line in csv:
                        if line.startswith('lon,lat'):  # possible header
                            continue
                        lon, lat = line.split(',')[:2]
                        lons.append(valid.longitude(lon))
                        lats.append(valid.latitude(lat))
            haz_sitecol = site.SiteCollection.from_points(
                lons, lats, req_site_params=req_site_params)
            if grid_spacing:
                grid = mesh.get_convex_hull().dilate(
                    grid_spacing).discretize(grid_spacing)
                haz_sitecol = site.SiteCollection.from_points(
                    grid.lons, grid.lats, req_site_params=req_site_params)
        else:
            raise RuntimeError('Missing exposures or missing sites')
        vs30orig = read_vs30(vs30_csv)
        logging.info('Associating %d hazard sites to %d site parameters',
                     len(haz_sitecol), len(vs30orig))
        sitecol, vs30, _ = assoc(
            vs30orig, haz_sitecol, assoc_distance, 'warn')
        sitecol.array['vs30'] = vs30['vs30']
        if z1pt0:
            sitecol.array['z1pt0'] = calculate_z1pt0(vs30['vs30'])
        if z2pt5:
            sitecol.array['z2pt5'] = calculate_z2pt5_ngaw2(vs30['vs30'])
        if vs30measured:
            sitecol.array['vs30measured'] = False  # it is inferred
        mon.hdf5['sitecol'] = sitecol
        write_csv(output, sitecol.array[fields])
    logging.info('Saved %d rows in %s' % (len(sitecol), output))
    logging.info(mon)
    return sitecol


prepare_site_model.opt('exposure_xml', 'exposure(s) in XML format', nargs='*')
prepare_site_model.opt('sites_csv', 'sites in CSV format', nargs='*')
prepare_site_model.arg('vs30_csv', 'files with lon,lat,vs30 and no header',
                       nargs='+')
prepare_site_model.flg('z1pt0', 'build the z1pt0', '-1')
prepare_site_model.flg('z2pt5', 'build the z2pt5', '-2')
prepare_site_model.flg('vs30measured', 'build the vs30measured', '-3')
prepare_site_model.opt('grid_spacing', 'grid spacing in km '
                       '(the default 0 means no grid)', type=float)
prepare_site_model.opt('assoc_distance',
                       'sites over this distance are discarded', type=float)
prepare_site_model.opt('output', 'output file')
