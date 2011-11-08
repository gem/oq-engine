# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

import os
import unittest
import subprocess
import shutil
import ConfigParser

from nose.plugins.attrib import attr

from tests.utils import helpers


DISAGG_DEMO_CONFIG = helpers.demo_file('disaggregation/config.gem')


class DisaggCalcQATestCase(unittest.TestCase, helpers.ConfigTestMixin):
    def setUp(self):
        super(DisaggCalcQATestCase, self).setUp()
        self.setup_config()
        os.environ.update(self.orig_env)
        cp = ConfigParser.SafeConfigParser()
        cp.read('openquake.cfg.test_bakk')
        cp.set('nfs', 'base_dir', '/tmp')
        cp.write(open('openquake.cfg', 'w'))

    def tearDown(self):
        super(DisaggCalcQATestCase, self).tearDown()
        self.teardown_config()
        shutil.rmtree(os.path.join(os.path.dirname(DISAGG_DEMO_CONFIG),
                                   'computed_output'))

    @attr('qa')
    def test(self):
        import openquake
        exepath = os.path.join(os.path.dirname(openquake.__file__), '..',
                               'bin', 'openquake')
        exitcode = subprocess.call(
            [exepath, '--config_file=%s' % DISAGG_DEMO_CONFIG])
        self.assertEqual(0, exitcode)
        # TODO: verify the output
