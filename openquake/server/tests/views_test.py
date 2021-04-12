# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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
import re
import sys
import json
import time
import pprint
import unittest
import numpy
import zlib
import gzip
import tempfile
import string
import random
from django.test import Client
from openquake.baselib.general import gettemp
from openquake.commonlib.logs import dbcmd
from openquake.engine.export import core
from openquake.server.db import actions
from openquake.server.dbserver import db, get_status
from openquake.commands import engine


def loadnpz(lines):
    bio = io.BytesIO(b''.join(ln for ln in lines))
    return numpy.load(bio)


class EngineServerTestCase(unittest.TestCase):
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
        for i in range(30):  # 30 seconds of timeout
            time.sleep(1)
            running_calcs = cls.get('list', is_running='true')
            if not running_calcs:
                return
        # to avoid issues on Jenkins
        raise unittest.SkipTest('Timeout waiting for %s' % running_calcs)

    def postzip(self, archive):
        with open(os.path.join(self.datadir, archive), 'rb') as a:
            resp = self.post('run', dict(archive=a))
        try:
            js = json.loads(resp.content.decode('utf8'))
        except Exception:
            raise ValueError(b'Invalid JSON response: %r' % resp.content)
        if resp.status_code == 200:  # ok case
            return js['job_id']
        else:  # error case
            return ''.join(js)  # traceback string

    # start/stop server utilities

    @classmethod
    def setUpClass(cls):
        assert get_status() == 'running'
        dbcmd('reset_is_running')  # cleanup stuck calculations
        cls.job_ids = []
        env = os.environ.copy()
        env['OQ_DISTRIBUTE'] = 'no'
        # let's impersonate the user openquake, the one running the WebUI:
        # we need to set LOGNAME on Linux and USERNAME on Windows
        env['LOGNAME'] = env['USERNAME'] = 'openquake'
        cls.c = Client()

    @classmethod
    def tearDownClass(cls):
        c = dbcmd('SELECT count(*) FROM job WHERE status=?x', 'complete')[0][0]
        assert c > 0, 'There are no jobs??'
        cls.wait()

    # tests

    def test_404(self):
        # looking for a missing calc_id
        resp = self.c.get('/v1/calc/0')
        assert resp.status_code == 404, resp

    def test_ok(self):
        job_id = self.postzip('archive_ok.zip')
        self.wait()
        log = self.get('%s/log/:' % job_id)
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
        self.assertEqual(len(dic['[AtkinsonBoore2003SInter]']), 7)

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
        self.assertEqual(sorted(dic['names']), ['number', 'value-structural'])

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
        extract_url = '/v1/calc/%s/extract/event_based_mfd?kind=mean' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertGreater(len(got['magnitudes']), 1)
        self.assertGreater(len(got['mean_frequency']), 1)

        # check rupture_info
        extract_url = '/v1/calc/%s/extract/rupture_info' % job_id
        got = loadnpz(self.c.get(extract_url))
        boundaries = gzip.decompress(got['boundaries']).split(b'\n')
        self.assertEqual(len(boundaries), 37)
        self.assertEqual(boundaries[0], b'POLYGON((-77.24583 17.99602, -77.25224 17.91156, -77.33583 17.90593, -77.32871 17.99129, -77.24583 17.99602))')
        self.assertEqual(boundaries[-1], b'POLYGON((-77.10000 18.92000, -77.10575 18.83643, -77.11150 18.75286, -77.11723 18.66929, -77.12297 18.58572, -77.12869 18.50215, -77.13442 18.41858, -77.14014 18.33500, -77.14584 18.25143, -77.15155 18.16786, -77.15725 18.08429, -77.16295 18.00072, -77.16864 17.91714, -77.17432 17.83357, -77.18000 17.75000, -77.26502 17.74263, -77.35004 17.73522, -77.43505 17.72777, -77.52006 17.72029, -77.60506 17.71277, -77.69004 17.70522, -77.77502 17.69763, -77.86000 17.69000, -77.84865 17.78072, -77.83729 17.87144, -77.82591 17.96215, -77.81452 18.05287, -77.80312 18.14359, -77.79172 18.23430, -77.78030 18.32502, -77.76886 18.41573, -77.75742 18.50644, -77.74596 18.59716, -77.73448 18.68787, -77.72300 18.77858, -77.71151 18.86929, -77.70000 18.96000, -77.62498 18.95510, -77.54997 18.95018, -77.47497 18.94523, -77.39996 18.94024, -77.32497 18.93523, -77.24997 18.93018, -77.17499 18.92511, -77.10000 18.92000))')

        # check num_events
        extract_url = '/v1/calc/%s/extract/num_events' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertEqual(got['num_events'], 41)

        # check gmf_data with no data
        extract_url = '/v1/calc/%s/extract/gmf_data?event_id=28' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertEqual(len(got['rlz-000']), 0)

        # check extract_sources
        extract_url = '/v1/calc/%s/extract/sources?' % job_id
        got = loadnpz(self.c.get(extract_url))
        self.assertEqual(list(got), ['wkt_gz', 'src_gz', 'array'])
        self.assertGreater(len(got['array']), 0)

    def test_classical(self):
        job_id = self.postzip('classical.zip')
        self.wait()
        # check that we get at least the following 6 outputs
        # fullreport, input, hcurves, hmaps, realizations, events
        # we can add more outputs in the future
        results = self.get('%s/results' % job_id)
        self.assertGreaterEqual(len(results), 5)

        # check the filename of the hmaps
        hmaps_id = results[2]['id']
        resp = self.c.head('/v1/calc/result/%s?export_type=csv' % hmaps_id)
        # remove output ID digits from the filename
        cd = re.sub(r'\d', '', resp._headers['content-disposition'][1])
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
        engine.del_calculation(job_id, True)

    def test_abort(self):
        resp = self.c.post('/v1/calc/0/abort')  # 0 is a non-existing job
        print(resp.content.decode('utf8'))

    def test_err_1(self):
        # the rupture XML file has a syntax error
        job_id = self.postzip('archive_err_1.zip')
        self.wait()

        # download the datastore, even if incomplete
        resp = self.c.get('/v1/calc/%s/datastore' % job_id)
        self.assertEqual(resp.status_code, 200)

        tb = self.get('%s/traceback' % job_id)
        if not tb:
            sys.stderr.write('Empty traceback, please check!\n')

        self.post('%s/remove' % job_id)
        # make sure job_id is no more in the list of jobs
        job_ids = [job['id'] for job in self.get('list')]
        self.assertFalse(job_id in job_ids)

    def test_err_2(self):
        # the file logic-tree-source-model.xml is missing
        tb_str = self.postzip('archive_err_2.zip')
        self.assertIn('No such file', tb_str)

    def test_err_3(self):
        # there is no file job.ini, job_hazard.ini or job_risk.ini
        tb_str = self.postzip('archive_err_3.zip')
        self.assertIn('Could not find any file of the form', tb_str)

    def test_available_gsims(self):
        resp = self.c.get('/v1/available_gsims')
        self.assertIn(b'ChiouYoungs2014PEER', resp.content)

    def test_ini_defaults(self):
        resp = self.c.get('/v1/ini_defaults')
        self.assertEqual(resp.status_code, 200)

    def test_validate_zip(self):
        with open(os.path.join(self.datadir, 'archive_err_1.zip'), 'rb') as a:
            resp = self.post('validate_zip', dict(archive=a))
        dic = json.loads(resp.content.decode('utf8'))
        # error Could not convert insuranceLimit->positivefloat
        pprint.pprint(dic)
        if dic['error_msg'] is None:  # this should not happen
            raise unittest.SkipTest(dic)

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
