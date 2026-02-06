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

import geopandas as gpd
from shapely.geometry import Point
from shapely.strtree import STRtree


class SpatialIndex:
    """
    Generic spatial index for polygonal geometries.
    Read-only, thread-safe after construction.
    """
    def __init__(self, parquet_path):
        self.gdf = gpd.read_parquet(parquet_path)
        self.geoms = self.gdf.geometry.values
        self.tree = STRtree(self.geoms)

    def _candidates(self, geom):
        return self.tree.query(geom)

    def locate(self, lon, lat):
        p = Point(lon, lat)
        for i in self._candidates(p):
            if self.geoms[i].covers(p):
                return self.gdf.iloc[int(i)]
        return None

    def nearby(self, lon, lat, threshold_deg):
        p = Point(lon, lat)
        buf = p.buffer(threshold_deg)
        found = []
        for i in self._candidates(buf):
            geom = self.geoms[i]
            if geom.distance(p) <= threshold_deg:
                found.append(self.gdf.iloc[int(i)])
        return found


class AdminSpatialIndex:
    def __init__(self, admin0=None, admin1=None, admin2=None):
        self.spatial_indices = {}
        if admin0:
            self.spatial_indices[0] = SpatialIndex(admin0)
        if admin1:
            self.spatial_indices[1] = SpatialIndex(admin1)
        if admin2:
            self.spatial_indices[2] = SpatialIndex(admin2)

    def locate(self, lon, lat, admin_level):
        return self.spatial_indices[admin_level].locate(lon, lat)

    def nearby(self, lon, lat, admin_level, threshold_deg):
        # threshold is in degrees
        return self.spatial_indices[admin_level].nearby(
            lon, lat, threshold_deg)


class MosaicSpatialIndex(SpatialIndex):
    def __init__(self, parquet_path):
        self.spatial_index = SpatialIndex(parquet_path)

    def locate(self, lon, lat):
        return self.spatial_index.locate(lon, lat)

    def nearby(self, lon, lat, threshold_deg):
        return self.spatial_index.nearby(lon, lat, threshold_deg)
