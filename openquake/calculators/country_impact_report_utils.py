#!/usr/bin/env python3
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

import functools
import logging
import pathlib
from dataclasses import dataclass
from shapely.validation import make_valid, explain_validity
import pandas as pd
import geopandas as gpd
from openquake.baselib import config


def get_configured_path(name, directory=False):
    """
    Return a configured path after checking that it exists.

    :param name: name of the entry in ``config.directory``
    :param directory: if true, require a directory; otherwise require a file
    :returns: the configured path as a :class:`pathlib.Path`
    :raises AttributeError: if the entry is missing or empty
    :raises FileNotFoundError: if the configured path does not exist
    """
    try:
        value = getattr(config.directory, name)
    except AttributeError as exc:
        raise AttributeError(
            f'config.directory.{name} must be specified') from exc
    if not value:
        raise AttributeError(
            f'config.directory.{name} must be specified')

    path = pathlib.Path(value).expanduser()
    exists = path.is_dir() if directory else path.is_file()
    if not exists:
        kind = 'directory' if directory else 'file'
        raise FileNotFoundError(
            f'Configured {kind} for config.directory.{name} '
            f'does not exist: {path}')
    return path


@dataclass
class EventContext:
    """
    Metadata describing the seismic event used in an impact report.

    :param name: human-readable name of the event
    :param date: event date and time as a formatted string
    :param hypocenter: event longitude and latitude
    :param shakemap_version: optional version identifier of the ShakeMap
    """
    name: str
    date: str
    hypocenter: tuple[float, float]
    shakemap_version: str = None


@dataclass
class ReportOptions:
    """
    Visual, text, and threshold settings used to build an impact report.

    :param disclaimer_txt: disclaimer text displayed in the report
    :param basemap_path: path to the raster basemap used by the maps
    :param threshold_deg: distance threshold used to select countries
    :param no_uncertainty: whether to omit uncertainty ranges
    :param loss_metric: name of the loss metric displayed in map titles
    """
    disclaimer_txt: str
    basemap_path: str
    threshold_deg: float
    no_uncertainty: bool
    loss_metric: str


LOSS_METADATA = {
    "occupants": {
        "label": "Fatalities",
        "title": "fatalities",
        "colors": [
            '#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d'],
    },
    "residents": {
        "label": "Rendered Homeless",
        "title": "population rendered homeless",
        "colors": [
            '#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043'],
    },
    "number": {
        "label": "Buildings destroyed",
        "title": "buildings destroyed",
        "colors": [
            '#ffffff', '#bdbdbd', '#737373', '#424242', '#000000'],
    },
}


# maxsize=1 is sufficient when only one admin-level boundary file is loaded
# per process (the common case). Increase to 2 if both adm1 and adm2 files
# are ever used within the same process.
@functools.lru_cache(maxsize=1)
def _read_admin_layer(fname):
    """Read and repair an administrative-boundary layer.

    :param fname: path to a vector file containing administrative boundaries
    :returns: a GeoDataFrame with valid geometries
    """
    gdf = gpd.read_file(fname)
    invalid = ~gdf.is_valid
    if invalid.any():
        for idx in gdf[invalid].index:
            reason = explain_validity(gdf.at[idx, "geometry"])
            logging.warning("Invalid geometry at index %s: %s", idx, reason)
        # fix invalid geometries
        gdf["geometry"] = gdf["geometry"].apply(make_valid)
    return gdf


@functools.lru_cache(maxsize=1)
def _read_countries_info(countries_info_path):
    """
    Load and cache the country metadata CSV.

    :param countries_info_path: path to the country metadata CSV
    :returns: a cached DataFrame containing country metadata

    The cache is keyed by the resolved path, so subsequent calls with the
    same path avoid disk I/O.
    """
    return pd.read_csv(countries_info_path)


@functools.lru_cache(maxsize=1)
def _read_world_cities(world_cities_path):
    """
    Load and cache the world-cities CSV.

    :param world_cities_path: path to the world-cities CSV
    :returns: a cached DataFrame containing city coordinates and metadata
    :raises ValueError: if the CSV does not contain an ``lng`` column

    The cache is keyed by the resolved path, so subsequent calls with the
    same path avoid disk I/O.
    """
    df = pd.read_csv(world_cities_path)
    if 'lng' not in df.columns:
        raise ValueError(f'Missing "lng" column in {world_cities_path}')
    return df


