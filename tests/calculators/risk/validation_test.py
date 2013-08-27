# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013, GEM Foundation.
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


import unittest
import mock

from openquake.engine.calculators.risk import validation
from openquake.engine.db import models


class HazardIMTTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()
        calc.risk_models = {
            'tax1': {
                'loss1': models.RiskModel('imt1', None, None)},
            'tax2': {
                'loss2': models.RiskModel('imt2', None, None)}}
        calc.hc.get_imts = mock.Mock(return_value=['imt1', 'imt2'])
        val = validation.HazardIMT(calc)

        self.assertIsNone(val.get_error())
        calc.hc.get_imts = mock.Mock(return_value=['imt1'])
        self.assertEqual(("There is no hazard output for: imt2. "
                          "The available IMTs are: imt1."), val.get_error())


class EmptyExposureTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()
        calc.taxonomies_asset_count = {}
        val = validation.EmptyExposure(calc)

        self.assertEqual(('Region of interest is not covered by '
                          'the exposure input. '
                          'This configuration is invalid. '
                          'Change the region constraint input or use a proper '
                          'exposure'), val.get_error())

        calc.taxonomies_asset_count = {'RM': 1, 'RC': 2}
        self.assertIsNone(val.get_error())


class OrphanTaxonomiesTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()
        val = validation.OrphanTaxonomies(calc)

        calc.rc.taxonomies_from_model = True
        calc.risk_models = {'RM': mock.Mock()}
        calc.taxonomies_asset_count = {'RC': 1, 'RM': 2}

        self.assertIsNone(val.get_error())

        calc.rc.taxonomies_from_model = False
        self.assertEqual("The following taxonomies are in the exposure model "
                         "but not in the risk model: set(['RC'])",
                         val.get_error())

        calc.risk_models = {'RM': mock.Mock(), 'RC': mock.Mock()}
        self.assertIsNone(val.get_error())


class ExposureLossTypesTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()
        val = validation.ExposureLossTypes(calc)

        calc.risk_models = {'RM': {'loss_type': mock.Mock()}}

        calc.rc.exposure_model.supports_loss_type = mock.Mock(
            return_value=False)

        self.assertEqual(("Invalid exposure "
                          "for computing loss type loss_type. "),
                         val.get_error())

        calc.rc.exposure_model.supports_loss_type = mock.Mock(
            return_value=True)
        self.assertIsNone(val.get_error())


class NoRiskModelsTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()
        calc.risk_models = None

        val = validation.NoRiskModels(calc)
        self.assertEqual(
            'At least one risk model of type %s must be defined' % (
                models.LOSS_TYPES), val.get_error())

        calc.risk_models = {'RM': mock.Mock()}
        self.assertIsNone(val.get_error())


class RequireClassicalHazardTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()

        val = validation.RequireClassicalHazard(calc)

        calc.rc.hazard_calculation.calculation_mode = 'classical'
        self.assertIsNone(val.get_error())

        calc.rc.hazard_calculation.calculation_mode = 'event_based'
        self.assertEqual(("The provided hazard calculation ID "
                          "is not a classical calculation"), val.get_error())

        calc.rc.hazard_calculation = None
        calc.rc.hazard_output.is_hazard_curve = mock.Mock(return_value=True)
        self.assertIsNone(val.get_error())

        calc.rc.hazard_output.is_hazard_curve = mock.Mock(return_value=False)
        self.assertEqual("The provided hazard output is not an hazard curve",
                         val.get_error())


class RequireScenarioHazardTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()

        val = validation.RequireScenarioHazard(calc)

        calc.rc.hazard_calculation.calculation_mode = 'scenario'
        self.assertIsNone(val.get_error())

        calc.rc.hazard_calculation.calculation_mode = 'event_based'
        self.assertEqual(("The provided hazard calculation ID "
                          "is not a scenario calculation"), val.get_error())

        calc.rc.hazard_calculation = None
        calc.rc.hazard_output.output_type = "gmf_scenario"
        self.assertIsNone(val.get_error())

        calc.rc.hazard_output.output_type = "gmf"
        self.assertEqual(("The provided hazard is not a "
                          "gmf scenario collection"),
                         val.get_error())


class RequireEventBasedHazardTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()

        val = validation.RequireEventBasedHazard(calc)

        calc.rc.hazard_calculation.calculation_mode = 'event_based'
        self.assertIsNone(val.get_error())

        calc.rc.hazard_calculation.calculation_mode = 'classical'
        self.assertEqual(("The provided hazard calculation ID "
                          "is not a event based calculation"), val.get_error())

        calc.rc.hazard_calculation = None
        calc.rc.hazard_output.output_type = "gmf"
        self.assertIsNone(val.get_error())
        calc.rc.hazard_output.output_type = "ses"
        self.assertIsNone(val.get_error())

        calc.rc.hazard_output.output_type = "gmf_scenario"
        self.assertEqual(("The provided hazard is not a "
                          "gmf or ses collection"),
                         val.get_error())


class ExposureHasInsuranceBoundsTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()

        val = validation.ExposureHasInsuranceBounds(calc)

        calc.rc.insured_losses = True
        calc.rc.exposure_model.has_insurance_bounds = mock.Mock(
            return_value=True)
        self.assertIsNone(val.get_error())

        calc.rc.insured_losses = True
        calc.rc.exposure_model.has_insurance_bounds = mock.Mock(
            return_value=False)
        self.assertEqual("Deductible or insured limit missing in exposure",
                         val.get_error())

        calc.rc.insured_losses = False
        calc.rc.exposure_model.has_insurance_bounds = mock.Mock(
            return_value=True)
        self.assertIsNone(val.get_error())

        calc.rc.insured_losses = False
        calc.rc.exposure_model.has_insurance_bounds = mock.Mock(
            return_value=False)
        self.assertIsNone(val.get_error())


class ExposureHasRetrofittedCostsTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()

        val = validation.ExposureHasRetrofittedCosts(calc)

        calc.rc.exposure_model.has_retrofitted_costs = mock.Mock(
            return_value=True)
        self.assertIsNone(val.get_error())

        calc.rc.exposure_model.has_retrofitted_costs = mock.Mock(
            return_value=False)
        self.assertEqual("Some assets do not have retrofitted costs",
                         val.get_error())


class ExposureHasTimeEventTestCase(unittest.TestCase):
    def test_get_error(self):
        calc = mock.Mock()
        val = validation.ExposureHasTimeEvent(calc)

        calc.rc.time_event = "night"

        calc.rc.exposure_model.has_time_event = mock.Mock(
            return_value=True)
        self.assertIsNone(val.get_error())

        calc.rc.exposure_model.has_time_event = mock.Mock(
            return_value=False)
        self.assertEqual("Some assets are missing an "
                         "occupancy with period=night", val.get_error())
