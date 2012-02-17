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


import itertools
import os
import numpy
import unittest

from openquake.calculators.risk.classical.core import ClassicalRiskCalculator
from openquake.calculators.risk.classical.core import _generate_loss_ratios
from openquake.calculators.risk.general import BaseRiskCalculator
from openquake.calculators.risk.general import BetaDistribution
from openquake.calculators.risk.general import compute_alpha
from openquake.calculators.risk.general import compute_beta
from openquake.db.models import OqCalculation
from openquake.engine import CalculationProxy
from openquake.engine import import_job_profile
from openquake import shapes
from openquake.input.exposure import ExposureDBWriter
from openquake.output.risk import LossMapDBWriter
from openquake.output.risk import LossMapNonScenarioXMLWriter
from openquake.parser.exposure import ExposurePortfolioFile

from tests.utils.helpers import SCHEMA_EXAMPLES_DIR
from tests.utils.helpers import assertDeepAlmostEqual
from tests.utils.helpers import DbTestCase
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


class BaseRiskCalculatorTestCase(unittest.TestCase):
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
        self.stddevs = [0.025, 0.040, 0.060, 0.080, 0.080]
        self.covs = [0.500, 0.400, 0.300, 0.200, 0.100]
        self.imls = [0.100, 0.200, 0.300, 0.450, 0.600]

    def test_compute_alphas(self):
        # expected alphas provided by Vitor

        expected_alphas = [3.750, 5.525, 8.689, 14.600, 19.200]

        alphas = [compute_alpha(mean_loss_ratio, stddev) for  mean_loss_ratio,
                stddev in itertools.izip(self.mean_loss_ratios, self.stddevs)]
        self.assertTrue(numpy.allclose(alphas, expected_alphas, atol=0.0002))

    def test_compute_betas(self):
        # expected betas provided by Vitor

        expected_betas = [71.250, 49.725, 34.756, 21.900, 4.800]

        betas = [compute_beta(mean_loss_ratio, stddev) for  mean_loss_ratio,
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

        assertDeepAlmostEqual(self, expected_beta_distributions,
            lrem, delta=0.0005)


class AssetsForSiteTestCase(unittest.TestCase, DbTestCase):
    """Test the BaseRiskCalculator.assets_for_site() function."""
    job = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(SCHEMA_EXAMPLES_DIR, "exposure-portfolio.xml")
        inputs = [("exposure", path)]
        cls.job = cls.setup_classic_job(inputs=inputs)
        parser = ExposurePortfolioFile(path)
        writer = ExposureDBWriter(cls.job.oq_job_profile.input_set, path)
        writer.serialize(parser)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    @staticmethod
    def _to_site(pg_point):
        return shapes.Site(pg_point.x, pg_point.y)

    def test_assets_for_site_with_existent_row(self):
        # Asset is found in the database.
        site = shapes.Site(9.15000, 45.16667)
        [asset] = BaseRiskCalculator.assets_for_site(self.job.id, site)
        self.assertEqual("asset_01", asset.asset_ref)
        self.assertEqual(site, self._to_site(asset.site))

    def test_assets_for_site_with_non_existent_row(self):
        # An empty list is returned when no assets exist for a given
        # job and site.
        site = shapes.Site(99.15000, 15.16667)
        self.assertEqual(
            [], BaseRiskCalculator.assets_for_site(self.job.id, site))
