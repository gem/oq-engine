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
I/O handling for risk calculators
"""

import collections
from openquake.risklib import scientific

from openquake.nrmllib.risk import parsers
from openquake.engine.input.exposure import ExposureDBWriter
from openquake.engine.db.models import RiskModel, DmgState


def exposure(job, exposure_model_input):
    """
    Load exposure assets and write them to database.

    :param exposure_model_input:
        the pathname to an exposure file
    """
    return ExposureDBWriter(job).serialize(
        parsers.ExposureModelParser(exposure_model_input))


def vulnerability(vulnerability_file):
    """
    :param vulnerability_file:
        the pathname to a vulnerability file
    :returns:
        an assoc list between taxonomies and `RiskModel` instances
    :raises:
        * `ValueError` if validation of any vulnerability function fails
    """
    vfs = dict()

    for record in parsers.VulnerabilityModelParser(vulnerability_file):
        taxonomy = record['ID']
        imt = record['IMT']
        loss_ratios = record['lossRatio']
        covs = record['coefficientsVariation']
        distribution = record['probabilisticDistribution']

        if taxonomy in vfs:
            raise ValueError("Error creating vulnerability function for "
                             "taxonomy %s. A taxonomy can not "
                             "be associated with "
                             "different vulnerability functions" % (
                             taxonomy))

        try:
            vfs[taxonomy] = RiskModel(
                imt,
                scientific.VulnerabilityFunction(
                    record['IML'],
                    loss_ratios,
                    covs,
                    distribution),
                None)
        except ValueError, err:
            msg = (
                "Invalid vulnerability function with ID '%s': %s"
                % (taxonomy, err.message)
            )
            raise ValueError(msg)

    return vfs.items()


def fragility(risk_calculation, fragility_input):
    damage_states, risk_models = _parse_fragility(fragility_input)

    for lsi, dstate in enumerate(damage_states):
        DmgState.objects.get_or_create(
            risk_calculation=risk_calculation, dmg_state=dstate, lsi=lsi)
    damage_state_ids = [d.id for d in DmgState.objects.filter(
        risk_calculation=risk_calculation).order_by('lsi')]

    return risk_models, damage_state_ids


def _parse_fragility(content):
    """
    Parse the fragility XML file and return fragility_model,
    fragility_functions, and damage_states for usage in get_risk_models.
    """
    iterparse = iter(parsers.FragilityModelParser(content))
    fmt, limit_states = iterparse.next()

    damage_states = ['no_damage'] + limit_states
    fragility_functions = collections.defaultdict(dict)

    tax_imt = dict()
    for taxonomy, iml, params, no_damage_limit in iterparse:
        tax_imt[taxonomy] = iml['IMT']

        if fmt == "discrete":
            if no_damage_limit is None:
                fragility_functions[taxonomy] = [
                    scientific.FragilityFunctionDiscrete(
                        iml['imls'], poes, iml['imls'][0])
                    for poes in params]
            else:
                fragility_functions[taxonomy] = [
                    scientific.FragilityFunctionDiscrete(
                        [no_damage_limit] + iml['imls'], [0.0] + poes,
                        no_damage_limit)
                    for poes in params]
        else:
            fragility_functions[taxonomy] = [
                scientific.FragilityFunctionContinuous(*mean_stddev)
                for mean_stddev in params]
    risk_models = dict((tax, dict(damage=RiskModel(tax_imt[tax], None, ffs)))
                       for tax, ffs in fragility_functions.items())
    return damage_states, risk_models
