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
from playwright.sync_api import expect


@pytest.mark.parametrize("user", [0], indirect=True)
@pytest.mark.parametrize("application_mode", ["RESTRICTED"], indirect=True)
def test_login(ui_logged_in_page, user, test_credentials):
    expect(ui_logged_in_page.get_by_text(
        f"Hello, {test_credentials['username']}")).to_be_visible()
    ui_logged_in_page.wait_for_load_state("networkidle")