def build_classifiers(df, *, breaks):
    """
    Build loss classifiers for the report map categories.

    :param df: DataFrame containing the labeled loss columns
    :param breaks: upper bounds used by the user-defined classifiers
    :returns: a mapping from loss label to a mapclassify classifier
    :raises RuntimeError: if mapclassify is not installed
    """
    try:
        import mapclassify
    except ImportError as exc:
        raise RuntimeError(
            "In order to build map classifiers 'mapclassify' should"
            " be installed."
        ) from exc
    return {meta["label"]: mapclassify.UserDefined(df[meta["label"]],
                                                   bins=breaks)
            for meta in LOSS_METADATA.values()}


def load_admin_boundaries(
        country_name, iso3, adm_level, crs="EPSG:4326"):
    """
    Load and normalize administrative boundaries for one country.

    :param country_name: country name used in error messages
    :param iso3: three-letter country code used to filter the layer
    :param adm_level: administrative level, currently 1 or 2
    :param crs: coordinate reference system for the returned geometries
    :returns: a GeoDataFrame with ``region_id``, ``region_name``, and
        ``country_iso3`` columns
    :raises NotImplementedError: if the administrative level is unsupported
    :raises ValueError: if no boundaries are found for the country
    """
    if adm_level not in (1, 2):
        raise NotImplementedError(f'Admin level {adm_level} not supported')
    fname = get_configured_path(
        f'admin{adm_level}_boundaries_file')
    # NOTE: be careful not mutating the cached object
    #       (in case we need to mutate it, we should make a copy
    #       right after reading)
    gdf = _read_admin_layer(fname)  # cached
    if "shapeID" in gdf.columns:  # geoBoundaries
        iso3_col = "shapeGroup"
        id_col = "shapeID"
        name_col = "shapeName"
    elif f"ID_{adm_level}" in gdf.columns:
        iso3_col = "ID_0"
        id_col = f"ID_{adm_level}"
        name_col = f"NAME_{adm_level}"
    else:
        raise RuntimeError(
            f"Unsupported admin schema. Columns: {list(gdf.columns)}"
        )
    # NOTE: here we make a copy, so we don't alter the cached object
    gdf = gdf[gdf[iso3_col] == iso3]
    if gdf.empty:
        raise ValueError(
            f"No boundaries found for country '{country_name}'")
    # normalize column names
    gdf = gdf.rename(columns={
        iso3_col: "country_iso3",
        id_col: "region_id",
        name_col: "region_name",
    })
    gdf["region_id"] = gdf["region_id"].astype(str)
    gdf["region_name"] = gdf["region_name"].astype(str)
    gdf["country_iso3"] = gdf["country_iso3"].astype(str)
    return gdf.to_crs(crs)


def points_to_gdf(df, lon_col="lon", lat_col="lat", crs=None):
    """
    Convert longitude and latitude columns into point geometries.

    :param df: DataFrame containing point coordinates
    :param lon_col: name of the longitude column
    :param lat_col: name of the latitude column
    :param crs: coordinate reference system assigned to the points
    :returns: a GeoDataFrame retaining the input columns and adding geometry
    """
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs=crs)
    return gdf


def aggregate_losses(points_gdf, admin_gdf, tags_agg):
    """
    Aggregate point losses by administrative region.

    :param points_gdf: GeoDataFrame containing loss points and loss columns
    :param admin_gdf: GeoDataFrame containing normalized region geometries
    :param tags_agg: names of the loss columns to sum
    :returns: administrative boundaries joined with summed loss columns

    Points outside the administrative boundaries are excluded from the
    aggregation.
    """
    joined = gpd.sjoin(points_gdf, admin_gdf, how="inner", predicate="within")
    group_col = 'region_id'
    merge_args = dict(on=group_col)
    aggregated = joined.groupby(group_col).agg(
        {col: "sum" for col in tags_agg})
    return admin_gdf.merge(aggregated, **merge_args)


def save_most_affected_regions(df, dstore, iso3, *, num_regions=5):
    """
    Save the regions with the highest number of fatalities.

    :param df: aggregated regional losses with a fatalities column
    :param dstore: datastore receiving the result
    :param iso3: three-letter country code used in the datastore path
    :param num_regions: maximum number of region names to save
    :returns: ``None``; the names are written to the datastore
    """
    fatalities_label = LOSS_METADATA["occupants"]["label"]
    regions = df.nlargest(
        num_regions, fatalities_label)['region_name'].dropna().tolist()
    dstore[f"impact/{iso3}/most_affected_regions"] = regions
