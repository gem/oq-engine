from playwright.sync_api import expect


class AeloPage:
    def __init__(self, page):
        self.page = page
        self.calculation_table = page.locator('#calculation_table')

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
        self.page.get_by_role("button", name="Submit").click()

    def latest_job_row(self):
        """
        Return the most recently created job row.
        Assumes newest job appears first.
        """
        return self.calculation_table.locator("tbody tr").first

    def abort_latest_job(self):
        job_row = self.latest_job_row()
        expect(job_row.get_by_text("executing")).to_be_visible(timeout=10_000)
        job_row.get_by_role("link", name="Abort").click(timeout=10_000)
        self.page.get_by_role("button", name="Yes, abort").click(timeout=10_000)
        expect(job_row.get_by_text("aborted")).to_be_visible(timeout=10_000)
