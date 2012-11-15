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

import itertools
import os
import numpy
import unittest
import json

from django.contrib.gis import geos

from openquake.calculators.risk.classical.core import ClassicalRiskCalculator
from openquake.calculators.risk.classical.core import _generate_loss_ratios
from openquake.calculators.risk.general import BaseRiskCalculator
from openquake.calculators.risk.general import BetaDistribution
from openquake.calculators.risk.general import compute_alpha
from openquake.calculators.risk.general import compute_beta
from openquake.calculators.risk.general import load_gmvs_at
from openquake.db import models
from openquake import engine
from openquake import kvs
from openquake import shapes
from openquake.output.risk import LossMapDBWriter
from openquake.output.risk import LossMapNonScenarioXMLWriter

from tests.utils import helpers


class ProbabilisticRiskCalculatorTestCase(unittest.TestCase):
    """Tests for
    :class:`openquake.calculators.risk.general.ProbabilisticRiskCalculator`.
    """

    def test_write_output(self):
        # Test that the loss map writers are properly called when
        # write_output is invoked.
        cfg_file = helpers.demo_file('classical_psha_based_risk/config.gem')

        job = engine.prepare_job()
        job_profile, params, sections = engine.import_job_profile(
            cfg_file, job)

        # Set conditional loss poe so that loss maps are created.
        # If this parameter is not specified, no loss maps will be serialized
        # at the end of the job.
        params['CONDITIONAL_LOSS_POE'] = '0.01'
        job_profile.conditional_loss_poe = [0.01]
        job_profile.save()

        job_ctxt = engine.JobContext(
            params, job.id, sections=sections,
            serialize_results_to=['xml', 'db'], oq_job_profile=job_profile,
            oq_job=job)

        calculator = ClassicalRiskCalculator(job_ctxt)

        # Mock the composed loss map serializer:
        with helpers.patch('openquake.writer.CompositeWriter'
                           '.serialize') as writer_mock:
            calculator.write_output()

            self.assertEqual(1, writer_mock.call_count)

            # Now test that the composite writer got the correct
            # 'serialize to' instructions. The composite writer should have
            # 1 DB and 1 XML loss map serializer:
            composite_writer = writer_mock.call_args[0][0]
            writers = composite_writer.writers

            self.assertEqual(2, len(writers))
            # We don't assume anything about the order of the writers,
            # and we don't care anyway in this test:
            self.assertTrue(any(
                isinstance(w, LossMapDBWriter) for w in writers))
            self.assertTrue(any(
                isinstance(w, LossMapNonScenarioXMLWriter) for w in writers))


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """Tests for
    :class:`openquake.calculators.risk.general.BaseRiskCalculator`.
    """

    def test__serialize_xml_filenames(self):
        # Test that the file names of the loss XML artifacts are correct.
        # See https://bugs.launchpad.net/openquake/+bug/894706.
        expected_lrc_file_name = (
            'losscurves-block-#%(job_id)s-block#%(block)s.xml')
        expected_lr_file_name = (
            'losscurves-loss-block-#%(job_id)s-block#%(block)s.xml')

        cfg_file = helpers.demo_file('classical_psha_based_risk/config.gem')

        job = engine.prepare_job()
        job_profile, params, sections = engine.import_job_profile(
            cfg_file, job)

        job_ctxt = engine.JobContext(
            params, job.id, sections=sections,
            serialize_results_to=['xml', 'db'], oq_job_profile=job_profile,
            oq_job=job)

        calculator = ClassicalRiskCalculator(job_ctxt)

        with helpers.patch('openquake.writer.FileWriter.serialize'):
            # The 'curves' key in the kwargs just needs to be present;
            # because of the serialize mock in place above, it doesn't need
            # to have a real value.

            # First, we test loss ratio curve output,
            # then we'll do the same test for loss curve output.

            # We expect to get a single file path back.
            [file_path] = calculator._serialize(
                0, **dict(curve_mode='loss_ratio', curves=[]))

            _dir, file_name = os.path.split(file_path)

            self.assertEqual(
                expected_lrc_file_name % dict(job_id=job.id,
                                              block=0),
                file_name)

            # The same test again, except for loss curves this time.
            [file_path] = calculator._serialize(
                0, **dict(curve_mode='loss', curves=[]))

            _dir, file_name = os.path.split(file_path)

            self.assertEqual(
                expected_lr_file_name % dict(job_id=job.id,
                                             block=0),
                file_name)


