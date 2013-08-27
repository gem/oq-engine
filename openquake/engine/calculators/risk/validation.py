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


"""
Custom validation module for risk calculators
"""

from openquake.engine.db import models


class Validator(object):
    """
    abstract class describing a risk calculator validator
    """
    def __init__(self, risk_calculator):
        self.calc = risk_calculator

    def get_error(self):
        raise NotImplementedError


class HazardIMT(Validator):
    """
    Check that a proper hazard output exists in any of the
    intensity measure types given in the risk models
    """
    def get_error(self):
        model_imts = models.required_imts(self.calc.risk_models)
        imts = self.calc.hc.get_imts()

        # check that the hazard data have all the imts needed by the
        # risk calculation
        missing = set(model_imts) - set(imts)

        if missing:
            return ("There is no hazard output for: %s. "
                    "The available IMTs are: %s." % (", ".join(missing),
                                                     ", ".join(imts)))


class EmptyExposure(Validator):
    """
    Checks that at least one asset is in the exposure
    """
    def get_error(self):
        if not sum(self.calc.taxonomies_asset_count.values()):
            return ('Region of interest is not covered by the exposure input. '
                    'This configuration is invalid. '
                    'Change the region constraint input or use a proper '
                    'exposure')


class OrphanTaxonomies(Validator):
    """
    Checks that the taxonomies in the risk models match with the ones
    in the exposure.
    """
    def get_error(self):
        taxonomies = self.calc.taxonomies_asset_count
        orphans = set(taxonomies) - set(self.calc.risk_models)
        if orphans and not self.calc.rc.taxonomies_from_model:
            return ('The following taxonomies are in the exposure model '
                    'but not in the risk model: %s' % orphans)


class ExposureLossTypes(Validator):
    """
    Check that the exposure has all the cost informations for the loss
    types given in the risk models
    """
    def get_error(self):
        loss_types = models.loss_types(self.calc.risk_models)

        for loss_type in loss_types:
            if not self.calc.rc.exposure_model.supports_loss_type(loss_type):
                return ("Invalid exposure "
                        "for computing loss type %s. " % loss_type)


class NoRiskModels(Validator):
    def get_error(self):
        if not self.calc.risk_models:
            return 'At least one risk model of type %s must be defined' % (
                models.LOSS_TYPES)


class RequireClassicalHazard(Validator):
    """
    Checks that the given hazard has hazard curves
    """
    def get_error(self):
        rc = self.calc.rc

        if rc.hazard_calculation:
            if rc.hazard_calculation.calculation_mode != 'classical':
                return ("The provided hazard calculation ID "
                        "is not a classical calculation")
        elif not rc.hazard_output.is_hazard_curve():
            return "The provided hazard output is not an hazard curve"


class RequireScenarioHazard(Validator):
    """
    Checks that the given hazard has ground motion fields got from a
    scenario hazard calculation
    """
    def get_error(self):
        rc = self.calc.rc

        if rc.hazard_calculation:
            if rc.hazard_calculation.calculation_mode != "scenario":
                return ("The provided hazard calculation ID "
                        "is not a scenario calculation")
        elif not rc.hazard_output.output_type == "gmf_scenario":
            return "The provided hazard is not a gmf scenario collection"


class RequireEventBasedHazard(Validator):
    """
    Checks that the given hazard has ground motion fields (or
    stochastic event set) got from a event based hazard calculation
    """
    def get_error(self):
        rc = self.calc.rc

        if rc.hazard_calculation:
            if rc.hazard_calculation.calculation_mode != "event_based":
                return ("The provided hazard calculation ID "
                        "is not a event based calculation")
        elif not rc.hazard_output.output_type in ["gmf", "ses"]:
            return "The provided hazard is not a gmf or ses collection"


class ExposureHasInsuranceBounds(Validator):
    """
    If insured losses are required we check for the presence of
    the deductible and insurance limit
    """

    def get_error(self):
        if (self.calc.rc.insured_losses and
            not self.calc.rc.exposure_model.has_insurance_bounds()):
            return "Deductible or insured limit missing in exposure"


class ExposureHasRetrofittedCosts(Validator):
    """
    Check that the retrofitted value is present in the exposure
    """
    def get_error(self):
        if not self.calc.rc.exposure_model.has_retrofitted_costs():
            return "Some assets do not have retrofitted costs"


class ExposureHasTimeEvent(Validator):
    """
    If fatalities are considered check that the exposure has the
    proper time_event
    """

    def get_error(self):
        if (self.calc.rc.vulnerability_input("occupants") is not None and
            not self.calc.rc.exposure_model.has_time_event(
                self.calc.rc.time_event)):
            return ("Some assets are missing an "
                    "occupancy with period=%s" % self.calc.rc.time_event)
