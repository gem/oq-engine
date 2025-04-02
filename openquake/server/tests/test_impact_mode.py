# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

import time
import os
import sys
import json
import tempfile
import string
import unittest
import secrets
import io
import numpy

import django
from django.test import Client, override_settings
from django.conf import settings
from django.http import HttpResponseNotFound
from openquake.baselib import config
from openquake.baselib.general import gettemp
from openquake.commonlib.dbapi import db
from openquake.commonlib.logs import dbcmd
from openquake.engine.engine import create_jobs

# NOTE: before importing User or any other model, django.setup() is needed,
#       otherwise it would raise:
#       django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.

CALC_RUN_TIMEOUT = 30


django.setup()
try:
    from django.contrib.auth.models import User  # noqa
except RuntimeError:
    # Django tests are meant to be run with the command
    # OQ_CONFIG_FILE=openquake/server/tests/data/openquake.cfg \
    # ./openquake/server/manage.py test tests.views_test
    raise unittest.SkipTest('Authentication not configured')


def loadnpz(lines):
    bio = io.BytesIO(b''.join(ln for ln in lines))
    return numpy.load(bio)


def get_email_content(directory, search_string):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                if search_string in content:
                    return content
    raise FileNotFoundError(
        f'No email was found containing the string {search_string}')


def get_or_create_user(level):
    # creating/getting a user of the given level
    # and returning the user object and its plain password
    username = f'django-test-user-level-{level}'
    email = f'django-test-user-level-{level}@email.test'
    password = ''.join((secrets.choice(
        string.ascii_letters + string.digits + string.punctuation)
        for i in range(8)))
    user, created = User.objects.get_or_create(username=username, email=email)
    if created:
        user.set_password(password)
    user.save()
    user.profile.level = level
    user.profile.save()
    return user, password  # user.password is the hashed password instead


class EngineServerTestCase(django.test.TestCase):
    datadir = os.path.join(os.path.dirname(__file__), 'data')

    # general utilities

    @classmethod
    def post(cls, path, data=None):
        return cls.c.post('/v1/calc/%s' % path, data)

    @classmethod
    def get(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data, HTTP_HOST='testserver')
        if not resp.status_code == 200:
            raise RuntimeError(resp.reason_phrase)
        return resp

    @classmethod
    def get_json(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data, HTTP_HOST='testserver')
        if 'list' not in path:
            print(resp.wsgi_request.META)
            print(resp)
        if hasattr(resp, 'content'):
            assert resp.content, (
                'No content from http://localhost:8800/v1/calc/%s (params: %s)'
                % (path, data))
            js = resp.content.decode('utf8')
        else:
            js = bytes(loadnpz(resp.streaming_content)['json'])
        if not js:
            print('Empty json from ')
            return {}
        try:
            return json.loads(js)
        except Exception:
            print('Invalid JSON, see %s' % gettemp(resp.content, remove=False),
                  file=sys.stderr)
            return {}

    @classmethod
    def wait(cls):
        # wait until all calculations stop
        for i in range(CALC_RUN_TIMEOUT):
            time.sleep(1)  # sec
            # NOTE: is_running is True both for 'submitted' and 'executing'
            #       job status
            running_calcs = cls.get_json('list', is_running='true')
            if not running_calcs:
                # NOTE: some more time is needed in order to wait for the
                # callback to finish and produce the email notification
                time.sleep(2)
                return

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        dbcmd('reset_is_running')  # cleanup stuck calculations
        cls.job_ids = []
        env = os.environ.copy()
        env['OQ_DISTRIBUTE'] = 'no'
        cls.user1, cls.password1 = get_or_create_user(1)  # level 1
        cls.c = Client()
        cls.c.login(username=cls.user1.username, password=cls.password1)
        cls.maxDiff = None

    @classmethod
    def tearDownClass(cls):
        try:
            cls.wait()
        finally:
            cls.user1.delete()
        super().tearDownClass()

    def impact_run_then_remove(
            self, data, failure_reason=None):
        with tempfile.TemporaryDirectory() as email_dir:
            with override_settings(EMAIL_FILE_PATH=email_dir):  # FIXME: it is ignored!
                resp = self.post('impact_run', data)
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
                self.wait()
                app_msgs_dir = os.path.join(
                    config.directory.custom_tmp or tempfile.gettempdir(),
                    'app-messages')
                for job_id in js:
                    if failure_reason:
                        tb = self.get_json('%s/traceback' % job_id)
                        if not tb:
                            sys.stderr.write(
                                'Empty traceback, please check!\n')
                        self.assertIn(failure_reason, '\n'.join(tb))
                    # NOTE: we should use the overridden EMAIL_FILE_PATH,
                    #       so email_dir would contain only the files
                    #       created to notify about the jobs created in
                    #       the test
                    for i in range(CALC_RUN_TIMEOUT):
                        try:
                            results = self.get_json('%s/result/list' % job_id)
                        except AssertionError as exc:
                            print(f'Results for job {job_id} not found yet:')
                            print(exc)
                            self.wait()
                            continue
                        if isinstance(results, HttpResponseNotFound):
                            print(f'Results for job {job_id} not found yet...')
                            self.wait()
                            continue
                        self.assertGreater(
                            len(results), 0,
                            'The job produced no outputs!')
                        break
                    else:
                        raise RuntimeError(
                            f'Unable to retrieve results for job {job_id}')
                    for i in range(CALC_RUN_TIMEOUT):
                        try:
                            email_content = get_email_content(
                                app_msgs_dir, f'Job {job_id} ')
                        except FileNotFoundError:
                            print(f'Email for job {job_id} not found yet...')
                            self.wait()
                            continue
                        else:
                            print(email_content)
                            break
                    else:
                        raise RuntimeError(
                            f'Unable to retrieve email for job {job_id}')
                    if failure_reason:
                        self.assertIn('failed', email_content)
                    else:
                        self.assertIn('finished correctly', email_content)
                    email_from = settings.EMAIL_HOST_USER
                    email_to = settings.EMAIL_SUPPORT
                    self.assertIn(f'From: {email_from}', email_content)
                    self.assertIn('To: django-test-user-level-1@email.test',
                                  email_content)
                    self.assertIn(f'Reply-To: {email_to}', email_content)
                    if failure_reason:
                        self.assertIn(failure_reason, email_content)
                    else:
                        self.assertIn('Please find the results here:',
                                      email_content)
                        self.assertIn(f'engine/{job_id}/outputs_impact',
                                      email_content)
        for job_id in js:
            # NOTE: the get_json utility decodes the json and returns a dict
            ret = self.get_json('%s/impact' % job_id)
            self.assertEqual(list(ret.keys()),
                             ['loss_type_descriptions', 'impact'])
            ret = self.get_json('%s/exposure_by_mmi' % job_id)
            self.assertEqual(list(ret.keys()),
                             ['column_descriptions', 'exposure_by_mmi'])
            ret = self.get('%s/download_aggrisk' % job_id)
            ret = self.get('%s/extract_html_table/aggrisk_tags' % job_id)
            ret = self.get('%s/extract_html_table/mmi_tags' % job_id)
            ret = self.get('%s/extract/losses_by_site' % job_id)
            ret = self.post('%s/remove' % job_id)
            if ret.status_code != 200:
                raise RuntimeError(
                    'Unable to remove job %s:\n%s' % (job_id, ret))

    def test_run_by_usgs_id_then_remove_calc(self):
        data = dict(usgs_id='us6000jllz',
                    approach='use_shakemap_from_usgs',
                    lon=37.0143, lat=37.2256, dep=10.0, mag=7.8,
                    rake=0.0, dip=90, strike=0,
                    time_event='night',
                    maximum_distance=100,
                    mosaic_model='MIE',
                    trt='Active Shallow Crust', truncation_level=3,
                    number_of_ground_motion_fields=2,
                    asset_hazard_distance=15, ses_seed=42,
                    local_timestamp='2023-02-06 04:17:34+03:00',
                    maximum_distance_stations='')
        self.impact_run_then_remove(data)

    # check that the URL 'run' cannot be accessed in ARISTOTLE mode
    def test_can_not_run_normal_calc(self):
        with open(os.path.join(self.datadir, 'archive_ok.zip'), 'rb') as a:
            resp = self.post('run', dict(archive=a))
        self.assertEqual(resp.status_code, 404, resp)

    # check that the URL 'validate_zip' cannot be accessed in ARISTOTLE mode
    def test_can_not_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', dict(archive=a))
        self.assertEqual(resp.status_code, 404, resp)


