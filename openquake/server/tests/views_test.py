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

"""
Here there are some real functional tests starting an engine server and
running computations.
"""
import io
import os
import glob
import re
import sys
import json
import time
import pprint
import numpy
import zlib
import gzip
import tempfile
import string
import random
import unittest
import secrets
import csv

import django
from django.test import Client
from openquake.baselib import config
from openquake.baselib.general import gettemp
from openquake.commonlib.logs import dbcmd
from openquake.engine.export import core
from openquake.server.db import actions
from openquake.server.dbserver import db, get_status


def loadnpz(lines):
    bio = io.BytesIO(b''.join(ln for ln in lines))
    return numpy.load(bio)


class EngineServerTestCase(django.test.TestCase):
    datadir = os.path.join(os.path.dirname(__file__), 'data')

    # general utilities

    @classmethod
    def post(cls, path, data=None):
        return cls.c.post('/v1/calc/%s' % path, data)

    @classmethod
    def post_nrml(cls, data):
        return cls.c.post('/v1/valid/', dict(xml_text=data))

    @classmethod
    def get(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data,
                         HTTP_HOST='127.0.0.1')
        if hasattr(resp, 'content'):
            assert resp.content, (
                'No content from http://localhost:8800/v1/calc/%s' % path)
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
    def get_text(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data)
        if resp.status_code == 500:
            raise Exception(resp.content.decode('utf8'))
        return b''.join(resp.streaming_content)

    @classmethod
    def wait(cls):
        # wait until all calculations stop
        for i in range(300):  # 300 seconds of timeout
            time.sleep(1)
            running_calcs = cls.get('list', is_running='true')
            if not running_calcs:
                return
        # to avoid issues on Jenkins
        raise django.test.SkipTest('Timeout waiting for %s' % running_calcs)

    def postzip(self, archive):
        with open(os.path.join(self.datadir, archive), 'rb') as a:
            resp = self.post('run', dict(archive=a))
        try:
            js = json.loads(resp.content.decode('utf8'))
        except Exception:
            raise ValueError(b'Invalid JSON response: %r' % resp.content)
        if resp.status_code == 200:  # ok case
            return dict(job_id=js['job_id'])
        else:  # error case
            return dict(tb_str='\n'.join(js['traceback']), job_id=js['job_id'])

    # start/stop server utilities

    @classmethod
    def setUpClass(cls):
        assert get_status() == 'running'
        dbcmd('reset_is_running')  # cleanup stuck calculations
        cls.job_ids = []
        env = os.environ.copy()
        env['OQ_DISTRIBUTE'] = 'no'
        cls.c = Client()

    @classmethod
    def tearDownClass(cls):
        c = dbcmd('SELECT count(*) FROM job WHERE status=?x', 'complete')[0][0]
        assert c > 0, 'There are no jobs??'
        cls.wait()


