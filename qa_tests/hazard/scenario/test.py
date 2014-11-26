# Copyright (c) 2010-2014, GEM Foundation.
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

import os
import tempfile
import shutil
import numpy
from nose.plugins.attrib import attr
from numpy.testing import assert_almost_equal

from openquake.engine import export
from openquake.engine.db import models
from openquake.commonlib.tests import check_equal
from qa_tests import _utils as qa_utils
from openquake.commonlib.tests.calculators.scenario_test import count_close
from openquake.qa_tests_data.scenario import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8)


class ScenarioHazardCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_1.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')

        gmvs_per_site = models.get_gmvs_per_site(output, 'PGA')
        actual = map(numpy.median, gmvs_per_site)
        expected_medians = [0.48155582, 0.21123045, 0.14484586]
        assert_almost_equal(actual, expected_medians, decimal=2)

    @attr('qa', 'hazard', 'scenario')
    def test_export(self):
        result_dir = tempfile.mkdtemp()
        cfg = os.path.join(os.path.dirname(case_1.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        exported_file = export.core.export(output.id, result_dir)
        check_equal(case_1.__file__, 'expected.xml', exported_file)
        shutil.rmtree(result_dir)


class ScenarioHazardCase2TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_2.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        actual = map(numpy.median, models.get_gmvs_per_site(output, 'PGA'))
        expected_medians = [0.37412136, 0.19021782, 0.1365383]
        assert_almost_equal(actual, expected_medians, decimal=2)


# job.ini contains intensity_measure_types = PGA, SA(0.1)
class ScenarioHazardCase3TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_3.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        actual = map(numpy.median, models.get_gmvs_per_site(output, 'PGA'))
        expected_medians_pga = [0.48155582, 0.21123045, 0.14484586]
        assert_almost_equal(actual, expected_medians_pga, decimal=2)

        actual = map(numpy.median, models.get_gmvs_per_site(output, 'SA(0.1)'))
        expected_medians_sa = [0.93913177, 0.40880148, 0.2692668]
        assert_almost_equal(actual, expected_medians_sa, decimal=2)


class ScenarioHazardCase4TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_4.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        actual = map(numpy.median, models.get_gmvs_per_site(output, 'PGA'))
        expected_medians = [0.41615372, 0.22797466, 0.1936226]
        assert_almost_equal(actual, expected_medians, decimal=2)


class ScenarioHazardCase5TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_5.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        gmfs = list(models.get_gmvs_per_site(output, 'PGA'))
        realizations = 1e5
        first_value = 0.5
        second_value = 1.0
        gmfs_within_range_fst = count_close(first_value, gmfs[0], gmfs[1])
        gmfs_within_range_snd = count_close(second_value, gmfs[0], gmfs[1])

        self.assertAlmostEqual(gmfs_within_range_fst / realizations,
                               0.03, places=2)
        self.assertAlmostEqual(gmfs_within_range_snd / realizations,
                               0.003, places=3)


class ScenarioHazardCase6TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_6.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        gmfs = list(models.get_gmvs_per_site(output, 'PGA'))
        realizations = 2e4
        first_value = 0.5
        second_value = 1.0
        gmfs_within_range_fst = count_close(first_value, gmfs[0], gmfs[1])
        gmfs_within_range_snd = count_close(second_value, gmfs[0], gmfs[1])
        self.assertAlmostEqual(gmfs_within_range_fst / realizations,
                               0.05, places=2)
        self.assertAlmostEqual(gmfs_within_range_snd / realizations,
                               0.006, places=3)


class ScenarioHazardCase7TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_7.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        [output] = export.core.get_outputs(job.id, 'gmf_scenario')
        gmfs = list(models.get_gmvs_per_site(output, 'PGA'))
        realizations = 1e5
        first_value = 0.5
        second_value = 1.0
        gmfs_within_range_fst = count_close(first_value, gmfs[0], gmfs[1])
        gmfs_within_range_snd = count_close(second_value, gmfs[0], gmfs[1])

        self.assertAlmostEqual(gmfs_within_range_fst / realizations,
                               0.02, places=2)
        self.assertAlmostEqual(gmfs_within_range_snd / realizations,
                               0.002, places=3)


# test for a GMPE requiring hypocentral depth, since it was
# broken: https://bugs.launchpad.net/oq-engine/+bug/1334524
class ScenarioHazardCase8TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'scenario')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_8.__file__), 'job.ini')
        self.run_hazard(cfg)
        # I am not checking anything, only that it runs
