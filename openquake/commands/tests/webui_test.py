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
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

from openquake.server.utils import check_webserver_running

ROOT = Path(__file__).parents[3]


class _NotFoundHandler(BaseHTTPRequestHandler):
    # emulates an HTTP server unrelated to the WebUI, answering 404
    # to the health check requests

    def do_HEAD(self):
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass  # keep the test output clean


class WebuiTestCase(unittest.TestCase):

    @unittest.skipIf(sys.platform == 'darwin', 'WebUI lifecycle is flaky on macOS')
    def test_webui_lifecycle(self):
        """Start, inspect, and stop the WebUI through the CLI."""
        oq = shutil.which('oq')
        self.assertIsNotNone(oq)
        env = os.environ.copy()
        env['OQ_CONFIG_FILE'] = str(
            ROOT / 'openquake/engine/multiuser.cfg')
        hostport = self._free_hostport()
        process = subprocess.Popen(
            [oq, 'webui', 'start', hostport, '-s'],
            cwd=ROOT, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        try:
            self._wait_for_webui(process, hostport)
            status = subprocess.run(
                [oq, 'webui', 'status', hostport], cwd=ROOT, env=env,
                capture_output=True, text=True, check=True)
            self.assertEqual(status.stdout.strip(), 'running')
            # a second start on the same address must fail loudly
            second = subprocess.run(
                [oq, 'webui', 'start', hostport, '-s'], cwd=ROOT, env=env,
                capture_output=True, text=True, timeout=60)
            self.assertEqual(second.returncode, 1)
            self.assertIn('already running', second.stderr)
            stopped = subprocess.run(
                [oq, 'webui', 'stop', hostport], cwd=ROOT, env=env,
                capture_output=True, text=True, check=True)
            self.assertEqual(stopped.stdout.strip(), 'stopped')
            self.assertIn(process.wait(timeout=10), [0, 15])
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)

    def test_foreign_http_server_is_not_webui(self):
        # an unrelated server answering 404 must not count as running
        with HTTPServer(('127.0.0.1', 0), _NotFoundHandler) as srv:
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            try:
                url = 'http://127.0.0.1:%d/v0/health' % (
                    srv.server_address[1])
                self.assertFalse(check_webserver_running(
                    url, max_retries=1, warn=False))
            finally:
                srv.shutdown()

    def test_silent_server_does_not_hang(self):
        # a socket accepting connections but never replying must time out
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            sock.listen()
            url = 'http://127.0.0.1:%d/' % sock.getsockname()[1]
            t0 = time.time()
            self.assertFalse(check_webserver_running(
                url, max_retries=1, warn=False, timeout=1))
            self.assertLess(time.time() - t0, 10)

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
