from playwright.sync_api import expect


class EnginePage:
    def __init__(self, page):
        self.page = page
        self.calculation_table = page.locator('#calculation_table')

    def latest_job_row(self):
        """
        Return the most recently created job row.
        Assumes newest job appears first.
        """
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

    def abort_job(self, job_id):
        job_row = self.get_job_row(job_id)
        expect(job_row.get_by_text("executing")).to_be_visible(
            timeout=80_000)
        job_row.get_by_role("link", name="Abort").click(timeout=20_000)
        self.page.get_by_role("button", name="Yes, abort").click(
            timeout=20_000)
        expect(self.page.get_by_text("has been aborted")).to_be_visible(
            timeout=20_000)
        self.page.get_by_role("button", name="Close").click(timeout=20_000)
        expect(job_row.get_by_text("failed")).to_be_visible(timeout=20_000)
