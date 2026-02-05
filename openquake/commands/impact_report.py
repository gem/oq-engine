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
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.postproc.plots import import_plt, plot_variable
from openquake.commonlib import datastore, logs
from openquake.commonlib.calc import get_close_regions
from openquake.qa_tests_data import global_risk


LOSS_TYPE_MAP = {
    "occupants": "Fatalities",
    "residents": "Homeless",
    "number": "Buildings",
}


def load_admin_boundaries(country, iso3, adm_level, boundaries_dir, wfp,
                          crs="EPSG:4326"):
    if wfp:
        shp = (
            Path(boundaries_dir)
            / "ADMIN_boundaries_PilotCO"
            / "WFP_pilotCO_admin2.shp"
        )
        admin_boundaries = gpd.read_file(shp)
        admin_boundaries = admin_boundaries[admin_boundaries["iso3"] == iso3]
    else:
        # FIXME: missing data
        shp = Path(boundaries_dir) / f"Adm{adm_level}_{country}.shp"
        admin_boundaries = gpd.read_file(shp)

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
        crs=crs,
    )
    return gdf


def aggregate_losses(*, points_gdf, admin_gdf, tags_agg, adm_level, wfp):
    joined = gpd.sjoin(
        points_gdf,
        admin_gdf,
        how="inner",
        predicate="within",
    )

    if wfp:
        group_col = "adm2_id"
        merge_args = dict(on="adm2_id")
    else:
        group_col = f"ID_{adm_level}_right"
        merge_args = dict(left_on=f"ID_{adm_level}", right_index=True)

    aggregated = (
        joined
        .groupby(group_col)
        .agg({col: "sum" for col in tags_agg})
    )

    return admin_gdf.merge(aggregated, **merge_args)


def save_most_affected_regions(df, *, adm_level, output_path, n=5):
    region_col = f"adm{adm_level}_name"
    (
        df.nlargest(n, "Fatalities")[region_col]
        .to_csv(output_path, index=False, header=False)
    )


def build_classifiers(df, *, breaks):
    return {
        "Fatalities": mapclassify.UserDefined(df["Fatalities"], bins=breaks),
        "Homeless": mapclassify.UserDefined(df["Homeless"], bins=breaks),
        "Buildings": mapclassify.UserDefined(df["Buildings"], bins=breaks),
    }


def plot_losses(country, iso3, adm_level, losses_df, cities,
                tags_agg, x_limits_country, y_limits_country,
                wfp, boundaries_dir, basemap_path, outputs_basedir):
    plt = import_plt()
    save_dir = Path(outputs_basedir) / country
    save_dir.mkdir(parents=True, exist_ok=True)

    admin_boundaries = load_admin_boundaries(
        country, iso3, adm_level, boundaries_dir, wfp)

    points_gdf = points_to_gdf(losses_df, crs=admin_boundaries.crs)

    df = aggregate_losses(
        points_gdf=points_gdf, admin_gdf=admin_boundaries,
        tags_agg=tags_agg, adm_level=adm_level, wfp=wfp)

    df = df.rename(columns=LOSS_TYPE_MAP)

    save_most_affected_regions(
        df, adm_level=adm_level,
        output_path=save_dir / "most_affected_regions.txt")

    classifiers = build_classifiers(
        df, breaks=[1, 10, 100, 1000])

    colors = {
        "Fatalities": [
            '#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d'],
        "Homeless": [
            '#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043'],
        "Buildings": [
            '#ffffff', '#bdbdbd', '#737373', '#424242', '#000000'],
    }

    titles = {
        "Fatalities": "Fatalities",
        "Homeless": "Homeless",
        "Buildings": "Buildings beyond repair",
    }

    for loss_type in LOSS_TYPE_MAP.values():
        fig, ax = plot_variable(
            df, admin_boundaries, loss_type, classifiers[loss_type],
            colors[loss_type], country=country, plot_title=titles[loss_type],
            legend_title=loss_type, cities=cities,
            x_limits=x_limits_country, y_limits=y_limits_country,
            basemap_path=basemap_path,
        )
        # NOTE: we might save it into the datastore instead
        fig.savefig(save_dir / f"{loss_type}_{country}.png", dpi=300,
                    bbox_inches="tight")
        plt.close(fig)
        # print(f"Total {loss_type}: {df[loss_type].sum()}")


def _scaled_image(path, max_w, max_h):
    # scale image preserving aspect ratio
    if not path.exists():
        return Paragraph(f"Missing image: {path.name}",
                         getSampleStyleSheet()["Normal"])
    img = PILImage.open(path)
    w, h = img.size
    scale = min(max_w / w, max_h / h)
    return Image(
        str(path),
        width=w * scale,
        height=h * scale,
    )


def _fmt_int(v):
    return "" if v is None else f"{int(round(v))}"


