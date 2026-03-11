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

import tempfile
import logging
import functools
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
from shapely.validation import make_valid, explain_validity

from PIL import Image as PILImage
import pandas as pd
import geopandas as gpd
from openquake import baselib
from openquake.baselib import config, sap
from openquake.calculators.extract import extract
from openquake.calculators.postproc.plots import plot_variable
from openquake.commonlib import logs
from openquake.commonlib.calc import get_close_regions


LOSS_METADATA = {
    "occupants": {
        "label": "Fatalities",
        "title": "Fatalities",
        "colors": [
            '#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d'],
    },
    "residents": {
        "label": "Displaced",
        "title": "Displaced population",
        "colors": [
            '#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043'],
    },
    "number": {
        "label": "Buildings lost",
        "title": "Buildings beyond repair",
        "colors": [
            '#ffffff', '#bdbdbd', '#737373', '#424242', '#000000'],
    },
}
LOSS_LABELS = [v["label"] for v in LOSS_METADATA.values()]


@functools.lru_cache(maxsize=2)
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
        fname = config.directory.admin1_boundaries_file
    elif adm_level == 2:
        fname = config.directory.admin2_boundaries_file
    else:
        raise NotImplementedError(f'Admin level {adm_level} not supported')
    if not fname:
        raise AttributeError(
            f'config.directory.admin{adm_level}_boundaries_file is missing')
    # NOTE: be careful not mutating the cached object
    #       (in case we need to mutate it, we should make a copy right after reading)
    gdf = _read_admin_layer(fname)
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


def load_losses_csv(csv_path):
    df = pd.read_csv(csv_path, header=[0, 1])
    df.columns = df.columns.get_level_values(1)
    df = df.drop(index=0).reset_index(drop=True)
    return df


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
            "In order to build map classifiers 'mapclassify' should be installed."
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
        return None
    summary_data = {}
    for label, lt in mapping.items():
        r = rows.loc[rows['loss_type'] == lt].iloc[0]
        if no_uncertainty:
            # Display only the central value
            summary_data[label] = f"{int(round(r.q50))}"
        else:
            # Display the range
            summary_data[label] = f"{int(round(r.q05))} - {int(round(r.q95))}"
    # Return None if all mean losses are approximately zero
    if all(r.lossmea < 1e-5 for _, r in
           rows.loc[rows['loss_type'].isin(mapping.values())].iterrows()):
        return None
    return summary_data


