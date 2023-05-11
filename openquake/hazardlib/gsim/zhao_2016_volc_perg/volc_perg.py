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

from collections import OrderedDict
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo import polygon as pgn
from openquake.hazardlib.geo.geodetic import npoints_between, distance
from openquake.hazardlib.geo.surface import PlanarSurface
#from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.scalerel.wc1994 import WC1994


def get_volc_zones(volc_polygons):
    """
    Construct polygons from the vertex coordinates provided for each volcanic 
    zone and assign the associated zone id
    :param volc_polygons:
        volc_polygons: Fiona collection of coordinates of volcanic zone polygon
        vertices and associated zone id per polygon 
    """
    # Get the volc zone polygons
    volc_zone_id = {}
    polygon_per_volc_zone_lon = {}
    polygon_per_volc_zone_lat = {}
    for idx, f in enumerate(volc_polygons):
        
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

def get_rupture(lon, lat, dep, msr, mag, aratio, strike, dip, rake, trt,
                ztor=None):
    """
    Creates a rupture given the hypocenter position
    """
    hypoc = Point(lon, lat, dep)
    srf = PlanarSurface.from_hypocenter(hypoc, msr, mag, aratio, strike, dip,
                                        rake, ztor)
    rup = BaseRupture(mag, rake, trt, hypoc, srf)
    rup.hypo_depth = dep
    return rup

def get_min_dist_rup_to_site(rup, sites):
    """
    Returns the minimum distance (in km) from the rupture surface to each site 
    and the corresponding point on the rupture surface
    :param rup:
        rup: Rupture context
    :param sites:
        sites: Sites collection
    """
    # Discretize each edge of the rupture surface
    top_left_lon = rup.surface.array[0][0][0] # from array to get floats
    top_left_lat = rup.surface.array[1][0][0]
    top_left_dep = rup.surface.array[2][0][0]
    
    top_right_lon = rup.surface.array[0][0][1]
    top_right_lat = rup.surface.array[1][0][1]
    top_right_dep = rup.surface.array[2][0][1]
    
    bottom_right_lon = rup.surface.array[0][0][2]
    bottom_right_lat = rup.surface.array[1][0][2]
    bottom_right_dep = rup.surface.array[2][0][2]
    
    bottom_left_lon = rup.surface.array[0][0][3]
    bottom_left_lat = rup.surface.array[1][0][3]
    bottom_left_dep = rup.surface.array[2][0][3]
    
    npoints_rup = 500

    top_edge = npoints_between(top_left_lon, top_left_lat,
                                        bottom_left_dep, top_right_lon,
                                        top_right_lat, top_right_dep, 
                                        npoints_rup)
    
    right_edge = npoints_between(top_right_lon, top_right_lat,
                                          top_right_dep, bottom_right_lon,
                                          bottom_right_lat, bottom_right_dep,
                                          npoints_rup)
    
    bottom_edge = npoints_between(bottom_right_lon, bottom_right_lat,
                                          bottom_right_dep, bottom_left_lon,
                                          bottom_left_lat, bottom_left_dep,
                                          npoints_rup)
    
    left_edge = npoints_between(bottom_right_lon, bottom_right_lat,
                                        bottom_right_dep, top_left_lon,
                                        top_left_lat, top_left_dep,
                                        npoints_rup)

    rupture_all_lats = np.concatenate((top_edge[1], right_edge[1],
                                       bottom_edge[1], left_edge[1]),
                                      axis = 0)
    rupture_all_lons = np.concatenate((top_edge[0], right_edge[0],
                                       bottom_edge[0], left_edge[0]),
                                      axis = 0)
    rupture_all_deps = np.concatenate((top_edge[2], right_edge[2],
                                       bottom_edge[2], left_edge[2]),
                                      axis = 0)
    
    # Get min dist from rupture to each site
    min_dist_rup_srf_to_site = {}
    min_dist_rup_pnt = {}
    for idx_site, site in enumerate(sites[0]):
        site_lon = sites[0][idx_site]
        site_lat = sites[1][idx_site]
        site_dep = 0
        store_distance = []
        for idx_npoint, val_npoint in enumerate(rupture_all_lats):
            store_distance.append(distance(site_lon, site_lat, site_dep,
                                   rupture_all_lons[idx_npoint],
                                   rupture_all_lats[idx_npoint],
                                   rupture_all_deps[idx_npoint]))
        
        # Minimum distance from rupture surface to site
        min_dist_rup_srf_to_site[idx_site] = np.min(np.abs(store_distance))
        
        # Point on rupture surface corresponding to minimum distance
        min_dist_rup_pnt_idx = np.argmin(np.min(store_distance))
        min_dist_rup_pnt[idx_site] = [rupture_all_lats[min_dist_rup_pnt_idx],
                            rupture_all_lons[min_dist_rup_pnt_idx],
                            rupture_all_deps[min_dist_rup_pnt_idx]]
        
    return min_dist_rup_srf_to_site, min_dist_rup_pnt
  
