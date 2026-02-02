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
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import rasterio
from rasterio.plot import show
import numpy as np
import mapclassify
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Image, ListFlowable, ListItem, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PIL import Image as PILImage
import pandas as pd
import geopandas as gpd
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.commonlib import datastore, logs
from openquake.commonlib.calc import get_close_regions
from openquake.qa_tests_data import global_risk


def plot_variable(df, country, admin_boundaries, column, plot_title,
                  legend_title, cities, digits, x_limits, y_limits,
                  colors, classifier, font_size, city_font_size,
                  title_font_size, SAVE_DIRECTORY):

    # 1. Calculate natural breaks
    rounded_bins = np.round(classifier.bins, digits)
    classifier.bins = rounded_bins  # overwrite the classifier boundaries

    df = df.copy()
    df['class'] = classifier(df[column])

    # 2. Prepare custom labels for the legend
    bins = classifier.bins
    labels = [f"{bins[i-1]:.{digits}f} - {bins[i]:.{digits}f}"
              for i in range(1, len(bins))]
    labels.insert(0, f"≤ {bins[0]:.{digits}f}")
    labels[-1] = f"> {bins[-2]:.{digits}f}"

    # 3. Define figure and axis
    fig, ax = plt.subplots(figsize=(10, 10))

    # 4. Plot each class with its corresponding color
    for i, color in enumerate(colors):
        subset = df[df['class'] == i]
        if subset.empty:
            continue  # skip classes with no geometries
        subset.plot(ax=ax, color=color, edgecolor='none', label=labels[i])

    # 5. Manually create legend handles based on color and label
    handles = [mpatches.Patch(color=color, label=label)
               for color, label in zip(colors, labels)]
    ax.legend(handles=handles, title=legend_title, framealpha=0.7,
              title_fontsize=font_size, loc='upper left')

    # 6. Plot administrative boundaries
    admin_boundaries.plot(ax=ax, alpha=0.4, edgecolor='black',
                          facecolor='none', linewidth=0.4)

    # 7. Add basemap
    # FIXME:
    # tif_path = "../data/eo_base_2020_clean_geo.tif"
    tif_path = "/home/ptormene/GIT/wfp/data/eo_base_2020_clean_geo.tif"
    with rasterio.open(tif_path) as src:
        show(src, ax=ax, alpha=0.8)  # Adjust alpha as needed

    # 8. Set geographic limits
    ax.set_xlim(x_limits)
    ax.set_ylim(y_limits)

    # 9. Annontate cities
    for city, (x, y) in cities.items():
        text = plt.text(x, y, city, fontsize=city_font_size,
                        color='black', fontweight='bold')
        text.set_path_effects(
            [path_effects.Stroke(linewidth=1.5, foreground='white'),
             path_effects.Normal()])

    # 10. Titles and labels
    plt.title(f'{plot_title}', fontsize=title_font_size)
    plt.xlabel('Longitude', fontsize=font_size)
    plt.ylabel('Latitude', fontsize=font_size)

    # 11. Adjust layout
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    fig.savefig(os.path.join(SAVE_DIRECTORY, f'{column}_{country}.png'),
                dpi=300, bbox_inches='tight')
    plt.close()


