# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2026 GEM Foundation
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
from openquake.hazardlib import nrml, site, sourceconverter, valid
from openquake.hazardlib.correlation_models.circulant_embedding import (
    RegularGridLayout)
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.regular_grid import regular_grid
from openquake.hazardlib.source.rupture import get_ruptures
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
                         'warn', ignore={'z1pt0', 'z2pt5'})


def _grid(mesh, spacing, regular):
    """Keep the old geographic discretization unless a regular grid is requested."""
    if regular:
        return regular_grid(mesh, spacing)
    return mesh.get_convex_hull().dilate(spacing).discretize(spacing)


def _exposure_sites(exposure_xml, spacing, regular, req_site_params, hdf5):
    exp = Exposure.read_all(exposure_xml, check_dupl=False)
    hdf5['assetcol'] = assetcol = site.SiteCollection.from_points(
        exp.mesh.lons, exp.mesh.lats, req_site_params=req_site_params)
    if not spacing:
        return assetcol
    grid = _grid(exp.mesh, spacing, regular)
    haz_sitecol = site.SiteCollection.from_points(
        grid.lons, grid.lats, req_site_params=req_site_params)
    if regular:
        # CE needs the complete rectangle, including cells without assets.
        return haz_sitecol
    logging.info('Associating exposure grid with %d locations to %d '
                 'exposure sites', len(haz_sitecol), len(exp.mesh))
    haz_sitecol, discarded = exp.associate(haz_sitecol, spacing * SQRT2)
    if len(discarded):
        logging.info('Discarded %d sites with assets '
                     '[use oq plot_assets]', len(discarded))
        hdf5['discarded'] = numpy.array(discarded)
    haz_sitecol.make_complete()
    return haz_sitecol


def _csv_sites(sites_csv, spacing, regular, req_site_params, output):
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
    if spacing:
        mesh = _grid(haz_sitecol.mesh, spacing, regular)
        haz_sitecol = site.SiteCollection.from_points(
            mesh.lons, mesh.lats, req_site_params=req_site_params)
    return haz_sitecol


def _check_exported_grid(output):
    """Validate the CSV coordinates that a calculation will actually read."""
    data = numpy.genfromtxt(output, names=True, delimiter=',',
                            usecols=('lon', 'lat'))
    RegularGridLayout.from_sites(Mesh(data['lon'], data['lat']))


def _rupture_sites(filename, spacing, maximum_distance, mesh_spacing,
                   req_site_params):
    """Read one scenario rupture and use all its finite surface vertices."""
    filename = str(filename)
    suffix = os.path.splitext(filename)[1].lower()
    if suffix in ('.xml', '.nrml'):
        nodes = nrml.read(filename)
        if len(nodes) != 1:
            raise ValueError('Rupture file must contain exactly one rupture')
        rupture = sourceconverter.RuptureConverter(mesh_spacing).convert_node(
            nodes[0])
    elif suffix == '.csv':
        if len(hdf5.read_csv(filename, {None: str})) != 1:
            raise ValueError('Rupture CSV must contain exactly one rupture')
        rupture = get_ruptures(filename)[0]
    else:
        raise ValueError('Rupture must be XML/NRML or OpenQuake rupture CSV')
    if rupture.surface is None:
        point = rupture.hypocenter
        lons, lats = numpy.array([point.longitude]), numpy.array(
            [point.latitude])
    else:
        lons = rupture.surface.mesh.lons.ravel()
        lats = rupture.surface.mesh.lats.ravel()
        # Curved surface meshes can include holes represented by NaNs.
        present = ~numpy.isnan(lons) & ~numpy.isnan(lats)
        lons, lats = lons[present], lats[present]
    if not len(lons):
        raise ValueError('Rupture has no finite geometry coordinates')
    grid = regular_grid(Mesh(lons, lats), spacing, padding=maximum_distance)
    return site.SiteCollection.from_points(
        grid.lons, grid.lats, req_site_params=req_site_params)


def _validate_inputs(exposure_xml, sites_csv, rupture, regular,
                     spacing, maximum_distance, mesh_spacing):
    """Check new modes before opening input files or creating a job."""
    if rupture:
        for name, value in [('Maximum distance', maximum_distance),
                            ('Rupture mesh spacing', mesh_spacing)]:
            if value is None or not numpy.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be finite and positive')
    elif maximum_distance is not None or mesh_spacing != 1:
        raise ValueError('Rupture-grid options require --rupture')
    if regular or rupture:
        if spacing is None or not numpy.isfinite(spacing) or spacing <= 0:
            raise ValueError('Regular grids require positive --grid-spacing')
        if sum((bool(exposure_xml), bool(len(sites_csv)), bool(rupture))) != 1:
            raise ValueError('Specify exactly one of exposure_xml, sites_csv '
                             'or rupture')


