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

import os
import re
import sys
import json
import pprint
import numpy
import zlib
import gzip
import tempfile
import string
import random
import logging

import django
from django.test import Client
from openquake.baselib import config
from openquake.commonlib.logs import dbcmd
from openquake.engine.export import core
from openquake.server.db import actions
from openquake.server.dbserver import db, get_status
from openquake.server.tests.views_test import EngineServerTestCase, loadnpz


class EngineServerPublicModeTestCase(EngineServerTestCase):
    """
    Here there are some real functional tests starting an engine server and
    running computations.
    """

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
        cls.wait()

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
        logging.disable(logging.CRITICAL)
        job_id = self.postzip('archive_err_1.zip')['job_id']
        self.wait()
        logging.disable(logging.NOTSET)

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
        logging.disable(logging.CRITICAL)
        resp = self.postzip('archive_err_2.zip')
        logging.disable(logging.NOTSET)
        self.assertIn('No such file', resp['tb_str'])
        self.post('%s/remove' % resp['job_id'])

    def test_err_3(self):
        # there is no file job.ini, job_hazard.ini or job_risk.ini
        logging.disable(logging.CRITICAL)
        resp = self.postzip('archive_err_3.zip')
        logging.disable(logging.NOTSET)
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
