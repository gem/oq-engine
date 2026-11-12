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

# NB: run these tests with OQ_APPLICATION_MODE=RESTRICTED,
import pytest
from openquake.server.tests.pages.login_page import LoginPage
from playwright.sync_api import expect


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["RESTRICTED"], indirect=True)
def test_login(ui_logged_in_page, user, test_credentials):
    expect(ui_logged_in_page.get_by_text(
        f"Hello, {test_credentials['username']}")).to_be_visible()
    ui_logged_in_page.wait_for_load_state("networkidle")


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["RESTRICTED"], indirect=True)
def test_login_logout(page, live_server, user, test_credentials,
                      application_mode):
    # log in and out by clicking on the buttons of the web interface
    LoginPage(page, live_server.url).check_login_and_logout(
        test_credentials['username'], test_credentials['password'])


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["RESTRICTED"], indirect=True)
def test_login_wrong_password(page, live_server, user, test_credentials,
                              application_mode):
    LoginPage(page, live_server.url).check_wrong_password(
        test_credentials['username'])