def _get_impact_summary_ranges(dstore):
    aggrisk_tags = extract(dstore, 'aggrisk_tags')
    mapping = {
        'Fatalities': 'occupants',
        'Displaced': 'residents',
        'Buildings lost': 'number',
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
    # FIXME: probably there is a more efficient way, rather than
    # exporting and reading the exported csv
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
        boundaries_dir, basemap_path, outputs_dir):

    tags_agg_losses = ["occupants", 'number', 'residents']

    countries_info_fname = os.path.join(
        os.path.dirname(global_risk.__file__), 'countries_info.csv')
    countries_info_df = pd.read_csv(countries_info_fname)
    country_info = countries_info_df.loc[
        countries_info_df["ISO3"] == iso3].iloc[0]
    iso3 = country_info["ISO3"]
    country = country_info["ENGLISH_COUNTRY"]
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

    # FIXME
    wfp = True
    adm_level = 2

    # Country-level comparison
    plot_losses(country, iso3, adm_level, losses_df, cities,
                tags_agg_losses, x_limits_country, y_limits_country,
                wfp, boundaries_dir, basemap_path, outputs_dir)

    # Paths
    country_pngs_dir = Path(outputs_dir) / country
    png1 = country_pngs_dir / f"Buildings_{country}.png"
    png2 = country_pngs_dir / f"Fatalities_{country}.png"
    png3 = country_pngs_dir / f"Homeless_{country}.png"

    # Document Setup (Reduced Margins)
    MARGIN = 20  # Reduced margin for a wider/taller layout area

    doc = SimpleDocTemplate(
        str(country_pngs_dir / f"ImpactReport_{country}.pdf"),
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

    event_text = f"<b>{event_name}, {event_date}</b>"
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
        [["", "Range of losses"],
         ["Fatalities", summary_ranges["Fatalities"]],
         ["Buildings lost", summary_ranges["Buildings lost"]],
         ["Displaced", summary_ranges["Displaced"]]],
        colWidths=[COL_W * 0.45, COL_W * 0.45], hAlign='LEFT'
    )
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("SIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))

    with open(country_pngs_dir / 'most_affected_regions.txt') as f:
        most_affected_regions = [line.strip() for line in f if line.strip()]

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
    img_top_right = _scaled_image(png1, COL_W - 10, ROW_H - 10)
    img_bot_left = _scaled_image(png2, COL_W - 10, ROW_H - 10)
    img_bot_right = _scaled_image(png3, COL_W - 10, ROW_H - 10)

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


def _get_notes(oqparam):
    notes = ''
    notes += f'Mosaic model: {oqparam.mosaic_model}'
    notes += (f'. Number of ground motion fields:'
              f' {oqparam.number_of_ground_motion_fields}')
    notes += f'. Truncation level: {oqparam.truncation_level}'
    notes += f'. Time of the event: {oqparam.time_event}'
    notes += f'. Tectonic region type: {oqparam.tectonic_region_type}'
    rupdic = oqparam.rupture_dict
    notes += f'. Rupture identifier: {rupdic["usgs_id"]}'
    notes += f'. Lon: {rupdic["lon"]}'
    notes += f'. Lat: {rupdic["lat"]}'
    notes += f'. Dep: {rupdic["dep"]}'
    notes += f'. Mag: {rupdic["mag"]}'
    notes += f'. Rake: {rupdic["rake"]}'
    notes += f'. Dip: {rupdic["dip"]}'
    notes += f'. Strike: {rupdic["strike"]}'
    return notes


def to_utc_string(ts: str) -> str:
    """
    Convert a timestamp with timezone offset (e.g. '+08:00')
    to the format: 'YYYY-MM-DD HH:MM:SS UTC'
    """
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        raise ValueError("Timestamp has no timezone information")
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'


def main(calc_id: int = -1, *, export_dir='.', boundaries_dir=None,
         basemap_path=None, outputs_dir=None):
    """
    Create a PDF impact report
    """
    # boundaries_dir = '/home/ptormene/GIT/wfp/boundaries/'  # FIXME
    # # FIXME:
    # # basemap_path = "../data/eo_base_2020_clean_geo.tif"
    # basemap_path = "/home/ptormene/GIT/wfp/data/eo_base_2020_clean_geo.tif"
    if not outputs_dir:
        oq_basedir = Path(baselib.__path__[0].rsplit('/', 2)[0])
        outputs_dir = oq_basedir / "outputs" / "impact"

    dstore = datastore.read(calc_id)
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
    dstore.close()
    iso3_codes = get_close_regions(
        lon, lat, buffer_radius=0.5, region_kind='country')
    iso3 = iso3_codes[0]  # TODO: handle multi-country case

    make_report_for_country(
        iso3, event_name, event_date, shakemap_version, time_of_calc,
        disclaimer_txt, notes_txt, losses_df, summary_ranges,
        boundaries_dir, basemap_path, outputs_dir)


main.calc_id = 'number of the calculation'
main.boundaries_dir = 'directory containing administrative boundaries'
main.basemap_path = 'path to the basemap'
main.outputs_dir = 'directory where to store impact outputs'
main.export_dir = dict(help='export directory', abbrev='-d')
