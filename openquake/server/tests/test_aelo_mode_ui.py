from openquake.server.tests.pages.aelo_page import AeloPage
from playwright.sync_api import expect


def test_aelo_run_job(authenticated_page):
    page = AeloPage(authenticated_page)

    page.set_location(45, 9)
    page.set_site_name("Pavia")
    page.select_asce_version("ASCE7-22")
    page.select_site_class("E")

    page.confirm_vs30_warning()

    page.select_site_class("C")
    expect(authenticated_page.locator("#site_class")).to_have_value("C")

    page.run_aelo_calc()

    job_row = page.latest_job_row()
    expect(job_row.get_by_text("executing")).to_be_visible(timeout=10_000)
    job_row.get_by_role("link", name="Abort").click()
    authenticated_page.get_by_role("button", name="Yes, abort").click()
    expect(job_row.get_by_text("aborted")).to_be_visible(timeout=10_000)
