# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
import unittest
from openquake.baselib import config


class ConfigPathsTestCase(unittest.TestCase):
    """Make sure that the config path search logic is tested"""

    def test_venv(self):
        venv = os.environ.get('VIRTUAL_ENV')
        if venv:
            self.assertIn(os.path.join(venv, 'openquake.cfg'), config.paths)
        else:
            self.assertIn('/etc/openquake/openquake.cfg', config.paths)

    def test_config_file(self):
        cfgfile = os.environ.get('OQ_CONFIG_FILE')
        if cfgfile:
            self.assertEqual(config.paths[0], cfgfile)