def main(
        vs30_csv,
        z1pt0=False,
        z2pt5=False,
        vs30measured=False,
        sentinel_z=False, # Set to -999 z1pt0 or z2pt5 if True
        regular_grid=False,
        *,
        exposure_xml=None,
        sites_csv=(),
        grid_spacing: float = 0,
        assoc_distance: float = 5,
        output='site_model.csv',
        rupture=None,
        maximum_distance: float = None,
        rupture_mesh_spacing: float = 1):
    """
    Prepare a site_model.csv file from exposure xml files/site csv files,
    vs30 csv files and a grid spacing which can be 0 (meaning no grid).
    For each site the closest vs30 parameter is used. The command can also
    generate (on demand) the additional fields z1pt0, z2pt5 and vs30measured
    which may be needed by your hazard model, depending on the required GSIMs.
    Use --regular-grid with a positive --grid-spacing for a complete
    rectangle compatible with circulant embedding.
    With --rupture, build a regular grid around one XML/NRML or CSV rupture,
    extending its projected bounds by --maximum-distance (in km) on each
    side. This defines the site-grid extent, not CE computational padding.
    """
    _validate_inputs(exposure_xml, sites_csv, rupture, regular_grid,
                     grid_spacing, maximum_distance, rupture_mesh_spacing)
    regular_grid = regular_grid or bool(rupture)
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
            if rupture:
                haz_sitecol = _rupture_sites(
                    rupture, grid_spacing, maximum_distance,
                    rupture_mesh_spacing, req_site_params)
            elif exposure_xml:
                haz_sitecol = _exposure_sites(
                    exposure_xml, grid_spacing, regular_grid,
                    req_site_params, hdf5)
            elif len(sites_csv):
                haz_sitecol = _csv_sites(
                    sites_csv, grid_spacing, regular_grid,
                    req_site_params, output)
            else:
                raise RuntimeError('Missing exposures or missing sites')
            associate(haz_sitecol, vs30_csv, assoc_distance)
            if z1pt0:
                if sentinel_z:
                    # Use vs30 - z1pt0 relationship in each GMM if -999
                    haz_sitecol.array['z1pt0'] = -999
                else:
                    # Compute from an NGAWest2 Vs30 to z1pt0 (CY14)
                    haz_sitecol.calculate_z1pt0()
            if z2pt5:
                if sentinel_z:
                    # Use vs30 - z1pt0 relationship in each GMM if -999
                    haz_sitecol.array['z2pt5'] = -999
                else:
                    # Compute from an NGAWest2 Vs30 to z2pt5 (CB14)
                    haz_sitecol.calculate_z2pt5()
            hdf5['sitecol'] = haz_sitecol
            if output:
                writers.write_csv(output, haz_sitecol.array[fields])
                if regular_grid:
                    _check_exported_grid(output)
        logging.info('Saved %d rows in %s' % (len(haz_sitecol), output))
        logging.info(mon)
    return haz_sitecol


main.vs30_csv = dict(help='files with lon,lat,vs30 and no header', nargs='+')
main.z1pt0 = dict(help='build the z1pt0', abbrev='-1')
main.z2pt5 = dict(help='build the z2pt5', abbrev='-2')
main.vs30measured = dict(help='build the vs30measured', abbrev='-3')
main.sentinel_z = dict(help='assign dummy -999 to z1pt0/z2pt5', abbrev='-999')
main.regular_grid = 'build a complete regular grid for circulant embedding'
main.exposure_xml = dict(help='exposure(s) in XML format', nargs='*')
main.sites_csv = dict(help='sites in CSV format (filenames)', nargs='*')
main.grid_spacing = 'grid spacing in km (the default 0 means no grid)'
main.assoc_distance = 'sites over this distance are discarded'
main.output = 'output file'
main.rupture = 'single XML/NRML or OpenQuake CSV scenario rupture'
main.maximum_distance = ('extend each side of the projected rupture bounds '
                         'by this distance in km (not an Rrup cutoff)')
main.rupture_mesh_spacing = 'rupture mesh spacing in km (default: 1)'
