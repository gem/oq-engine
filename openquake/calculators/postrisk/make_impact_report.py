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
import pathlib
import tempfile
import logging
import functools
import difflib
import urllib.request
import json
import unicodedata
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
from shapely.validation import make_valid, explain_validity
from dataclasses import dataclass
from PIL import Image as PILImage
import pandas as pd
import geopandas as gpd
from openquake import baselib
from openquake.baselib import config, sap
from openquake.calculators.extract import extract
from openquake.calculators.postproc.plots import plot_variable, MapDataElements
from openquake.commonlib import logs
from openquake.commonlib.readinput import get_close_countries

cd = pathlib.Path(__file__).parent

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
LOSS_LABELS = [v["label"] for v in LOSS_METADATA.values()]

COUNTRY_PROFILES_REPO_TREE_URL = (
    "https://api.github.com/repos/gem/risk-profiles/git/trees/master"
    "?recursive=1")
COUNTRY_PROFILES_BASE_URL = "https://github.com/gem/risk-profiles/tree/master"


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


def _strip_accents(text):
    # Decompose accented characters (e.g. ü -> u + combining diaeresis),
    # then drop the combining marks. "Türkiye" -> "Turkiye".
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _normalize(name):
    name = _strip_accents(name)
    return name.strip().lower().replace("_", " ").replace("-", " ")


