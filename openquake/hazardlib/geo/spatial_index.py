# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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

import warnings
import os
import geopandas as gpd
import numpy
from pathlib import Path
from functools import lru_cache
from shapely import contains_xy
from shapely.geometry import Point
from shapely.strtree import STRtree
from openquake.baselib import config
from openquake.qa_tests_data import global_risk, mosaic


class SpatialIndex:
    """
    Generic spatial index for polygonal geometries.
    Read-only, thread-safe after construction.
    """
    def __init__(self, geodata_path, region_code_field):
        """
        :param geodata_path: path to parquet / gpkg / shp
        :param region_code_field: column containing region identifiers
        """
        geodata_path = Path(geodata_path)
        if not geodata_path.exists():
            raise FileNotFoundError(geodata_path)
        suffix = geodata_path.suffix.lower()
        if suffix == '.parquet':
            # NOTE: assuming .parquet file obtained via the
            #       geodata_to_parquet command
            gdf = gpd.read_parquet(geodata_path)
        elif suffix in ('.gpkg', '.shp'):
            warnings.warn(
                f"Loading '{geodata_path}' geometry; consider"
                f" converting to Parquet for faster startup.",
                RuntimeWarning,
            )
            gdf = gpd.read_file(geodata_path)
            if gdf.crs is None:
                raise ValueError(f"Missing CRS in {geodata_path}")
            if gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(4326)
            gdf["geometry"] = gdf.geometry.make_valid()
            gdf = gdf[gdf.geometry.notnull()]
        else:
            raise ValueError(
                f"Unsupported spatial format '{suffix}'. "
                "Supported: .parquet, .gpkg, .shp"
            )
        self.gdf = gdf
        if region_code_field not in self.gdf.columns:
            raise ValueError(
                f"Missing region_code_field '{region_code_field}'. "
                f"Available columns: {list(self.gdf.columns)}"
            )
        self.region_code_field = region_code_field
        self.geoms = self.gdf.geometry.values
        self.tree = STRtree(self.geoms)

    def _candidates(self, geom):
        return self.tree.query(geom)

    def locate(self, lon, lat, region_code_only=True):
        p = Point(lon, lat)
        for i in self._candidates(p):
            if self.geoms[i].covers(p):
                if region_code_only:
                    return self.gdf.iloc[int(i)][self.region_code_field]
                else:
                    return self.gdf.iloc[int(i)]
        return None

    def nearby(self, lon, lat, threshold_deg, region_code_only=True):
        p = Point(lon, lat)
        buf = p.buffer(threshold_deg)
        found = []
        for i in self._candidates(buf):
            if self.geoms[i].intersects(buf):
                if region_code_only:
                    found.append(self.gdf.iloc[int(i)][self.region_code_field])
                else:
                    found.append(self.gdf.iloc[int(i)])
        return found

    def locate_many(self, lonlats, exclude=()):
        """
        Bulk geolocation of multiple points.

        :param lonlats: array-like of shape (N, 2) or (N, 3),
            i.e. with or without depth
        :param exclude: iterable of codes to skip
        :return: numpy.array of codes, one per point
        """
        if not isinstance(lonlats, numpy.ndarray):
            lonlats = numpy.asarray(lonlats)
        lonlats2d = lonlats[:, :2]  # discard depth if present
        # initialize all points with default value
        codes_out = numpy.full(len(lonlats2d), '???', dtype=object)
        if exclude:
            df = self.gdf[~self.gdf[self.region_code_field].isin(exclude)]
        else:
            df = self.gdf
        # group by code, perform OR across multiple geometries
        for code, group in df.groupby(self.region_code_field):
            mask = numpy.zeros(len(lonlats2d), dtype=bool)
            for geom in group.geometry:
                mask |= contains_xy(geom, lonlats2d)
            codes_out[mask] = code
        return codes_out


class MosaicSpatialIndex(SpatialIndex):
    pass


class AdminSpatialIndex(SpatialIndex):
    """
    Spatial index for a single administrative level (0, 1, or 2).
    """
    def __init__(self, geodata_path, region_code_field, admin_level):
        if admin_level not in (0, 1, 2):
            raise ValueError(f"Invalid admin level: {admin_level}")
        self.admin_level = admin_level
        super().__init__(geodata_path, region_code_field)


@lru_cache(maxsize=1)
def get_mosaic_spatial_index():
    region_code_field = 'code'  # FIXME: in openquake.cfg?
    try:
        geodata_path = config.directory['mosaic_geodata_path']
    except KeyError:
        mosaic_dir = config.directory.mosaic_dir
        geodata_path = os.path.join(mosaic_dir, 'mosaic.gpkg')
        if not os.path.exists(geodata_path):
            geodata_path = os.path.join(
                os.path.dirname(mosaic.__file__), 'mosaic.gpkg')
        # FIXME: there is an inconsistency between mosaic.gpkg and
        #        ModelBoundaries.gpkg with respect to the field containing
        #        the model codes ('name' vs 'code')
        region_code_field = 'name'
        warnings.warn(
            f"Missing 'mosaic_geodata_path' in openquake.cfg [directory]."
            f" Using {geodata_path}.", RuntimeWarning)
    return MosaicSpatialIndex(geodata_path, region_code_field)


@lru_cache(maxsize=3)
def get_admin_spatial_index(admin_level):
    # FIXME: specify region_code_field in openquake.cfg?
    if admin_level == 0:
        region_code_field = 'shapeGroup'
    else:
        region_code_field = 'shapeName'
    try:
        geodata_path = config.directory[f'admin{admin_level}_geodata_path']
    except KeyError:
        if admin_level == 0:
            # Fallback to the simplified gpkg in qa_tests_data
            geodata_path = os.path.join(
                os.path.dirname(global_risk.__file__),
                'geoBoundariesCGAZ_ADM0.gpkg')
            warnings.warn(
                f"Missing 'admin0_geodata_path' in openquake.cfg [directory]."
                f" Using {geodata_path}.", RuntimeWarning)
        else:
            raise RuntimeError(
                f"Missing f'admin{admin_level}_geodata_path' in"
                f" openquake.cfg [directory]")
    admin_spatial_index = AdminSpatialIndex(
        geodata_path, region_code_field, admin_level)
    return admin_spatial_index
