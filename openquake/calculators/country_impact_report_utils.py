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

import os
import functools
import logging
import pathlib
from dataclasses import dataclass
from shapely.validation import make_valid, explain_validity
import pandas as pd
import geopandas as gpd
from openquake.baselib import config


cd = pathlib.Path(__file__).parent


@dataclass
class EventContext:
    """Metadata related to the seismic event."""
    name: str
    date: str
    hypocenter: tuple[float, float]
    shakemap_version: str = None


@dataclass
class ReportOptions:
    """Visual, text, and threshold configurations for the report."""
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
        "label": "Displaced",
        "title": "displaced population",
        "colors": [
            '#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043'],
    },
    "number": {
        "label": "Buildings lost",
        "title": "buildings beyond repair",
        "colors": [
            '#ffffff', '#bdbdbd', '#737373', '#424242', '#000000'],
    },
}


# maxsize=1 is sufficient when only one admin-level boundary file is loaded
# per process (the common case). Increase to 2 if both adm1 and adm2 files
# are ever used within the same process.
@functools.lru_cache(maxsize=1)
def _read_admin_layer(fname):
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
    Load and cache the countries CSV keyed on the resolved file path.
    Subsequent calls with the same path return the in-memory DataFrame
    without any disk I/O.
    """
    return pd.read_csv(countries_info_path)


@functools.lru_cache(maxsize=1)
def _read_world_cities(world_cities_path):
    """
    Load and cache the world-cities CSV keyed on the resolved file path.
    """
    df = pd.read_csv(world_cities_path)
    if 'lng' not in df.columns:
        raise ValueError(f'Missing "lng" column in {world_cities_path}')
    return df


def build_classifiers(df, *, breaks):
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
    if adm_level == 1:
        try:
            fname = config.directory.admin1_boundaries_file
        except AttributeError:
            # checking if the file is present in the oq-engine directory
            if not os.path.exists(
                    fname := cd.parent.parent /
                    'World_Adm1_updated.gpkg'):
                raise AttributeError(
                    'config.directory.admin1_boundaries_file is missing')
    elif adm_level == 2:
        try:
            fname = config.directory.admin2_boundaries_file
        except AttributeError as exc:
            raise AttributeError(
                'config.directory.admin2_boundaries_file is missing') from exc
    else:
        raise NotImplementedError(f'Admin level {adm_level} not supported')
    if not fname:
        raise AttributeError(
            f'config.directory.admin{adm_level}_boundaries_file is missing')
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
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs=crs)
    return gdf


def aggregate_losses(points_gdf, admin_gdf, tags_agg):
    joined = gpd.sjoin(points_gdf, admin_gdf, how="inner", predicate="within")
    group_col = 'region_id'
    merge_args = dict(on=group_col)
    aggregated = joined.groupby(group_col).agg(
        {col: "sum" for col in tags_agg})
    return admin_gdf.merge(aggregated, **merge_args)


def save_most_affected_regions(df, dstore, iso3, *, num_regions=5):
    fatalities_label = LOSS_METADATA["occupants"]["label"]
    regions = df.nlargest(
        num_regions, fatalities_label)['region_name'].dropna().tolist()
    dstore[f"impact/{iso3}/most_affected_regions"] = regions