def discretise_lines(min_dist_rup_pnt, sites):
    """
    Discretize the line of minimum distance from rupture surface to each site,
    and create mesh with matching discretization.
    :param min_dist_rup_pnt:
        rup: Minimum distance from each site to the rupture
    :param sites:
        sites: Sites collection
    """
    # Fix to zero to compute horz. dist. as in Zhao et al. 2016 
    fix_depth = 0
    
    # Discretise line into 1000 points
    npoints_line = 1000
    
    # Get line from rupture to each site
    line_mesh = {}
    for idx_site, site in enumerate(sites[0]):
        site_lon = sites[0][idx_site]
        site_lat = sites[1][idx_site]        
        min_dist_rup_pnt_per_site = min_dist_rup_pnt[idx_site]
        # Discretise shortest dist from rup srf to site and store as line
        dsct_line = npoints_between(site_lon, site_lat, fix_depth,
                                             min_dist_rup_pnt_per_site[1],
                                             min_dist_rup_pnt_per_site[0],
                                             fix_depth, npoints_line)
        # Create mesh of discretized line
        mesh_lons = dsct_line[0]
        mesh_lats = dsct_line[1]
        line_mesh[idx_site] = pgn.Mesh(mesh_lons, mesh_lats)
    return line_mesh

def get_dist_traversed_per_zone(line_mesh, volc_pgn_store,
                                polygon_per_zone, sites):
    """
    Find the intercepts of the line from rupture surface to each site within
    each volcanic zone polygon (if present) and returns the distance traversed
    per polygon
    :param line_mesh:
        line_mesh: Dict of meshes representing the line from each site to the
        rupture
    :param volc_pgn_store:
        volc_pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon
    :param polygon_per_zone:
        polygon_per_zone: Polygon for each zone
    :param sites:
        sites: Sites collection
    """
    # Store the distanc per volc zone per site (i.e. per record)
    dist_per_volc_zone_per_site = OrderedDict([(site_idx, {}) for site_idx,
                                               site in enumerate(sites[0])])  
    in_zone_coo_per_zone_per_site = OrderedDict([(site_idx, {}) for site_idx,
                                               site in enumerate(sites[0])])  
    
    # For each site...
    for idx_site, site in enumerate(sites[0]):
        mesh_per_site = line_mesh[idx_site]
        mesh_lons = mesh_per_site.lons
        mesh_lats = mesh_per_site.lats
        
        # Get distance between each point
        line_spacing = distance(mesh_lons[0], mesh_lats[0], 0,
                                         mesh_lons[1], mesh_lats[1], 0)

        # For each zone...
        for idx_zone, zone in enumerate(volc_pgn_store['volc_zone']):
            zone_id = volc_pgn_store['volc_zone'][zone]
            # Check if any points of mesh lie within zone
            checks_per_zone = polygon_per_zone[zone_id].intersects(
                mesh_per_site)

            # N points in zone * line spacing = distance in zone
            num_pnts_in_zone = len(np.argwhere(checks_per_zone == True))
            dist_per_volc_zone = num_pnts_in_zone * line_spacing
            dist_per_volc_zone_per_site[idx_site][zone_id] = dist_per_volc_zone   
            
            # Get coordinates of mesh points in zone
            in_zone_lons, in_zone_lats = [], []
            for idx_pnt, pnt in enumerate(checks_per_zone):
                if checks_per_zone[idx_pnt] == True:
                    in_zone_lons.append(mesh_lons[idx_pnt])
                    in_zone_lats.append(mesh_lats[idx_pnt])
            in_zone_coo_per_zone_per_site[idx_site][zone_id] = [
                in_zone_lons, in_zone_lats]
    return dist_per_volc_zone_per_site, in_zone_coo_per_zone_per_site

