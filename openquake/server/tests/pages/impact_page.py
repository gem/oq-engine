from importlib.resources import files
from playwright.sync_api import expect
from openquake.server.tests.pages.engine_page import EnginePage


class ImpactPage(EnginePage):
    def set_rupture_identifier(self, usgs_id):
        self.page.locator('#usgs_id').fill(usgs_id)

    def select_shakemap_version(self):
        self.page.wait_for_function(
            "document.querySelector('select#shakemap_version').options.length > 0",
            timeout=30_000
        )

    def retrieve_data(self):
        self.page.locator("#submit_impact_get_rupture").click()

    def run_impact_calc(self):
        self.page.locator("#submit_impact_calc").click()

    def set_time_of_the_event(self, value):
        selector = self.page.locator('select#time_event')
        expect(selector).to_be_editable()
        selector.select_option(label=value)

    def set_no_uncertainty(self):
        self.no_uncertainty_ckb().check()

    def rupture_identifier(self):
        return self.page.locator('input#usgs_id')

    def local_timestamp(self):
        return self.page.locator('input#local_timestamp')

    def no_uncertainty_ckb(self):
        return self.page.locator('input#no_uncertainty')

    def rupture_map(self):
        return self.page.locator('div#rupture-map')

    def intensity_map(self):
        return self.page.locator('div#intensity-map')

    def pga_map(self):
        return self.page.locator('div#pga-map')


class ImpactPageLevel0(ImpactPage):
    pass


class ImpactPageLevel1(ImpactPage):
    pass


class ImpactPageLevel2(ImpactPage):

    def set_approach(self, approach_label):
        # We could find a better approach to make sure the handler is ready
        self.page.wait_for_timeout(200)

        approach = self.page.get_by_role("radio", name=approach_label)
        approach.check()
        expect(approach).to_be_checked()

    def set_longitude(self, lon):
        self.page.locator("input#lon").fill(str(lon))

    def set_latitude(self, lat):
        self.page.locator("input#lat").fill(str(lat))

    def set_depth(self, dep):
        self.page.locator("input#dep").fill(str(dep))

    def set_magnitude(self, mag):
        self.page.locator("input#mag").fill(str(mag))

    def set_aspect_ratio(self, ar):
        self.page.locator("input#aspect_ratio").fill(str(ar))

    def set_rake(self, rake):
        self.page.locator("input#rake").fill(str(rake))

    def set_dip(self, dip):
        self.page.locator("input#dip").fill(str(dip))

    def set_strike(self, strike):
        self.page.locator("input#strike").fill(str(strike))

    def choose_rupture_model(self):
        expect(self.page.locator("input#rupture_file_input")).to_be_visible()
        rupture_file = (
            files("openquake.hazardlib.tests.shakemap.data")
            / "fault_rupture.xml"
        )

        self.page.set_input_files(
            "input[type=file]#rupture_file_input",
            rupture_file,
        )

    def confirm_relocated_hypocenter_warning(self):
        expect(self.page.get_by_text("it was moved")).to_be_visible(timeout=15_000)
        modal = self.page.get_by_text("it was moved")
        self.page.get_by_role("button", name="Close").click()
        expect(modal).not_to_be_visible()

    def select_nodal_plane(self):
        expect(self.page.locator('select#nodal_plane')).to_be_visible()
        self.page.wait_for_function(
            "document.querySelector('select#nodal_plane').options.length > 0",
            timeout=30_000
        )

    def retrieve_stations_from_usgs(self):
        get_stations_btn = self.page.get_by_role("button",
                                                 name="Retrieve from the USGS")
        expect(get_stations_btn).to_be_visible()
        get_stations_btn.click()
        expect(self.page.locator(
               'input#station_data_file_loaded')).not_to_have_value('')
