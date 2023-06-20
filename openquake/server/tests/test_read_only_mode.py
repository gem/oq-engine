# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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


# NOTE: before importing User or any other model, django.setup() is needed,
#       otherwise it would raise:
#       django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.

import os
import glob
import sys
import json
import tempfile
import string
import unittest
import secrets
import csv

import django
from django.test import Client
from openquake.commonlib.logs import dbcmd
from openquake.server.dbserver import get_status
from openquake.server.tests.views_test import EngineServerTestCase

django.setup()
try:
    from django.contrib.auth.models import User  # noqa
except RuntimeError:
    # Django tests are meant to be run with the command
    # OQ_CONFIG_FILE=openquake/server/tests/data/openquake.cfg \
    # ./openquake/server/manage.py test tests.views_test
    raise unittest.SkipTest('Use Django to run such tests')


class EngineServerReadOnlyModeTestCase(EngineServerTestCase):

    @classmethod
    def setUpClass(cls):
        assert get_status() == 'running'
        dbcmd('reset_is_running')  # cleanup stuck calculations
        cls.c = Client()

    def test_can_not_run_aelo_calc(self):
        params = dict(
            lon=10, lat=45, vs30='800.0', siteid='SITE')
        resp = self.post('aelo_run', params)
        assert resp.status_code == 404, resp

    def test_can_not_abort_calc(self):
        resp = self.post('0/abort')
        assert resp.status_code == 404, resp

    def test_can_not_remove_calc(self):
        resp = self.post('0/remove')
        assert resp.status_code == 404, resp

    def test_can_not_run_normal_calc(self):
        with open(os.path.join(self.datadir, 'archive_ok.zip'), 'rb') as a:
            resp = self.post('run', dict(archive=a))
        assert resp.status_code == 404, resp

    def test_can_not_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', dict(archive=a))
        assert resp.status_code == 404, resp

