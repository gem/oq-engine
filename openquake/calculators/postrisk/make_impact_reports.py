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

import pathlib
import tempfile
import logging
from datetime import datetime, timezone
import pandas as pd
from openquake.baselib import config, sap
from openquake.calculators.country_impact_report_builder import (
    CountryImpactReportBuilder)
from openquake.calculators.extract import extract
from openquake.calculators.country_impact_report_utils import (
    EventContext, ReportOptions, LOSS_METADATA)
from openquake.commonlib import logs
from openquake.commonlib.readinput import get_close_countries

cd = pathlib.Path(__file__).parent

LOSS_LABELS = [v["label"] for v in LOSS_METADATA.values()]

DISCLAIMER_TXT = '''
    This is an automatically generated draft. Content has not been verified for
    accuracy by a human reviewer. The metrics presented were estimated based on
    ground shaking information from ShakeMap only. Impact assessments are
    subject to changes as more information becomes available.'''


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
    loss_threshold = 1
    if all(r.lossmea < loss_threshold for _, r in rows.iterrows()):
        logging.info(f"Estimated losses for country {iso3} are negligible"
                     f" (all lossmea < {loss_threshold}). Skipping report.")
        return None
    summary_data = {}
    for label, lt in mapping.items():
        matching_rows = rows.loc[rows['loss_type'] == lt]
        if not matching_rows.empty:
            r = matching_rows.iloc[0]
            q50 = int(round(r.get('q50', 0)))
            q05 = int(round(r.get('q05', 0)))
            q95 = int(round(r.get('q95', 0)))
            exposed_val = int(round(r.get('value', 0)))
        else:
            q50 = q05 = q95 = exposed_val = 0
        # Format with thousands separators
        if no_uncertainty:
            # Display only the central value
            summary_data[label] = f"{q50:,}"
        else:
            # Display the range
            summary_data[label] = f"{q05:,} - {q95:,}"
        summary_data[f"{label}_exposed"] = f"{exposed_val:,}"
    return summary_data


def make_report_for_country(
        iso3, adm_level, event, options, losses_df, summary_data,
        dstore, time_of_calc, oqparam):
    builder = CountryImpactReportBuilder(
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


def _open_dstore(dstore):
    """
    Resolve the dstore argument (path/int from CLI, or an open Datastore),
    returning (dstore, calc_id).
    """
    if isinstance(dstore, (str, int)):
        # NOTE: called from the command line
        from openquake.commonlib import datastore
        calc_id = int(dstore)
        dstore = datastore.read(calc_id, mode='r+')
    else:
        calc_id = dstore.calc_id
    return dstore, calc_id


def _get_basemap_path():
    try:
        return config.directory.basemap_file
    except AttributeError:
        logging.error('config.directory.basemap_file is missing!')
        return None


def _is_no_uncertainty(oqparam):
    # If the ground motion is fully deterministic, we suppress uncertainty
    # ranges in the report and show only the central (point) estimate.
    return (oqparam.number_of_ground_motion_fields == 1
            and abs(oqparam.truncation_level) < 1e-8)


def _get_losses_df(avg_losses):
    """
    Use the median (quantile-0.5) as the representative point estimate for
    the spatial loss maps, consistent with how _get_impact_summary_data
    displays the central value. Fall back to the mean only if the median is
    unavailable (e.g. a calculation run without quantile outputs).
    """
    if (hasattr(avg_losses, 'quantile-0.5')
            and avg_losses['quantile-0.5'] is not None):
        return pd.DataFrame(avg_losses['quantile-0.5']), 'Median'
    elif hasattr(avg_losses, 'mean') and avg_losses.mean is not None:
        logging.warning(
            "Median losses not available; falling back to mean for "
            "loss maps.")
        return pd.DataFrame(avg_losses.mean), 'Mean'
    else:
        raise RuntimeError(
            "avg_losses has neither 'quantile' nor 'mean' attribute; "
            "cannot build losses DataFrame.")


def _get_event_name(rupdic):
    try:
        return rupdic['description']
    except KeyError:
        return rupdic['title']


def _get_shakemap_version(rupdic):
    try:
        return rupdic['shakemap_desc']
    except KeyError:
        return None


def _get_threshold_deg(threshold_deg, mag):
    if threshold_deg is None:
        threshold_deg = get_dynamic_threshold(mag)
        logging.info(f"Magnitude {mag} detected. Using dynamic"
                     f" threshold: {threshold_deg} degrees.")
        return threshold_deg
    return float(threshold_deg)


def _build_report_contexts(dstore, oqparam, calc_id, threshold_deg):
    """
    Gather everything needed to build per-country reports and return
    (event_ctx, report_opts, losses_df, iso3_codes, time_of_calc).
    """
    mag = oqparam.rupture_dict['mag']
    lon = oqparam.rupture_dict['lon']
    lat = oqparam.rupture_dict['lat']
    no_uncertainty = _is_no_uncertainty(oqparam)

    avg_losses = extract(dstore, 'avg_losses?kind=stats')
    losses_df, loss_metric = _get_losses_df(avg_losses)

    rupdic = oqparam.rupture_dict
    event_name = _get_event_name(rupdic)
    # FIXME: do we prefer to show UTC or perhaps it is more intuitive
    #        to show the local time?
    event_date = to_utc_string(oqparam.local_timestamp)
    shakemap_version = _get_shakemap_version(rupdic)

    job = logs.dbcmd('get_job', calc_id)
    time_of_calc = job.start_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'

    threshold_deg = _get_threshold_deg(threshold_deg, mag)
    # close countries are ordered by ascending distance
    iso3_codes = get_close_countries(lon, lat, buffer_radius=threshold_deg)
    if not iso3_codes:
        raise RuntimeError(
            "No country within {threshold_deg} from the hypocenter")

    event_ctx = EventContext(
        name=event_name, date=event_date, hypocenter=(lon, lat),
        shakemap_version=shakemap_version)
    report_opts = ReportOptions(
        disclaimer_txt=DISCLAIMER_TXT,
        basemap_path=_get_basemap_path(), threshold_deg=threshold_deg,
        no_uncertainty=no_uncertainty, loss_metric=loss_metric)

    return event_ctx, report_opts, losses_df, iso3_codes, time_of_calc


def main(dstore, adm_level=1, threshold_deg=None):
    """
    Create an impact report in PDF and PNG formats
    """
    dstore, calc_id = _open_dstore(dstore)
    adm_level = int(adm_level)

    dstore.close()
    dstore.open('r+')
    dstore.export_dir = config.directory.custom_tmp or tempfile.gettempdir()
    oqparam = dstore['oqparam']

    event_ctx, report_opts, losses_df, iso3_codes, time_of_calc = (
        _build_report_contexts(dstore, oqparam, calc_id, threshold_deg))

    for iso3 in iso3_codes:
        summary_data = _get_impact_summary_data(
            dstore, iso3, report_opts.no_uncertainty)
        if summary_data is not None:
            make_report_for_country(
                iso3, adm_level, event_ctx, report_opts,
                losses_df, summary_data, dstore, time_of_calc, oqparam)


if __name__ == '__main__':
    sap.run(main)
