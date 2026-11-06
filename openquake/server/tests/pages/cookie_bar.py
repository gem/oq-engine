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


class CookieBar:
    """
    The cookie consent bar, managed by the cookiebar module of
    django-cookie-consent
    """
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url
        self.bar = page.locator('.cookie-bar')

    def open_as_new_visitor(self):
        # anonymous users are redirected to the login page, which also
        # displays the cookie bar
        self.page.context.clear_cookies()
        self.page.goto(f'{self.base_url}/engine/')

    def check_accept_essential_cookies(self):
        """
        With only essential cookies configured (see the fixture
        0001_cookie_consent_required_plus_hide_cookie_bar.json) the bar
        asks to accept them and the decline button is hidden
        """
        self.open_as_new_visitor()
        expect(self.bar).to_be_visible()
        expect(self.bar).to_contain_text(
            'This site needs essential cookies to function properly')
        expect(self.bar.locator('.cc-cookie-decline')).to_be_hidden()
        expect(self.page.locator('body')).to_have_class(
            re.compile('with-cookie-bar'))
        # the consent is sent to the server, which sets the cookie
        with self.page.expect_response(
                lambda resp: resp.url.endswith('/cookies/accept/')
                and resp.request.method == 'POST') as resp_info:
            self.bar.get_by_text('Accept and continue').click()
        assert resp_info.value.ok, resp_info.value.status
        expect(self.bar).to_have_count(0)
        expect(self.page.locator('body')).not_to_have_class(
            re.compile('with-cookie-bar'))
        cookies = {c['name'] for c in self.page.context.cookies()}
        assert 'cookie_consent' in cookies, cookies
        # the choice is remembered: the bar is not displayed anymore
        self.page.reload()
        self.page.wait_for_load_state('networkidle')
        expect(self.bar).to_have_count(0)

    def check_cookies_info_page(self):
        self.open_as_new_visitor()
        self.bar.get_by_role('link', name='Cookies info').click()
        expect(self.page).to_have_url(re.compile(r'/cookies/$'))
        expect(self.page.get_by_role(
            'heading', name='Essential cookies')).to_be_visible()
