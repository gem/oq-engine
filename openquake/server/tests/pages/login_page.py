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

import re
from playwright.sync_api import expect

LOGIN_URL = re.compile(r'/accounts/login/')


class LoginPage:
    """
    Log in and out through the graphical interface, as a user would do
    """
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def greeting(self, username):
        return self.page.get_by_text(f'Hello, {username}')

    def login(self, username, password):
        """
        Open the engine page, which redirects anonymous users to the
        login form, and fill the form
        """
        self.page.context.clear_cookies()
        self.page.goto(f'{self.base_url}/engine/')
        expect(self.page).to_have_url(LOGIN_URL)
        self.page.get_by_label('Username').fill(username)
        self.page.get_by_label('Password').fill(password)
        self.page.get_by_role('button', name='Log in').click()

    def logout(self):
        """
        Click on the logout button in the header (a POST form, since
        Django >= 5.0 does not accept GET requests to log out)
        """
        self.page.get_by_role('button', name='logout').click()
        expect(self.page).to_have_url(LOGIN_URL)

    def check_logged_in(self, username):
        expect(self.page).to_have_url(f'{self.base_url}/engine/')
        expect(self.greeting(username)).to_be_visible()
        expect(self.page.get_by_role('button', name='logout')).to_be_visible()

    def check_logged_out(self, username):
        expect(self.greeting(username)).to_have_count(0)
        expect(self.page.get_by_role('button', name='Log in')).to_be_visible()
        # the session was really closed: going back to the engine page
        # leads again to the login form
        self.page.goto(f'{self.base_url}/engine/')
        expect(self.page).to_have_url(LOGIN_URL)
        expect(self.greeting(username)).to_have_count(0)

    def check_login_and_logout(self, username, password):
        self.login(username, password)
        self.check_logged_in(username)
        self.logout()
        self.check_logged_out(username)

    def check_wrong_password(self, username):
        self.login(username, 'wrong-' + username)
        expect(self.page).to_have_url(LOGIN_URL)
        expect(self.page.get_by_text(
            'Please enter a correct username and password')).to_be_visible()
        expect(self.greeting(username)).to_have_count(0)
