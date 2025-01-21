# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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

from openquake.hazardlib.geo import polygon as pgn
from openquake.hazardlib.geo.geodetic import npoints_between, distance


def discretise_lines(ctx):
    """
    Discretize the line of minimum distance from each rupture surface to each
    site and create mesh with matching discretization
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    """
    # Get line from each rupture to each site
    l_mesh = {}
    for idx_path, val_site in enumerate(ctx.lon):

        # Discretise shortest dist from rup srf to site and store as line
        # Fix depth to zero as within Zhao et al. 2016
        dsct_line = npoints_between(ctx.lon[idx_path], ctx.lat[idx_path], 0,
                                    ctx.clon[idx_path], ctx.clat[idx_path], 0,
                                    100)

        # Create mesh of discretized line
        l_mesh[idx_path] = pgn.Mesh(dsct_line[0], dsct_line[1])

    return l_mesh


def get_dist_traversed_per_zone(l_mesh, pgn_store, pgn_zone, ctx):
    """
    Find the intercepts of the line from each rupture surface to each site
    within each volcanic zone polygon (if present) and returns the distance
    traversed per polygon.

    :param l_mesh:
        l_mesh: Dict of meshes representing the line from each rupture to
        each site
    :param pgn_store:
        pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon
    :param pgn_zone:
        pgn_zone: Polygon for each zone
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    """
    # Store the distance per volc zone per travel path
    r_zone_path, pnts_in_zone = {}, {}
    for path_idx, site in enumerate(ctx.lon):
        r_zone_path[path_idx], pnts_in_zone[path_idx] = {}, {}

    # For each travel path
    for idx_path, site in enumerate(ctx.lon):
        mesh_lons, mesh_lats = l_mesh[idx_path].lons, l_mesh[idx_path].lats

        # Get distance between each point
        line_spacing = distance(mesh_lons[0], mesh_lats[0], 0,
                                mesh_lons[1], mesh_lats[1], 0)

        # For each zone...
        for idx_zone, zone in enumerate(pgn_store['zone']):
            zone_id = pgn_store['zone'][zone]

            # Check if any points of mesh lie within zone
            checks = pgn_zone[zone_id].intersects(l_mesh[idx_path])

            # N points in zone * line spacing = distance in zone
            r_per_zone = len(np.argwhere(checks)) * line_spacing
            r_zone_path[idx_path][zone_id] = r_per_zone

            # Get coordinates of mesh points in zone
            in_zone_lons, in_zone_lats = [], []
            for idx_pnt, pnt in enumerate(checks):
                if checks[idx_pnt]:
                    in_zone_lons.append(mesh_lons[idx_pnt])
                    in_zone_lats.append(mesh_lats[idx_pnt])
            pnts_in_zone[idx_path][zone_id] = [in_zone_lons, in_zone_lats]

    return r_zone_path, pnts_in_zone


def get_total_rvolc_per_path(r_zone_path, pgn_store):
    """
    Get total rvolc per travel path. Note that total distance traversed through
    volcanic zones for each travel path in the Zhao et al. (2016) papers is
    capped at minimum of 12 km (assuming the zone is actually traversed) and
    maximum of 80 km.
    :param r_zone_path:
        r_zone_path: Dict of distance traversed per zone per travel path
    :param pgn_store:
        pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon
    """
    # Stack dist per zone per path
    r_values = np.stack([list(r_zone_path[path].values())
                         for path in r_zone_path])

    # Sum over zones to get total r per path
    rvolc_per_path = r_values.sum(axis=1)

    # Apply min/max bounds on rvolc as described in Zhao et al. 2016 per path
    rvolc_per_path[np.logical_and(rvolc_per_path > 0.0,
                                  rvolc_per_path <= 12.0)] = 12.0
    rvolc_per_path[rvolc_per_path >= 80.0] = 80.0

    return rvolc_per_path


def get_rvolcs(ctx, pgn_store, pgn_zone):
    """
    Get total distance per travel path through anelastically attenuating
    volcanic zones (rvolc) as described within the Zhao et al. 2016 GMMs.
    The rvolc value is computed for each rupture to each site stored within
    each ground-motion computation context
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    :param pgn_store:
        pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon
    :param pgn_zone:
        pgn_zone: Polygon for each zone
    """
    # Discretise the line from closest pnt on each rup to each site
    l_mesh = discretise_lines(ctx)

    # Get the distances traversed across each volcanic zone
    r_zone_path, _pnts_in_zone = get_dist_traversed_per_zone(l_mesh, pgn_store,
                                                             pgn_zone, ctx)

    # Get the total distance traversed across each zone, with limits placed on
    # the minimum and maximum of rvolc as described within the Zhao et al. 2016
    # GMMs
    rvolc_per_path = get_total_rvolc_per_path(r_zone_path, pgn_store)

    return rvolc_per_path