def plot_losses(country, iso3, adm_level, avg_losses_mean_fname, cities,
                TAGS_AGG, x_limits_country, y_limits_country,
                font_size, city_font_size, title_font_size, wfp):

    # # INITIALISATION
    boundaries_dir = '/home/ptormene/GIT/wfp/boundaries/'  # FIXME

    # Save directory
    # SAVE_DIRECTORY = os.path.join('..', 'outputs', 'impact', f'{country}')
    BASE = Path(__file__).resolve().parent.parent.parent
    SAVE_DIRECTORY = BASE / 'outputs' / 'impact' / country

    # Create folders
    os.makedirs(os.path.join(SAVE_DIRECTORY), exist_ok=True)

    # Shapefiles
    if wfp:
        shapefile_path = os.path.join(
            boundaries_dir, "ADMIN_boundaries_PilotCO",
            "WFP_pilotCO_admin2.shp")
        admin_boundaries = gpd.read_file(shapefile_path)
        admin_boundaries = admin_boundaries[admin_boundaries["iso3"] == iso3]
        admin_boundaries = admin_boundaries.to_crs("EPSG:4326")
    else:
        # FIXME: missing
        shapefile_path = os.path.join(
            boundaries_dir, f'Adm{adm_level}_{country}.shp')
        admin_boundaries = gpd.read_file(shapefile_path)
        admin_boundaries = admin_boundaries.to_crs("EPSG:4326")

    # ACTUAL EXPOSURE

    # Load Calculations for Actual Exposure
    assets = pd.read_csv(avg_losses_mean_fname, header=[0, 1])
    new_columns = assets.columns.get_level_values(1)
    assets.columns = new_columns
    assets = assets.drop(0, axis=0)
    assets = assets.reset_index(drop=True)

    # Create a GeoDataFrame from exposure data
    try:
        csv_data_geom_actual = gpd.GeoDataFrame(
            assets, geometry=gpd.points_from_xy(
                assets['lon'], assets['lat']))
    except Exception as e:
        print(f"Error creating GeoDataFrame: {e}")

    csv_data_geom_actual.crs = admin_boundaries.crs

    # Perform the spatial join
    joined_data_actual = gpd.sjoin(
        csv_data_geom_actual, admin_boundaries,
        how='inner', predicate='within')

    if wfp:
        # Group by the correct column
        aggregated_data_actual = joined_data_actual.groupby(
            'adm2_id').agg({col: 'sum' for col in TAGS_AGG})

        # Merge with admin boundaries using adm2_id
        df_actual = admin_boundaries.merge(
            aggregated_data_actual, on='adm2_id')

    else:
        # Group by the correct column
        aggregated_data_actual = joined_data_actual.groupby(
            f'ID_{adm_level}_right').agg({col: 'sum' for col in TAGS_AGG})

        # Merge with admin boundaries using ID_2
        df_actual = admin_boundaries.merge(
            aggregated_data_actual, left_on=f'ID_{adm_level}',
            right_index=True)

    # (Optional) Print to verify
    df_actual.rename(
        columns={'occupants': 'Fatalities', 'residents': 'Homeless',
                 'number': 'Buildings'}, inplace=True)

    # Determine the 5 most affected regions in terms of fatalities
    most_affected_regions = df_actual.nlargest(5, 'Fatalities')[
        f'adm{adm_level}_name']
    most_affected_regions.to_csv(
        os.path.join(SAVE_DIRECTORY, 'most_affected_regions.txt'),
        index=False, header=False)

    # Define your custom break thresholds (upper limits of each bin)
    breaks = [1, 10, 100, 1000]

    classifier_actual_fatalities = mapclassify.UserDefined(
        df_actual['Fatalities'], bins=breaks)
    classifier_actual_homeless = mapclassify.UserDefined(
        df_actual['Homeless'], bins=breaks)
    classifier_actual_buildings = mapclassify.UserDefined(
        df_actual['Buildings'], bins=breaks)

    digits_losses = 0

    # Plot titles
    title_actual_fatalities = 'Fatalities'
    title_actual_homeless = 'Homeless'
    title_actual_buildings = 'Buildings beyond repair'

    colors_fatalities = ['#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d']
    colors_homeless = ['#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043']
    colors_buildings = ['#ffffff', '#bdbdbd', '#737373', '#424242', '#000000']

    # Plots Actual
    plot_variable(df_actual, country, admin_boundaries, 'Fatalities',
                  title_actual_fatalities, 'Fatalities', cities, digits_losses,
                  x_limits_country, y_limits_country, colors_fatalities,
                  classifier_actual_fatalities, font_size, city_font_size,
                  title_font_size, SAVE_DIRECTORY)

    plot_variable(df_actual, country, admin_boundaries, 'Homeless',
                  title_actual_homeless, 'Homeless', cities, digits_losses,
                  x_limits_country, y_limits_country, colors_homeless,
                  classifier_actual_homeless, font_size, city_font_size,
                  title_font_size, SAVE_DIRECTORY)

    plot_variable(df_actual, country, admin_boundaries, 'Buildings',
                  title_actual_buildings, 'Buildings', cities, digits_losses,
                  x_limits_country, y_limits_country, colors_buildings,
                  classifier_actual_buildings, font_size, city_font_size,
                  title_font_size, SAVE_DIRECTORY)

    print(f"Total fatalities: {df_actual['Fatalities'].sum()}")
    print(f"Total homeless: {df_actual['Homeless'].sum()}")
    print(f"Total buildings beyond repair: {df_actual['Buildings'].sum()}")


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


