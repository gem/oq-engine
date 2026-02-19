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
        job_row = self.latest_job_row()
        expect(job_row.get_by_text("executing")).to_be_visible(timeout=20_000)
        job_row.get_by_role("link", name="Abort").click(timeout=10_000)
        self.page.get_by_role("button", name="Yes, abort").click(timeout=10_000)
        self.page.get_by_role("button", name="Close").click(timeout=10_000)
        expect(job_row.get_by_text("failed")).to_be_visible(timeout=10_000)