class CountryReportBuilder:
    """
    Builds and stores a single-country impact PDF report.
    """
    # Layout constants
    MARGIN = 20
    DISCLAIMER_H = 40
    HEADER_H = 60
    NOTES_H = 80
    SAFETY_BUFFER = 20
    LOGO_W = 100

    def __init__(
            self, iso3, event_name, event_date, shakemap_version, time_of_calc,
            disclaimer_txt, notes_txt, losses_df, summary_data, basemap_path,
            adm_level, dstore, hypocenter, threshold_deg, no_uncertainty):
        try:
            import reportlab
            from reportlab import platypus
        except ImportError as exc:
            raise RuntimeError(
                "In order to create an Impact PDF report,"
                " 'reportlab' should be installed"
                ) from exc
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
        self.event_name = event_name
        self.event_date = event_date
        self.shakemap_version = shakemap_version
        self.time_of_calc = time_of_calc
        self.disclaimer_txt = disclaimer_txt
        self.notes_txt = notes_txt
        self.losses_df = losses_df
        self.summary_data = summary_data
        self.basemap_path = basemap_path
        self.adm_level = adm_level
        self.dstore = dstore
        self.hypocenter = hypocenter
        self.threshold_deg = threshold_deg
        self.no_uncertainty = no_uncertainty

        self.styles = self.getSampleStyleSheet()

        self.x_limits = None
        self.y_limits = None
        self.cities = {}

        self._load_country_info()
        self._compute_layout()

        self._register_unicode_font()
        self.styles["Normal"].fontName = "DejaVu"
        self.styles["Italic"].fontName = "DejaVu-Italic"
        self.styles["Heading1"].fontName = "DejaVu-Bold"

    def _register_unicode_font(self):
        import matplotlib
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase.pdfmetrics import registerFontFamily

        dejavu_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        pdfmetrics.registerFont(
            TTFont("DejaVu",
                   str(dejavu_dir / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(
            TTFont("DejaVu-Bold",
                   str(dejavu_dir / "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFont(
            TTFont("DejaVu-Italic",
                   str(dejavu_dir / "DejaVuSans-Oblique.ttf")))
        pdfmetrics.registerFont(
            TTFont("DejaVu-BoldItalic",
                   str(dejavu_dir / "DejaVuSans-BoldOblique.ttf")))
        registerFontFamily(
            "DejaVu",
            normal="DejaVu",
            bold="DejaVu-Bold",
            italic="DejaVu-Italic",
            boldItalic="DejaVu-BoldItalic",
        )

    def _one_line_paragraph(
            self, text, base_style, max_width, min_font_size=8, step=0.5):
        """
        Try to keep paragraph on one line by reducing font size if needed.
        """
        font_size = base_style.fontSize

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
        countries_info_file = config.directory.countries_info_file
        if not countries_info_file:
            raise AttributeError(
                'config.directory.countries_info_file is missing')
        df = pd.read_csv(countries_info_file)
        row = df.loc[df["ISO3"] == self.iso3].iloc[0]
        self.country_name = row["ENGLISH_COUNTRY"]

    def _get_cities_in_viewport(self, num_cities=15):
        """
        Finds Top num_cities cities within the map viewport belonging
        to the current country
        """
        world_cities_file = config.directory.world_cities_file
        if not world_cities_file:
            raise AttributeError(
                'config.directory.world_cities_file is missing')
        df = pd.read_csv(world_cities_file)
        # NOTE: assuming that the CSV uses 'lng' for longitude
        if 'lng' not in df:
            ValueError(f'Missing "lng" column in {world_cities_file}')
        # Pull the pre-calculated limits
        min_lon, max_lon = self.x_limits
        min_lat, max_lat = self.y_limits
        # Spatial query + Country filter
        mask = (df['iso3'] == self.iso3) & \
               (df['lng'] >= min_lon) & (df['lng'] <= max_lon) & \
               (df['lat'] >= min_lat) & (df['lat'] <= max_lat)
        viewport_cities = df[mask].copy()
        # Take the biggest ones
        top_cities = viewport_cities.sort_values(
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

    def _generate_country_plot(self):
        import matplotlib.pyplot as plt
        tags_agg_losses = list(LOSS_METADATA)
        admin_boundaries = load_admin_boundaries(
            self.country_name, self.iso3, self.adm_level)
        points_gdf = points_to_gdf(self.losses_df, crs=admin_boundaries.crs)
        df = aggregate_losses(points_gdf, admin_boundaries, tags_agg_losses)
        df = df.rename(columns={k: v["label"]
                                for k, v in LOSS_METADATA.items()})
        save_most_affected_regions(df, self.dstore, self.iso3)
        self.x_limits, self.y_limits = self._compute_viewport_from_boundaries(df)
        self.cities = self._get_cities_in_viewport()

        classifiers = build_classifiers(df, breaks=[1, 10, 100, 1000])
        images = {}
        for meta in LOSS_METADATA.values():
            label = meta["label"]
            fig, ax = plot_variable(
                df, admin_boundaries, label, classifiers[label],
                meta["colors"], country_name=self.country_name,
                plot_title=meta["title"],
                legend_title=label, cities=self.cities,
                x_limits=self.x_limits, y_limits=self.y_limits,
                basemap_path=self.basemap_path, epicenter=self.hypocenter)
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            images[label] = buf.getvalue()
        return df, images

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
            fontSize=11,
        )

        # subtracting also the padding
        title_width = self.page_width - self.LOGO_W - 12

        event_text = f"<b>{self.event_name}. {self.event_date}</b>"
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
            / "OQ-Logo-Standard-RGB-72DPI-01.png"  # FIXME: is this the right one?
        )

        logo_img = self._scaled_image(
            logo_path,
            self.LOGO_W,
            self.HEADER_H - 10,
        )

        txt = f"Time of the calculation: {self.time_of_calc}"
        if self.shakemap_version is not None:
            txt += f" &nbsp;&nbsp;ShakeMap version: {self.shakemap_version}"
        header_text = [
            event_paragraph,
            self._one_line_paragraph(
                txt,
                self.styles["Italic"],
                max_width=title_width,
            ),
        ]

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

    def _build_grid(self):
        # Determine column header based on uncertainty
        col_header = "Estimated losses" if self.no_uncertainty else "Range of losses"
        table_data = [["", col_header]] + [
            [meta["label"], self.summary_data[meta["label"]]]
            for meta in LOSS_METADATA.values()
        ]

        if self.no_uncertainty:
            table_data.append(["No uncertainty was included", ""])

        summary_table = self.Table(
            table_data,
            colWidths=[self.col_w * 0.45, self.col_w * 0.45],
            hAlign="LEFT",
        )

        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors.whitesmoke),
            ("SIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]

        if self.no_uncertainty:
            # Span the last row across both columns and italicize
            last_row_idx = len(table_data) - 1
            style_cmds.append(("SPAN", (0, last_row_idx), (1, last_row_idx)))
            style_cmds.append(("FONTNAME", (0, last_row_idx), (0, last_row_idx),
                               "Helvetica-Oblique"))

        summary_table.setStyle(self.TableStyle(style_cmds))

        most_affected = self.dstore[
            f"impact/{self.iso3}/most_affected_regions"
        ]

        left_bundle = [
            self.Paragraph(
                f"<b>Summary of impact for {self.country_name}:</b>",
                self.styles["Normal"]),
            self.Spacer(1, 4),
            summary_table,
            self.Spacer(1, 12),
            self.Paragraph("<b>Most affected regions</b>",
                           self.styles["Normal"]),
            self.ListFlowable(
                [self.ListItem(self.Paragraph(x, self.styles["Normal"]))
                 for x in most_affected],
                bulletType="bullet",
                leftIndent=15,
            ),
        ]

        img_top_right = self._scaled_image_from_bytes(
            self.images[LOSS_METADATA['number']['label']],
            self.col_w - 10,
            self.row_h - 10,
        )

        img_bot_left = self._scaled_image_from_bytes(
            self.images[LOSS_METADATA['occupants']['label']],
            self.col_w - 10,
            self.row_h - 10,
        )

        img_bot_right = self._scaled_image_from_bytes(
            self.images[LOSS_METADATA['residents']['label']],
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
        tbl = self.Table(
            [[self.Paragraph(f"<b>Notes</b>: {self.notes_txt}",
                             self.styles["Normal"])]],
            colWidths=[self.page_width],
            rowHeights=[self.NOTES_H],
        )

        tbl.setStyle(self.TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, self.colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), self.colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
        ]))

        return tbl

    def build(self):
        logging.info(f'Making impact PDF report for {self.iso3}...')
        self.df, self.images = self._generate_country_plot()

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
                [self._build_grid()],
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
        report_path = f'impact/{self.iso3}/report_pdf'
        self.dstore[report_path] = buffer.getvalue()
        logging.info(
            f'The report was saved into the datastore as {report_path}')


def make_report_for_country(
        iso3, event_name, event_date, shakemap_version, time_of_calc,
        disclaimer_txt, notes_txt, losses_df, summary_data,
        basemap_path, adm_level, dstore, hypocenter, threshold_deg, no_uncertainty):
    builder = CountryReportBuilder(
        iso3, event_name, event_date, shakemap_version, time_of_calc,
        disclaimer_txt, notes_txt, losses_df, summary_data, basemap_path,
        adm_level, dstore, hypocenter, threshold_deg, no_uncertainty)
    builder.build()


def _get_notes(oqparam):
    notes = ''
    if oqparam.notes:
        notes += oqparam.notes + '<br/>'
    rupdic = oqparam.rupture_dict
    notes += f'Rupture identifier: {rupdic["usgs_id"]}'
    notes += f'. Lon: {rupdic["lon"]}'
    notes += f'. Lat: {rupdic["lat"]}'
    notes += f'. Dep: {rupdic["dep"]}'
    notes += f'. Mag: {rupdic["mag"]}'
    notes += f'. Rake: {rupdic["rake"]}'
    notes += f'. Dip: {rupdic["dip"]}'
    notes += f'. Strike: {rupdic["strike"]}'
    notes += f'. <br/>Mosaic model: {oqparam.mosaic_model}'
    notes += (f'. Number of ground motion fields:'
              f' {oqparam.number_of_ground_motion_fields}')
    notes += f'. Truncation level: {oqparam.truncation_level}'
    notes += f'. Time of the event: {oqparam.time_event}'
    notes += f'. Tectonic region type: {oqparam.tectonic_region_type}'
    return notes


def to_utc_string(ts: str) -> str:
    """
    Convert a timestamp with timezone offset (e.g. '+08:00')
    to the format: 'YYYY-MM-DD HH:MM:SS UTC'
    """
    ret_str = 'Time of the event: '
    if not ts:
        return ret_str + "unknown"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        logging.warning("Timestamp has no timezone information")
        return ret_str + dt.strftime('%Y-%m-%d %H:%M:%S')
    dt_utc = dt.astimezone(timezone.utc)
    return ret_str + dt_utc.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'


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
    Create a PDF impact report
    """
    if isinstance(dstore, (str, int)):
        # NOTE: called from the command line
        from openquake.commonlib import datastore
        calc_id = int(dstore)
        dstore = datastore.read(calc_id, mode='r+')
    else:
        calc_id = dstore.calc_id
    adm_level = int(adm_level)
    basemap_path = config.directory.basemap_file
    if not basemap_path:
        raise AttributeError('config.directory.basemap_file is missing')
    dstore.close()
    dstore.open('r+')
    dstore.export_dir = config.directory.custom_tmp or tempfile.gettempdir()
    oqparam = dstore['oqparam']
    mag = oqparam.rupture_dict['mag']
    lon = oqparam.rupture_dict['lon']
    lat = oqparam.rupture_dict['lat']
    if (oqparam.number_of_ground_motion_fields == 1
            and abs(oqparam.truncation_level) < 1e-8):
        no_uncertainty = True
    else:
        no_uncertainty = False
    hypocenter = (lon, lat)
    avg_losses = extract(dstore, 'avg_losses?kind=stats')
    losses_df = pd.DataFrame(avg_losses.mean)
    rupdic = oqparam.rupture_dict
    event_name = rupdic['description']
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
    This is an automatically generated draft. Content has not been verified
    for accuracy by a human reviewer. Please treat all figures as provisional
    until a final validated version is issued.'''
    notes_txt = _get_notes(oqparam)
    if threshold_deg is None:
        threshold_deg = get_dynamic_threshold(mag)
        logging.info(f"Magnitude {mag} detected. Using dynamic"
                     f" threshold: {threshold_deg} degrees.")
    else:
        threshold_deg = float(threshold_deg)
    iso3_codes = get_close_regions(
        lon, lat, buffer_radius=threshold_deg, region_kind='country')
    if not iso3_codes:
        raise RuntimeError(
            "No country within {threshold_deg} from the hypocenter")
    for iso3 in iso3_codes:
        summary_data = _get_impact_summary_data(dstore, iso3, no_uncertainty)
        if summary_data is not None:
            make_report_for_country(
                iso3, event_name, event_date, shakemap_version, time_of_calc,
                disclaimer_txt, notes_txt, losses_df, summary_data,
                basemap_path, adm_level, dstore, hypocenter,
                threshold_deg, no_uncertainty)


if __name__ == '__main__':
    sap.run(main)
