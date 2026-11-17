# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

# NB: run these tests with OQ_APPLICATION_MODE=AELO,
import pytest
from openquake.server.tests.pages.login_page import LoginPage
from openquake.server.tests.pages.cookie_bar import CookieBar
from openquake.server.tests.pages.aelo_page import AeloPage
from playwright.sync_api import expect


@pytest.mark.parametrize("user", [1, 2], indirect=True)
@pytest.mark.parametrize("application_mode", ["AELO"], indirect=True)
def test_aelo_run_job(application_mode, authenticated_page, user):
    page = AeloPage(authenticated_page)

    page.set_location(45, 9)
    page.set_site_name("Pavia")
    page.select_asce_version("ASCE7-22")
    page.select_site_class("E")

    page.confirm_vs30_warning()

    page.select_site_class("C")
    expect(authenticated_page.locator("#site_class")).to_have_value("C")

    page.run_aelo_calc()

    job_id = page.get_job_id_from_new_job()
    page.abort_job(job_id)
    page.remove_job(job_id)


@pytest.mark.parametrize("application_mode", ["AELO"], indirect=True)
def test_cookie_bar(page, live_server, essential_cookie_groups,
                    application_mode):
    # a new visitor accepts the essential cookies from the cookie bar
    CookieBar(page, live_server.url).check_accept_essential_cookies()


@pytest.mark.parametrize("application_mode", ["AELO"], indirect=True)
def test_cookies_info_page(page, live_server, essential_cookie_groups,
                           application_mode):
    CookieBar(page, live_server.url).check_cookies_info_page()


@pytest.mark.parametrize("user", [1], indirect=True)
@pytest.mark.parametrize("application_mode", ["AELO"], indirect=True)
def test_login_logout(page, live_server, user, test_credentials,
                      application_mode):
    # log in and out by clicking on the buttons of the web interface
    LoginPage(page, live_server.url).check_login_and_logout(
        test_credentials['username'], test_credentials['password'])


@pytest.mark.parametrize("user", [1], indirect=True)
@pytest.mark.parametrize("application_mode", ["AELO"], indirect=True)
def test_login_wrong_password(page, live_server, user, test_credentials,
                              application_mode):
    LoginPage(page, live_server.url).check_wrong_password(
        test_credentials['username'])
