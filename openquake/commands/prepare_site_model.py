# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
import os
import gzip
import logging
import numpy
from openquake.baselib import performance, writers, hdf5
from openquake.hazardlib import site, valid
from openquake.risklib.asset import Exposure
from openquake.commonlib import datastore

SQRT2 = 1.414
vs30_dt = numpy.dtype([('lon', float), ('lat', float), ('vs30', float)])


def read(fname):
    if fname.endswith('.gz'):
        return gzip.open(fname, 'rt', encoding='utf-8-sig')
    else:
        return open(fname, 'rt', encoding='utf-8-sig')


def read_vs30(fnames, forbidden):
    """
    :param fnames: a list of CSV files with fields lon,lat,vs30
    :param forbidden: forbidden name for the input files
    :returns: a vs30 array of dtype vs30dt
    """
    data = []
    for fname in fnames:
        check_fname(fname, 'vs30_csv', forbidden)
        with read(fname) as f:
            for line in f:
                data.append(tuple(line.split(',')))
    return numpy.array(data, vs30_dt)


def check_fname(fname, kind, forbidden):
    """
    Raise a NameError if fname == forbidden
    """
    if os.path.basename(fname).lower() == forbidden:
        raise NameError('A file of kind %s cannot be called %r!'
                        % (kind, forbidden))


def associate(sitecol, vs30fnames, assoc_distance):
    if vs30fnames[0].endswith('.hdf5'):
        geohashes = numpy.unique(sitecol.geohash(2))
        with hdf5.File(vs30fnames[0]) as f:
            data = []
            for gh in geohashes:
                try:
                    arr = f[gh][:]
                except KeyError:
                    logging.error('Missing data for geohash %s' % gh)
                else:
                    data.append(arr)
            data = numpy.concatenate(data)
            vs30orig = numpy.zeros(len(data), vs30_dt)
            vs30orig['lon'] = data[:, 0]
            vs30orig['lat'] = data[:, 1]
            vs30orig['vs30'] = data[:, 2]
    else:
        vs30orig = read_vs30(vs30fnames, 'site_model.csv')
    logging.info('Associating {:_d} hazard sites to {:_d} site parameters'.
                 format(len(sitecol), len(vs30orig)))
    return sitecol.assoc(vs30orig, assoc_distance,
                         ignore={'z1pt0', 'z2pt5'})


def main(
        vs30_csv,
        z1pt0=False,
        z2pt5=False,
        vs30measured=False,
        *,
        exposure_xml=None,
        sites_csv=(),
        grid_spacing: float = 0,
        assoc_distance: float = 5,
        output='site_model.csv'):
    """
    Prepare a site_model.csv file from exposure xml files/site csv files,
    vs30 csv files and a grid spacing which can be 0 (meaning no grid).
    For each site the closest vs30 parameter is used. The command can also
    generate (on demand) the additional fields z1pt0, z2pt5 and vs30measured
    which may be needed by your hazard model, depending on the required GSIMs.
    """
    log, hdf5 = datastore.create_job_dstore("prepare site model")
    with hdf5, log:
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
        with performance.Monitor(measuremem=True) as mon:
            if exposure_xml:
                exp = Exposure.read_all(exposure_xml, check_dupl=False)
                hdf5['assetcol'] = assetcol = site.SiteCollection.from_points(
                    exp.mesh.lons, exp.mesh.lats,
                    req_site_params=req_site_params)
                if grid_spacing:
                    grid = exp.mesh.get_convex_hull().dilate(
                        grid_spacing).discretize(grid_spacing)
                    haz_sitecol = site.SiteCollection.from_points(
                        grid.lons, grid.lats, req_site_params=req_site_params)
                    logging.info(
                        'Associating exposure grid with %d locations to %d '
                        'exposure sites', len(haz_sitecol), len(exp.mesh))
                    haz_sitecol, discarded = exp.associate(
                        haz_sitecol, grid_spacing * SQRT2)
                    if len(discarded):
                        logging.info('Discarded %d sites with assets '
                                     '[use oq plot_assets]', len(discarded))
                        hdf5['discarded'] = numpy.array(discarded)
                    haz_sitecol.make_complete()
                else:
                    haz_sitecol = assetcol
                    discarded = []
            elif len(sites_csv):
                if hasattr(sites_csv, 'lon'):
                    # sites_csv can be a DataFrame when used programmatically
                    lons = sites_csv.lon.to_numpy()
                    lats = sites_csv.lat.to_numpy()
                else:
                    # sites_csv is a list of filenames
                    lons, lats = [], []
                    for fname in sites_csv:
                        check_fname(fname, 'sites_csv', output)
                        with read(fname) as csv:
                            for line in csv:
                                if line.startswith('lon,lat'):
                                    continue
                                lon, lat = line.split(',')[:2]
                                lons.append(valid.longitude(lon))
                                lats.append(valid.latitude(lat))
                haz_sitecol = site.SiteCollection.from_points(
                    lons, lats, req_site_params=req_site_params)
                if grid_spacing:
                    grid = haz_sitecol.mesh.get_convex_hull().dilate(
                        grid_spacing).discretize(grid_spacing)
                    haz_sitecol = site.SiteCollection.from_points(
                        grid.lons, grid.lats, req_site_params=req_site_params)
            else:
                raise RuntimeError('Missing exposures or missing sites')
            associate(haz_sitecol, vs30_csv, assoc_distance)
            if z1pt0:
                haz_sitecol.calculate_z1pt0()
            if z2pt5:
                haz_sitecol.calculate_z2pt5()
            hdf5['sitecol'] = haz_sitecol
            if output:
                writers.write_csv(output, haz_sitecol.array[fields])
        logging.info('Saved %d rows in %s' % (len(haz_sitecol), output))
        logging.info(mon)
    return haz_sitecol


main.vs30_csv = dict(help='files with lon,lat,vs30 and no header', nargs='+')
main.z1pt0 = dict(help='build the z1pt0', abbrev='-1')
main.z2pt5 = dict(help='build the z2pt5', abbrev='-2')
main.vs30measured = dict(help='build the vs30measured', abbrev='-3')
main.exposure_xml = dict(help='exposure(s) in XML format', nargs='*')
main.sites_csv = dict(help='sites in CSV format (filenames)', nargs='*')
main.grid_spacing = 'grid spacing in km (the default 0 means no grid)'
main.assoc_distance = 'sites over this distance are discarded'
main.output = 'output file'
