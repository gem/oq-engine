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
from urllib.parse import urljoin

import pytest
from django.contrib.auth import get_user_model
from openquake.commonlib.logs import dbcmd
from openquake.server.tests.pages.login_page import LoginPage
from openquake.server.tests.pages.cookie_bar import CookieBar
from openquake.server.tests.pages.aelo_page import AeloPage
from playwright.sync_api import expect


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["AELO"], indirect=True)
def test_aelo_ui_level_0(application_mode, authenticated_page, user,
                         client, tmp_path):
    page = AeloPage(authenticated_page)
    expect(authenticated_page.locator('#aelo_run_form')).to_have_count(0)
    expect(authenticated_page.locator('#submit_aelo_calc')).to_have_count(0)
    response = authenticated_page.request.post(
        urljoin(authenticated_page.url, '/v1/calc/aelo_run'),
        form={'lon': '9', 'lat': '45'})
    assert response.status == 403
    owner = get_user_model().objects.create_user('aelo-ui-owner')
    owner.profile.level = 2
    owner.profile.save()
    job_ids = []
    try:
        for name in ('Private site', 'Shared site'):
            job_id = dbcmd('create_job', str(tmp_path), 'classical',
                           f'AELO for {name}', owner.username)
            job_ids.append(job_id)
            dbcmd('update_job', job_id,
                  {'status': 'complete', 'is_running': False})
        private_id, shared_id = job_ids
        client.force_login(owner)
        assert client.post(
            f'/v1/calc/{shared_id}/share').status_code == 200
        authenticated_page.reload()
        shared_row = page.get_job_row(shared_id)
        expect(shared_row).to_be_visible()
        expect(page.get_job_row(private_id)).to_have_count(0)
        outputs_link = shared_row.get_by_role('link', name='Outputs')
        expect(outputs_link).to_have_attribute(
            'href', f'/engine/{shared_id}/outputs_aelo')
        for action in ('Share', 'Unshare', 'Remove', 'Abort'):
            expect(shared_row.get_by_role(
                'link', name=action, exact=True)).to_have_count(0)
        assert client.post(
            f'/v1/calc/{shared_id}/unshare').status_code == 200
        authenticated_page.reload()
        expect(page.get_job_row(shared_id)).to_have_count(0)
    finally:
        for job_id in job_ids:
            dbcmd('del_calc', job_id, owner.username, False)
        owner.delete()


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
