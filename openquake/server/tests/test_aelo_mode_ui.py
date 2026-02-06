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

import pytest
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

    page.abort_latest_job()
