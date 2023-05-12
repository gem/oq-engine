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


class EngineServerAeloModeTestCase(EngineServerTestCase):

    @classmethod
    def setUpClass(cls):
        assert get_status() == 'running'
        dbcmd('reset_is_running')  # cleanup stuck calculations
        cls.job_ids = []
        env = os.environ.copy()
        env['OQ_DISTRIBUTE'] = 'no'
        username = 'django-test-user'
        email = 'django-test-user@email.test'
        password = ''.join((secrets.choice(
            string.ascii_letters + string.digits + string.punctuation)
            for i in range(8)))
        cls.user, created = User.objects.get_or_create(
            username=username, email=email)
        if created:
            cls.user.set_password(password)
            cls.user.save()
        cls.c = Client()
        cls.c.login(username=username, password=password)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.wait()
        finally:
            cls.user.delete()

    def aelo_run(self, params, failure_reason=None):
        with tempfile.TemporaryDirectory() as email_dir:
            # FIXME: EMAIL_FILE_PATH is ignored. This would cause concurrency
            # issues in case tests run in parallel, because we are checking the
            # last email that was created instead of the only email created in
            # a test-specific directory
            with self.settings(EMAIL_FILE_PATH=email_dir):
                resp = self.post('aelo_run', params)
                if resp.status_code == 400:
                    self.assertIsNotNone(failure_reason)
                    content = json.loads(resp.content)
                    self.assertIn(failure_reason, content['error_msg'])
                    return
                self.assertEqual(resp.status_code, 200)
                # the job is supposed to start
                # and, if failure_reason is not None, to fail afterwards
                try:
                    js = json.loads(resp.content.decode('utf8'))
                except Exception:
                    raise ValueError(
                        b'Invalid JSON response: %r' % resp.content)
                job_id = js['job_id']
                self.wait()
                if failure_reason:
                    tb = self.get('%s/traceback' % job_id)
                    if not tb:
                        sys.stderr.write('Empty traceback, please check!\n')
                    self.assertIn(failure_reason, '\n'.join(tb))
                else:
                    results = self.get('%s/results' % job_id)
                    self.assertGreater(
                        len(results), 0, 'The job produced no outputs!')
                # # FIXME: we should use the overridden EMAIL_FILE_PATH,
                # #        so email_dir would contain only one file
                # email_file = os.listdir(email_dir)[0]
                email_files = glob.glob('/tmp/app-messages/*')
                email_file = max(email_files, key=os.path.getctime)
                with open(os.path.join(email_dir, email_file), 'r') as f:
                    email_content = f.read()
                    print(email_content)
                if failure_reason:
                    self.assertIn('failed', email_content)
                else:
                    self.assertIn('finished correctly', email_content)
                self.assertIn('From: aelonoreply@openquake.org', email_content)
                self.assertIn('To: django-test-user@email.test', email_content)
                self.assertIn('Reply-To: aelosupport@openquake.org',
                              email_content)
                self.assertIn(
                    f"Input values: lon = {params['lon']},"
                    f" lat = {params['lat']}, vs30 = {params['vs30']},"
                    f" siteid = {params['siteid']}", email_content)
                if failure_reason:
                    self.assertIn(failure_reason, email_content)
                else:
                    self.assertIn('Please find the results here:',
                                  email_content)
                    self.assertIn(f'engine/{job_id}/outputs', email_content)
        self.post('%s/remove' % job_id)

    def get_tested_lon_lat(self, model):
        test_sites_csv = 'openquake/qa_tests_data/mosaic/test_sites.csv'
        with open(test_sites_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if row['model'] == model:
                    break
            else:
                raise ValueError(f'No tested site was found for {model}')
            return float(row['lon']), float(row['lat'])

    def test_aelo_successful_run_CCA(self):
        lon, lat = self.get_tested_lon_lat('CCA')
        params = dict(
            lon=lon, lat=lat, vs30='800.0', siteid='CCA_SITE')
        self.aelo_run(params)

    # NOTE: we can easily add tests for other models as follows:

    # def test_aelo_successful_run_EUR(self):
    #     lon, lat = self.get_tested_lon_lat('EUR')
    #     params = dict(
    #         lon=lon, lat=lat, vs30='800.0', siteid='EUR_SITE')
    #     self.aelo_run(params)

    # def test_aelo_successful_run_JPN(self):
    #     lon, lat = self.get_tested_lon_lat('JPN')
    #     params = dict(
    #         lon=lon, lat=lat, vs30='800.0', siteid='JPN_SITE')
    #     self.aelo_run(params)

    def test_aelo_failing_run_mosaic_model_not_found(self):
        params = dict(
            lon='-86.0', lat='88.0', vs30='800.0', siteid='SOMEWHERE')
        failure_reason = (
            f"Site at lon={params['lon']} lat={params['lat']}"
            f" is not covered by any model!")
        self.aelo_run(params, failure_reason)

    def aelo_invalid_input(self, params, expected_error):
        resp = self.post('aelo_run', params)
        self.assertEqual(resp.status_code, 400)
        err_msg = json.loads(resp.content.decode('utf8'))
        print(err_msg)
        self.assertIn(expected_error, err_msg)

    def test_aelo_invalid_latitude(self):
        params = dict(lon='-86', lat='100', vs30='800', siteid='CCA_SITE')
        self.aelo_invalid_input(params, 'latitude 100.0 > 90')

    def test_aelo_invalid_longitude(self):
        params = dict(lon='-186', lat='12', vs30='800', siteid='CCA_SITE')
        self.aelo_invalid_input(params, 'longitude -186.0 < -180')

    def test_aelo_invalid_vs30(self):
        params = dict(lon='-86', lat='12', vs30='-800', siteid='CCA_SITE')
        self.aelo_invalid_input(params, 'float -800.0 < 0')

    def test_aelo_invalid_siteid(self):
        params = dict(lon='-86', lat='12', vs30='800', siteid='CCA SITE')
        self.aelo_invalid_input(
            params,
            "Invalid ID 'CCA SITE': the only accepted chars are a-zA-Z0-9_-:")

    def test_aelo_can_not_run_normal_calc(self):
        with open(os.path.join(self.datadir, 'archive_ok.zip'), 'rb') as a:
            resp = self.post('run', dict(archive=a))
        assert resp.status_code == 404, resp

    def test_aelo_can_not_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', dict(archive=a))
        assert resp.status_code == 404, resp
