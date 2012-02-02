# Copyright (c) 2010-2012, GEM Foundation.
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
import numpy
import unittest

from openquake.engine import CalculationProxy
from openquake.engine import import_job_profile
from openquake.db.models import OqCalculation
from openquake.output.risk import LossMapDBWriter
from openquake.output.risk import LossMapNonScenarioXMLWriter
from openquake.calculators.risk.classical.core import ClassicalRiskCalculator
from openquake.calculators.risk.general import _compute_alphas
from openquake.calculators.risk.general import _compute_betas
from openquake.calculators.risk.general import compute_beta_distributions

from tests.utils.helpers import demo_file
from tests.utils.helpers import patch


class ProbabilisticRiskCalculatorTestCase(unittest.TestCase):
    """Tests for
    :class:`openquake.calculators.risk.general.ProbabilisticRiskCalculator`.
    """

    def test_write_output(self):
        # Test that the loss map writers are properly called when
        # write_output is invoked.
        cfg_file = demo_file('classical_psha_based_risk/config.gem')

        job_profile, params, sections = import_job_profile(cfg_file)

        # Set conditional loss poe so that loss maps are created.
        # If this parameter is not specified, no loss maps will be serialized
        # at the end of the calculation.
        params['CONDITIONAL_LOSS_POE'] = '0.01'
        job_profile.conditional_loss_poe = [0.01]
        job_profile.save()

        calculation = OqCalculation(owner=job_profile.owner,
                                    oq_job_profile=job_profile)
        calculation.save()

        calc_proxy = CalculationProxy(
            params, calculation.id, sections=sections,
            serialize_results_to=['xml', 'db'], oq_job_profile=job_profile,
            oq_calculation=calculation)

        calculator = ClassicalRiskCalculator(calc_proxy)

        # Mock the composed loss map serializer:
        with patch('openquake.writer.CompositeWriter'
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


class BaseRiskCalculator(unittest.TestCase):
    """Tests for
    :class:`openquake.calculators.risk.general.BaseRiskCalculator`.
    """

    def test__serialize_xml_filenames(self):
        # Test that the file names of the loss XML artifacts are correct.
        # See https://bugs.launchpad.net/openquake/+bug/894706.
        expected_lrc_file_name = (
            'losscurves-block-#%(calculation_id)s-block#%(block)s.xml')
        expected_lr_file_name = (
            'losscurves-loss-block-#%(calculation_id)s-block#%(block)s.xml')

        cfg_file = demo_file('classical_psha_based_risk/config.gem')

        job_profile, params, sections = import_job_profile(cfg_file)

        calculation = OqCalculation(owner=job_profile.owner,
                                    oq_job_profile=job_profile)
        calculation.save()

        calc_proxy = CalculationProxy(
            params, calculation.id, sections=sections,
            serialize_results_to=['xml', 'db'], oq_job_profile=job_profile,
            oq_calculation=calculation)

        calculator = ClassicalRiskCalculator(calc_proxy)

        with patch('openquake.writer.FileWriter.serialize'):
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
                expected_lrc_file_name % dict(calculation_id=calculation.id,
                                              block=0),
                file_name)

            # The same test again, except for loss curves this time.
            [file_path] = calculator._serialize(
                0, **dict(curve_mode='loss', curves=[]))

            _dir, file_name = os.path.split(file_path)

            self.assertEqual(
                expected_lr_file_name % dict(calculation_id=calculation.id,
                                             block=0),
                file_name)


class BetaDistributionTestCase(unittest.TestCase):
    """ Beta Distribution related testcase """

    def setUp(self):
        self.mean_loss_ratios = [0.050, 0.100, 0.200, 0.400, 0.800]
        self.stdevs = [0.025, 0.040, 0.060, 0.080, 0.080]

    def test_compute_alphas(self):
        # expected alphas provided by Vitor

        expected_alphas = [3.750, 5.525, 8.689, 14.600, 19.200]

        self.assertTrue(numpy.allclose(_compute_alphas(self.mean_loss_ratios,
            self.stdevs), expected_alphas, atol=0.0002))

    def test_compute_betas(self):
        # expected betas provided by Vitor

        expected_betas = [71.250, 49.725, 34.756, 21.900, 4.800]

        self.assertTrue(numpy.allclose(_compute_betas(self.mean_loss_ratios,
             self.stdevs), expected_betas, atol=0.0001))

    def test_compute_beta_dist(self):

        # lrems provided by Vitor
        lrems = [0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1,
            0.12, 0.14, 0.16, 0.18, 0.2, 0.24, 0.28, 0.32, 0.36, 0.4, 0.48,
            0.56, 0.64, 0.72, 0.8, 0.84, 0.86, 0.88, 0.9, 1]

        # expected beta distributions provided by Vitor
        expected_beta_distributions = [
            1.0, 1.0, 1.0, 1.0, 1.0,
            0.99, 1.0, 1.0, 1.0, 1.0,
            0.918, 0.998, 1.0, 1.0, 1.0,
            0.776, 0.989, 1.0, 1.0, 1.0,
            0.603, 0.963, 1.0, 1, 1.0,
            0.436, 0.916, 1.0, 1, 1.0,
            0.298, 0.846, 0.999, 1.0, 1.0,
            0.193, 0.757, 0.996, 1.0, 1.0,
            0.12, 0.657, 0.992, 1.0, 1.0,
            0.072, 0.553, 0.983, 1.0, 1.0,
            0.042, 0.452, 0.97, 1.0, 1.0,
            0.013, 0.279, 0.921, 1.0, 1.0,
            0.004, 0.156, 0.841, 1.0, 1.0,
            0.001, 0.081, 0.731, 1.0, 1.0,
            0, 0.038, 0.602, 0.999, 1.0,
            0, 0.017, 0.47, 0.997, 1.0,
            0, 0.003, 0.241, 0.982, 1.0,
            0, 0, 0.1, 0.936, 1.0,
            0, 0, 0.033, 0.838, 1.0,
            0, 0, 0.009, 0.682, 1.0,
            0, 0, 0.002, 0.491, 1.0,
            0, 0, 0, 0.162, 1.0,
            0, 0, 0, 0.026, 0.995,
            0, 0, 0, 0.002, 0.963,
            0, 0, 0, 0, 0.84,
            0, 0, 0, 0, 0.541,
            0, 0, 0, 0, 0.341,
            0, 0, 0, 0, 0.245,
            0, 0, 0, 0, 0.159,
            0, 0, 0, 0, 0.09,
            0, 0, 0, 0, 0]

        beta_distributions = compute_beta_distributions(self.mean_loss_ratios,
            self.stdevs, lrems)

        self.assertTrue(numpy.allclose(beta_distributions,
                expected_beta_distributions, atol=0.0005))
