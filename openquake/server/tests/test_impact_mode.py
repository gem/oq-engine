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

import time
import os
import sys
import json
import tempfile
import numpy
import pandas
from io import BytesIO

import django
from django.apps import apps
from django.test import Client, override_settings
from django.conf import settings
from django.http import HttpResponseNotFound
from openquake.baselib import config
from openquake.baselib.general import gettemp
from openquake.commonlib.logs import dbcmd
from openquake.commonlib.readinput import loadnpz
from openquake.server.tests.views_test import get_or_create_user

CALC_RUN_TIMEOUT = 60


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


def check_email(job_id, expected_error):
    app_msgs_dir = os.path.join(
        config.directory.custom_tmp or tempfile.gettempdir(),
        'app-messages')
    # NOTE: we should use the overridden EMAIL_FILE_PATH,
    #       so email_dir would contain only the files
    #       created to notify about the jobs created in
    #       the test
    email_content = get_email_content(app_msgs_dir, f'Job {job_id} ')
    if expected_error:
        assert 'failed' in email_content
    else:
        assert 'finished correctly' in email_content
    email_from = settings.EMAIL_HOST_USER
    email_to = settings.EMAIL_SUPPORT
    assert f'From: {email_from}' in email_content
    assert 'To: django-test-user-level-1@email.test' in email_content
    assert f'Reply-To: {email_to}' in email_content
    if expected_error:
        assert expected_error in email_content
    else:
        assert 'Please find the results here:' in email_content
        assert f'engine/{job_id}/outputs_impact' in email_content


