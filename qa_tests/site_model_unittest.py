# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import ConfigParser
import os
import unittest

from nose.plugins.attrib import attr

from openquake.db import models

from tests.utils import helpers


class SiteModelConfigsTestCase(unittest.TestCase, helpers.ConfigTestCase):
    """Run each of the hazard calculators end-to-end with a site model defined
    in the configuration.

    We don't check any of the results; we just make sure the calculations can
    run to completion."""

    def _do_test(self, cfg):
        helpers.run_job(cfg)
        job = models.OqJob.objects.latest('id')
        self.assertEqual('succeeded', job.status)

    @attr('slow')
    def test_classical(self):
        self._do_test(
            helpers.demo_file(
                'simple_fault_demo_hazard/config_with_site_model.gem'
            )
        )

    @attr('slow')
    def test_event_based(self):
        self._do_test(
            helpers.demo_file('event_based_hazard/config_with_site_model.gem')
        )

    @attr('slow')
    def test_disagg(self):
        self.setup_config()
        os.environ.update(self.orig_env)
        cp = ConfigParser.SafeConfigParser()
        cp.read('openquake.cfg.test_bakk')
        cp.set('nfs', 'base_dir', '/tmp')
        cp.write(open('openquake.cfg', 'w'))

        try:
            self._do_test(
                helpers.demo_file('disaggregation/config_with_site_model.gem')
            )
        finally:
            self.teardown_config()

    @attr('slow')
    def test_uhs(self):
        self._do_test(
            helpers.demo_file('uhs/config_with_site_model.gem')
        )
