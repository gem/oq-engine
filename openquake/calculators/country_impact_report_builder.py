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
import logging
from io import BytesIO
from pathlib import Path
from PIL import Image as PILImage
from openquake import baselib
from openquake.baselib import config
from openquake.calculators.country_impact_report_utils import (
    EventContext, ReportOptions, LOSS_METADATA, _read_countries_info,
    _read_world_cities, build_classifiers, load_admin_boundaries,
    points_to_gdf, aggregate_losses, save_most_affected_regions)
from openquake.calculators.postproc.plots import plot_variable, MapDataElements

cd = Path(__file__).parent

COUNTRY_PROFILES_BASE_URL = "https://github.com/gem/risk-profiles/tree/master"


class CountryImpactReportBuilder:
    """
    Builds and stores a single-country impact report.
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
                "In order to create an impact report,"
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
            # checking if the directory is present in the oq-engine directory
            if not os.path.exists(
                    fonts_dir := cd.parent.parent / 'fonts'):
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
            # checking if the file is present in the oq-engine directory
            if not os.path.exists(
                    countries_info_file := cd.parent.parent /
                    'countries_info.csv'):
                raise AttributeError(
                    'config.directory.countries_info_file is missing')

        path_str = str(Path(countries_info_file).resolve())
        df = _read_countries_info(path_str)   # cached
        row = df.loc[df["ISO3"] == self.iso3].iloc[0]
        self.country_name = row["ENGLISH_COUNTRY"]
        self.country_region = row["GEM_REGION"]

    def _get_notes(self, oqparam):
        notes_data = {
            "user_note": oqparam.notes if oqparam.notes else None,
            "profile_link": None,
            "metadata": []
        }
        country_profile_link = (f'{COUNTRY_PROFILES_BASE_URL}/'
                                f'{self.country_region}/'
                                f'{self.country_name}')
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
            # checking if the file is present in the oq-engine directory
            if not os.path.exists(
                    world_cities_file := cd.parent.parent /
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
        body_left_style = self.ParagraphStyle(
            "GridBodyTextLeft",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=11,
            alignment=0,  # Left-aligned for text labels
        )
        body_right_style = self.ParagraphStyle(
            "GridBodyTextRight",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=11,
            alignment=2,  # Right-aligned for numeric metrics
        )
        title_style = self.ParagraphStyle(
            "GridSectionTitle",
            parent=self.styles["Normal"],
            fontName="NotoSans-Bold",
            fontSize=11,
            leading=14,
        )
        return body_left_style, body_right_style, title_style

    def _build_summary_table(self, body_left_style, body_right_style):
        col_header = ("Estimated losses" if self.no_uncertainty
                      else "Range of losses (5% - 95%)")
        table_data = [[
            self.Paragraph("<b>Impact metric</b>", body_left_style),
            self.Paragraph("<b>Exposed value</b>", body_right_style),
            self.Paragraph(f"<b>{col_header}</b>", body_right_style)
        ]]
        for meta in LOSS_METADATA.values():
            # NOTE: in order to make it easier to understand and communicate,
            # we use 'residents' for both 'Fatalities' and 'Displaced'
            if meta["label"] in ["Fatalities", "Displaced"]:
                exposed_key = LOSS_METADATA["residents"]["label"] + "_exposed"
            else:
                exposed_key = meta["label"] + "_exposed"
            table_data.append([
                self.Paragraph(meta["label"], body_left_style),
                self.Paragraph(self.summary_data[exposed_key],
                               body_right_style),
                self.Paragraph(self.summary_data[meta["label"]],
                               body_right_style)
            ])
        summary_table = self.Table(
            table_data,
            colWidths=[self.col_w * 0.32,
                       self.col_w * 0.32,
                       self.col_w * 0.32],
            hAlign="LEFT",
        )
        style_cmds = [
            ("GRID", (0, 0), (-1, -1), 0.5, self.colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), self.colors.whitesmoke),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        summary_table.setStyle(self.TableStyle(style_cmds))
        return summary_table

    def _build_left_bundle(self, summary_table, body_left_style, title_style):
        most_affected = self.dstore[
            f"impact/{self.iso3}/most_affected_regions"
        ]
        left_bundle = [
            self.Paragraph(
                f"Summary of impact for {self.country_name}:",
                title_style),
            self.Spacer(1, 4),
            summary_table,
            self.Spacer(1, 6),
        ]

        maximum_distance = 300  # FIXME function argument
        exposed_value_txt = (
            f'The exposed value refers to the assets and population located'
            f' within a {maximum_distance}km radius of the epicentre.')
        left_bundle.append(
            self.Paragraph(exposed_value_txt, body_left_style))
        if self.no_uncertainty:
            left_bundle.extend([
                self.Spacer(1, 4),
                self.Paragraph("No uncertainty was included",
                               body_left_style)])
        left_bundle.append(self.Spacer(1, 18))
        left_bundle.extend([
            self.Paragraph("Regions with highest number of fatalities:",
                           title_style),
            self.ListFlowable(
                [self.ListItem(self.Paragraph(region_name, self.ParagraphStyle(
                    "region",
                    parent=body_left_style,
                    fontName=self._select_font(region_name),
                ))) for region_name in most_affected],
                bulletType="bullet",
                leftIndent=15,
            ),
        ])
        return left_bundle

    # NOTE: passing images explicitly to avoid implicit ordering dependency
    def _build_grid(self, images):
        body_left_style, body_right_style, title_style = self._grid_styles()
        summary_table = self._build_summary_table(body_left_style,
                                                  body_right_style)
        left_bundle = self._build_left_bundle(
            summary_table, body_left_style, title_style)

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

        # Spread the remaining system metadata across 3 columns
        notes_items = self.notes.get("metadata", [])
        for i in range(0, len(notes_items), 3):
            row = [self.Paragraph(item, notes_style)
                   for item in notes_items[i:i+3]]
            while len(row) < 3:
                row.append(self.Paragraph("", notes_style))
            grid_data.append(row)

        # Add safety cushion at the bottom of the last metadata row
        styles_to_apply.append(('BOTTOMPADDING', (0, -1), (2, -1), 6))

        t = self.Table(grid_data, colWidths=[180, 180, 180])
        t.setStyle(self.TableStyle(styles_to_apply))
        story.append(t)
        return story

    def build(self):
        logging.info(f'Making impact report for {self.iso3}...')
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
            f'The impact report in PDF format was saved into the datastore'
            f' as {pdf_path}')

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
            f'The impact report in PNG format was saved into the datastore'
            f' as {png_path}')
