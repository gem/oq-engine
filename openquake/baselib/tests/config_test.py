# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2026 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import logging
import tempfile
import unittest
import subprocess
from openquake.baselib import config


class ConfigPathsTestCase(unittest.TestCase):
    """Make sure that the config path search logic is tested"""

    def test_venv(self):
        venv = os.environ.get('VIRTUAL_ENV')
        if venv:
            self.assertIn(os.path.join(venv, 'openquake.cfg'), config.paths)
        else:
            logging.warning('To run the tests, you should use a '
                            'development installation with a virtualenv')

    def test_config_file(self):
        # OQ_CONFIG_FILE is read last, so that it has the precedence; it is
        # checked in a new process, since config.paths is computed at import
        with tempfile.NamedTemporaryFile(
                'w', suffix='.cfg', delete=False) as f:
            f.write('[dbserver]\nport = 1999\n')
        self.addCleanup(os.remove, f.name)
        code = ('from openquake.baselib import config; '
                'print(config.paths[-1], config.dbserver.port)')
        out = subprocess.run(
            [sys.executable, '-c', code], capture_output=True, text=True,
            env=dict(os.environ, OQ_CONFIG_FILE=f.name), check=True).stdout
        self.assertEqual(out.split(), [f.name, '1999'])
