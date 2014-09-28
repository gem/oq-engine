# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2014, GEM Foundation.
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
Reading risk models for risk calculators
"""
import collections
from openquake.risklib import workflows
from openquake.commonlib.riskmodels import \
    get_vulnerability_functions, get_fragility_functions

# loss types (in the risk models) and cost types (in the exposure)
# are the sames except for fatalities -> occupants


def loss_type_to_cost_type(lt):
    """Convert a loss_type string into a cost_type string"""
    return 'occupants' if lt == 'fatalities' else lt


def cost_type_to_loss_type(ct):
    """Convert a cost_type string into a loss_type string"""
    return 'fatalities' if ct == 'occupants' else ct


def get_taxonomy_vfs(inputs, loss_types, retrofitted=False):
    """
    Given a dictionary {key: pathname} and a list of loss_types (for instance
    ['structural', 'nonstructural', ...]) look for keys with name
    <cost_type>__vulnerability, parse them and yield triples
    (imt, taxonomy, vf_by_loss_type)
    """
    retro = '_retrofitted' if retrofitted else ''
    vulnerability_functions = collections.defaultdict(dict)
    for loss_type in loss_types:
        key = '%s_vulnerability%s' % (loss_type_to_cost_type(loss_type), retro)
        if key not in inputs:
            continue
        vf_dict = get_vulnerability_functions(inputs[key])
        for (imt, tax), vf in vf_dict.iteritems():
            vulnerability_functions[imt, tax][loss_type] = vf
    return vulnerability_functions.iteritems()


def get_risk_models(inputs, loss_types, insured_losses=False,
                    retrofitted=False):
    """
    Given a directory path name and a list of loss_types (for instance
    ['structural', 'nonstructural', ...]) look for files with name
    <loss_type>__vulnerability_model.xml, parse them and return a
    dictionary {taxonomy: risk_model}.
    """
    risk_models = {}
    for (imt, taxonomy), vf_by_loss_type in get_taxonomy_vfs(
            inputs, loss_types, retrofitted):
        workflow = workflows.Scenario(vf_by_loss_type, insured_losses)
        risk_models[imt, taxonomy] = workflows.RiskModel(
            imt, taxonomy, workflow)
    return risk_models


class List(list):
    """
    Class to store lists of objects with common attributes
    """
    def __init__(self, elements, **attrs):
        list.__init__(self, elements)
        vars(self).update(attrs)


def get_damage_states_and_risk_models(fname):
    """
    Parse the fragility XML file and return a list of
    damage_states and a dictionary {taxonomy: risk model}
    """
    risk_models = {}
    damage_states, fragility_functions = get_fragility_functions(fname)
    for taxonomy, ffs in fragility_functions.iteritems():
        risk_models[ffs.imt, taxonomy] = workflows.RiskModel(
            ffs.imt, taxonomy, workflows.Damage(dict(damage=ffs)))

    return damage_states, risk_models
