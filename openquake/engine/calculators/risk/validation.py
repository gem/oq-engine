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

from openquake.engine import logs
from openquake.engine.db import models


class Validator(object):
    """
    abstract class describing a risk calculator validator
    """
    def __init__(self, risk_calculator):
        self.calc = risk_calculator

    def get_errors(self):
        raise NotImplementedError


class HazardIMT(Validator):
    """
    Check that a proper hazard output exists in any of the
    intensity measure types given in the risk models
    """
    def get_errors(self):
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
    def get_errors(self):
        if not sum(self.calc.taxonomies_asset_count):
            return ('Region of interest is not covered by the exposure input. '
                    'This configuration is invalid. '
                    'Change the region constraint input or use a proper '
                    'exposure')


class OrphanTaxonomies(Validator):
    """
    Checks that the taxonomies in the risk models match with the ones
    in the exposure.
    """
    def get_errors(self):
        taxonomies = self.calc.taxonomies_asset_count
        orphans = set(taxonomies) - set(self.calc.risk_models)
        if orphans:
            msg = ('The following taxonomies are in the exposure model '
                   'but not in the risk model: %s' % sorted(orphans))
            if self.rc.taxonomies_from_model:
                # only consider the taxonomies in the fragility model
                taxonomies = dict(
                    (t, taxonomies[t])
                    for t in taxonomies if t in self.calc.risk_models)
                logs.LOG.warn(msg)
            else:
                # all taxonomies in the exposure must be covered
                return msg


class ExposureLossTypes(Validator):
    """
    Check that the exposure has all the cost informations for the loss
    types given in the risk models
    """
    def get_errors(self):
        loss_types = models.loss_types(self.calc.risk_models)

        for loss_type in loss_types:
            cost_type = models.cost_type(loss_type)

            if loss_type != "fatalities":
                if not self.rc.exposure_model.exposuredata_set.filter(
                        cost__cost_type__name=cost_type).exists():
                    return ("Invalid exposure "
                            "for computing loss type %s. " % loss_type)
                else:
                    if self.rc.exposure_model.missing_occupants():
                        return "Invalid exposure for computing fatalities."


class NoRiskModels(Validator):
    def get_errors(self):
        if not self.calc.risk_models:
            return 'At least one risk model of type %s must be defined' % (
                models.LOSS_TYPES)
