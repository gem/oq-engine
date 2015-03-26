#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Here there are some real functional tests starting an engine server and
running computations.
"""

import os
import sys
import json
import time
import unittest
import subprocess

import requests

if requests.__version__ < '1.0.0':
    requests.Response.text = property(lambda self: self.content)


class EngineServerTestCase(unittest.TestCase):
    hostport = 'localhost:8761'
    datadir = os.path.join(os.path.dirname(__file__), 'data')

    # general utilities

    @classmethod
    def get(cls, path, **params):
        resp = requests.get('http://%s/v1/calc/%s' % (cls.hostport, path),
                            params=params)
        assert resp.status_code == 200, resp
        return json.loads(resp.text)

    @classmethod
    def get_text(cls, path, **params):
        resp = requests.get('http://%s/v1/calc/%s' % (cls.hostport, path),
                            params=params)
        assert resp.status_code == 200, resp
        return resp.text

    @classmethod
    def wait(cls):
        # wait until all calculations stop
        while True:
            running_calcs = cls.get('list', is_running='true')
            if not running_calcs:
                break
            time.sleep(1)

    def postzip(self, archive):
        with open(os.path.join(self.datadir, archive)) as a:
            resp = requests.post('http://%s/v1/calc/run' % self.hostport,
                                 dict(database='platform'),
                                 files=dict(archive=a))
        job_id = json.loads(resp.text)['job_id']
        self.job_ids.append(job_id)
        time.sleep(1)  # wait a bit for the calc to start
        return job_id

    # start/stop server utilities

    @classmethod
    def setUpClass(cls):
        cls.job_ids = []
        env = os.environ.copy()
        env['OQ_NO_DISTRIBUTE'] = '1'
        cls.proc = subprocess.Popen(
            [sys.executable, '-m', 'openquake.server.manage', 'runserver',
             cls.hostport, '--noreload'], env=env, stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.wait()

        data = cls.get('list', job_type='hazard', relevant='true')
        assert len(data) > 0

        nodata = cls.get('list', job_type='hazard', relevant='false')
        assert nodata == [], nodata

        cls.proc.kill()

    # tests

    def test_404(self):
        # looking for a missing calc_id
        resp = requests.get('http://%s/v1/calc/0' % self.hostport)
        assert resp.status_code == 404, resp

    def test_ok(self):
        job_id = self.postzip('archive_ok.zip')
        log = self.get('%d/log/:' % job_id)
        self.assertGreater(len(log), 0)
        self.wait()
        results = self.get('%d/results' % job_id)
        for res in results:
            text = self.get_text('result/%d' % res['id'])
            self.assertGreater(len(text), 0)
        self.assertGreater(len(results), 0)

    def test_err_1(self):
        # the rupture XML file has a syntax error
        job_id = self.postzip('archive_err.zip')
        self.wait()
        tb = self.get('%d/traceback' % job_id)
        print 'Error in job', job_id, '\n'.join(tb)
        self.assertGreater(len(tb), 0)

    # TODO: add more tests for error situations
