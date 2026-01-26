from importlib.resources import files
from playwright.sync_api import expect
from openquake.server.tests.pages.engine_page import EnginePage


class ImpactPage(EnginePage):
    def set_rupture_identifier(self, usgs_id):
        self.page.locator('#usgs_id').fill(usgs_id)

    def select_shakemap_version(self, value):
        shakemap_version_select = self.page.locator('select#shakemap_version')
        expect(shakemap_version_select.locator(
            f'option[value="{value}"]')).to_have_count(1, timeout=20_000)
        shakemap_version_select.select_option(value=value)
        expect(shakemap_version_select).to_have_value(value)

    def retrieve_data(self):
        self.page.locator("#submit_impact_get_rupture").click()

    def run_impact_calc(self):
        self.page.locator("#submit_impact_calc").click()

    def set_time_of_the_event(self, value):
        selector = self.page.locator('select#time_event')
        expect(selector).to_be_editable()
        selector.select_option(label=value)

    def set_no_uncertainty(self):
        no_uncertainty_ckb = self.page.locator('input#no_uncertainty')
        expect(no_uncertainty_ckb).to_be_visible()
        expect(no_uncertainty_ckb).not_to_be_checked()
        no_uncertainty_ckb.check()
        expect(self.page.locator(
            'input#truncation_level')).to_have_value('0')
        expect(self.page.locator(
            'input#number_of_ground_motion_fields')).to_have_value('1')

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

    def retrieve_stations_from_usgs(self, expect_no_seismic_stations=False):
        get_stations_btn = self.page.get_by_role("button",
                                                 name="Retrieve from the USGS")
        expect(get_stations_btn).to_be_visible()
        get_stations_btn.click()
        station_data_loaded = self.page.locator('input#station_data_file_loaded')
        if expect_no_seismic_stations:
            self.page.get_by_role("button", name="Close").click()
            expect(station_data_loaded).to_have_value('N.A. (conversion issue)')
        else:
            expect(station_data_loaded).not_to_have_value('')
