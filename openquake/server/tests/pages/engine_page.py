import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect


class EnginePage:
    def __init__(self, page):
        self.page = page
        self.calculation_table = page.locator('#calculation_table')
        self.new_job_id = None

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
        """Identify the submitted job independently of its current status."""
        assert self.new_job_id is not None, 'No job submission was captured'
        expect(self.get_job_row(self.new_job_id)).to_be_visible(
            timeout=50_000)
        return self.new_job_id

    def _submit_calculation(self, button, endpoint, timeout=50_000):
        # Register before clicking: fast responses and short jobs must not
        # be missed. Never infer identity from a transient table status.
        self.new_job_id = None
        with self.page.expect_response(
                lambda response: response.url.endswith(endpoint)
                and response.request.method == 'POST',
                timeout=timeout) as response_info:
            button.click()
        response = response_info.value
        assert response.ok, (
            f'Calculation submission failed ({response.status}): '
            f'{response.text()}')
        data = response.json()
        if endpoint.endswith('/impact_run'):
            # IMPACT returns a mapping from calculation IDs to job details.
            assert len(data) == 1, f'Expected one submitted job: {data}'
            [data] = data.values()
        assert data.get('job_id'), f'Submission returned no job_id: {data}'
        self.new_job_id = str(data['job_id'])

    def wait_for_job_completion(self, job_id):
        job_row = self.get_job_row(job_id)
        expect(job_row).to_contain_text("complete", timeout=120_000)

    def _confirm_action(self, action):
        # Wait for the custom modal before querying its dynamically labelled
        # button; this also verifies that the initiating click was handled.
        modal = self.page.locator("#confirmModal")
        expect(modal).to_be_visible(timeout=20_000)
        button = modal.locator(".btn-confirm")
        expect(button).to_have_text(f"Yes, {action}")
        button.click(timeout=20_000)

    def abort_job(self, job_id):
        job_row = self.get_job_row(job_id)
        abort_link = job_row.get_by_role("link", name="Abort", exact=True)
        terminal_status = job_row.locator('td').nth(6).filter(
            has_text=re.compile(r'complete|failed'))
        # Polls may skip executing altogether. A completed job needs no abort;
        # an unexpected failure must still fail the test.
        expect(abort_link.or_(terminal_status).first).to_be_visible(
            timeout=80_000)
        if terminal_status.is_visible():
            expect(terminal_status).to_have_text('complete')
            return
        try:
            self._click_clear_of_backdrop(abort_link, timeout=10_000)
        except PlaywrightTimeoutError:
            # Completion can also remove the link while click is retrying.
            expect(job_row.locator('td').nth(6)).to_have_text('complete')
            return
        self._confirm_action("abort")
        # short jobs may finish before the abort reaches the server, which
        # then refuses it: both outcomes are valid, so check the row state
        aborted = self.page.get_by_text("has been aborted")
        finished = self.page.get_by_text("is not running")
        expect(aborted.or_(finished)).to_be_visible(timeout=20_000)
        was_aborted = aborted.is_visible()
        self.page.get_by_role("button", name="Close").click(timeout=20_000)
        if was_aborted:
            # Signal delivery is not an acknowledgement from the worker.
            # It can persist completion, or record SIGINT as a failed job.
            expect(job_row.locator('td').nth(6)).to_contain_text(
                re.compile(r'\b(complete|failed)\b'),
                timeout=20_000)
        else:
            expect(job_row.get_by_text("complete")).to_be_visible(
                timeout=20_000)

    def remove_job(self, job_id):
        job_row = self.get_job_row(job_id)
        self._click_clear_of_backdrop(
            job_row.get_by_role("link", name="Remove"))
        self._confirm_action("remove")
        expect(self.page.get_by_text("has been removed")).to_be_visible(
            timeout=30_000)
        self.page.get_by_role("button", name="Close").click(timeout=30_000)

    def to_outputs(self, job_id):
        job_row = self.get_job_row(job_id)
        job_row.get_by_role("link", name="Outputs").click(timeout=10_000)
        self.page.wait_for_load_state("networkidle")

    def to_report(self):
        """Open the report after it has been persisted by the job."""
        # match the first page only, not the "(ISO3, page 2)" link
        report_link = self.page.get_by_role(
            "link", name=re.compile(r"^Show impact report \(\w+\)$"))
        for _ in range(12):
            try:
                report_link.click(timeout=10_000)
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