class BetaDistributionTestCase(unittest.TestCase):
    """ Beta Distribution related testcase """

    def setUp(self):
        self.mean_loss_ratios = [0.050, 0.100, 0.200, 0.400, 0.800]
        self.stddevs = [0.025, 0.040, 0.060, 0.080, 0.080]
        self.covs = [0.500, 0.400, 0.300, 0.200, 0.100]
        self.imls = [0.100, 0.200, 0.300, 0.450, 0.600]

    def test_compute_alphas(self):
        # expected alphas provided by Vitor

        expected_alphas = [3.750, 5.525, 8.689, 14.600, 19.200]

        alphas = [compute_alpha(mean_loss_ratio, stddev) for mean_loss_ratio,
                stddev in itertools.izip(self.mean_loss_ratios, self.stddevs)]
        self.assertTrue(numpy.allclose(alphas, expected_alphas, atol=0.0002))

    def test_compute_betas(self):
        # expected betas provided by Vitor

        expected_betas = [71.250, 49.725, 34.756, 21.900, 4.800]

        betas = [compute_beta(mean_loss_ratio, stddev) for mean_loss_ratio,
                stddev in itertools.izip(self.mean_loss_ratios, self.stddevs)]
        self.assertTrue(numpy.allclose(betas, expected_betas, atol=0.0001))

    def test_compute_beta_dist(self):

        # expected beta distributions provided by Vitor
        expected_beta_distributions = [
            [1.0000000, 1.0000000, 1.0000000, 1.0000000, 1.0000000],
            [0.9895151, 0.9999409, 1.0000000, 1.0000000, 1.0000000],
            [0.9175720, 0.9981966, 0.9999997, 1.0000000, 1.0000000],
            [0.7764311, 0.9887521, 0.9999922, 1.0000000, 1.0000000],
            [0.6033381, 0.9633258, 0.9999305, 1.0000000, 1.0000000],
            [0.4364471, 0.9160514, 0.9996459, 1.0000000, 1.0000000],
            [0.2975979, 0.8460938, 0.9987356, 1.0000000, 1.0000000],
            [0.1931667, 0.7574557, 0.9964704, 1.0000000, 1.0000000],
            [0.1202530, 0.6571491, 0.9917729, 0.9999999, 1.0000000],
            [0.0722091, 0.5530379, 0.9832939, 0.9999997, 1.0000000],
            [0.0420056, 0.4521525, 0.9695756, 0.9999988, 1.0000000],
            [0.0130890, 0.2790107, 0.9213254, 0.9999887, 1.0000000],
            [0.0037081, 0.1564388, 0.8409617, 0.9999306, 1.0000000],
            [0.0009665, 0.0805799, 0.7311262, 0.9996882, 1.0000000],
            [0.0002335, 0.0384571, 0.6024948, 0.9988955, 1.0000000],
            [0.0000526, 0.0171150, 0.4696314, 0.9967629, 1.0000000],
            [0.0000022, 0.0027969, 0.2413923, 0.9820831, 1.0000000],
            [0.0000001, 0.0003598, 0.0998227, 0.9364072, 1.0000000],
            [0.0000000, 0.0000367, 0.0334502, 0.8381920, 0.9999995],
            [0.0000000, 0.0000030, 0.0091150, 0.6821293, 0.9999959],
            [0.0000000, 0.0000002, 0.0020162, 0.4909782, 0.9999755],
            [0.0000000, 0.0000000, 0.0000509, 0.1617086, 0.9995033],
            [0.0000000, 0.0000000, 0.0000005, 0.0256980, 0.9945488],
            [0.0000000, 0.0000000, 0.0000000, 0.0016231, 0.9633558],
            [0.0000000, 0.0000000, 0.0000000, 0.0000288, 0.8399534],
            [0.0000000, 0.0000000, 0.0000000, 0.0000001, 0.5409583],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.3413124],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.1589844],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0421052],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0027925],
            [0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000]]

        vuln_function = shapes.VulnerabilityFunction(self.imls,
                            self.mean_loss_ratios, self.covs)

        # steps = 5
        loss_ratios = _generate_loss_ratios(vuln_function, 5)

        lrem = numpy.empty((len(loss_ratios), vuln_function.imls.size), float)

        for col, _ in enumerate(vuln_function):
            for row, loss_ratio in enumerate(loss_ratios):
                lrem[row][col] = BetaDistribution.survival_function(loss_ratio,
                    col=col, vf=vuln_function)

        helpers.assertDeepAlmostEqual(self, expected_beta_distributions,
                                      lrem, delta=0.0005)


RISK_DEMO_CONFIG_FILE = helpers.demo_file(
    "classical_psha_based_risk/config.gem")


class LoadGroundMotionValuesTestCase(unittest.TestCase):

    job_id = "1234"
    region = shapes.Region.from_simple((0.1, 0.1), (0.2, 0.2))

    def setUp(self):
        kvs.mark_job_as_current(self.job_id)
        kvs.cache_gc(self.job_id)

    def tearDown(self):
        kvs.mark_job_as_current(self.job_id)
        kvs.cache_gc(self.job_id)

    def test_load_gmvs_at(self):
        """
        Exercise the function
        :func:`openquake.calculators.risk.general.load_gmvs_at`.
        """

        gmvs = [
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.117},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.167},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.542}]

        expected_gmvs = [0.117, 0.167, 0.542]
        point = self.region.grid.point_at(shapes.Site(0.1, 0.2))

        # we expect this point to be at row 1, column 0
        self.assertEqual(1, point.row)
        self.assertEqual(0, point.column)

        key = kvs.tokens.ground_motion_values_key(self.job_id, point)

        # place the test values in kvs
        for gmv in gmvs:
            kvs.get_client().rpush(key, json.JSONEncoder().encode(gmv))

        actual_gmvs = load_gmvs_at(self.job_id, point)
        self.assertEqual(expected_gmvs, actual_gmvs)
