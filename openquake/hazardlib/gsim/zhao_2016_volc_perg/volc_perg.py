# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import pandas as pd
import fiona

from collections import OrderedDict
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo import polygon as pgn
from openquake.hazardlib.geo.geodetic import npoints_between, distance


def get_volc_zones(volc_polygons):
    """
    Construct polygons from the vertex coordinates provided for each volcanic
    zone and assign the associated zone id
    :param volc_polygons:
        volc_polygons: Coordinates of volcanic zone polygon
        vertices and associated zone id per polygon
    """
    # Get the volc zone polygons
    with fiona.open(volc_polygons,'r') as inp:
        volc_zone_id = {}
        polygon_per_volc_zone_lon = {}
        polygon_per_volc_zone_lat = {}
        for idx, f in enumerate(inp):

            # Get zone_id
            tmp_props_per_zone = pd.Series(f['properties'])
            volc_zone_id[idx] = tmp_props_per_zone[0]

            # Per zone get lat and lon of each polygon vertices
            for idx_coord, coord in enumerate(f['geometry']['coordinates'][0]):
                polygon_per_volc_zone_lon[
                    volc_zone_id[idx], idx_coord] = f['geometry'][
                        'coordinates'][0][idx_coord][0]
                polygon_per_volc_zone_lat[
                    volc_zone_id[idx], idx_coord] = f['geometry'][
                        'coordinates'][0][idx_coord][1]

    # Store all required info in dict
    volc_pgn_store = {'volc_zone': volc_zone_id,
                      'lons_per_zone': polygon_per_volc_zone_lon,
                      'lats_per_zone': polygon_per_volc_zone_lat}

    # Set dict for volcanic zones
    zone_dict = OrderedDict([(volc_pgn_store['volc_zone'][zone], {}
                              ) for zone in volc_pgn_store['volc_zone']])

    # Get polygon per zone
    pnts_per_zone = zone_dict
    polygon_per_zone = zone_dict
    for zone in volc_pgn_store['volc_zone']:
        zone_id = volc_pgn_store['volc_zone'][zone]
        for coord_idx, coord in enumerate(volc_pgn_store['lons_per_zone']):
            if zone_id in coord:
                pnts_per_zone[zone_id][coord_idx] = Point(volc_pgn_store[
                    'lons_per_zone'][zone_id, coord[1]],
                          volc_pgn_store['lats_per_zone'][zone_id, coord[1]])
            else:
                pass
        pnts_list_per_zone = []
        for idx, coordinates in enumerate(pnts_per_zone[zone_id]):
            pnts_list_per_zone.append(pnts_per_zone[zone_id][coordinates])
        polygon_per_zone[zone_id] =  pgn.Polygon(pnts_list_per_zone)
    return volc_pgn_store, polygon_per_zone

def discretise_lines(ctx):
    """
    Discretize the line of minimum distance from each rupture surface to each
    site and create mesh with matching discretization
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    """
    # Fix to zero to compute horz. dist. as in Zhao et al. 2016
    fix_depth = 0

    # Discretise line into 1000 points
    npoints_line = 1000

    # Get line from each rupture to each site
    line_mesh = {}

    for idx_path, val_site in enumerate(ctx.lon):

        site_lon = ctx.lon[idx_path]
        site_lat = ctx.lat[idx_path]
        min_dist_rup_pnt_per_path_lon = ctx.clon[idx_path]
        min_dist_rup_pnt_per_path_lat = ctx.clat[idx_path]

        # Discretise shortest dist from rup srf to site and store as line
        dsct_line = npoints_between(site_lon, site_lat, fix_depth,
                                    min_dist_rup_pnt_per_path_lon,
                                    min_dist_rup_pnt_per_path_lat,
                                    fix_depth, npoints_line)

        # Create mesh of discretized line
        mesh_lons = dsct_line[0]
        mesh_lats = dsct_line[1]
        line_mesh[idx_path] = pgn.Mesh(mesh_lons, mesh_lats)
    return line_mesh

