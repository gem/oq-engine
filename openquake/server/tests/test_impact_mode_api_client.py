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

# NB: run these tests with OQ_APPLICATION_MODE=IMPACT
"""
Run bin/impact_api_client.py, the example given to the users running impact
calculations programmatically, against a temporary WebUI, as a user would.
"""

import os
import sys
import subprocess

import django

from openquake.commonlib import logs
from openquake.server.tests.views_test import (
    get_or_create_user, start_webui, stop_webui)

SCRIPT = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'bin',
                      'impact_api_client.py')
# version 5 of the ShakeMap of us6000phrk, as in test_impact_mode.py
SHAKEMAP_ID = 'urn:usgs-product:us:shakemap:us6000phrk:1736792435199'
MAX_WAIT = 1200  # seconds for the calculation


class ImpactApiClientTestCase(django.test.TransactionTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logs.dbcmd('reset_is_running')  # cleanup stuck calculations
        cls.webserver, cls.webserver_thread, cls.c = start_webui()

    @classmethod
    def tearDownClass(cls):
        stop_webui(cls.webserver, cls.webserver_thread)
        super().tearDownClass()

    def test_impact_api_client(self):
        # a level 1 user, as the users of the impact service
        user, password = get_or_create_user(1)
        env = dict(os.environ, OQ_USERNAME=user.username,
                   OQ_PASSWORD=password)
        cmd = [sys.executable, SCRIPT, 'us6000phrk',
               '--host', self.c.base_url, '--shakemap-id', SHAKEMAP_ID,
               '--max-wait', str(MAX_WAIT)]
        try:
            proc = subprocess.run(
                cmd, env=env, capture_output=True, text=True,
                timeout=MAX_WAIT + 600)
        finally:
            user.delete()
        print(proc.stdout)
        self.assertEqual(proc.returncode, 0, proc.stderr)
