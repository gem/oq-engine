from playwright.sync_api import expect


def test_login(ui_logged_in_page, test_credentials):
    expect(ui_logged_in_page.get_by_text(
        f"Hello, {test_credentials['username']}")).to_be_visible()
