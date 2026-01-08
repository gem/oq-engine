# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2026 GEM Foundation
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


import os
import glob
import sys
import json
import tempfile
import string
import unittest
import secrets
import csv
import logging

import django
from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.conf import settings
from openquake.baselib import config
from openquake.calculators.base import get_aelo_version
from openquake.commonlib.oqvalidation import OqParam, ASCE_VERSIONS
from openquake.commonlib.logs import dbcmd
from openquake.server.tests.views_test import EngineServerTestCase
from openquake.server.views import get_disp_val

django.setup()
try:
    User = get_user_model()
except RuntimeError:
    raise unittest.SkipTest('Use Django to run such tests')


class EngineServerAeloModeTestCase(EngineServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        super().tearDownClass()

    def aelo_run_then_remove(self, params, failure_reason=None):
        with tempfile.TemporaryDirectory() as email_dir:
            # FIXME: EMAIL_FILE_PATH is ignored. This would cause concurrency
            # issues in case tests run in parallel, because we are checking the
            # last email that was created instead of the only email created in
            # a test-specific directory
            with override_settings(EMAIL_FILE_PATH=email_dir):
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
                app_msgs_dir = os.path.join(
                    config.directory.custom_tmp or tempfile.gettempdir(),
                    'app-messages')
                email_files = glob.glob(os.path.join(app_msgs_dir, '*'))
                email_file = max(email_files, key=os.path.getctime)
                with open(os.path.join(email_dir, email_file), 'r') as f:
                    email_content = f.read()
                    print(email_content)
                if failure_reason:
                    self.assertIn('failed', email_content)
                else:
                    self.assertIn('finished correctly', email_content)
                email_from = settings.EMAIL_HOST_USER
                email_to = settings.EMAIL_SUPPORT
                asce_version = params.get(
                    'asce_version', OqParam.asce_version.default)
                self.assertIn(f'From: {email_from}', email_content)
                self.assertIn('To: django-test-user@email.test', email_content)
                self.assertIn(f'Reply-To: {email_to}', email_content)
                self.assertIn(
                    f"Site name: {params['siteid']}\n"
                    f"Latitude: {params['lat']}, Longitude: {params['lon']}\n"
                    f"Site Class: Vs30 = {params['vs30']} m/s\n"
                    f"ASCE standard: {ASCE_VERSIONS[asce_version]}\n"
                    f"AELO version: {get_aelo_version()}\n\n", email_content)
                if failure_reason:
                    self.assertIn(failure_reason, email_content)
                else:
                    self.assertIn('Please find the results here:',
                                  email_content)
                    self.assertIn(f'engine/{job_id}/outputs', email_content)
        # Check that the Django views to visualize simplified and advanced outputs
        # pages do not raise any exceptions
        self.c.get(f'/engine/{job_id}/outputs')
        self.c.get(f'/engine/{job_id}/outputs_aelo')
        self.c.get(f'/v1/calc/{job_id}/download_png/hcurves.png')
        self.c.get(f'/v1/calc/{job_id}/download_png/site.png')
        self.c.get(f'/v1/calc/{job_id}/download_png/mce.png')
        self.c.get(f'/v1/calc/{job_id}/download_png/disagg_by_src-All-IMTs.png')
        ret = self.post('%s/remove' % job_id)
        if ret.status_code != 200:
            raise RuntimeError('Unable to remove job %s:\n%s' % (job_id, ret))

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

    def test_aelo_successful_run_CCA_then_remove_calc(self):
        lon, lat = self.get_tested_lon_lat('CCA')
        params = dict(
            lon=lon, lat=lat, vs30='800.0', siteid='CCA_SITE')
        self.aelo_run_then_remove(params)

    # NOTE: we can easily add tests for other models as follows:

    # def test_aelo_successful_run_EUR(self):
    #     lon, lat = self.get_tested_lon_lat('EUR')
    #     params = dict(
    #         lon=lon, lat=lat, vs30='800.0', siteid='EUR_SITE')
    #     self.aelo_run_then_remove(params)

    # def test_aelo_successful_run_JPN(self):
    #     lon, lat = self.get_tested_lon_lat('JPN')
    #     params = dict(
    #         lon=lon, lat=lat, vs30='800.0', siteid='JPN_SITE')
    #     self.aelo_run_then_remove(params)

    def test_aelo_failing_run_mosaic_model_not_found(self):
        params = dict(
            lon='-86.0', lat='88.0', vs30='800.0', siteid='SOMEWHERE')
        failure_reason = (
            f"Site at lon={params['lon']} lat={params['lat']}"
            f" is not covered by any model!")
        self.aelo_run_then_remove(params, failure_reason)

    def aelo_invalid_input(self, params, expected_error):
        # NOTE: avoiding to print the expected traceback
        logging.disable(logging.CRITICAL)
        resp = self.post('aelo_run', params)
        logging.disable(logging.NOTSET)
        self.assertEqual(resp.status_code, 400)
        resp_dict = json.loads(resp.content.decode('utf8'))
        print(resp_dict)
        self.assertIn(expected_error, resp_dict['error_msg'])

    def test_aelo_invalid_latitude(self):
        params = dict(lon='-86', lat='100', vs30='800', siteid='CCA_SITE')
        self.aelo_invalid_input(params, 'latitude 100.0 > 90')

    def test_aelo_invalid_longitude(self):
        params = dict(lon='-186', lat='12', vs30='800', siteid='CCA_SITE')
        self.aelo_invalid_input(params, 'longitude -186.0 < -180')

    def test_aelo_invalid_vs30(self):
        params = dict(lon='-86', lat='12', vs30='-800', siteid='CCA_SITE')
        self.aelo_invalid_input(params, 'vs30 -800.0 is smaller than the minimum (150)')
        params = dict(lon='-86', lat='12', vs30='4000', siteid='CCA_SITE')
        self.aelo_invalid_input(params, 'vs30 4000.0 is bigger than the maximum (1525)')

    def test_aelo_invalid_siteid(self):
        siteid = 'a' * (settings.MAX_AELO_SITE_NAME_LEN + 1)
        params = dict(lon='-86', lat='12', vs30='800', siteid=siteid)
        self.aelo_invalid_input(
            params,
            "site name can not be longer than %s characters" %
            settings.MAX_AELO_SITE_NAME_LEN)

    def test_aelo_can_not_run_normal_calc(self):
        with open(os.path.join(self.datadir, 'archive_ok.zip'), 'rb') as a:
            resp = self.post('run', dict(archive=a))
        assert resp.status_code == 404, resp

    def test_aelo_can_not_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', dict(archive=a))
        assert resp.status_code == 404, resp

    def test_announcement(self):
        # NOTE: this test might be moved to the currently missing
        #       test_restricted_mode.py. Anyway, both the AELO and the
        #       RESTRICTED modes imply LOCKDOWN=True and add the announcements
        #       app to the INSTALLED_APPS.
        announcement_model = apps.get_model(app_label='announcements',
                                            model_name='Announcement')
        announcement = announcement_model(
            title='TEST TITLE', content='Test content', show=False)
        announcement.save()
        announcement.delete()

    def test_displayed_values(self):
        test_vals_in = [
            0.0000, 0.30164, 1.10043, 0.00101, 0.00113, 0.00115,
            0.0101, 0.0109, 0.0110, 0.1234, 0.126, 0.109, 0.101,
            0.991, 0.999, 1.001, 1.011, 1.101, 1.1009, 1.5000]
        expected = [
            '0.0', '0.30', '1.10', '0.0010', '0.0011', '0.0012', '0.010',
            '0.011', '0.011', '0.12', '0.13', '0.11', '0.10', '0.99',
            '1.00', '1.00', '1.01', '1.10', '1.10', '1.50']
        computed = [get_disp_val(v) for v in test_vals_in]
        assert expected == computed

    def test_aelo_changelog(self):
        resp = self.c.get('/engine/aelo_changelog')
        self.assertEqual(resp.status_code, 200)

    def test_aelo_site_classes(self):
        resp = self.c.get('/v1/aelo_site_classes')
        resp = json.loads(resp.content.decode('utf8'))
        self.assertEqual(resp['ASCE7-22']['default'],
                         {'display_name': 'Default', 'vs30': [260, 365, 530]})
        self.assertEqual(resp['ASCE7-22']['BC'],
                         {'display_name': 'BC - Soft rock', 'vs30': 760})
        self.assertEqual(resp['ASCE7-16']['BC'],
                         {'display_name': 'B-C boundary', 'vs30': 760})
