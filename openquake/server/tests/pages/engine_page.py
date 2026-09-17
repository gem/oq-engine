import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect


class EnginePage:
    def __init__(self, page):
        self.page = page
        self.calculation_table = page.locator('#calculation_table')

    def _click_clear_of_backdrop(self, locator, timeout=30_000):
        # Guard against a stale/fading .modal-backdrop from a prior
        # modal intercepting pointer events on this click.
        self.page.locator(".modal-backdrop").wait_for(
            state="detached", timeout=10_000)
        locator.click(timeout=timeout)

    def latest_job_row(self):
        """Return the most recently created job row."""
        return self.calculation_table.locator("tbody tr").first

    def abort_latest_job(self):
        self.abort_job(self.get_job_id_from_new_job())

    def get_job_row(self, job_id):
        return self.page.locator("tr").filter(
            has=self.page.locator("td:first-child").get_by_text(
                str(job_id), exact=True))

    def get_job_id_from_new_job(self):
        executing_status = self.page.get_by_text("executing")
        expect(executing_status).to_be_visible(timeout=50_000)
        target_row = self.page.locator("tr").filter(
            has_text="executing").first
        return target_row.locator("td").first.inner_text().strip()

    def wait_for_job_completion(self, job_id):
        job_row = self.get_job_row(job_id)
        expect(job_row).to_contain_text("complete", timeout=120_000)

    def abort_job(self, job_id):
        job_row = self.get_job_row(job_id)
        expect(job_row.get_by_text("executing")).to_be_visible(
            timeout=80_000)
        self._click_clear_of_backdrop(
            job_row.get_by_role("link", name="Abort"), timeout=20_000)
        self.page.get_by_role("button", name="Yes, abort").click(
            timeout=20_000)
        expect(self.page.get_by_text("has been aborted")).to_be_visible(
            timeout=20_000)
        self.page.get_by_role("button", name="Close").click(timeout=20_000)
        expect(job_row.get_by_text("failed")).to_be_visible(timeout=20_000)

    def remove_job(self, job_id):
        job_row = self.get_job_row(job_id)
        self._click_clear_of_backdrop(
            job_row.get_by_role("link", name="Remove"))
        self.page.get_by_role("button", name="Yes, remove").click(
            timeout=30_000)
        expect(self.page.get_by_text("has been removed")).to_be_visible(
            timeout=30_000)
        self.page.get_by_role("button", name="Close").click(timeout=30_000)

    def to_outputs(self, job_id):
        job_row = self.get_job_row(job_id)
        job_row.get_by_role("link", name="Outputs").click(timeout=10_000)
        self.page.wait_for_load_state("networkidle")

    def to_report(self):
        """Open the report after it has been persisted by the job."""
        report_link = self.page.get_by_role(
            "link", name=re.compile(r"^Show impact report"))
        for _ in range(3):
            try:
                report_link.click(timeout=5_000)
                return
            except PlaywrightTimeoutError:
                # The job can be marked complete just before the report
                # datasets become visible to the web process.
                self.page.reload(wait_until="networkidle")
        report_link.click(timeout=10_000)

    def to_calculations(self):
        self.page.get_by_text("Back to Calculations").click(timeout=10_000)
        self.page.wait_for_load_state("networkidle")

    def download_job(self):
        with self.page.expect_download() as download_info:
            self.page.get_by_text("Download job.zip").click()
        download = download_info.value
        assert download.suggested_filename.endswith(".zip")
        assert download.path() is not None

    def download_datastore(self):
        with self.page.expect_download() as download_info:
            self.page.get_by_text("Download hdf5 datastore").click()
        download = download_info.value
        assert download.suggested_filename.startswith('calc_')
        assert download.suggested_filename.endswith(".hdf5")
        assert download.path() is not None