@functools.lru_cache(maxsize=1)
def _get_country_dirs():
    """Fetch the repo tree once and return {normalized_country_name: path}."""
    req = urllib.request.Request(
        COUNTRY_PROFILES_REPO_TREE_URL,
        headers={"Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)

    if data.get("truncated"):
        raise RuntimeError(
            "GitHub tree response was truncated; repo is too large for a "
            "single recursive call. Consider paginating per-continent instead."
        )

    country_dirs = {}
    for entry in data["tree"]:
        if entry["type"] != "tree":
            continue
        path = entry["path"]
        if path.count("/") == 1:  # depth-1 dir, i.e. Continent/Country
            _, country = path.split("/")
            country_dirs[_normalize(country)] = path
    return country_dirs


def get_country_profile_link(country_name):
    """Return the risk-profiles URL for a given country name, fetched live
    from the GitHub repo (no local dictionary needed).

    Raises KeyError (with close-match suggestions) if not found.
    """
    country_dirs = _get_country_dirs()
    key = _normalize(country_name)

    if key in country_dirs:
        return f"{COUNTRY_PROFILES_BASE_URL}/{country_dirs[key]}"

    close = difflib.get_close_matches(
        key, country_dirs.keys(), n=3, cutoff=0.6)
    suggestion = f" Did you mean: {', '.join(close)}?" if close else ""
    raise KeyError(
        f"No country profile found for {country_name!r}.{suggestion}")


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


def load_admin_boundaries(
        country_name, iso3, adm_level, crs="EPSG:4326"):
    if adm_level == 1:
        try:
            fname = config.directory.admin1_boundaries_file
        except AttributeError:
            # checking if the file is present in oq-engine
            if not os.path.exists(
                    fname := cd.parent.parent.parent /
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


def _get_impact_summary_data(dstore, iso3, no_uncertainty):
    aggrisk_tags = extract(dstore, 'aggrisk_tags')
    mapping = {
        meta["label"]: loss_type
        for loss_type, meta in LOSS_METADATA.items()
    }
    rows = aggrisk_tags.loc[
        (aggrisk_tags['ID_0'] == iso3) &
        (aggrisk_tags['loss_type'].isin(mapping.values()))
    ]
    if rows.empty:
        logging.info(
            f"No losses estimated for country {iso3}. Skipping report")
        return None
    if all(r.lossmea < 1e-5 for _, r in rows.iterrows()):
        logging.info(f"Estimated losses for country {iso3} are negligible"
                     f" (all lossmea < 1e-5). Skipping report.")
        return None
    summary_data = {}
    for label, lt in mapping.items():
        matching_rows = rows.loc[rows['loss_type'] == lt]
        if not matching_rows.empty:
            r = matching_rows.iloc[0]
            q50 = int(round(r.get('q50', 0)))
            q05 = int(round(r.get('q05', 0)))
            q95 = int(round(r.get('q95', 0)))
        else:
            q50 = q05 = q95 = 0
        # Format with thousands separators
        if no_uncertainty:
            # Display only the central value
            summary_data[label] = f"{q50:,}"
        else:
            # Display the range
            summary_data[label] = f"{q05:,} - {q95:,}"
    return summary_data


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


class CountryReportBuilder:
    """
    Builds and stores a single-country impact PDF report.
    """
    # Layout constants
    MARGIN = 20
    DISCLAIMER_H = 40
    HEADER_H = 80
    NOTES_H = 80
    SAFETY_BUFFER = 20
    LOGO_W = 100

    def __init__(
            self, iso3, adm_level, event: EventContext, options: ReportOptions,
            losses_df, summary_data, dstore, time_of_calc, oqparam):
        try:
            import reportlab
            from reportlab import platypus
        except ImportError as exc:
            raise RuntimeError(
                "In order to create an Impact PDF report,"
                " 'reportlab' should be installed"
                ) from exc
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise RuntimeError(
                "In order to save an Impact report as PNG,"
                " 'PyMuPDF' should be installed"
                ) from exc

        self.fitz = fitz
        self.reportlab = reportlab
        self.SimpleDocTemplate = platypus.SimpleDocTemplate
        self.Paragraph = platypus.Paragraph
        self.Table = platypus.Table
        self.TableStyle = platypus.TableStyle
        self.Image = platypus.Image
        self.ListFlowable = platypus.ListFlowable
        self.ListItem = platypus.ListItem
        self.Spacer = platypus.Spacer
        self.getSampleStyleSheet = reportlab.lib.styles.getSampleStyleSheet
        self.ParagraphStyle = reportlab.lib.styles.ParagraphStyle
        self.colors = reportlab.lib.colors
        self.A4 = reportlab.lib.pagesizes.A4

        self.iso3 = iso3
        self.adm_level = adm_level
        self.losses_df = losses_df
        self.summary_data = summary_data
        self.dstore = dstore
        self.time_of_calc = time_of_calc

        # Unpacking EventContext
        self.event_name = event.name
        self.event_date = event.date
        self.shakemap_version = event.shakemap_version
        self.hypocenter = event.hypocenter

        # Unpacking ReportOptions
        self.disclaimer_txt = options.disclaimer_txt
        self.basemap_path = options.basemap_path
        self.threshold_deg = options.threshold_deg
        self.no_uncertainty = options.no_uncertainty
        self.loss_metric = options.loss_metric

        self.styles = self.getSampleStyleSheet()

        self.x_limits = None
        self.y_limits = None
        self.cities = {}

        self._load_country_info()
        self.notes = self._get_notes(oqparam)
        self._compute_layout()

        self._register_unicode_font()
        self.styles["Normal"].fontName = "NotoSans"
        self.styles["Italic"].fontName = "NotoSans-Italic"
        self.styles["Heading1"].fontName = "NotoSans-Bold"

    def _register_unicode_font(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase.pdfmetrics import registerFontFamily

        try:
            fonts_dir = config.directory.fonts_dir
        except AttributeError:
            # checking if the directory is present in oq-engine
            if not os.path.exists(
                    fonts_dir := cd.parent.parent.parent / 'fonts'):
                raise AttributeError(
                    'config.directory.fonts_dir is missing')
        fonts_dir = Path(fonts_dir)

        # family_name -> font file prefix
        font_families = {
            "NotoSans":      "NotoSansSC",  # default: Latin, Cyrillic,
                                            #          Greek, Chinese
            "NotoSans-TC":   "NotoSansTC",  # Traditional Chinese
            "NotoSans-JP":   "NotoSansJP",  # Japanese
            "NotoSans-KR":   "NotoSansKR",  # Korean
            "NotoSans-AR":   "NotoSansArabic",      # Arabic
            "NotoSans-Deva": "NotoSansDevanagari",  # Hindi, Nepali, etc.
            "NotoSans-Beng": "NotoSansBengali",     # Bengali
            "NotoSans-Thai": "NotoSansThai",        # Thai
        }
        for family, name in font_families.items():
            regular = fonts_dir / f"{name}-Regular.ttf"
            bold = fonts_dir / f"{name}-Bold.ttf"
            if not regular.exists():
                logging.warning(f"Font not found: {regular}, skipping")
                continue
            bold_path = str(bold) if bold.exists() else str(regular)
            pdfmetrics.registerFont(TTFont(family,             str(regular)))
            pdfmetrics.registerFont(TTFont(f"{family}-Bold",   bold_path))
            pdfmetrics.registerFont(TTFont(f"{family}-Italic", str(regular)))
            registerFontFamily(
                family,
                normal=family,
                bold=f"{family}-Bold",
                italic=f"{family}-Italic",
                boldItalic=f"{family}-Bold",
            )

    def _select_font(self, text):
        """Pick the right font family based on Unicode block detection."""
        text = str(text)  # handle non-string input gracefully
        for ch in text:
            cp = ord(ch)
            if 0x0600 <= cp <= 0x06FF:
                return "NotoSans-AR"
            if 0x0900 <= cp <= 0x097F:
                return "NotoSans-Deva"
            if 0x0980 <= cp <= 0x09FF:
                return "NotoSans-Beng"
            if 0x0E00 <= cp <= 0x0E7F:
                return "NotoSans-Thai"
            if 0xAC00 <= cp <= 0xD7AF:
                return "NotoSans-KR"
            if 0x3040 <= cp <= 0x309F:
                return "NotoSans-JP"  # Hiragana
            if 0x30A0 <= cp <= 0x30FF:
                return "NotoSans-JP"  # Katakana
            if 0x4E00 <= cp <= 0x9FFF:
                return "NotoSans"
            if 0xF900 <= cp <= 0xFAFF:
                return "NotoSans-TC"
        return "NotoSans"

    def _one_line_paragraph(
            self, text, base_style, max_width, min_font_size=8, step=0.5):
        """
        Try to keep paragraph on one line by reducing font size if needed.
        """
        font_size = base_style.fontSize

        font_name = self._select_font(text)
        if font_name != base_style.fontName:
            base_style = self.ParagraphStyle(
                name="tmp_font",
                parent=base_style,
                fontName=font_name,
            )

        while font_size >= min_font_size:
            style = self.ParagraphStyle(
                name="tmp",
                parent=base_style,
                fontSize=font_size,
                leading=font_size * 1.2,
            )
            p = self.Paragraph(text, style)
            w, h = p.wrap(max_width, 1000)

            # one line ≈ leading height
            if h <= style.leading * 1.05:
                return p

            font_size -= step

        # fallback: smallest font
        style.fontSize = min_font_size
        style.leading = min_font_size * 1.2
        return self.Paragraph(text, style)

    def _scaled_image(self, path, max_w, max_h):
        # scale image preserving aspect ratio
        if not path.exists():
            return self.Paragraph(f"Missing image: {path.name}",
                                  self.getSampleStyleSheet()["Normal"])
        img = PILImage.open(path)
        w, h = img.size
        scale = min(max_w / w, max_h / h)
        return self.Image(str(path), width=w*scale, height=h*scale)

    def _scaled_image_from_bytes(self, image_data, max_w, max_h):
        # If it is an HDF5 dataset, read it
        try:
            image_data = image_data[()]
        except Exception:
            pass
        # scale image preserving aspect ratio
        img = PILImage.open(BytesIO(image_data))
        w, h = img.size
        scale = min(max_w / w, max_h / h)
        return self.Image(BytesIO(image_data), width=w*scale, height=h*scale)

    def _compute_viewport_from_boundaries(
            self, aggregated_gdf, padding_deg=0.5):
        """
        Derive the map viewport from the bounding box of admin boundaries
        of all regions with at least one non-zero loss
        """
        loss_labels = [meta["label"] for meta in LOSS_METADATA.values()]
        mask = aggregated_gdf[loss_labels].gt(0).any(axis=1)
        affected = aggregated_gdf[mask]
        bounds = affected.geometry.total_bounds  # (minx, miny, maxx, maxy)
        return (
            [bounds[0] - padding_deg, bounds[2] + padding_deg],
            [bounds[1] - padding_deg, bounds[3] + padding_deg],
        )

    def _load_country_info(self):
        try:
            countries_info_file = config.directory.countries_info_file
        except AttributeError:
            # checking if the file is present in oq-engine
            if not os.path.exists(
                    countries_info_file := cd.parent.parent.parent /
                    'countries_info.csv'):
                raise AttributeError(
                    'config.directory.countries_info_file is missing')

        path_str = str(Path(countries_info_file).resolve())
        df = _read_countries_info(path_str)   # cached
        row = df.loc[df["ISO3"] == self.iso3].iloc[0]
        self.country_name = row["ENGLISH_COUNTRY"]

    def _get_notes(self, oqparam):
        notes_data = {
            "user_note": oqparam.notes if oqparam.notes else None,
            "profile_link": None,
            "metadata": []
        }
        try:
            country_profile_link = get_country_profile_link(self.country_name)
        except KeyError as exc:
            logging.warning(str(exc))
        else:
            notes_data["profile_link"] = (
                f"Seismic Risk Profile for the Country: "
                f"<font color='blue'><u><a href='{country_profile_link}'>"
                f"{country_profile_link}</a></u></font>"
            )
        rupdic = oqparam.rupture_dict
        meta = notes_data["metadata"]
        meta.append(f'USGS identifier: {rupdic["usgs_id"]}')
        meta.append(f'Longitude: {rupdic["lon"]}')
        meta.append(f'Latitude: {rupdic["lat"]}')
        meta.append(f'Depth: {rupdic["dep"]}')
        meta.append(f'Magnitude: {rupdic["mag"]}')
        meta.append(f'Rake: {rupdic["rake"]}')
        meta.append(f'Dip: {rupdic["dip"]}')
        meta.append(f'Strike: {rupdic["strike"]}')
        if rupdic['approach'] != 'use_shakemap_from_usgs':
            meta.append(f'Mosaic model: {oqparam.mosaic_model}')
            meta.append(
                f'Tectonic region type: {oqparam.tectonic_region_type}')
        meta.append(f'Number of ground motion fields:'
                    f' {oqparam.number_of_ground_motion_fields}')
        meta.append(f'Truncation level: {oqparam.truncation_level}')
        meta.append(f'Considered time of the event: {oqparam.time_event}')
        return notes_data

    def _get_cities_in_viewport(self, num_cities=15):
        """
        Finds Top num_cities cities within the map viewport belonging
        to the current country
        """
        try:
            # NOTE: using for the report a file structured differently with
            # respect to openquake/qa_tests_data/mosaic/worldcities.csv
            # We may want to replace the other file with this, changing also
            # the expected column names.
            world_cities_file = config.directory.world_cities_file
        except AttributeError:
            # checking if the file is present in oq-engine
            if not os.path.exists(
                    world_cities_file := cd.parent.parent.parent /
                    'worldcities.csv'):
                raise AttributeError(
                    'config.directory.world_cities_file is missing')
        path_str = str(Path(world_cities_file).resolve())
        df = _read_world_cities(path_str)   # cached
        # Pull the pre-calculated limits
        min_lon, max_lon = self.x_limits
        min_lat, max_lat = self.y_limits
        # Spatial query + Country filter
        mask = (df['iso3'] == self.iso3) & \
               (df['lng'] >= min_lon) & (df['lng'] <= max_lon) & \
               (df['lat'] >= min_lat) & (df['lat'] <= max_lat)
        # Take the biggest ones
        top_cities = df[mask].sort_values(
            'population', ascending=False).head(num_cities)
        return {row['city_ascii']: [row['lng'], row['lat']]
                for _, row in top_cities.iterrows()}

    def _compute_layout(self):
        self.page_width = self.A4[0] - (2 * self.MARGIN)
        self.page_height = self.A4[1] - (2 * self.MARGIN)

        self.grid_total_h = (
            self.page_height
            - self.DISCLAIMER_H
            - self.HEADER_H
            - self.NOTES_H
            - self.SAFETY_BUFFER
        )

        self.row_h = self.grid_total_h / 2
        self.col_w = self.page_width / 2

    def _generate_country_plots(self):
        import matplotlib.pyplot as plt
        tags_agg_losses = list(LOSS_METADATA)
        admin_boundaries = load_admin_boundaries(
            self.country_name, self.iso3, self.adm_level)
        points_gdf = points_to_gdf(self.losses_df, crs=admin_boundaries.crs)
        aggloss_df = aggregate_losses(
            points_gdf, admin_boundaries, tags_agg_losses)
        aggloss_df = aggloss_df.rename(columns={k: v["label"]
                                       for k, v in LOSS_METADATA.items()})
        save_most_affected_regions(aggloss_df, self.dstore, self.iso3)
        self.x_limits, self.y_limits = self._compute_viewport_from_boundaries(
            aggloss_df)
        self.cities = self._get_cities_in_viewport()

        classifiers = build_classifiers(aggloss_df, breaks=[1, 10, 100, 1000])
        images = {}
        for meta in LOSS_METADATA.values():
            label = meta["label"]
            plot_title = f'{self.loss_metric} {meta["title"]}'
            elements = MapDataElements(
                plot_title=plot_title,
                # legend_title=label,  # already in plot title
                cities=self.cities,
                x_limits=self.x_limits,
                y_limits=self.y_limits,
                basemap_path=self.basemap_path,
                epicenter=self.hypocenter
            )
            fig, ax = plot_variable(
                aggloss_df, admin_boundaries, label,
                classifiers[label], meta["colors"],
                elements=elements
            )
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            images[label] = buf.getvalue()
        return images

    def _build_disclaimer(self):
        tbl = self.Table(
            [[self.Paragraph(f"<b>DISCLAIMER</b>: {self.disclaimer_txt}",
                             self.styles["Normal"])]],
            colWidths=[self.page_width],
            rowHeights=[self.DISCLAIMER_H],
        )

        tbl.setStyle(self.TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), self.colors.lightcoral),
            ("BOX",         (0, 0), (-1, -1), 1, self.colors.red),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))

        return tbl

    def _build_header(self):
        event_style = self.ParagraphStyle(
            "EventTitle",
            parent=self.styles["Normal"],
            fontName="NotoSans-Bold",
            fontSize=12,
            leading=14,
        )

        meta_style = self.ParagraphStyle(
            "HeaderMeta",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=11
        )

        # subtracting also the padding
        title_width = self.page_width - self.LOGO_W - 12

        # Line 1: Bold event name
        event_text = f"<b>{self.event_name}</b>"
        event_paragraph = self._one_line_paragraph(
            event_text,
            event_style,
            max_width=title_width,
        )

        oq_basedir = Path(baselib.__path__[0].rsplit("/", 2)[0])
        logo_path = (
            oq_basedir
            / "doc"
            / "_static"
            / "OQ-Logo-Standard-RGB-72DPI-01.png"  # FIXME: is this logo ok?
        )

        logo_img = self._scaled_image(
            logo_path,
            self.LOGO_W,
            self.HEADER_H - 10,
        )

        # Build individual paragraph blocks for lines 2, 3, and 4
        sm_version_txt = None
        if self.shakemap_version is not None:
            sm_version_txt = f'ShakeMap version: {self.shakemap_version}'
        date_txt = f"Time of the event: {self.event_date}"
        calc_txt = f"Time of the calculation: {self.time_of_calc}"
        header_text = [event_paragraph]
        if sm_version_txt:
            header_text.append(
                self._one_line_paragraph(
                    sm_version_txt, meta_style, max_width=title_width))
        header_text.extend([
            self._one_line_paragraph(
                date_txt, meta_style, max_width=title_width),
            self._one_line_paragraph(
                calc_txt, meta_style, max_width=title_width),
        ])

        tbl = self.Table(
            [[header_text, logo_img]],
            colWidths=[self.page_width - self.LOGO_W, self.LOGO_W],
            rowHeights=[self.HEADER_H],
        )

        tbl.setStyle(self.TableStyle([
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("ALIGN",      (1, 0), (1, 0), "RIGHT"),  # logo to the right
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))

        return tbl

    def _grid_styles(self):
        body_style = self.ParagraphStyle(
            "GridBodyText",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=11,
        )
        title_style = self.ParagraphStyle(
            "GridSectionTitle",
            parent=self.styles["Normal"],
            fontName="NotoSans-Bold",
            fontSize=11,
            leading=14,
        )
        return body_style, title_style

    def _build_summary_table(self, body_style):
        col_header = ("Estimated losses" if self.no_uncertainty
                      else "Range of losses (5% - 95%)")
        table_data = [[
            self.Paragraph("<b>Impact metric</b>", body_style),
            self.Paragraph(f"<b>{col_header}</b>", body_style)
        ]]
        for meta in LOSS_METADATA.values():
            table_data.append([
                self.Paragraph(meta["label"], body_style),
                self.Paragraph(self.summary_data[meta["label"]], body_style)
            ])
        if self.no_uncertainty:
            table_data.append([
                self.Paragraph("No uncertainty was included", body_style), ""])

        summary_table = self.Table(
            table_data,
            colWidths=[self.col_w * 0.42, self.col_w * 0.48],
            hAlign="LEFT",
        )
        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors.whitesmoke),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]
        if self.no_uncertainty:
            last_row_idx = len(table_data) - 1
            style_cmds.append(("SPAN", (0, last_row_idx), (1, last_row_idx)))
        summary_table.setStyle(self.TableStyle(style_cmds))
        return summary_table

    def _build_left_bundle(self, summary_table, body_style, title_style):
        most_affected = self.dstore[
            f"impact/{self.iso3}/most_affected_regions"
        ]
        return [
            self.Paragraph(
                f"<b>Summary of impact for {self.country_name}:</b>",
                title_style),
            self.Spacer(1, 4),
            summary_table,
            self.Spacer(1, 12),
            self.Paragraph("<b>Regions with highest number of fatalities:</b>",
                           title_style),
            self.ListFlowable(
                [self.ListItem(self.Paragraph(region_name, self.ParagraphStyle(
                    "region",
                    parent=body_style,
                    fontName=self._select_font(region_name),
                ))) for region_name in most_affected],
                bulletType="bullet",
                leftIndent=15,
            ),
        ]

    # NOTE: passing images explicitly to avoid implicit ordering dependency
    def _build_grid(self, images):
        body_style, title_style = self._grid_styles()
        summary_table = self._build_summary_table(body_style)
        left_bundle = self._build_left_bundle(
            summary_table, body_style, title_style)

        img_top_right = self._scaled_image_from_bytes(
            images[LOSS_METADATA['number']['label']],
            self.col_w - 10,
            self.row_h - 10,
        )
        img_bot_left = self._scaled_image_from_bytes(
            images[LOSS_METADATA['occupants']['label']],
            self.col_w - 10,
            self.row_h - 10,
        )
        img_bot_right = self._scaled_image_from_bytes(
            images[LOSS_METADATA['residents']['label']],
            self.col_w - 10,
            self.row_h - 10,
        )
        tbl = self.Table(
            [
                [left_bundle, img_top_right],
                [img_bot_left, img_bot_right],
            ],
            colWidths=[self.col_w, self.col_w],
            rowHeights=[self.row_h, self.row_h],
        )
        tbl.setStyle(self.TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 1), "CENTER"),
            ("ALIGN", (0, 1), (0, 1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return tbl

    def _build_notes(self):
        """
        Builds a bordered notes box with dedicated, dynamic rows for full-width
        user notes and web links, anchoring a 3-column metadata grid below.
        """
        story = []
        if not self.notes or not isinstance(self.notes, dict):
            return story
        grid_data = []

        styles_to_apply = [
            ('BOX', (0, 0), (-1, -1), 1, self.reportlab.lib.colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]

        # Create a compact font style variant for the notes box
        notes_style = self.ParagraphStyle(
            'NotesStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=7.5
        )
        # Header and Optional User Custom Notes Row
        user_note = self.notes.get("user_note")
        header_text = (
            f"<b>Notes:</b> {user_note}" if user_note else "<b>Notes:</b>")
        grid_data.append([self.Paragraph(header_text, notes_style), "", ""])
        styles_to_apply.append(('SPAN', (0, 0), (2, 0)))
        # Keep spacing tight below title
        styles_to_apply.append(('BOTTOMPADDING', (0, 0), (2, 0), 0))

        # Optional Standalone Profile Link Row
        profile_link = self.notes.get("profile_link")
        if profile_link:
            grid_data.append(
                [self.Paragraph(profile_link, notes_style), "", ""])
            link_row_idx = len(grid_data) - 1
            styles_to_apply.append(
                ('SPAN', (0, link_row_idx), (2, link_row_idx)))
            styles_to_apply.append(
                ('BOTTOMPADDING', (0, link_row_idx), (2, link_row_idx), 2))

        # 3. Spread the remaining system metadata across 3 columns
        notes_items = self.notes.get("metadata", [])
        for i in range(0, len(notes_items), 3):
            row = [self.Paragraph(item, notes_style)
                   for item in notes_items[i:i+3]]
            while len(row) < 3:
                row.append(self.Paragraph("", notes_style))
            grid_data.append(row)

        # 4. Add safety cushion at the bottom of the last metadata row
        styles_to_apply.append(('BOTTOMPADDING', (0, -1), (2, -1), 6))

        t = self.Table(grid_data, colWidths=[180, 180, 180])
        t.setStyle(self.TableStyle(styles_to_apply))
        story.append(t)
        return story

    def build(self):
        logging.info(f'Making impact PDF report for {self.iso3}...')
        images = self._generate_country_plots()

        buffer = BytesIO()

        doc = self.SimpleDocTemplate(
            buffer,
            pagesize=self.A4,
            leftMargin=self.MARGIN,
            rightMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=self.MARGIN,
        )

        master_layout = self.Table(
            [
                [self._build_disclaimer()],
                [self._build_header()],
                [self._build_grid(images)],
                [self._build_notes()],
            ],
            colWidths=[self.page_width],
            rowHeights=[
                self.DISCLAIMER_H,
                self.HEADER_H,
                self.grid_total_h,
                self.NOTES_H,
            ],
        )

        master_layout.setStyle(self.TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        doc.build([master_layout])

        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        pdf_path = f'impact/{self.iso3}/report_pdf'
        self.dstore[pdf_path] = pdf_bytes
        logging.info(
            f'The report PDF was saved into the datastore as {pdf_path}')

        # Generate and save an exact PNG duplicate of the layout
        pdf_doc = self.fitz.open(stream=pdf_bytes, filetype="pdf")
        # NOTE: this grid is hard-coded to a single A4 page
        page = pdf_doc.load_page(0)
        # Render to a crisp image at 3.0x scaling (~300 DPI equivalent)
        pix = page.get_pixmap(matrix=self.fitz.Matrix(3.0, 3.0))
        png_path = f'impact/{self.iso3}/report_png'
        self.dstore[png_path] = pix.tobytes("png")
        pdf_doc.close()
        logging.info(
            f'The report PNG was saved into the datastore as {png_path}')


def make_report_for_country(
        iso3, adm_level, event, options, losses_df, summary_data,
        dstore, time_of_calc, oqparam):
    builder = CountryReportBuilder(
        iso3, adm_level, event, options, losses_df, summary_data,
        dstore, time_of_calc, oqparam)
    builder.build()


def to_utc_string(ts: str) -> str:
    """
    Convert a timestamp with timezone offset (e.g. '+08:00')
    to the format: 'YYYY-MM-DD HH:MM:SS UTC'
    """
    if not ts:
        return "unknown"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        logging.warning("Timestamp has no timezone information")
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'


def get_dynamic_threshold(mag):
    """
    Returns a search threshold in degrees based on earthquake magnitude.
    """
    if mag < 5.0:
        return 1.0  # ~111 km
    elif mag < 6.5:
        return 2.0  # ~222 km
    elif mag < 7.5:
        return 3.0  # ~333 km
    else:
        return 5.0  # ~555 km


def main(dstore, adm_level=1, threshold_deg=None):
    """
    Create an impact report in PDF and PNG formats
    """
    if isinstance(dstore, (str, int)):
        # NOTE: called from the command line
        from openquake.commonlib import datastore
        calc_id = int(dstore)
        dstore = datastore.read(calc_id, mode='r+')
    else:
        calc_id = dstore.calc_id
    adm_level = int(adm_level)
    try:
        basemap_path = config.directory.basemap_file
    except AttributeError:
        basemap_path = None
        logging.error('config.directory.basemap_file is missing!')
    dstore.close()
    dstore.open('r+')
    dstore.export_dir = config.directory.custom_tmp or tempfile.gettempdir()
    oqparam = dstore['oqparam']
    mag = oqparam.rupture_dict['mag']
    lon = oqparam.rupture_dict['lon']
    lat = oqparam.rupture_dict['lat']
    # If the ground motion is fully deterministic, we suppress uncertainty
    # ranges in the report and show only the central (point) estimate.
    no_uncertainty = (
        oqparam.number_of_ground_motion_fields == 1
        and abs(oqparam.truncation_level) < 1e-8
    )
    hypocenter = (lon, lat)
    avg_losses = extract(dstore, 'avg_losses?kind=stats')
    # Use the median (quantile-0.5) as the representative point estimate for
    # the spatial loss maps, consistent with how _get_impact_summary_data
    # displays the central value.  Fall back to the mean only if the median is
    # unavailable (e.g. a calculation run without quantile outputs).
    loss_metric = None
    if hasattr(avg_losses, 'quantile-0.5') and avg_losses[
            'quantile-0.5'] is not None:
        losses_df = pd.DataFrame(avg_losses['quantile-0.5'])
        loss_metric = 'Median'
    elif hasattr(avg_losses, 'mean') and avg_losses.mean is not None:
        logging.warning(
            "Median losses not available; falling back to mean for loss maps.")
        losses_df = pd.DataFrame(avg_losses.mean)
        loss_metric = 'Mean'
    else:
        raise RuntimeError(
            "avg_losses has neither 'quantile' nor 'mean' attribute; "
            "cannot build losses DataFrame.")
    rupdic = oqparam.rupture_dict
    try:
        event_name = rupdic['description']
    except KeyError:
        event_name = rupdic['title']
    # FIXME: do we prefer to show UTC or perhaps it is more intuitive
    #        to show the local time?
    event_date = to_utc_string(oqparam.local_timestamp)
    try:
        shakemap_version = rupdic['shakemap_desc']
    except KeyError:
        shakemap_version = None
    job = logs.dbcmd('get_job', calc_id)
    time_of_calc = job.start_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
    disclaimer_txt = '''
    This is an automatically generated draft. Content has not been verified for
    accuracy by a human reviewer. The metrics presented were estimated based on
    ground shaking information from ShakeMap only. Impact assessments are
    subject to changes as more information becomes available.'''
    if threshold_deg is None:
        threshold_deg = get_dynamic_threshold(mag)
        logging.info(f"Magnitude {mag} detected. Using dynamic"
                     f" threshold: {threshold_deg} degrees.")
    else:
        threshold_deg = float(threshold_deg)
    iso3_codes = get_close_countries(lon, lat, buffer_radius=threshold_deg)
    if not iso3_codes:
        raise RuntimeError(
            "No country within {threshold_deg} from the hypocenter")
    event_ctx = EventContext(
        name=event_name, date=event_date, hypocenter=hypocenter,
        shakemap_version=shakemap_version)
    report_opts = ReportOptions(
        disclaimer_txt=disclaimer_txt,
        basemap_path=basemap_path, threshold_deg=threshold_deg,
        no_uncertainty=no_uncertainty, loss_metric=loss_metric)
    for iso3 in iso3_codes:
        summary_data = _get_impact_summary_data(dstore, iso3, no_uncertainty)
        if summary_data is not None:
            make_report_for_country(
                iso3, adm_level, event_ctx, report_opts,
                losses_df, summary_data, dstore, time_of_calc, oqparam)


if __name__ == '__main__':
    sap.run(main)