def get_total_rvolc_per_path(dist_per_volc_zone_per_site, volc_pgn_store):
    """
    Get total rvolc per travel path (one per site in gm calculation context).
    Note that total distance traversed through volcanic zones for each travel
    path in the Zhao et al. (2016) papers is capped at minimum of 12 km
    (assuming the zone is actually traversed) and maximum of 80 km.
    :param dist_per_volc_zone_per_site:
        dist_per_volc_zone_per_site: Dict of distance traversed per zone per
        site (i.e. per travel path)
    :param volc_pgn_store:
        volc_pgn_store: Dict of zone ids + latitude and longitude of vertices
        used to construct each polygon
    """
    rvolc_per_path = []
    # For each travel path...
    for path_idx, path in enumerate(dist_per_volc_zone_per_site):
        rvolc_store = []
        # For each zone...
        for idx_zone, zone in enumerate(volc_pgn_store['volc_zone']):
            zone_id = volc_pgn_store['volc_zone'][zone]
            # Get rvolc per zone
            rvolc = dist_per_volc_zone_per_site[path_idx][zone_id]
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
    The rvolc value is computed for each site stored within each ground-motion
    computation context (i.e. for each site w.r.t. the given rupture context).
    :param ctx:
        ctx: Context of ruptures and sites to compute ground-motions for
    :param volc_polygons:
        volc_polygons: Fiona collection of coordinates of volcanic zone polygon
        vertices and associated zone id per polygon 
    """
    # Read in volcanic zones and get polygons with att. rates
    volc_pgn_store, polygon_per_zone  = get_volc_zones(volc_polygons)   
    
    # Get the rupture context (use WC1994 and assume aratio = 2)
    rup = get_rupture(ctx.hypo_lon[0], ctx.hypo_lat[0], ctx.hypo_depth[0], WC1994(),
                      ctx.mag[0], 2, ctx.strike[0], ctx.dip[0], ctx.rake[0],
                      trt = 'const.TRT.SUBDUCTION_INTERFACE')
    
    # Get the lan, lon and fix elevation per site
    sites = [ctx.lon, ctx.lat]
     
    # Get min dist from rup surface to site and corresponding pnt on rup
    min_dist_rup_srf_to_site, min_dist_rup_pnt = get_min_dist_rup_to_site(
        rup, sites)
    
    # Discretise the line from closest pnt on rup to site and get intercepts
    line_mesh = discretise_lines(min_dist_rup_pnt, sites)
 
    # Get the distances traversed across each volcanic zone
    dist_per_volc_zone_per_site,\
        in_zone_coo_per_zone_per_site = get_dist_traversed_per_zone(
        line_mesh, volc_pgn_store, polygon_per_zone, sites)
    
    # Get the total distance traversed across each zone, with limits placed on
    # the minimum and maximum of rvolc as described within the Zhao et al. 2016
    # GMMs
    rvolc_per_path = get_total_rvolc_per_path(dist_per_volc_zone_per_site,
                                              volc_pgn_store)
    return rvolc_per_path
 

"""
PLACED BASERUPTURE HERE FOR NOW (IMPORT ERROR ISSUE???)
"""   
import abc
import itertools
from openquake.baselib import general
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.surface.base import BaseSurface    

def to_checksum8(cls1, cls2):
    """
    Convert a pair of classes into a numeric code (uint8)
    """
    names = '%s,%s' % (cls1.__name__, cls2.__name__)
    return sum(map(ord, names)) % 256


class BaseRupture(metaclass=abc.ABCMeta):
    """
    Rupture object represents a single earthquake rupture.

    :param mag:
        Magnitude of the rupture.
    :param rake:
        Rake value of the rupture.
        See :class:`~openquake.hazardlib.geo.nodalplane.NodalPlane`.
    :param tectonic_region_type:
        Rupture's tectonic regime. One of constants
        in :class:`openquake.hazardlib.const.TRT`.
    :param hypocenter:
        A :class:`~openquake.hazardlib.geo.point.Point`, rupture's hypocenter.
    :param surface:
        An instance of subclass of
        :class:`~openquake.hazardlib.geo.surface.base.BaseSurface`.
        Object representing the rupture surface geometry.
    :param rupture_slip_direction:
        Angle describing rupture propagation direction in decimal degrees.

    :raises ValueError:
        If magnitude value is not positive, or tectonic region type is unknown.

    NB: if you want to convert the rupture into XML, you should set the
    attribute surface_nodes to an appropriate value.
    """
    _code = {}

    @classmethod
    def init(cls):
        """
        Initialize the class dictionary `._code` by encoding the
        bidirectional correspondence between an integer in the range 0..255
        (the code) and a pair of classes (rupture_class, surface_class).
        This is useful when serializing the rupture to and from HDF5.
        :returns: {code: pair of classes}
        """
        rupture_classes = [BaseRupture] + list(
            general.gen_subclasses(BaseRupture))
        surface_classes = list(general.gen_subclasses(BaseSurface))
        code2cls = {}
        BaseRupture.str2code = {}
        for rup, sur in itertools.product(rupture_classes, surface_classes):
            chk = to_checksum8(rup, sur)
            if chk in code2cls and code2cls[chk] != (rup, sur):
                raise ValueError('Non-unique checksum %d for %s, %s' %
                                 (chk, rup, sur))
            cls._code[rup, sur] = chk
            code2cls[chk] = rup, sur
            BaseRupture.str2code['%s %s' % (rup.__name__, sur.__name__)] = chk
        return code2cls

    def __init__(self, mag, rake, tectonic_region_type, hypocenter,
                 surface, rupture_slip_direction=None, weight=None):
        if not mag > 0:
            raise ValueError('magnitude must be positive')
        NodalPlane.check_rake(rake)
        self.tectonic_region_type = tectonic_region_type
        self.rake = rake
        self.mag = mag
        self.hypocenter = hypocenter
        self.surface = surface
        self.rupture_slip_direction = rupture_slip_direction
        self.ruid = None

    @property
    def code(self):
        """Returns the code (integer in the range 0 .. 255) of the rupture"""
        return self._code[self.__class__, self.surface.__class__]

    def size(self):
        """
        Dummy method for compatibility with the RuptureContext.

        :returns: 1
        """
        return 1