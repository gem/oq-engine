# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023-2026 GEM Foundation
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
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone

# FIXME: add to engine requirements? Only for impact?
import mapclassify
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Image, ListFlowable, ListItem, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from PIL import Image as PILImage
import pandas as pd
import geopandas as gpd
from openquake import baselib
from openquake.baselib import config
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.postproc.plots import import_plt, plot_variable
from openquake.commonlib import datastore, logs
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
    admin_boundaries = gpd.read_file(fname)
    admin_boundaries = admin_boundaries[admin_boundaries["shapeGroup"] == iso3]
    return admin_boundaries.to_crs(crs)


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


def aggregate_losses(*, points_gdf, admin_gdf, tags_agg, adm_level):
    joined = gpd.sjoin(points_gdf, admin_gdf, how="inner", predicate="within")
    group_col = 'shapeID'
    merge_args = dict(on=group_col)
    aggregated = joined.groupby(group_col).agg(
        {col: "sum" for col in tags_agg})
    return admin_gdf.merge(aggregated, **merge_args)


def save_most_affected_regions(df, dstore, iso3, *, adm_level, n=5):
    region_col = 'shapeName'
    fatalities_label = LOSS_METADATA["occupants"]["label"]
    regions = df.nlargest(n, fatalities_label)[region_col].dropna().tolist()
    dstore[f"impact/{iso3}/most_affected_regions"] = regions


def build_classifiers(df, *, breaks):
    return {meta["label"]: mapclassify.UserDefined(df[meta["label"]],
                                                   bins=breaks)
            for meta in LOSS_METADATA.values()}


def plot_losses(country_name, iso3, adm_level, losses_df, cities,
                tags_agg, x_limits_country, y_limits_country,
                basemap_path, dstore):
    plt = import_plt()

    admin_boundaries = load_admin_boundaries(
        country_name, iso3, adm_level)

    points_gdf = points_to_gdf(losses_df, crs=admin_boundaries.crs)

    df = aggregate_losses(
        points_gdf=points_gdf, admin_gdf=admin_boundaries,
        tags_agg=tags_agg, adm_level=adm_level)

    df = df.rename(columns={k: v["label"] for k, v in LOSS_METADATA.items()})

    save_most_affected_regions(df, dstore, iso3, adm_level=adm_level)

    classifiers = build_classifiers(
        df, breaks=[1, 10, 100, 1000])

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
            basemap_path=basemap_path,
        )
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        dstore[f"impact/{iso3}/png/{label}"] = buf.getvalue()


def _scaled_image(path, max_w, max_h):
    # scale image preserving aspect ratio
    if not path.exists():
        return Paragraph(f"Missing image: {path.name}",
                         getSampleStyleSheet()["Normal"])
    img = PILImage.open(path)
    w, h = img.size
    scale = min(max_w / w, max_h / h)
    return Image(str(path), width=w*scale, height=h*scale)


def _scaled_image_from_bytes(image_data, max_w, max_h):
    # If it is an HDF5 dataset, read it
    try:
        image_data = image_data[()]
    except Exception:
        pass
    # scale image preserving aspect ratio
    img = PILImage.open(BytesIO(image_data))
    w, h = img.size
    scale = min(max_w / w, max_h / h)
    return Image(BytesIO(image_data), width=w*scale, height=h*scale)


def _fmt_int(v):
    return "" if v is None else f"{int(round(v))}"


def _get_impact_summary_ranges(dstore):
    # FIXME: the totals are for ALL countries
    aggrisk_tags = extract(dstore, 'aggrisk_tags')
    mapping = {
        meta["label"]: loss_type
        for loss_type, meta in LOSS_METADATA.items()
    }

    rows = aggrisk_tags.loc[
        (aggrisk_tags['ID'] == '*total*') &
        (aggrisk_tags['loss_type'].isin(mapping.values()))
    ]

    summary_ranges = {
        label: f"{_fmt_int(r.q05)} - {_fmt_int(r.q95)}"
        for label, lt in mapping.items()
        for r in [rows.loc[rows['loss_type'] == lt].iloc[0]]
    }
    return summary_ranges


def _get_losses(dstore):
    # TODO: check if there is a better way
    fnames = export(('avg_losses-stats', 'csv'), dstore)
    avg_losses_mean_fname = [
        fname for fname in fnames if 'avg_losses-mean' in fname][0]
    losses_df = load_losses_csv(avg_losses_mean_fname)
    return losses_df


