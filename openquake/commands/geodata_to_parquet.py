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

import geopandas as gpd


def main(input_path, parquet_path):
    """
    Convert a GeoPackage or a Shapefile to a Parquet binary file
    suitable for fast spatial lookup.
    """
    gdf = gpd.read_file(input_path)
    if gdf.crs is None:
        raise ValueError('CRS is missing')
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    gdf = gdf[gdf.geometry.notnull()]
    gdf['geometry'] = gdf.geometry.make_valid()
    # pyarrow is the fastest; zstd has a good compression/speed tradeoff
    gdf.to_parquet(parquet_path, engine='pyarrow', compression='zstd')
    print(f'Geographic data stored to {parquet_path}')


main.input_path = dict(help='path of the GeoPackage or Shapefile to convert')
main.parquet_path = dict(
    help='path of the .parquet binary file to store data into')
