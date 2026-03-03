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
import tempfile
import logging
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone

from PIL import Image as PILImage
import pandas as pd
import geopandas as gpd
from openquake import baselib
from openquake.baselib import config, sap
from openquake.calculators.extract import extract
from openquake.calculators.postproc.plots import plot_variable
from openquake.commonlib import logs
from openquake.commonlib.calc import get_close_regions
from openquake.qa_tests_data import global_risk


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
    gdf = gpd.read_file(fname)
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


def save_most_affected_regions(df, dstore, iso3, *, n=5):
    fatalities_label = LOSS_METADATA["occupants"]["label"]
    regions = df.nlargest(n, fatalities_label)['region_name'].dropna().tolist()
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


def plot_losses(country_name, iso3, adm_level, losses_df, cities,
                tags_agg, x_limits_country, y_limits_country,
                basemap_path, dstore, hypocenter):
    import matplotlib.pyplot as plt
    admin_boundaries = load_admin_boundaries(
        country_name, iso3, adm_level)
    points_gdf = points_to_gdf(losses_df, crs=admin_boundaries.crs)
    df = aggregate_losses(points_gdf, admin_boundaries, tags_agg)
    df = df.rename(columns={k: v["label"] for k, v in LOSS_METADATA.items()})
    classifiers = build_classifiers(
        df, breaks=[1, 10, 100, 1000])
    images = {}
    for meta in LOSS_METADATA.values():
        label = meta["label"]
        title = meta["title"]
        colors = meta["colors"]
        fig, ax = plot_variable(
            df, admin_boundaries, label, classifiers[label],
            colors, country_name=country_name,
            plot_title=title,
            legend_title=label, cities=cities,
            x_limits=x_limits_country, y_limits=y_limits_country,
            basemap_path=basemap_path, hypocenter=hypocenter,
        )
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        images[label] = buf.getvalue()
    return df, images


def _get_impact_summary_ranges(dstore, iso3):
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
    summary_ranges = {
        label: f"{int(round(r.q05))} - {int(round(r.q95))}"
        for label, lt in mapping.items()
        for r in [rows.loc[rows['loss_type'] == lt].iloc[0]]
    }
    return summary_ranges


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
            disclaimer_txt, notes_txt, losses_df, summary_ranges, basemap_path,
            adm_level, dstore, hypocenter):
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
        self.summary_ranges = summary_ranges
        self.basemap_path = basemap_path
        self.adm_level = adm_level
        self.dstore = dstore
        self.hypocenter = hypocenter

        self.styles = self.getSampleStyleSheet()

        self._load_country_info()
        self._compute_layout()

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

    def _load_country_info(self):
        fname = os.path.join(
            os.path.dirname(global_risk.__file__),
            "countries_info.csv",
        )
        df = pd.read_csv(fname)

        row = df.loc[df["ISO3"] == self.iso3].iloc[0]

        self.country_name = row["ENGLISH_COUNTRY"]
        # "GEM_REGION": country_info["GEM_REGION"],
        # "CRS": country_info["CRS"],
        self.x_limits = [row["X_MIN"], row["X_MAX"]]
        self.y_limits = [row["Y_MIN"], row["Y_MAX"]]
        self.cities = {
            row["CAPITAL"]: [row["CAPITAL_LON"], row["CAPITAL_LAT"]]
        }
        # # it might be needed if we have more than just the capital
        # cities = config.get("cities", {})
        # if isinstance(cities, dict) and len(cities) > 3:
        #     cities = dict(list(cities.items())[:3])

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
        tags_agg_losses = list(LOSS_METADATA)
        df, images = plot_losses(
            self.country_name, self.iso3, self.adm_level, self.losses_df,
            self.cities, tags_agg_losses, self.x_limits, self.y_limits,
            self.basemap_path, self.dstore, self.hypocenter)
        save_most_affected_regions(df, self.dstore, self.iso3)
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

        event_text = f"<b>{self.event_name}; {self.event_date}</b>"
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

        header_text = [
            event_paragraph,
            self.Paragraph(
                f"Time of the calculation: {self.time_of_calc} "
                f"&nbsp;&nbsp;ShakeMap version: {self.shakemap_version}",
                self.styles["Italic"],
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
        summary_table = self.Table(
            [["", "Range of losses"]]
            + [
                [meta["label"], self.summary_ranges[meta["label"]]]
                for meta in LOSS_METADATA.values()
            ],
            colWidths=[self.col_w * 0.45, self.col_w * 0.45],
            hAlign="LEFT",
        )

        summary_table.setStyle(self.TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors.whitesmoke),
            ("SIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))

        most_affected = self.dstore[
            f"impact/{self.iso3}/most_affected_regions"
        ]

        left_bundle = [
            self.Paragraph(
                f"<b>Summary of impact for {self.iso3}:</b>", self.styles["Normal"]),
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
        disclaimer_txt, notes_txt, losses_df, summary_ranges,
        basemap_path, adm_level, dstore, hypocenter):
    builder = CountryReportBuilder(
        iso3, event_name, event_date, shakemap_version, time_of_calc,
        disclaimer_txt, notes_txt, losses_df, summary_ranges, basemap_path,
        adm_level, dstore, hypocenter)
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
    hypocenter = (lon, lat)
    avg_losses = extract(dstore, 'avg_losses?kind=stats')
    losses_df = pd.DataFrame(avg_losses.mean)
    rupdic = oqparam.rupture_dict
    event_name = rupdic['title']
    # FIXME: do we prefer to show UTC or perhaps it is more intuitive
    #        to show the local time?
    event_date = to_utc_string(oqparam.local_timestamp)
    shakemap_version = rupdic['shakemap_desc']
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
        summary_ranges = _get_impact_summary_ranges(dstore, iso3)
        if summary_ranges is not None:
            make_report_for_country(
                iso3, event_name, event_date, shakemap_version, time_of_calc,
                disclaimer_txt, notes_txt, losses_df, summary_ranges,
                basemap_path, adm_level, dstore, hypocenter)


if __name__ == '__main__':
    sap.run(main)