class ShareJobTestCase(django.test.TestCase):

    @classmethod
    def post(cls, path, data=None):
        return cls.c.post('/v1/calc/%s' % path, data)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user0, cls.password0 = get_or_create_user(0)  # level 0
        cls.user1, cls.password1 = get_or_create_user(1)  # level 1
        cls.user2, cls.password2 = get_or_create_user(2)  # level 2
        cls.c = Client()

    @classmethod
    def tearDownClass(cls):
        cls.user0.delete()
        cls.user1.delete()
        cls.user2.delete()
        super().tearDownClass()

    def remove_calc(self, calc_id):
        ret = self.post('%s/remove' % calc_id)
        if ret.status_code != 200:
            raise RuntimeError(
                'Unable to remove job %s:\n%s' % (calc_id, ret))

    def test_share_complete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_share_complete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.json(),
                         {'success': f'The status of calculation {job.calc_id} was'
                                     f' changed from "complete" to "shared"'})
        self.remove_calc(job.calc_id)

    def test_share_incomplete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_share_incomplete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'created', 'is_running': 1}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.json(),
                         {'error': f'Can not share calculation {job.calc_id} from'
                                   f' status "created"'})
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'failed', 'is_running': 0}, job.calc_id)
        self.remove_calc(job.calc_id)

    def test_share_shared_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_share_shared_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'shared', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.json(),
                         {'success': f'Calculation {job.calc_id} was already shared'})
        self.remove_calc(job.calc_id)

    def test_unshare_complete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_complete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.json(),
                         {'success': f'Calculation {job.calc_id} was already complete'})
        self.remove_calc(job.calc_id)

    def test_unshare_incomplete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_incomplete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'created', 'is_running': 1}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.json(),
                         {'error': f'Can not force the status of calculation'
                                   f' {job.calc_id} from "created" to "complete"'})
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'failed', 'is_running': 0}, job.calc_id)
        self.remove_calc(job.calc_id)

    def test_unshare_shared_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'shared', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.json(),
                         {'success': f'The status of calculation {job.calc_id} was'
                                     f' changed from "shared" to "complete"'})
        self.remove_calc(job.calc_id)

    def test_share_or_unshare_user_level_below_2(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_job_levels_below_2')
        [job] = create_jobs([job_dic], user_name=self.user1.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job.calc_id)

        self.c.login(username=self.user1.username, password=self.password1)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.status_code, 403)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.status_code, 403)

        self.c.login(username=self.user0.username, password=self.password0)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.status_code, 403)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.status_code, 403)

        self.c.login(username=self.user1.username, password=self.password1)
        self.remove_calc(job.calc_id)