class ImpactModeTestCase(django.test.TestCase):
    datadir = os.path.join(os.path.dirname(__file__), 'data')

    # general utilities

    @classmethod
    def post(cls, path, prefix='/v1/calc/', data=None):
        return cls.c.post(f'{prefix}{path}', data)

    @classmethod
    def get(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data, HTTP_HOST='testserver')
        if not resp.status_code == 200:
            raise RuntimeError(resp.content.decode('utf8'))
        return resp

    @classmethod
    def get_json(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data, HTTP_HOST='testserver')
        if hasattr(resp, 'content'):
            assert resp.content, (
                'No content from http://localhost:8800/v1/calc/%s (params: %s)'
                % (path, data))
            js = resp.content.decode('utf8')
        else:
            js = bytes(loadnpz(resp.streaming_content)['json'])
        if not js:
            print(f'Empty json from {path}')
            return {}
        try:
            return json.loads(js)
        except Exception:
            print('Invalid JSON, see %s' % gettemp(resp.content, remove=False),
                  file=sys.stderr)
            return {}

    @classmethod
    def wait(cls, job_id):
        # wait until the calculation stops
        for i in range(CALC_RUN_TIMEOUT):
            time.sleep(1)  # sec
            # NOTE: is_running is True both for 'submitted' and 'executing'
            #       job status
            job_dic = cls.get_json(f'{job_id}/status')
            if job_dic['status'] in ['complete', 'failed', 'shared',
                                     'aborted', 'deleted']:
                # NOTE: some more time is needed in order to wait for the
                # callback to finish and produce the email notification
                time.sleep(2)
                return job_dic

    @classmethod
    def get_response_content(cls, response):
        """
        Extract content from either HttpResponse or FileResponse
        NOTE: the django test client works differently with respect to requests.Session
        """
        if hasattr(response, 'content'):
            return response.content
        else:
            return b''.join(response.streaming_content)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group = apps.get_model('auth', 'Group')
        Permission = apps.get_model('auth', 'Permission')
        dbcmd('reset_is_running')  # cleanup stuck calculations
        cls.job_ids = []
        env = os.environ.copy()
        env['OQ_DISTRIBUTE'] = 'no'
        cls.user1, cls.password1 = get_or_create_user(1)  # level 1
        cls.users_who_can_view_exposure, _ = Group.objects.get_or_create(
            name='Users who can view the exposure')
        perm = Permission.objects.get(codename='can_view_exposure')
        cls.users_who_can_view_exposure.permissions.add(perm)
        cls.c = Client()
        cls.c.login(username=cls.user1.username, password=cls.password1)
        cls.maxDiff = None

    @classmethod
    def tearDownClass(cls):
        cls.user1.delete()
        super().tearDownClass()

    def impact_run_then_remove(
            self, endpoint, data, expected_error=None):
        with tempfile.TemporaryDirectory() as email_dir:
            with override_settings(EMAIL_FILE_PATH=email_dir):  # FIXME: it is ignored!
                resp = self.post(endpoint, data=data)
                if resp.status_code != 200:
                    content = json.loads(resp.content)
                    print(content, file=sys.stderr)
                    self.assertIsNotNone(expected_error)
                    self.assertIn(expected_error, content['error_msg'])
                    return
                # the job is supposed to start
                # and, if expected_error is not None, to fail afterwards
                try:
                    [job_id] = json.loads(resp.content.decode('utf8'))
                except Exception:
                    raise ValueError(
                        b'Invalid JSON response: %r' % resp.content)
                job_dic = self.wait(job_id)
                tb = self.get_json('%s/traceback' % job_id)
                if job_dic is None:
                    raise TimeoutError()
                elif job_dic['status'] == 'failed':
                    if expected_error:
                        if not tb:
                            raise Exception('Empty traceback')
                        self.assertIn(expected_error, '\n'.join(tb))
                    else:
                        raise Exception('\n'.join(tb))
                check_email(job_id, expected_error)
                if job_dic['status'] == 'failed':
                    return
                try:
                    results = self.get_json('%s/result/list' % job_id)
                except AssertionError as exc:
                    print(f'Results for job {job_id} not found yet:')
                    print(exc)
                if isinstance(results, HttpResponseNotFound):
                    print(f'Results for job {job_id} not found yet...')
                self.assertGreater(
                    len(results), 0,
                    'The job produced no outputs!')
        # Check that the Django views to visualize simplified and advanced outputs
        # pages do not raise any exceptions
        self.c.get(f'/engine/{job_id}/outputs')
        self.c.get(f'/engine/{job_id}/outputs_impact')
        # NOTE: the get_json utility decodes the json and returns a dict
        ret = self.get_json('%s/impact' % job_id)
        self.assertEqual(list(ret), ['loss_type_descriptions', 'impact'])
        ret = self.get_json('%s/exposure_by_mmi' % job_id)
        self.assertEqual(list(ret), ['column_descriptions', 'exposure_by_mmi'])
        ret = self.get('%s/download_aggrisk' % job_id)
        ret = self.get('%s/extract_html_table/aggrisk_tags' % job_id)
        ret = self.get('%s/extract_html_table/mmi_tags' % job_id)
        ret = self.get('%s/extract/losses_by_asset' % job_id)
        content = self.get_response_content(ret)
        losses_by_asset_mean = numpy.load(BytesIO(content))['rlz-000']
        dic = {key: losses_by_asset_mean[key]
               for key in losses_by_asset_mean.dtype.names}
        pandas.DataFrame(dic)
        ret = self.get('%s/extract/losses_by_site' % job_id)
        content = self.get_response_content(ret)
        losses_by_site = numpy.load(BytesIO(content))
        pandas.DataFrame.from_dict(
            {item: losses_by_site[item] for item in losses_by_site})
        ret = self.get('%s/extract/losses_by_location' % job_id)
        content = self.get_response_content(ret)
        losses_by_location = numpy.load(BytesIO(content))
        pandas.DataFrame.from_dict(
            {item: losses_by_location[item] for item in losses_by_location})
        ret = self.get('%s/extract/exposure_by_location' % job_id)
        content = self.get_response_content(ret)
        exposure_by_location = numpy.load(BytesIO(content))
        pandas.DataFrame.from_dict(
            {item: exposure_by_location[item] for item in exposure_by_location})

        # check that users can download hidden outputs only if their level is at
        # least 2 or if they have the can_view_exposure permission

        # level 1 users without the can_view_exposure permission can't see the exposure
        ret = self.get('%s/results' % job_id)
        results = json.loads(ret.content.decode('utf8'))
        exposure_urls = [res['url'] for res in results if res['type'] == 'exposure']
        self.assertEqual(len(exposure_urls), 0)
        # ...and without can_view_exposure they can't extract the assetcol
        ret = self.c.get(f'/v1/calc/{job_id}/extract/assetcol')
        self.assertEqual(ret.status_code, 403)

        # level 1 users with the can_view_exposure permission can see the exposure
        self.user1.groups.add(self.users_who_can_view_exposure)
        ret = self.get('%s/results' % job_id)
        results = json.loads(ret.content.decode('utf8'))
        [download_url] = [res['url'] for res in results if res['type'] == 'exposure']
        download_exposure_url = download_url
        ret = self.c.get(download_url)
        self.assertEqual(ret.status_code, 200)
        # ...and with can_view_exposure they can extract the assetcol
        ret = self.c.get(f'/v1/calc/{job_id}/extract/assetcol')
        self.assertEqual(ret.status_code, 200)

        # level 2 users without the show_exposure group can see the exposure
        self.user1.groups.remove(self.users_who_can_view_exposure)
        self.user1.profile.level = 2
        self.user1.profile.save()
        self.user1.save()
        # try to download the exposure, knowing the corresponding url
        ret = self.c.get(download_exposure_url)
        self.assertEqual(ret.status_code, 200)
        # check if the exposure is shown in the list of downloadable results
        ret = self.get('%s/results' % job_id)
        results = json.loads(ret.content.decode('utf8'))
        [exposure_url] = [res['url'] for res in results if res['type'] == 'exposure']
        ret = self.c.get(exposure_url)
        self.assertEqual(ret.status_code, 200)
        # ...and even without can_view_exposure they can extract the assetcol
        ret = self.c.get(f'/v1/calc/{job_id}/extract/assetcol')
        self.assertEqual(ret.status_code, 200)

        # level 0 users without the can_view_exposure permission can't see the exposure
        self.user1.profile.level = 0
        self.user1.profile.save()
        self.user1.save()
        # try to download the exposure, knowing the corresponding url
        ret = self.c.get(download_exposure_url)
        self.assertEqual(ret.status_code, 403)
        # check if the exposure is shown in the list of downloadable results
        ret = self.get('%s/results' % job_id)
        results = json.loads(ret.content.decode('utf8'))
        exposure_urls = [res['url'] for res in results if res['type'] == 'exposure']
        self.assertEqual(len(exposure_urls), 0)
        # ...and without can_view_exposure they can't extract the assetcol
        ret = self.c.get(f'/v1/calc/{job_id}/extract/assetcol')
        self.assertEqual(ret.status_code, 403)

        # level 1 users without the can_view_exposure permission can't see the exposure
        self.user1.profile.level = 1
        self.user1.profile.save()
        self.user1.save()
        # try to download the exposure, knowing the corresponding url
        ret = self.c.get(download_exposure_url)
        self.assertEqual(ret.status_code, 403)
        # check if the exposure is shown in the list of downloadable results
        ret = self.get('%s/results' % job_id)
        results = json.loads(ret.content.decode('utf8'))
        exposure_urls = [res['url'] for res in results if res['type'] == 'exposure']
        self.assertEqual(len(exposure_urls), 0)
        # ...and without can_view_exposure they can't extract the assetcol
        ret = self.c.get(f'/v1/calc/{job_id}/extract/assetcol')
        self.assertEqual(ret.status_code, 403)

        ret = self.post('%s/remove' % job_id)
        if ret.status_code != 200:
            raise RuntimeError(
                'Unable to remove job %s:\n%s' % (job_id, ret))

    def test_run_by_usgs_id_then_remove_calc_failure(self):
        shakemap_version = 'urn:usgs-product:us:shakemap:us6000jllz:1675824364065'
        data = dict(usgs_id='us6000jllz',
                    approach='use_shakemap_from_usgs',
                    shakemap_version=shakemap_version,
                    lon=37.60602, lat=37.6446,
                    dep=9.0, mag=7.8,
                    rake=0.0, dip=90, strike=51.88112,
                    time_event='day',
                    maximum_distance=100,
                    mosaic_model='ARB',
                    trt='TECTONIC_REGION_1',
                    truncation_level=3,
                    number_of_ground_motion_fields=2,
                    asset_hazard_distance=15, ses_seed=42,
                    maximum_distance_stations='', msr='WC1994',
                    description=('us6000jllz: M 7.8 - Pazarcik earthquake,'
                                 ' Kahramanmaras earthquake sequence'))
        expected_error = 'IMT SA(0.6) is required'
        self.impact_run_then_remove('impact_run', data, expected_error)

    def test_run_by_usgs_id_then_remove_calc_success(self):
        # NOTE: this case tests the extractor for losses_by_site in the case discarding
        # sites that do not correspond to any assets, e.g. for the JRC script that uses
        # shakemap_id = 'urn:usgs-product:us:shakemap:us6000phrk:1735953132990'
        # {
        #     "id": "urn:usgs-product:us:shakemap:us6000phrk:1736792435199",
        #     "number": "5",
        #     "utc_date_time": "2025-01-13 18:20:35"
        # },
        usgs_id = 'us6000phrk'
        resp = self.post('impact_get_shakemap_versions',
                         prefix='/v1/', data={'usgs_id': usgs_id})
        js = json.loads(resp.content.decode('utf8'))
        [shakemap_id] = [version['id'] for version in js['shakemap_versions']
                         if version['number'] == '5']
        data = dict(usgs_id=usgs_id, shakemap_version=shakemap_id)
        self.impact_run_then_remove('impact_run_with_shakemap', data)

    # check that the URL 'run' cannot be accessed in IMPACT mode
    def test_can_not_run_normal_calc(self):
        with open(os.path.join(self.datadir, 'archive_ok.zip'), 'rb') as a:
            resp = self.post('run', data=dict(archive=a))
        self.assertEqual(resp.status_code, 404, resp)

    # check that the URL 'validate_zip' cannot be accessed in IMPACT mode
    def test_can_not_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', data=dict(archive=a))
        self.assertEqual(resp.status_code, 404, resp)

    def test_get_impact_form_defaults(self):
        resp = self.c.get('/v1/get_impact_form_defaults')
        resp = json.loads(resp.content.decode('utf8'))
        expected_list = ['usgs_id', 'rupture_from_usgs', 'rupture_file', 'lon',
                         'lat', 'dep', 'mag', 'aspect_ratio', 'rake',
                         'local_timestamp', 'time_event', 'dip', 'strike',
                         'maximum_distance', 'truncation_level',
                         'number_of_ground_motion_fields', 'asset_hazard_distance',
                         'ses_seed', 'station_data_file_from_usgs',
                         'station_data_file', 'maximum_distance_stations',
                         'msr', 'rupture_was_loaded', 'rupture_file_input',
                         'station_data_file_input', 'station_data_file_loaded',
                         'description']
        self.assertEqual(list(resp), expected_list)

    def test_impact_get_shakemap_versions(self):
        resp = self.c.post('/v1/impact_get_shakemap_versions',
                           data={'usgs_id': 'us6000jllz'})
        resp = json.loads(resp.content.decode('utf8'))
        self.assertIn('shakemap_versions', resp)
        self.assertIn('usgs_preferred_version', resp)
        self.assertIsNone(resp['shakemap_versions_issue'])

    def test_impact_get_nodal_planes_and_info(self):
        resp = self.c.post('/v1/impact_get_nodal_planes_and_info',
                           data={'usgs_id': 'us6000jllz'})
        resp = json.loads(resp.content.decode('utf8'))
        self.assertIn('nodal_planes', resp)
        self.assertIsNone(resp['nodal_planes_issue'])
        self.assertIn('info', resp)

    def test_impact_get_stations_from_usgs(self):
        shakemap_version = 'urn:usgs-product:us:shakemap:us6000jllz:1756920117251'
        resp = self.c.post('/v1/impact_get_stations_from_usgs',
                           data={'usgs_id': 'us6000jllz',
                                 'shakemap_version': shakemap_version})
        resp = json.loads(resp.content.decode('utf8'))
        self.assertIn('station_data_file', resp)
        self.assertIn('n_stations', resp)
        self.assertIsNone(resp['station_data_issue'])