def _get_impact_summary_ranges(aggrisk_tags):
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
        label: f"{r.q05:.6g} - {r.q95:.6g}"
        for label, lt in mapping.items()
        for r in [rows.loc[rows['loss_type'] == lt].iloc[0]]
    }
    return summary_ranges


def main(calc_id: int = -1, *, export_dir='.'):
    """
    Create a PDF impact report
    """
    dstore = datastore.read(calc_id)
    dstore.export_dir = export_dir
    lon = dstore['oqparam'].rupture_dict['lon']
    lat = dstore['oqparam'].rupture_dict['lat']
    tags_agg_losses = ["occupants", 'number', 'residents']
    aggrisk_tags = extract(dstore, 'aggrisk_tags')
    fnames = export(('avg_losses-stats', 'csv'), dstore)

    oqparam = dstore['oqparam']
    rupdic = oqparam.rupture_dict
    event_date = oqparam.local_timestamp
    event_name = rupdic['title']
    shakemap_version = rupdic['shakemap_desc']

    job = logs.dbcmd('get_job', calc_id)
    time_of_calc = job.start_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'

    disclaimer_txt = 'TODO'
    notes_txt = 'TODO'

    dstore.close()

    summary_ranges = _get_impact_summary_ranges(aggrisk_tags)

    avg_losses_mean_fname = [
        fname for fname in fnames if 'avg_losses-mean' in fname][0]
    iso3_codes = get_close_regions(
        lon, lat, buffer_radius=0.5, region_kind='country')
    iso3 = iso3_codes[0]  # TODO: handle case multi-country

    country_info_fname = os.path.join(
        os.path.dirname(global_risk.__file__), 'country_info.csv')
    df = pd.read_csv(country_info_fname)

    # select the row of interest
    row = df.loc[df["ISO3"] == iso3].iloc[0]

    iso3 = row["ISO3"]
    country = row["ENGLISH_COUNTRY"]

    # "GEM_REGION": row["GEM_REGION"],
    # "CRS": row["CRS"],

    x_limits_country = [row["X_MIN"], row["X_MAX"]]
    y_limits_country = [row["Y_MIN"], row["Y_MAX"]]

    cities = {row["CAPITAL"]: [
        row["CAPITAL_LON"], row["CAPITAL_LAT"]]}
    # # it might be needed if we have more than just the capital
    # cities = config.get("cities", {})
    # if isinstance(cities, dict) and len(cities) > 3:
    #     cities = dict(list(cities.items())[:3])

    # FIXME
    wfp = True
    adm_level = 2

    font_size = 18
    city_font_size = 14
    title_font_size = 20

    # Country-level comparison
    plot_losses(country, iso3, adm_level, avg_losses_mean_fname, cities,
                tags_agg_losses, x_limits_country, y_limits_country,
                font_size, city_font_size, title_font_size, wfp)

    # Paths
    BASE = Path(__file__).resolve().parent.parent.parent
    country_pngs_dir = BASE / "outputs" / "impact" / country
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
    # A4 is (595.27, 841.89) points
    page_width = A4[0] - (2 * MARGIN)
    page_height = A4[1] - (2 * MARGIN)

    # Height Allocations
    DISCLAIMER_H = 40
    HEADER_H = 60
    NOTES_H = 80
    SAFETY_BUFFER = 20  # Buffer to ensure it stays on one page
    GRID_TOTAL_H = page_height - DISCLAIMER_H - HEADER_H - NOTES_H - SAFETY_BUFFER

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
    LOGO_PATH = BASE / 'doc' / '_static' / 'OQ-Logo-Standard-RGB-72DPI-01.png'
    LOGO_W = 100

    # Event Header
    header_text = [
        Paragraph(f"<b>{event_name}, {event_date}</b>", styles["Heading2"]),
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


main.calc_id = 'number of the calculation'
main.export_dir = dict(help='export directory', abbrev='-d')
