import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["RESTRICTED"], indirect=True)
def test_login(ui_logged_in_page, user, test_credentials):
    expect(ui_logged_in_page.get_by_text(
        f"Hello, {test_credentials['username']}")).to_be_visible()
    ui_logged_in_page.wait_for_load_state("networkidle")
