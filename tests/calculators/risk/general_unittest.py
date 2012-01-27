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
import unittest

from openquake.engine import CalculationProxy
from openquake.engine import import_job_profile
from openquake.db.models import OqCalculation
from openquake.output.risk import LossMapDBWriter
from openquake.output.risk import LossMapNonScenarioXMLWriter
from openquake.calculators.risk.classical.core import ClassicalRiskCalculator

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
