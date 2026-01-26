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

import pytest
from openquake.server.tests.pages.impact_page import (
    ImpactPageLevel0, ImpactPageLevel1, ImpactPageLevel2)
from playwright.sync_api import expect


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_0(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel0(authenticated_page)
    # TODO: check that:
    #       * there is no input form
    #       * only shared calculations are visible


# TODO (for all workflows):
# make sure that the correct elements of the UI are shown/hidden at each stage


@pytest.mark.parametrize("user", [1], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_1(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel1(authenticated_page)
    page.set_rupture_identifier('us6000phrk')
    page.select_shakemap_version(
        value='urn:usgs-product:us:shakemap:us6000phrk:1738891320927')
    page.retrieve_data()
    expect(page.intensity_map()).to_be_visible(timeout=50_000)
    expect(page.pga_map()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).not_to_be_editable()
    page.set_time_of_the_event('Night')
    page.set_no_uncertainty()
    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_2_use_shakemap(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel2(authenticated_page)
    page.set_approach('Use ShakeMap from the USGS')
    expect(page.rupture_identifier()).to_be_visible()
    page.set_rupture_identifier('us6000phrk')
    page.select_shakemap_version(
        value='urn:usgs-product:us:shakemap:us6000phrk:1738891320927')
    page.retrieve_data()
    expect(page.intensity_map()).to_be_visible(timeout=50_000)
    expect(page.pga_map()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).not_to_be_editable()
    page.set_time_of_the_event('Night')
    page.set_no_uncertainty()
    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_2_use_point_rupture(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel2(authenticated_page)
    page.set_approach('Use point rupture from the USGS')
    expect(page.rupture_identifier()).to_be_visible()
    page.set_rupture_identifier('us6000jllz')
    page.select_shakemap_version(
        value='urn:usgs-product:us:shakemap:us6000jllz:1756921940993')
    page.retrieve_stations_from_usgs()
    page.retrieve_data()
    expect(page.rupture_map()).to_be_visible(timeout=50_000)
    expect(page.local_timestamp()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).not_to_be_editable()
    page.set_time_of_the_event('Night')
    page.set_no_uncertainty()
    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_2_build_rupture(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel2(authenticated_page)
    page.set_approach('Build rupture from USGS nodal plane solutions')
    expect(page.rupture_identifier()).to_be_visible()
    page.set_rupture_identifier('usp0001ccb')
    page.select_shakemap_version(
        value="urn:usgs-product:atlas:shakemap:usp0001ccb:1594164792087")
    page.retrieve_stations_from_usgs()
    page.select_nodal_plane()
    page.retrieve_data()
    expect(page.rupture_map()).to_be_visible(timeout=50_000)
    expect(page.local_timestamp()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).not_to_be_editable()
    page.set_time_of_the_event('Night')
    page.set_no_uncertainty()

    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_2_use_shakemap_fault_rupture(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel2(authenticated_page)
    page.set_approach('Use ShakeMap fault rupture from the USGS')
    expect(page.rupture_identifier()).to_be_visible()
    page.set_rupture_identifier('us6000phrk')
    page.select_shakemap_version(
        value='urn:usgs-product:us:shakemap:us6000phrk:1738891320927')
    page.retrieve_stations_from_usgs(expect_no_seismic_stations=True)
    page.retrieve_data()
    expect(page.rupture_map()).to_be_visible(timeout=50_000)
    expect(page.local_timestamp()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).not_to_be_editable()
    page.set_time_of_the_event('Night')
    page.set_no_uncertainty()

    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_2_use_finite_fault(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel2(authenticated_page)
    page.set_approach('Use finite fault model from the USGS')
    expect(page.rupture_identifier()).to_be_visible()
    page.set_rupture_identifier('us6000jllz')
    page.select_shakemap_version(
        value='urn:usgs-product:us:shakemap:us6000jllz:1756921940993')
    page.retrieve_stations_from_usgs()
    page.retrieve_data()
    expect(page.rupture_map()).to_be_visible(timeout=50_000)
    expect(page.local_timestamp()).to_be_visible(timeout=30_000)
    expect(page.local_timestamp()).not_to_be_editable()
    page.set_time_of_the_event('Night')
    page.set_no_uncertainty()
    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_2_provide_rupture_nrml(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel2(authenticated_page)
    page.set_approach('Provide earthquake rupture in OpenQuake NRML format')
    page.choose_rupture_model()
    page.retrieve_data()
    expect(page.rupture_map()).to_be_visible(timeout=50_000)
    page.confirm_relocated_hypocenter_warning()
    # expect(page.local_timestamp()).not_to_be_visible(timeout=30_000)
    page.set_no_uncertainty()
    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
@pytest.mark.parametrize("default_usgs_id", [""], indirect=True)
def test_impact_ui_level_2_provide_rupture_params(
        application_mode, authenticated_page, user, default_usgs_id):
    page = ImpactPageLevel2(authenticated_page)
    page.set_approach('Provide earthquake rupture parameters')
    page.set_longitude(37.6)
    page.set_latitude(37.6)
    page.set_depth(20.0)
    page.set_magnitude(7.8)
    page.set_aspect_ratio(2)
    page.set_rake(0.0)
    page.set_dip(90)
    page.set_strike(51.9)
    page.retrieve_data()
    expect(page.rupture_map()).to_be_visible(timeout=50_000)
    page.set_time_of_the_event('Night')
    page.set_no_uncertainty()
    page.run_impact_calc()
    page.abort_latest_job()
