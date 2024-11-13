# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2024 GEM Foundation
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
import logging
import io
import numpy
import pathlib

import django
# from django.apps import apps
from django.test import Client, override_settings
from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.utils.datastructures import MultiValueDict
from django.http import HttpResponseNotFound
from openquake.commonlib.logs import dbcmd
from openquake.baselib.general import gettemp

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openquake.server.settings')

# NOTE: before importing User or any other model, django.setup() is needed,
#       otherwise it would raise:
#       django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.


# NOTE: Overriding the APPLICATION_MODE is tricky, because settings are first loaded
# (also importing the local_settings and producing the cascade consequences), then it
# becomes late for overriding. Therefore we need the local settings to contain the
# correct application mode in advance, or we need to define the OQ_APPLICATION_MODE
# before running tests.
ARISTOTLE_SETTINGS = {
    'EMAIL_HOST_USER': 'aristotlenoreply@openquake.org',
    'EMAIL_SUPPORT': 'aristotlesupport@openquake.org',
}


django.setup()
try:
    from django.contrib.auth.models import User  # noqa
except RuntimeError:
    # Django tests are meant to be run with the command
    # OQ_CONFIG_FILE=openquake/server/tests/data/openquake.cfg \
    # ./openquake/server/manage.py test tests.views_test
    raise unittest.SkipTest('Use Django to run such tests')


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


class EngineServerTestCase(django.test.TestCase):
    datadir = os.path.join(os.path.dirname(__file__), 'data')

    # general utilities

    @classmethod
    def post(cls, path, data=None):
        return cls.c.post('/v1/calc/%s' % path, data)

    @classmethod
    def get(cls, path, **data):
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
        for i in range(300):  # 300 seconds of timeout
            time.sleep(1)
            # NOTE: is_running is True both for 'submitted' and 'executing'
            #       job status
            running_calcs = cls.get('list', is_running='true')
            if not running_calcs:
                # NOTE: some more time is needed in order to wait for the
                # callback to finish and produce the email notification
                time.sleep(2)
                return


