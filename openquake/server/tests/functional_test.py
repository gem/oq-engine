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
Here there are real functional tests starting an engine server and
running computations.
"""

import os
import sys
import json
import time
import unittest
import subprocess

import requests


class EngineServerTestCase(unittest.TestCase):
    hostport = 'localhost:8761'
    datadir = os.path.join(os.path.dirname(__file__), 'data')

    @classmethod
    def get(cls, path, **params):
        resp = requests.get('http://%s/v1/calc/%s' % (cls.hostport, path),
                            params=params)
        assert resp.status_code == 200, resp
        return json.loads(resp.text)

    @classmethod
    def wait(cls):
        # wait until all calculations stop
        while True:
            running_calcs = cls.get('list', is_running='true')
            if not running_calcs:
                break
            time.sleep(1)

    @classmethod
    def setUpClass(cls):
        cls.job_ids = []
        env = os.environ.copy()
        env['OQ_NO_DISTRIBUTE'] = '1'
        cls.proc = subprocess.Popen(
            [sys.executable, '-m', 'openquake.server.manage', 'runserver',
             cls.hostport, '--noreload'], env=env)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.wait()

        data = cls.get('list', job_type='hazard', relevant='true')
        assert len(data) > 0

        nodata = cls.get('list', job_type='hazard', relevant='false')
        assert nodata == [], nodata

        cls.proc.kill()

    def postzip(self, archive):
        with open(os.path.join(self.datadir, archive)) as a:
            resp = requests.post('http://%s/v1/calc/run' % self.hostport,
                                 dict(database='platform'),
                                 files=dict(archive=a))
        job_id = json.loads(resp.text)['job_id']
        self.job_ids.append(job_id)
        return job_id

    def test_ok(self):
        job_id = self.postzip('archive_ok.zip')
        time.sleep(1)
        log = self.get('%d/log/:' % job_id)
        self.assertGreater(len(log), 0)

    def test_err(self):
        job_id = self.postzip('archive_err.zip')
        self.wait()
        time.sleep(1)
        tb = self.get('%d/traceback' % job_id)
        self.assertGreater(len(tb), 0)
