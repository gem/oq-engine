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
from functools import lru_cache
from shapely.geometry import Point
from shapely.strtree import STRtree
from openquake.baselib import config


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
            if self.geoms[i].intersects(buf):
                found.append(self.gdf.iloc[int(i)])
        return found


class MosaicSpatialIndex(SpatialIndex):
    pass


class AdminSpatialIndex(SpatialIndex):
    """
    Spatial index for a single administrative level (0, 1, or 2).
    """
    def __init__(self, parquet_path, admin_level):
        if admin_level not in (0, 1, 2):
            raise ValueError(f"Invalid admin level: {admin_level}")
        self.admin_level = admin_level
        super().__init__(parquet_path)


@lru_cache(maxsize=1)
def get_mosaic_spatial_index():
    try:
        path = config.directory['mosaic_parquet_path']
    except KeyError:
        raise RuntimeError(
            "Missing 'mosaic_parquet_path' in openquake.cfg [directory]"
        )
    return MosaicSpatialIndex(path)


@lru_cache(maxsize=1)
def get_admin_spatial_index(admin_level):
    try:
        path = config.directory[f'admin{admin_level}_parquet_path']
    except KeyError:
        raise RuntimeError(
            f"Missing f'admin{admin_level}_parquet_path' in openquake.cfg [directory]"
        )
    admin_spatial_index = AdminSpatialIndex(path, admin_level)
    return admin_spatial_index
