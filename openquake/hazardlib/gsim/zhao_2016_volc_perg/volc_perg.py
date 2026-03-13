# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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


FIXED_DEPTH = 0.
N_POINTS = 100


def get_dist_traversed_per_zone(volc_pgns, ctx):
    """
    Find the intercepts of the line from each rupture surface to each site
    within each volcanic zone polygon (if present) and returns the distance
    traversed per polygon.

    :param l_mesh:
        l_mesh: Dict of meshes representing the line from each rupture to
        each site
    :param volc_pgns:
        volc_pgns: Polygon for each zone
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    """
    r_zone_path = {}

    # For each travel path
    for idx_path, _site in enumerate(ctx.lon):

        # Discretise the line
        dsct_line = npoints_between(
                    ctx.lon[idx_path], ctx.lat[idx_path], FIXED_DEPTH,
                    ctx.clon[idx_path], ctx.clat[idx_path], FIXED_DEPTH,
                    N_POINTS)

        # Create mesh of discretized line
        mesh = pgn.Mesh(dsct_line[0], dsct_line[1])

        # Distance between consecutive discretised points along the path
        line_spacing = distance(
            mesh.lons[0], mesh.lats[0], FIXED_DEPTH,
            mesh.lons[1], mesh.lats[1], FIXED_DEPTH)

        # N points intersecting zone * spacing = distance traversed in zone
        r_zone_path[idx_path] = {
            zone_id: np.count_nonzero(polygon.intersects(mesh)) * line_spacing
            for zone_id, polygon in volc_pgns.items()
        }

    return r_zone_path


def get_total_rvolc_per_path(r_zone_path):
    """
    Get total rvolc per travel path. Note that total distance traversed through
    volcanic zones for each travel path in the Zhao et al. (2016) papers is
    capped at minimum of 12 km (assuming the zone is actually traversed) and
    maximum of 80 km.
    :param r_zone_path:
        r_zone_path: Dict of distance traversed per zone per travel path
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


def get_rvolcs(ctx, pgn_store):
    """
    Get total distance per travel path through anelastically attenuating
    volcanic zones (rvolc) as described within the Zhao et al. 2016 GMMs.
    The rvolc value is computed for each rupture to each site stored within
    each ground-motion computation context
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    :param pgn_store:
        pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon and the polygons themselves
    """
    # Get the distances traversed across each volcanic zone
    r_zone_path = get_dist_traversed_per_zone(pgn_store, ctx)

    # Get the total distance traversed across each zone, with limits placed on
    # the min and max of rvolc as described within the Zhao et al. 2016 GMMs
    rvolc_per_path = get_total_rvolc_per_path(r_zone_path)

    return rvolc_per_path