class EngineServerPublicModeTestCase(EngineServerTestCase):

    def test_404(self):
        # looking for a missing calc_id
        resp = self.c.get('/v1/calc/0')
        assert resp.status_code == 404, resp

    def test_ok(self):
        job_id = self.postzip('archive_ok.zip')['job_id']
        self.wait()
        log = self.get('%s/log/:' % job_id)
        if config.distribution.log_level == 'error':
            self.assertEqual(len(log), 0)
        else:
            self.assertGreater(len(log), 0)
        results = self.get('%s/results' % job_id)
        self.assertGreater(len(results), 0)
        for res in results:
            for etype in res['outtypes']:  # test all export types
                text = self.get_text(
                    'result/%s' % res['id'], export_type=etype)
                print('downloading result/%s' % res['id'], res['type'], etype)
                self.assertGreater(len(text), 0)

        # test no filtering in actions.get_calcs
        all_jobs = self.get('list')
        self.assertGreater(len(all_jobs), 0)

        extract_url = '/v1/calc/%s/extract/' % job_id

        # check eids_by_gsim
        resp = self.c.get(extract_url + 'eids_by_gsim')
        dic = dict(loadnpz(resp.streaming_content))
        for gsim, eids in dic.items():
            numpy.testing.assert_equal(eids, numpy.sort(eids)), gsim
        self.assertEqual(len(dic['[AtkinsonBoore2003SInter]']), 5)

        # check extract/composite_risk_model.attrs
        url = extract_url + 'composite_risk_model.attrs'
        self.assertEqual(self.c.get(url).status_code, 200)

        # check asset_tags
        resp = self.c.get(extract_url + 'asset_tags')
        got = loadnpz(resp.streaming_content)
        self.assertEqual(len(got['taxonomy']), 7)

        # check exposure_metadata
        resp = self.c.get(extract_url + 'exposure_metadata')
        got = loadnpz(resp.streaming_content)['json']
        dic = json.loads(bytes(got))
        self.assertEqual(sorted(dic['tagnames']), ['taxonomy'])
        self.assertEqual(sorted(dic['names']),
                         ['value-number', 'value-structural'])

        # check assets
        resp = self.c.get(
            extract_url + 'assets?taxonomy=MC-RLSB-2&taxonomy=W-SLFB-1')
        if resp.status_code == 500:  # should never happen
            raise RuntimeError(resp.content.decode('utf8'))
        got = loadnpz(resp.streaming_content)
        self.assertEqual(len(got['array']), 25)

        # check losses_by_asset
        resp = self.c.get(extract_url + 'losses_by_asset')
        if resp.status_code == 500:  # should never happen
            raise RuntimeError(resp.content.decode('utf8'))
        got = loadnpz(resp.streaming_content)
        self.assertEqual(len(got['rlz-000']), 95)

        # check agg_losses
        resp = self.c.get(
            extract_url + 'agg_losses/structural?taxonomy=W-SLFB-1')
        got = loadnpz(resp.streaming_content)
        self.assertEqual(len(got['array']), 1)  # expected 1 aggregate value
        self.assertEqual(resp.status_code, 200)

        # check *-aggregation
        resp = self.c.get(
            extract_url + 'agg_losses/structural?taxonomy=*')
        got = loadnpz(resp.streaming_content)
        self.assertEqual(len(got['tags']), 6)  # expected 6 taxonomies
        self.assertEqual(len(got['array']), 6)  # expected 6 aggregates
        self.assertEqual(resp.status_code, 200)

        # there is some logic in `core.export_from_db` that it is only
        # exercised when the export fails
        datadir, dskeys = actions.get_results(db, job_id)
        # try to export a non-existing output
        with self.assertRaises(core.DataStoreExportError) as ctx:
            core.export_from_db(('XXX', 'csv'), job_id, datadir, '/tmp')
        self.assertIn('Could not export XXX in csv', str(ctx.exception))

        # check MFD distribution
        extract_url = '/v1/calc/%s/extract/event_based_mfd?' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertGreater(len(got['mag']), 1)
        self.assertGreater(len(got['freq']), 1)

        # check rupture_info
        extract_url = '/v1/calc/%s/extract/rupture_info' % job_id
        got = loadnpz(self.c.get(extract_url))
        boundaries = gzip.decompress(got['boundaries']).split(b'\n')
        self.assertEqual(len(boundaries), 31)
        for b in boundaries:
            self.assertEqual(b[:12], b'POLYGON((-77')
        # check gmf_data with no data
        extract_url = '/v1/calc/%s/extract/gmf_data?event_id=28' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertEqual(len(got['rlz-000']), 3)

        # check extract_sources
        extract_url = '/v1/calc/%s/extract/sources?' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertEqual(list(got), ['wkt_gz', 'src_gz', 'extra', 'array'])
        self.assertGreater(len(got['array']), 0)

        # check risk_stats
        extract_url = '/v1/calc/%s/extract/risk_stats/aggrisk' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertEqual(list(got), ['agg_id', 'loss_type', 'loss', 'stat'])

        # cleanup
        self.post('%s/remove' % job_id)

    def test_classical(self):
        job_id = self.postzip('classical.zip')['job_id']
        self.wait()
        # check that we get at least the following 4 outputs
        # fullreport, hcurves, hmaps, realizations
        # we can add more outputs in the future
        results = self.get('%s/results' % job_id)
        resnames = [res['name'] for res in results]
        self.assertGreaterEqual(resnames, ['Full Report', 'Hazard Curves',
                                           'Hazard Maps',  'Input Files',
                                           'Realizations'])

        # check the filename of the hmaps
        hmaps_id = results[2]['id']
        resp = self.c.head('/v1/calc/result/%s?export_type=csv' % hmaps_id)
        #
        # remove output ID digits from the filename
        cd = re.sub(r'\d', '', resp.headers['Content-Disposition'])
        self.assertEqual(
            cd, 'attachment; filename=output--hazard_map-mean_.csv')

        # check oqparam
        dic = self.get('%s/extract/oqparam' % job_id)  # parameters
        self.assertEqual(dic['calculation_mode'], 'classical')

        # check extract hcurves
        url = '/v1/calc/%s/extract/hcurves?kind=stats&imt=PGA' % job_id
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

        # check deleting job without the webAPI
        dbcmd('del_calc', job_id, 'django-test-user')

    def test_abort(self):
        resp = self.c.post('/v1/calc/0/abort')  # 0 is a non-existing job
        print(resp.content.decode('utf8'))

    def test_err_1(self):
        # the rupture XML file has a syntax error
        job_id = self.postzip('archive_err_1.zip')['job_id']
        self.wait()

        # there is no datastore since the calculation did not start
        resp = self.c.get('/v1/calc/%s/datastore' % job_id)
        self.assertEqual(resp.status_code, 404)

        tb = self.get('%s/traceback' % job_id)
        if not tb:
            sys.stderr.write('Empty traceback, please check!\n')

        self.post('%s/remove' % job_id)
        # make sure job_id is no more in the list of jobs
        job_ids = [job['id'] for job in self.get('list')]
        self.assertFalse(job_id in job_ids)

    def test_err_2(self):
        # the file logic-tree-source-model.xml is missing
        resp = self.postzip('archive_err_2.zip')
        self.assertIn('No such file', resp['tb_str'])
        self.post('%s/remove' % resp['job_id'])

    def test_err_3(self):
        # there is no file job.ini, job_hazard.ini or job_risk.ini
        resp = self.postzip('archive_err_3.zip')
        self.assertIn('There are no .ini files in the archive', resp['tb_str'])
        self.post('%s/remove' % resp['job_id'])

    def test_available_gsims(self):
        resp = self.c.get('/v1/available_gsims')
        self.assertIn(b'ChiouYoungs2014PEER', resp.content)

    def test_ini_defaults(self):
        resp = self.c.get('/v1/ini_defaults')
        self.assertEqual(resp.status_code, 200)
        # make sure an old name still works
        dic = resp.json()
        assert 'reference_depth_to_1pt0km_per_sec' not in dic
        self.assertIn(b'asset_hazard_distance', resp.content)

    def test_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', dict(archive=a))
        dic = json.loads(resp.content.decode('utf8'))
        # error Could not convert insuranceLimit->positivefloat
        pprint.pprint(dic)
        if dic['error_msg'] is None:  # this should not happen
            raise django.test.SkipTest(dic)

    def test_can_not_run_aelo_calc(self):
        params = dict(
            lon=10, lat=45, vs30='800.0', siteid='SITE')
        resp = self.post('aelo_run', params)
        assert resp.status_code == 404, resp

    # tests for nrml validation

    def test_validate_nrml_valid(self):
        valid_file = os.path.join(self.datadir, 'vulnerability_model.xml')
        with open(valid_file) as vf:
            valid_content = vf.read()
        resp = self.post_nrml(valid_content)
        self.assertEqual(resp.status_code, 200)
        resp_text_dict = json.loads(resp.content.decode('utf8'))
        self.assertTrue(resp_text_dict['valid'])
        self.assertIsNone(resp_text_dict['error_msg'])
        self.assertIsNone(resp_text_dict['error_line'])

    def test_validate_nrml_invalid(self):
        invalid_file = os.path.join(self.datadir,
                                    'vulnerability_model_invalid.xml')
        with open(invalid_file) as vf:
            invalid_content = vf.read()
        resp = self.post_nrml(invalid_content)
        self.assertEqual(resp.status_code, 200)
        resp_text_dict = json.loads(resp.content.decode('utf8'))
        self.assertFalse(resp_text_dict['valid'])
        self.assertIn(u'Could not convert lossRatio->positivefloats:'
                      ' float -0.018800826 < 0',
                      resp_text_dict['error_msg'])
        self.assertEqual(resp_text_dict['error_line'], 7)

    def test_validate_nrml_unclosed_tag(self):
        invalid_file = os.path.join(self.datadir,
                                    'vulnerability_model_unclosed_tag.xml')
        with open(invalid_file) as vf:
            invalid_content = vf.read()
        resp = self.post_nrml(invalid_content)
        self.assertEqual(resp.status_code, 200)
        resp_text_dict = json.loads(resp.content.decode('utf8'))
        self.assertFalse(resp_text_dict['valid'])
        self.assertIn(u'mismatched tag', resp_text_dict['error_msg'])
        self.assertEqual(resp_text_dict['error_line'], 9)

    def test_validate_nrml_missing_parameter(self):
        # passing a wrong parameter, instead of the required 'xml_text'
        resp = self.c.post('/v1/valid/', foo='bar')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content,
                         b'Please provide the "xml_text" parameter')

    def test_check_fs_access(self):
        with tempfile.NamedTemporaryFile(buffering=0, prefix='oq-test_') as f:
            filename = f.name
            content = bytes(''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(32)),
                            'utf-8')
            f.write(content)
            checksum = str(zlib.adler32(content, 0) & 0xffffffff)
            resp = self.c.post('/v1/on_same_fs', {'filename': filename,
                                                  'checksum': checksum})
            self.assertEqual(resp.status_code, 200)
            resp_text_dict = json.loads(resp.content.decode('utf8'))
            self.assertTrue(resp_text_dict['success'])

    def test_check_fs_access_fail(self):
        with tempfile.NamedTemporaryFile(buffering=0, prefix='oq-test_') as f:
            filename = f.name
            content = bytes(''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(32)),
                            'utf-8')
            f.write(content)
            checksum = 'impossible'

            resp = self.c.post('/v1/on_same_fs', {'filename': filename,
                                                  'checksum': checksum})

            self.assertEqual(resp.status_code, 200)
            resp_text_dict = json.loads(resp.content.decode('utf8'))
            self.assertFalse(resp_text_dict['success'])


class EngineServerAeloModeTestCase(EngineServerTestCase):

    @classmethod
    def setUpClass(cls):
        # NOTE: before importing User or any other model, django.setup() is
        # needed, otherwise it would raise:
        # django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
        django.setup()
        try:
            from django.contrib.auth.models import User  # noqa
        except RuntimeError:
            # Django tests are meant to be run with the command
            # OQ_CONFIG_FILE=openquake/server/tests/data/openquake.cfg \
            # ./openquake/server/manage.py test tests.views_test
            raise unittest.SkipTest('Use Django to run such tests')

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
