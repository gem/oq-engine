# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import shutil
import socket
import subprocess
import time
import unittest
from pathlib import Path

import requests

ROOT = Path(__file__).parents[3]


class WebuiTestCase(unittest.TestCase):

    def test_webui_lifecycle(self):
        """Start, inspect, and stop the WebUI through the CLI."""
        oq = shutil.which('oq')
        self.assertIsNotNone(oq)
        env = os.environ.copy()
        env['OQ_CONFIG_FILE'] = str(
            ROOT / 'openquake/engine/multiuser.cfg')
        hostport = self._free_hostport()
        process = subprocess.Popen(
            [oq, 'webui', 'start', '-s', hostport],
            cwd=ROOT, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        try:
            self._wait_for_webui(process, hostport)
            status = subprocess.run(
                [oq, 'webui', 'status', hostport], cwd=ROOT, env=env,
                capture_output=True, text=True, check=True)
            self.assertEqual(status.stdout.strip(), 'running')
            stopped = subprocess.run(
                [oq, 'webui', 'stop', hostport], cwd=ROOT, env=env,
                capture_output=True, text=True, check=True)
            self.assertEqual(stopped.stdout.strip(), 'stopped')
            self.assertEqual(process.wait(timeout=10), 0)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)

    def _free_hostport(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            return '127.0.0.1:%d' % sock.getsockname()[1]

    def _wait_for_webui(self, process, hostport):
        for _ in range(60):
            if process.poll() is not None:
                output = process.stdout.read()
                self.fail('WebUI exited early:\n%s' % output)
            try:
                response = requests.head(
                    'http://' + hostport, allow_redirects=True,
                    timeout=1)
                if response.ok:
                    return
            except requests.RequestException:
                pass
            time.sleep(0.5)
        self.fail('WebUI did not start within 30 seconds')


if __name__ == '__main__':
    unittest.main()
