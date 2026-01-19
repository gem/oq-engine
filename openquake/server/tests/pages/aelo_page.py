from openquake.server.tests.pages.engine_page import EnginePage
from playwright.sync_api import expect


class AeloPage(EnginePage):
    def set_location(self, lat, lon):
        self.page.locator("#lat").fill(str(lat))
        self.page.locator("#lon").fill(str(lon))

    def set_site_name(self, name):
        self.page.locator("#siteid").fill(name)

    def select_asce_version(self, version):
        self.page.locator("#asce_version").select_option(version)

    def select_site_class(self, cls):
        self.page.locator("#site_class").select_option(cls)

    def confirm_vs30_warning(self):
        modal = self.page.get_by_text("The Vs30 is less than 200 m/s")
        expect(modal).to_be_visible()
        self.page.get_by_role("button", name="OK").click()
        expect(modal).not_to_be_visible()

    def run_aelo_calc(self):
        self.page.locator("#submit_aelo_calc").click()