def get_dist_traversed_per_zone(line_mesh, volc_pgn_store, polygon_per_zone,
                                ctx):
    """
    Find the intercepts of the line from each rupture surface to each site within
    each volcanic zone polygon (if present) and returns the distance traversed
    per polygon
    :param line_mesh:
        line_mesh: Dict of meshes representing the line from each rupture to
        each site
    :param volc_pgn_store:
        volc_pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon
    :param polygon_per_zone:
        polygon_per_zone: Polygon for each zone
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    """
    # Store the distanc per volc zone per travel path
    dist_per_volc_zone_per_path = OrderedDict([(path_idx, {}) for path_idx,
                                               site in enumerate(ctx.lon)])
    in_zone_coo_per_zone_per_path = OrderedDict([(path_idx, {}) for path_idx,
                                               site in enumerate(ctx.lon)])

    # For each travel path
    for idx_path, site in enumerate(ctx.lon):
        mesh_per_path = line_mesh[idx_path]
        mesh_lons = mesh_per_path.lons
        mesh_lats = mesh_per_path.lats

        # Get distance between each point
        line_spacing = distance(mesh_lons[0], mesh_lats[0], 0,
                                         mesh_lons[1], mesh_lats[1], 0)

        # For each zone...
        for idx_zone, zone in enumerate(volc_pgn_store['volc_zone']):
            zone_id = volc_pgn_store['volc_zone'][zone]

            # Check if any points of mesh lie within zone
            checks_per_zone = polygon_per_zone[zone_id].intersects(
                mesh_per_path)

            # N points in zone * line spacing = distance in zone
            num_pnts_in_zone = len(np.argwhere(checks_per_zone == True))
            dist_per_volc_zone = num_pnts_in_zone * line_spacing
            dist_per_volc_zone_per_path[idx_path][zone_id] = dist_per_volc_zone

            # Get coordinates of mesh points in zone
            in_zone_lons, in_zone_lats = [], []
            for idx_pnt, pnt in enumerate(checks_per_zone):
                if checks_per_zone[idx_pnt] == True:
                    in_zone_lons.append(mesh_lons[idx_pnt])
                    in_zone_lats.append(mesh_lats[idx_pnt])
            in_zone_coo_per_zone_per_path[idx_path][zone_id] = [
                in_zone_lons, in_zone_lats]
    return dist_per_volc_zone_per_path, in_zone_coo_per_zone_per_path

def get_total_rvolc_per_path(dist_per_volc_zone_per_path, volc_pgn_store):
    """
    Get total rvolc per travel path. Note that total distance traversed through
    volcanic zones for each travel path in the Zhao et al. (2016) papers is
    capped at minimum of 12 km (assuming the zone is actually traversed) and
    maximum of 80 km.
    :param dist_per_volc_zone_per_path:
        dist_per_volc_zone_per_path: Dict of distance traversed per zone per
        travel path
    :param volc_pgn_store:
        volc_pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon
    """
    rvolc_per_path = []
    # For each travel path...
    for path_idx, path in enumerate(dist_per_volc_zone_per_path):
        rvolc_store = []
        # For each zone...
        for idx_zone, zone in enumerate(volc_pgn_store['volc_zone']):
            zone_id = volc_pgn_store['volc_zone'][zone]
            # Get rvolc per zone
            rvolc = dist_per_volc_zone_per_path[path_idx][zone_id]
            rvolc_store.append(rvolc)
        # Sum over all zones per path for the total rvolc per path
        rvolc_per_path.append(np.sum(np.array(rvolc_store)))
    rvolc_per_path = np.array(rvolc_per_path)
    # Apply min/max bounds on rvolc as described in Zhao et al. 2016 per path
    rvolc_per_path[np.logical_and(rvolc_per_path > 0.0,
                                  rvolc_per_path <= 12.0)] = 12.0
    rvolc_per_path[rvolc_per_path >= 80.0] = 80.0
    return rvolc_per_path

def get_rvolcs(ctx, volc_polygons):
    """
    Get total distance per travel path through anelastically attenuating
    volcanic zones (rvolc) as described within the Zhao et al. 2016 GMMs.
    The rvolc value is computed for each rupture to each site stored within
    each ground-motion computation context
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    :param volc_polygons:
        volc_polygons: Fiona collection of coordinates of volcanic zone polygon
        vertices and associated zone id per polygon
    """
    # Read in volcanic zones and get polygons with att. rates
    volc_pgn_store, polygon_per_zone  = get_volc_zones(volc_polygons)

    # Discretise the line from closest pnt on each rup to each site
    line_mesh = discretise_lines(ctx)

    # Get the distances traversed across each volcanic zone
    dist_per_volc_zone_per_path,\
        in_zone_coo_per_zone_per_path = get_dist_traversed_per_zone(
        line_mesh, volc_pgn_store, polygon_per_zone, ctx)

    # Get the total distance traversed across each zone, with limits placed on
    # the minimum and maximum of rvolc as described within the Zhao et al. 2016
    # GMMs
    rvolc_per_path = get_total_rvolc_per_path(dist_per_volc_zone_per_path,
                                              volc_pgn_store)
    return rvolc_per_path
