from openquake.server.tests.pages.engine_page import EnginePage
from playwright.sync_api import expect


class ImpactPage(EnginePage):
    def set_rupture_identifier(self, usgs_id):
        self.page.locator('#usgs_id').fill(usgs_id)

    def retrieve_shakemap_data(self):
        self.page.locator("#submit_impact_get_rupture").click()

    def run_impact_calc(self):
        self.page.locator("#submit_impact_calc").click()

    def local_timestamp(self):
        return self.page.locator('input#local_timestamp')

    def set_time_of_the_event(self, value):
        selector = self.page.locator('select#time_event')
        expect(selector).to_be_editable()
        selector.select_option(label=value)

    def no_uncertainty_ckb(self):
        return self.page.locator('input#no_uncertainty')

    def set_no_uncertainty(self):
        self.no_uncertainty_ckb().check()


class ImpactPageLevel0(ImpactPage):
    pass


class ImpactPageLevel1(ImpactPage):
    pass


class ImpactPageLevel2(ImpactPage):
    pass
