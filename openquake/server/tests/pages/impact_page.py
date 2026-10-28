from importlib.resources import files
from playwright.sync_api import expect
from openquake.server.tests.pages.engine_page import EnginePage

# Rupture/station requests can make two serial USGS downloads, each with
# five 30-second attempts and exponential backoff.
USGS_REQUEST_TIMEOUT = 330_000


class ImpactPage(EnginePage):
    def set_rupture_identifier(self, usgs_id):
        self.page.locator('#usgs_id').fill(usgs_id)

    def select_shakemap_version(self, value):
        selector = self.page.locator('select#shakemap_version')
        expect(self.page.locator('input#usgs_id')).to_be_enabled(
            timeout=180_000)
        expect(self.page.locator(
            '.populating_shakemap_version')).to_be_hidden(timeout=180_000)
        options = selector.locator('option')
        expect(options).not_to_have_count(0, timeout=180_000)
        error_option = selector.locator('option[value="error"]')
        if error_option.count():
            raise AssertionError(
                f'Unable to load ShakeMap versions: '
                f'{error_option.inner_text()}')
        option = selector.locator(f'option[value="{value}"]')
        if not option.count():
            available = options.evaluate_all(
                'items => items.map(item => '
                '`${item.value}: ${item.textContent}`)')
            raise AssertionError(
                f'ShakeMap version {value!r} is not available; '
                f'current options: {available}')
        selector.select_option(value=value)
        expect(selector).to_have_value(value)

    def select_another_shakemap_version(self):
        selector = self.page.locator('select#shakemap_version')
        current = selector.input_value()
        values = selector.locator('option').evaluate_all(
            'items => items.map(item => item.value)')
        [value, *_] = [val for val in values if val != current]
        selector.select_option(value=value)
        expect(selector).to_have_value(value)

    def retrieve_data(self):
        self.page.locator('.modal-backdrop').wait_for(
            state='detached', timeout=15_000)
        with self.page.expect_response(
                lambda response: response.url.endswith(
                    '/v1/calc/impact_get_rupture_data'),
                timeout=USGS_REQUEST_TIMEOUT) as response_info:
            self.page.locator("#submit_impact_get_rupture").click()
        response = response_info.value
        if not response.ok:
            raise AssertionError(
                f'Rupture retrieval failed ({response.status}): '
                f'{response.text()}')
        data = response.json()
        map_fields = ('rupture_png', 'mmi_map_png', 'pga_map_png')
        if not any(data.get(field) for field in map_fields):
            raise AssertionError(
                f'Rupture retrieval returned no map; keys: '
                f'{sorted(data)}')

    def run_impact_calc(self):
        with self.page.expect_response(
                lambda response: response.url.endswith(
                    '/v1/calc/impact_run'),
                timeout=USGS_REQUEST_TIMEOUT) as response_info:
            self.page.locator("#submit_impact_calc").click()
        response = response_info.value
        if not response.ok:
            raise AssertionError(
                f'Impact calculation submission failed '
                f'({response.status}): {response.text()}')

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

    def set_make_impact_reports(self):
        reports_ckb = self.page.locator('input#make_impact_reports')
        expect(reports_ckb).to_be_visible()
        reports_ckb.check()
        expect(reports_ckb).to_be_checked()

    def rupture_identifier(self):
        return self.page.locator('input#usgs_id')

    def local_timestamp(self):
        return self.page.locator('input#local_timestamp')

    def maximum_distance(self):
        return self.page.locator('input#maximum_distance')

    def truncation_level(self):
        return self.page.locator('input#truncation_level')

    def description(self):
        return self.page.locator('input#description')

    def run_impact_calc_btn(self):
        return self.page.locator('#submit_impact_calc')

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
        # the input is un-hidden by the approach handler, which may be slow
        expect(self.page.locator("input#rupture_file_input")).to_be_visible(
            timeout=50_000)
        rupture_file = (
            files("openquake.hazardlib.tests.shakemap.data")
            / "fault_rupture.xml"
        )

        self.page.set_input_files(
            "input[type=file]#rupture_file_input",
            rupture_file,
        )

    def confirm_relocated_hypocenter_warning(self):
        expect(self.page.get_by_text("it was moved")).to_be_visible(
            timeout=50_000)
        modal = self.page.get_by_text("it was moved")
        self.page.get_by_role("button", name="Close").click()
        expect(modal).not_to_be_visible()

    def select_nodal_plane(self):
        # the select is empty (hence not visible) until the nodal planes
        # are retrieved from the USGS, so wait for the options first
        self.page.wait_for_function(
            "document.querySelector('select#nodal_plane').options.length > 0",
            timeout=30_000
        )
        expect(self.page.locator('select#nodal_plane')).to_be_visible()

    def retrieve_stations_from_usgs(self, expect_no_seismic_stations=False):
        get_stations_btn = self.page.get_by_role("button",
                                                 name="Retrieve from the USGS")
        expect(get_stations_btn).to_be_visible(timeout=15_000)
        with self.page.expect_response(
                lambda response: response.url.endswith(
                    '/v1/impact_get_stations_from_usgs'),
                timeout=USGS_REQUEST_TIMEOUT) as response_info:
            get_stations_btn.click(timeout=15_000)
        response = response_info.value
        if not response.ok:
            raise AssertionError(
                f'Station retrieval failed ({response.status}): '
                f'{response.text()}')
        data = response.json()
        issue = data.get('station_data_issue')
        if issue:
            expected_no_station_messages = (
                'no features', 'no seismic', 'none of them are seismic',
                'no stations were found', 'all discarded',
                'station_type" is not specified')
            if (not expect_no_seismic_stations or
                    not any(text in issue.lower()
                            for text in expected_no_station_messages)):
                raise AssertionError(f'Station retrieval failed: {issue}')
        elif expect_no_seismic_stations:
            raise AssertionError(
                'Expected the selected ShakeMap to have no usable stations')
        station_data_loaded = self.page.locator(
            'input#station_data_file_loaded')
        if expect_no_seismic_stations:
            expect(station_data_loaded).to_have_value(
                'N.A. (conversion issue)', timeout=USGS_REQUEST_TIMEOUT)
            self.page.get_by_role("button", name="Close").click(
                timeout=15_000)
        else:
            expect(station_data_loaded).not_to_have_value(
                '', timeout=USGS_REQUEST_TIMEOUT)
