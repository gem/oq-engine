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

import logging
import collections

from openquake.nrmllib.node import read_nodes, LiteralNode, context
from openquake.nrmllib import InvalidFile
from openquake.risklib import scientific, workflows
from openquake.commonlib import valid
from openquake.commonlib.oqvalidation import vulnerability_files


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


############################ vulnerability ##################################

class VulnerabilityNode(LiteralNode):
    """
    Literal Node class used to validate discrete vulnerability functions
    """
    validators = valid.parameters(
        vulnerabilitySetID=valid.name,
        vulnerabilityFunctionID=valid.name_with_dashes,
        assetCategory=str,
        # the assetCategory here has nothing to do with the category
        # in the exposure model and it is not used by the engine
        lossCategory=valid.name,
        IML=valid.IML,
        lossRatio=valid.positivefloats,
        coefficientsVariation=valid.positivefloats,
        probabilisticDistribution=valid.Choice('LN', 'BT'),
    )


def filter_vset(elem):
    return elem.tag.endswith('discreteVulnerabilitySet')


def get_vulnerability_functions(fname):
    """
    :param fname:
        path of the vulnerability filter
    :returns:
        a dictionary imt, taxonomy -> vulnerability function
    """
    imts = set()
    taxonomies = set()
    vf_dict = {}  # imt, taxonomy -> vulnerability function
    for vset in read_nodes(fname, filter_vset, VulnerabilityNode):
        imt_str, imls, min_iml, max_iml = ~vset.IML
        if imt_str in imts:
            raise InvalidFile('Duplicated IMT %s: %s, line %d' %
                              (imt_str, fname, vset.imt.lineno))
        imts.add(imt_str)
        for vfun in vset.getnodes('discreteVulnerability'):
            taxonomy = vfun['vulnerabilityFunctionID']
            if taxonomy in taxonomies:
                raise InvalidFile(
                    'Duplicated vulnerabilityFunctionID: %s: %s, line %d' %
                    (taxonomy, fname, vfun.lineno))
            taxonomies.add(taxonomy)
            with context(fname, vfun):
                loss_ratios = ~vfun.lossRatio
                coefficients = ~vfun.coefficientsVariation
            if len(loss_ratios) != len(imls):
                raise InvalidFile(
                    'There are %d loss ratios, but %d imls: %s, line %d' %
                    (len(loss_ratios), len(imls), fname,
                     vfun.lossRatio.lineno))
            if len(coefficients) != len(imls):
                raise InvalidFile(
                    'There are %d coefficients, but %d imls: %s, line %d' %
                    (len(coefficients), len(imls), fname,
                     vfun.coefficientsVariation.lineno))
            with context(fname, vfun):
                vf_dict[imt_str, taxonomy] = scientific.VulnerabilityFunction(
                    imt_str, imls, loss_ratios, coefficients,
                    vfun['probabilisticDistribution'])
    return vf_dict


def get_imtls_from_vulnerabilities(inputs):
    """
    :param inputs:
        a dictionary {losstype_vulnerability: fname}
    :returns:
        a dictionary imt_str -> imls
    """
    # NB: different loss types may have different IMLs for the same IMT
    # in that case we merge the IMLs
    imtls = {}
    for loss_type, fname in vulnerability_files(inputs).iteritems():
        for (imt, taxonomy), vf in get_vulnerability_functions(fname).items():
            imls = list(vf.imls)
            if imt in imtls and imtls[imt] != imls:
                logging.info(
                    'Different levels for IMT %s: got %s, expected %s '
                    'in %s', imt, vf.imls, imtls[imt], fname)
                imtls[imt] = sorted(set(imls + imtls[imt]))
            else:
                imtls[imt] = imls
    return imtls


############################ fragility ##################################

class FragilityNode(LiteralNode):
    validators = valid.parameters(
        format=valid.ChoiceCI('discrete', 'continuous'),
        lossCategory=valid.name,
        IML=valid.IML,
        params=valid.fragilityparams,
        limitStates=valid.namelist,
        description=valid.utf8,
        type=valid.ChoiceCI('lognormal'),
        poEs=valid.probabilities,
        noDamageLimit=valid.positivefloat,
    )


class List(list):
    """
    Class to store lists of objects with common attributes
    """
    def __init__(self, elements, **attrs):
        list.__init__(self, elements)
        vars(self).update(attrs)


def get_fragility_functions(fname):
    """
    :param fname:
        path of the fragility file
    :returns:
        damage_states list and dictionary taxonomy -> functions
    """
    [fmodel] = read_nodes(
        fname, lambda el: el.tag.endswith('fragilityModel'), FragilityNode)
    # ~fmodel.description is ignored
    limit_states = ~fmodel.limitStates
    tag = 'ffc' if fmodel['format'] == 'continuous' else 'ffd'
    fragility_functions = {}  # taxonomy -> functions
    for ffs in fmodel.getnodes('ffs'):
        nodamage = ffs.attrib.get('noDamageLimit')
        taxonomy = ~ffs.taxonomy
        imt_str, imls, min_iml, max_iml = ~ffs.IML
        fragility_functions[taxonomy] = List([], imt=imt_str, imls=imls)
        lstates = []
        for ff in ffs.getnodes(tag):
            lstates.append(ff['ls'])
            if tag == 'ffc':
                with context(fname, ff):
                    mean_stddev = ~ff.params
                fragility_functions[taxonomy].append(
                    scientific.FragilityFunctionContinuous(*mean_stddev))
            else:  # discrete
                with context(fname, ff):
                    poes = ~ff.poEs
                if nodamage is None:
                    fragility_functions[taxonomy].append(
                        scientific.FragilityFunctionDiscrete(
                            imls, poes, imls[0]))
                else:
                    fragility_functions[taxonomy].append(
                        scientific.FragilityFunctionDiscrete(
                            [nodamage] + imls, [0.0] + poes, nodamage))
        if lstates != limit_states:
            raise InvalidFile("Expected limit states %s, got %s in %s" %
                             (limit_states, lstates, fname))

    return ['no_damage'] + limit_states, fragility_functions