def one_line_paragraph(text, base_style, max_width, min_font_size=8, step=0.5):
    """
    Try to keep paragraph on one line by reducing font size if needed.
    """
    font_size = base_style.fontSize

    while font_size >= min_font_size:
        style = ParagraphStyle(
            name="tmp",
            parent=base_style,
            fontSize=font_size,
            leading=font_size * 1.2,
        )
        p = Paragraph(text, style)
        w, h = p.wrap(max_width, 1000)

        # one line ≈ leading height
        if h <= style.leading * 1.05:
            return p

        font_size -= step

    # fallback: smallest font
    style.fontSize = min_font_size
    style.leading = min_font_size * 1.2
    return Paragraph(text, style)


def make_report_for_country(
        iso3, event_name, event_date, shakemap_version, time_of_calc,
        disclaimer_txt, notes_txt, losses_df, summary_ranges,
        basemap_path, adm_level, dstore):

    tags_agg_losses = list(LOSS_METADATA)

    countries_info_fname = os.path.join(
        os.path.dirname(global_risk.__file__), 'countries_info.csv')
    countries_info_df = pd.read_csv(countries_info_fname)
    country_info = countries_info_df.loc[
        countries_info_df["ISO3"] == iso3].iloc[0]
    country_name = country_info["ENGLISH_COUNTRY"]
    # "GEM_REGION": country_info["GEM_REGION"],
    # "CRS": country_info["CRS"],
    x_limits_country = [country_info["X_MIN"], country_info["X_MAX"]]
    y_limits_country = [country_info["Y_MIN"], country_info["Y_MAX"]]
    cities = {country_info["CAPITAL"]: [
        country_info["CAPITAL_LON"], country_info["CAPITAL_LAT"]]}
    # # it might be needed if we have more than just the capital
    # cities = config.get("cities", {})
    # if isinstance(cities, dict) and len(cities) > 3:
    #     cities = dict(list(cities.items())[:3])

    # Country-level comparison
    plot_losses(country_name, iso3, adm_level, losses_df, cities,
                tags_agg_losses, x_limits_country, y_limits_country,
                basemap_path, dstore)

    # Document Setup (Reduced Margins)
    MARGIN = 20  # Reduced margin for a wider/taller layout area

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,    # Top margin equals bottom margin
        bottomMargin=MARGIN,
    )

    styles = getSampleStyleSheet()

    event_style = ParagraphStyle(
        "EventTitle",
        parent=styles["Normal"],
        fontSize=11,
    )

    # A4 is (595.27, 841.89) points
    page_width = A4[0] - (2 * MARGIN)
    page_height = A4[1] - (2 * MARGIN)

    # Height Allocations
    DISCLAIMER_H = 40
    HEADER_H = 60
    NOTES_H = 80
    SAFETY_BUFFER = 20  # Buffer to ensure it stays on one page
    GRID_TOTAL_H = (
        page_height - DISCLAIMER_H - HEADER_H - NOTES_H - SAFETY_BUFFER)

    ROW_H = GRID_TOTAL_H / 2
    COL_W = page_width / 2

    # Disclaimer
    disclaimer_tbl = Table(
        [[Paragraph(f"<b>DISCLAIMER</b>: {disclaimer_txt}",
                    styles["Normal"])]],
        colWidths=[page_width], rowHeights=[DISCLAIMER_H]
    )
    disclaimer_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), colors.lightcoral),
        ("BOX",         (0, 0), (-1, -1), 1, colors.red),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))

    # Path to your logo
    oq_basedir = Path(baselib.__path__[0].rsplit('/', 2)[0])
    LOGO_PATH = (
        oq_basedir / 'doc' / '_static' / 'OQ-Logo-Standard-RGB-72DPI-01.png')
    LOGO_W = 100

    event_text = f"<b>{event_name}; {event_date}</b>"
    event_paragraph = one_line_paragraph(
        event_text,
        event_style,
        max_width=page_width,
    )

    # Event Header
    header_text = [
        event_paragraph,
        Paragraph(
            f"Time of the calculation: {time_of_calc} &nbsp;&nbsp;"
            f" ShakeMap version: {shakemap_version}",
            styles["Italic"])
    ]

    # Helper to scale the logo to fit the header height
    logo_img = _scaled_image(LOGO_PATH, LOGO_W, HEADER_H - 10)

    # Create a two-column header table
    header_tbl = Table(
        [[header_text, logo_img]],
        colWidths=[page_width - LOGO_W, LOGO_W],
        rowHeights=[HEADER_H]
    )

    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),  # Logo pushed to the right
        ("TOPPADDING", (0, 0), (-1, -1), 10),
    ]))

    # Top-Left Content
    summary_table = Table(
        [["", "Range of losses"]] +
        [[meta["label"], summary_ranges[meta["label"]]]
         for meta in LOSS_METADATA.values()],
        colWidths=[COL_W * 0.45, COL_W * 0.45], hAlign='LEFT'
    )
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("SIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    most_affected_regions = dstore[f"impact/{iso3}/most_affected_regions"]

    left_bundle = [
        Paragraph("<b>Summary of impact:</b>", styles["Normal"]),
        Spacer(1, 4),
        summary_table,
        Spacer(1, 12),
        Paragraph("<b>Most affected regions</b>", styles["Normal"]),
        ListFlowable(
            [ListItem(Paragraph(item, styles["Normal"]))
             for item in most_affected_regions],
            bulletType="bullet", leftIndent=15
        )
    ]

    # Images (2x2 Grid)
    img_top_right = _scaled_image_from_bytes(
        dstore[f"impact/{iso3}/png/{LOSS_METADATA['number']['label']}"][()],
        COL_W - 10, ROW_H - 10)
    img_bot_left = _scaled_image_from_bytes(
        dstore[f"impact/{iso3}/png/{LOSS_METADATA['occupants']['label']}"][()],
        COL_W - 10, ROW_H - 10)
    img_bot_right = _scaled_image_from_bytes(
        dstore[f"impact/{iso3}/png/{LOSS_METADATA['residents']['label']}"][()],
        COL_W - 10, ROW_H - 10)
    grid_tbl = Table(
        [
            [left_bundle, img_top_right],
            [img_bot_left, img_bot_right]
        ],
        colWidths=[COL_W, COL_W],
        rowHeights=[ROW_H, ROW_H]
    )
    grid_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 1), "CENTER"),
        ("ALIGN", (0, 1), (0, 1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    # Notes
    notes_tbl = Table(
        [[Paragraph(f"<b>Notes</b>: {notes_txt}",
                    styles["Normal"])]],
        colWidths=[page_width], rowHeights=[NOTES_H]
    )
    notes_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))

    # Master Assembly
    master_layout = Table(
        [
            [disclaimer_tbl],
            [header_tbl],
            [grid_tbl],
            [notes_tbl]
        ],
        colWidths=[page_width],
        rowHeights=[DISCLAIMER_H, HEADER_H, GRID_TOTAL_H, NOTES_H]
    )

    master_layout.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    doc.build([master_layout])
    pdf_buffer.seek(0)
    dstore[f"impact/{iso3}/report_pdf"] = pdf_buffer.getvalue()


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
        # FIXME: log properly or add a note to the pdf
        print("Timestamp has no timezone information")
        return ret_str + dt.strftime('%Y-%m-%d %H:%M:%S')
    dt_utc = dt.astimezone(timezone.utc)
    return ret_str + dt_utc.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'


