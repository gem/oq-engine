from playwright.sync_api import expect


class EnginePage:
    def __init__(self, page):
        self.page = page
        self.calculation_table = page.locator('#calculation_table')

    def get_job_row(self, job_id):
        return self.page.locator("tr").filter(has_text=job_id)

    def get_job_id_from_new_job(self):
        executing_status = self.page.get_by_text("executing")
        expect(executing_status).to_be_visible(timeout=20_000)
        target_row = self.page.locator("tr").filter(has_text="executing").first
        job_id = target_row.locator("td").first.inner_text()
        return job_id.strip()

    def wait_for_job_completion(self, job_id):
        job_row = self.get_job_row(job_id)
        expect(job_row).to_contain_text("complete", timeout=120_000)

    def abort_job(self, job_id):
        job_row = self.get_job_row(job_id)
        expect(job_row.get_by_text("executing")).to_be_visible(timeout=80_000)
        job_row.get_by_role("link", name="Abort").click(timeout=10_000)
        self.page.get_by_role("button", name="Yes, abort").click(
            timeout=10_000)
        self.page.get_by_role("button", name="Close").click(timeout=10_000)
        expect(job_row.get_by_text("failed")).to_be_visible(timeout=10_000)

    def remove_job(self, job_id):
        job_row = self.get_job_row(job_id)
        job_row.get_by_role("link", name="Remove").click(timeout=10_000)
        self.page.get_by_role("button", name="Yes, remove").click(
            timeout=10_000)
        self.page.get_by_role("button", name="Close").click(timeout=10_000)

    def to_outputs(self, job_id):
        job_row = self.get_job_row(job_id)
        job_row.get_by_role("link", name="Outputs").click(timeout=10_000)

    def to_report(self):
        self.page.get_by_text("Show impact report").click(timeout=10_000)

    def to_calculations(self):
        self.page.get_by_text("Back to Calculations").click(timeout=10_000)

    def download_job(self):
        with self.page.expect_download() as download_info:
            self.page.get_by_text("Download job.zip").click()
        download = download_info.value
        # assert download.suggested_filename.startswith('calc_')
        assert download.suggested_filename.endswith(".zip")
        path = download.path()
        assert path is not None

    def download_datastore(self):
        with self.page.expect_download() as download_info:
            self.page.get_by_text("Download hdf5 datastore").click()
        download = download_info.value
        assert download.suggested_filename.startswith('calc_')
        assert download.suggested_filename.endswith(".hdf5")
        path = download.path()
        assert path is not None
