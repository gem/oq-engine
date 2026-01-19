import pytest
from openquake.server.tests.pages.impact_page import ImpactPage
from playwright.sync_api import expect


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
def test_impact_ui_level_0(application_mode, authenticated_page, user):
    page = ImpactPage(authenticated_page)
    # TODO: check that:
    #       * there is no input form
    #       * only shared calculations are visible


@pytest.mark.parametrize("user", [1], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
def test_impact_ui_level_1(application_mode, authenticated_page, user):
    page = ImpactPage(authenticated_page)

    page.set_rupture_identifier('us6000rfbw')
    page.retrieve_shakemap_data()
    expect(page.local_timestamp()).to_be_visible(timeout=25_000)
    expect(page.no_uncertainty_ckb()).to_be_visible()
    expect(page.no_uncertainty_ckb()).not_to_be_checked()
    page.set_no_uncertainty()

    page.run_impact_calc()
    page.abort_latest_job()


@pytest.mark.parametrize("user", [2], indirect=True)
@pytest.mark.parametrize("application_mode", ["IMPACT"], indirect=True)
def test_impact_ui_level_2(application_mode, authenticated_page, user):
    page = ImpactPage(authenticated_page)

    page.set_rupture_identifier('us6000rfbw')

    # page.run_impact_calc()
    # page.abort_latest_job()