@override_settings(**ARISTOTLE_SETTINGS)
class EngineServerAristotleModeTestCase(EngineServerTestCase):

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
        cls.maxDiff = None

    @classmethod
    def tearDownClass(cls):
        try:
            cls.wait()
        finally:
            cls.user.delete()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.assertEqual(settings.APPLICATION_MODE, 'ARISTOTLE',
                         'You may need to define OQ_APPLICATION_MODE=ARISTOTLE')

    def aristotle_run_then_remove(
            self, data, failure_reason=None):
        with tempfile.TemporaryDirectory() as email_dir:
            email_backend = 'django.core.mail.backends.filebased.EmailBackend'
            with override_settings(
                    EMAIL_FILE_PATH=email_dir,  # FIXME: this is ignored!
                    EMAIL_BACKEND=email_backend):
                resp = self.post('aristotle_run', data)
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
                app_msgs_dir = os.path.join(tempfile.gettempdir(),
                                            'app-messages')
                for job_id in js:
                    if failure_reason:
                        tb = self.get('%s/traceback' % job_id)
                        if not tb:
                            sys.stderr.write(
                                'Empty traceback, please check!\n')
                        self.assertIn(failure_reason, '\n'.join(tb))
                    # NOTE: we should use the overridden EMAIL_FILE_PATH,
                    #       so email_dir would contain only the files
                    #       created to notify about the jobs created in
                    #       the test
                    for i in range(300):  # 300 seconds of timeout
                        try:
                            results = self.get('%s/result/list' % job_id)
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
                    for i in range(300):  # 300 seconds of timeout
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
                    self.assertIn('To: django-test-user@email.test',
                                  email_content)
                    self.assertIn(f'Reply-To: {email_to}', email_content)
                    if failure_reason:
                        self.assertIn(failure_reason, email_content)
                    else:
                        self.assertIn('Please find the results here:',
                                      email_content)
                        self.assertIn(f'engine/{job_id}/outputs_aristotle',
                                      email_content)
        for job_id in js:
            ret = self.post('%s/remove' % job_id)
            if ret.status_code != 200:
                raise RuntimeError(
                    'Unable to remove job %s:\n%s' % (job_id, ret))

    def test_get_rupture_data_from_shakemap_conversion_error(self):
        usgs_id = 'us6000jllz'
        data = dict(usgs_id=usgs_id)
        ret = self.post('aristotle_get_rupture_data', data=data)
        ret_dict = json.loads(ret.content)
        # NOTE: values returned by the USGS often change with time, so we check
        # only that all the expected keys are present and a subset of stable
        # values
        expected_keys = [
            'is_point_rup', 'local_timestamp', 'time_event', 'lon', 'lat',
            'dep', 'mag', 'rake', 'usgs_id',
            'rupture_file', 'rupture_file_from_usgs', 'error',
            'station_data_file_from_usgs', 'mosaic_models', 'trts']
        self.assertEqual(sorted(ret_dict.keys()), sorted(expected_keys))
        self.assertEqual(ret_dict['rupture_file'], None)
        self.assertEqual(ret_dict['local_timestamp'],
                         '2023-02-06 04:17:34+03:00')
        self.assertEqual(ret_dict['time_event'], 'night')
        self.assertEqual(ret_dict['mosaic_models'], ['ARB', 'MIE'])
        self.assertEqual(ret_dict['trts'], {
            'ARB': ['TECTONIC_REGION_1',
                    'TECTONIC_REGION_2',
                    'TECTONIC_REGION_3',
                    'TECTONIC_REGION_4',
                    'Active Shallow Crust EMME',
                    'Stable Shallow Crust EMME',
                    'Subduction Interface EMME',
                    'Subduction Inslab EMME',
                    'Deep Seismicity EMME'],
            'MIE': ['Active Shallow Crust',
                    'Stable Shallow Crust',
                    'Subduction Interface',
                    'Subduction Inslab',
                    'Deep Seismicity']})
        self.assertIn('Unable to convert the rupture from the USGS format',
                      ret_dict['error'])
        self.assertEqual(ret_dict['is_point_rup'], True)
        self.assertEqual(ret_dict['usgs_id'], 'us6000jllz')

    def test_get_rupture_data_from_shakemap_correctly_converted(self):
        usgs_id = 'us7000n7n8'
        data = dict(usgs_id=usgs_id)
        ret = self.post('aristotle_get_rupture_data', data=data)
        ret_dict = json.loads(ret.content)
        # NOTE: values returned by the USGS often change with time, so we check
        # only that all the expected keys are present and a subset of stable
        # values
        expected_keys = [
            'is_point_rup', 'local_timestamp', 'time_event', 'lon', 'lat',
            'dep', 'mag', 'rake', 'usgs_id',
            'rupture_file', 'rupture_file_from_usgs',
            'station_data_error',
            'station_data_file_from_usgs', 'trts', 'mosaic_models', 'trt']
        self.assertEqual(sorted(ret_dict.keys()), sorted(expected_keys))
        rupfile = ret_dict['rupture_file']
        self.assertTrue(
            pathlib.Path(rupfile).resolve().is_file(),
            f'Rupture file {rupfile} does not exist')
        self.assertEqual(ret_dict['rupture_file'],
                         ret_dict['rupture_file_from_usgs'])
        self.assertEqual(
            ret_dict['station_data_error'],
            'Unable to collect station data for rupture'
            ' identifier "us7000n7n8": stationlist.json was'
            ' downloaded, but it contains no features')
        self.assertEqual(ret_dict['local_timestamp'],
                         '2024-08-18 07:10:26+12:00')
        self.assertEqual(ret_dict['time_event'], 'transit')
        self.assertEqual(ret_dict['mosaic_models'], ['NEA'])
        self.assertEqual(ret_dict['trts'], {
            'NEA': ['Cratonic Crust', 'Stable Continental Crust',
                    'Active Shallow Crust', 'Subduction Interface',
                    'Subduction IntraSlab']})
        self.assertEqual(ret_dict['trt'], 'Active Shallow Crust')
        self.assertEqual(ret_dict['is_point_rup'], False)
        self.assertEqual(ret_dict['usgs_id'], 'us7000n7n8')

    def test_get_point_rupture_data_from_shakemap(self):
        usgs_id = 'us7000n05d'
        data = dict(usgs_id=usgs_id)
        ret = self.post('aristotle_get_rupture_data', data=data)
        ret_dict = json.loads(ret.content)
        # NOTE: values returned by the USGS often change with time, so we check
        # only that all the expected keys are present and a subset of stable
        # values
        expected_keys = [
            'is_point_rup', 'local_timestamp', 'time_event', 'lon', 'lat',
            'dep', 'mag', 'rake', 'usgs_id',
            'rupture_file', 'rupture_file_from_usgs',
            'station_data_file_from_usgs', 'trts',
            'mosaic_models']
        self.assertEqual(sorted(ret_dict.keys()), sorted(expected_keys))
        self.assertEqual(ret_dict['rupture_file'], None)
        self.assertEqual(ret_dict['is_point_rup'], True)
        self.assertEqual(ret_dict['usgs_id'], 'us7000n05d')
        self.assertEqual(ret_dict['mosaic_models'], ['SAM'])

    def test_get_rupture_data_from_finite_fault(self):
        usgs_id = 'us6000jllz'
        data = dict(usgs_id=usgs_id, ignore_shakemap=True)
        ret = self.post('aristotle_get_rupture_data', data=data)
        ret_dict = json.loads(ret.content)
        # NOTE: values returned by the USGS often change with time, so we check
        # only that all the expected keys are present and a subset of stable
        # values
        expected_keys = [
            'is_point_rup', 'local_timestamp', 'time_event', 'lon', 'lat',
            'dep', 'mag', 'rake', 'usgs_id',
            'rupture_file', 'rupture_file_from_usgs',
            'station_data_file_from_usgs', 'trts',
            'mosaic_models']
        self.assertEqual(sorted(ret_dict.keys()), sorted(expected_keys))
        self.assertEqual(ret_dict['rupture_file'], None)
        self.assertEqual(ret_dict['usgs_id'], 'us6000jllz')
        self.assertEqual(ret_dict['mosaic_models'], ['ARB', 'MIE'])
        self.assertEqual(ret_dict['trts'], {
            'ARB': ['TECTONIC_REGION_1',
                    'TECTONIC_REGION_2',
                    'TECTONIC_REGION_3',
                    'TECTONIC_REGION_4',
                    'Active Shallow Crust EMME',
                    'Stable Shallow Crust EMME',
                    'Subduction Interface EMME',
                    'Subduction Inslab EMME',
                    'Deep Seismicity EMME'],
            'MIE': ['Active Shallow Crust',
                    'Stable Shallow Crust',
                    'Subduction Interface',
                    'Subduction Inslab',
                    'Deep Seismicity']})

    def test_run_by_usgs_id_then_remove_calc(self):
        data = dict(usgs_id='us6000jllz',
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
        self.aristotle_run_then_remove(data)

    def get_data(self):
        data = {'usgs_id': ['FromFile'], 'lon': ['84.4'], 'lat': ['27.6'],
                'dep': ['30'], 'mag': ['7'], 'rake': ['90'], 'dip': ['90'],
                'strike': ['0'],
                'time_event': ['day'],
                'maximum_distance': ['100'],
                'trt': ['active shallow crust normal'],
                'truncation_level': ['3'],
                'number_of_ground_motion_fields': ['2'],
                'asset_hazard_distance': ['15'], 'ses_seed': ['42'],
                'local_timestamp': [''],
                'maximum_distance_stations': [''],
                'mosaic_model': ['IND']}  # close to both 'CHN' and 'IND'
        return data

    def get_path_and_content(self, filename):
        curr_file_path = os.path.abspath(__file__)
        folder_path = os.path.dirname(curr_file_path)
        file_path = os.path.join(
            folder_path, 'data', filename)
        with open(file_path, 'rb') as file:
            file_content = file.read()
        return file_path, file_content

    def create_temporary_uploaded_file(self, name, content, content_type):
        temp_file = TemporaryUploadedFile(
            name=name,
            content_type=content_type,
            size=len(content),
            charset='utf-8'
        )
        temp_file.write(content)
        temp_file.seek(0)  # Ensure the file pointer is at the beginning
        return temp_file

    def test_run_by_rupture_model_then_remove_calc(self):
        data = self.get_data()
        rupture_file_path, rupture_file_content = self.get_path_and_content(
            'fault_rupture.xml')
        rupture_uploaded_file = self.create_temporary_uploaded_file(
            rupture_file_path, rupture_file_content, 'text/xml')
        files = MultiValueDict({"rupture_file": rupture_uploaded_file})
        data.update(files)
        self.aristotle_run_then_remove(data)

    def test_run_by_rupture_model_with_stations_then_remove_calc(self):
        data = self.get_data()
        data['maximum_distance_stations'] = '100'
        rupture_file_path, rupture_file_content = self.get_path_and_content(
            'fault_rupture.xml')
        stations_file_path, stations_file_content = self.get_path_and_content(
            'stationlist_seismic.csv')
        rupture_uploaded_file = self.create_temporary_uploaded_file(
            rupture_file_path, rupture_file_content, 'text/xml')
        stations_uploaded_file = self.create_temporary_uploaded_file(
            stations_file_path, stations_file_content, 'text/csv')
        files = MultiValueDict({
            'rupture_file': rupture_uploaded_file,
            'station_data_file': stations_uploaded_file})
        data.update(files)
        self.aristotle_run_then_remove(data)

    @unittest.skip("TODO: to be implemented")
    def test_failing_site_association_error(self):
        pass

    def invalid_input(self, params, expected_error):
        # NOTE: avoiding to print the expected traceback
        logging.disable(logging.CRITICAL)
        resp = self.post('aristotle_run', params)
        logging.disable(logging.NOTSET)
        self.assertEqual(resp.status_code, 400)
        resp_dict = json.loads(resp.content.decode('utf8'))
        print(resp_dict)
        self.assertIn(expected_error, resp_dict['error_msg'])

    @unittest.skip("TODO: to be implemented")
    def test_invalid_latitude(self):
        pass

    @unittest.skip("TODO: to be implemented")
    def test_invalid_longitude(self):
        pass

    def test_can_not_run_normal_calc(self):
        with open(os.path.join(self.datadir, 'archive_ok.zip'), 'rb') as a:
            resp = self.post('run', dict(archive=a))
        self.assertEqual(resp.status_code, 404, resp)

    def test_can_not_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', dict(archive=a))
        self.assertEqual(resp.status_code, 404, resp)