def main(calc_id: int = -1, *, adm_level=2, threshold_deg=3):
    """
    Create a PDF impact report
    """
    adm_level = int(adm_level)
    basemap_path = config.directory.basemap_file
    if not basemap_path:
        raise AttributeError('config.directory.basemap_file is missing')
    export_dir = config.directory.custom_tmp or tempfile.gettempdir()
    dstore = datastore.read(calc_id, mode='r+')
    dstore.export_dir = export_dir
    lon = dstore['oqparam'].rupture_dict['lon']
    lat = dstore['oqparam'].rupture_dict['lat']
    summary_ranges = _get_impact_summary_ranges(dstore)
    losses_df = _get_losses(dstore)
    oqparam = dstore['oqparam']
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
    iso3_codes = get_close_regions(
        lon, lat, buffer_radius=threshold_deg, region_kind='country')
    if not iso3_codes:
        raise RuntimeError(
            "No country within {threshold_deg} from the hypocenter")
    # TODO: handle multi-country case (hypocenter close to borders)
    iso3 = iso3_codes[0]
    make_report_for_country(
        iso3, event_name, event_date, shakemap_version, time_of_calc,
        disclaimer_txt, notes_txt, losses_df, summary_ranges,
        basemap_path, adm_level, dstore)
    dstore.close()


main.calc_id = 'number of the calculation'
main.adm_level = 'administrative level of country geometries'
