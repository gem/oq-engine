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
import re
import logging
import collections

import numpy

from openquake.commonlib.node import read_nodes, context
from openquake.commonlib import InvalidFile
from openquake.risklib import scientific
from openquake.baselib.general import AccumDict
from openquake.commonlib.nrml import nodefactory

VULNERABILITY_KEY = re.compile('(structural|nonstructural|contents|'
                               'business_interruption|occupants)_([\w_]+)')


def vulnerability_files(inputs):
    """
    Return a dict cost_type -> path for the known vulnerability keys

    :param inputs: a dictionary key -> path name
    """
    vfs = {}
    for key in inputs:
        match = VULNERABILITY_KEY.match(key)
        if match:
            vfs[match.group(1)] = inputs[key]
    return vfs


def fragility_files(inputs):
    """
    Return a dict of the form {} or {'damage': path}.

    :param inputs: a dictionary key -> path name

    NB: at the moment there is a single fragility key, so the output
    contains at most one element.
    """
    return {'damage': inputs[key] for key in inputs if key == 'fragility'}


# loss types (in the risk models) and cost types (in the exposure)
# are the sames except for fatalities -> occupants

def loss_type_to_cost_type(lt):
    """
    Convert a loss_type string into a cost_type string.

    :param lt: loss type
    """
    return 'occupants' if lt == 'fatalities' else lt


def cost_type_to_loss_type(ct):
    """
    Convert a cost_type string into a loss_type string

    :param ct: loss type
    """
    return 'fatalities' if ct == 'occupants' else ct


def get_vfs(inputs, retrofitted=False):
    """
    Given a dictionary {key: pathname}, look for keys with name
    <cost_type>__vulnerability, parse them and returns a dictionary
    imt, taxonomy -> vf_by_loss_type.

    :param inputs: a dictionary key -> pathname
    :param retrofitted: a flag (default False)
    """
    retro = '_retrofitted' if retrofitted else ''
    vulnerability_functions = collections.defaultdict(dict)
    for cost_type in vulnerability_files(inputs):
        key = '%s_vulnerability%s' % (cost_type, retro)
        if key not in inputs:
            continue
        vf_dict = get_vulnerability_functions(inputs[key])
        for (imt, tax), vf in vf_dict.iteritems():
            vulnerability_functions[imt, tax][
                cost_type_to_loss_type(cost_type)] = vf
    return vulnerability_functions


############################ vulnerability ##################################


def filter_vset(elem):
    return elem.tag.endswith('discreteVulnerabilitySet')


# this works only for discreteVulnerabilitySet, since there are no
# continuousVulnerabilitySet
def get_vulnerability_functions(fname):
    """
    :param fname:
        path of the vulnerability filter
    :returns:
        a dictionary imt, taxonomy -> vulnerability function
    """
    # NB: the vulnerabilitySetID is not an unique ID!
    # it is right to have several vulnerability sets with the same ID
    # the IMTs can also be duplicated and with different levels, each
    # vulnerability function in a set will get its own levels
    imts = set()
    taxonomies = set()
    vf_dict = {}  # imt, taxonomy -> vulnerability function
    for vset in read_nodes(fname, filter_vset,
                           nodefactory['vulnerabilityModel']):
        imt_str, imls, min_iml, max_iml, imlUnit = ~vset.IML
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
                    taxonomy, imt_str, imls, loss_ratios, coefficients,
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

def get_fragility_functions(fname, continuous_fragility_discretization,
                            steps_per_interval=None):
    """
    :param fname:
        path of the fragility file
    :param continuous_fragility_discretization:
        continuous_fragility_discretization parameter
    :param steps_per_interval:
        steps_per_interval parameter
    :returns:
        damage_states list and dictionary taxonomy -> functions
    """
    [fmodel] = read_nodes(
        fname, lambda el: el.tag.endswith('fragilityModel'),
        nodefactory['fragilityModel'])
    # ~fmodel.description is ignored
    limit_states = ~fmodel.limitStates
    tag = 'ffc' if fmodel['format'] == 'continuous' else 'ffd'
    fragility_functions = AccumDict()  # taxonomy -> functions
    for ffs in fmodel.getnodes('ffs'):
        add_zero_value = False
        # NB: the noDamageLimit is only defined for discrete fragility
        # functions. It is a way to set the starting point of the functions:
        # if noDamageLimit is at the left of each IMLs, it means that the
        # function starts at zero at the given point, so we need to add
        # noDamageLimit to the list of IMLs and zero to the list of poes
        nodamage = ffs.attrib.get('noDamageLimit')
        taxonomy = ~ffs.taxonomy
        imt_str, imls, min_iml, max_iml, imlUnit = ~ffs.IML

        if fmodel['format'] == 'discrete':
            if nodamage is not None and nodamage < imls[0]:
                # discrete fragility
                imls = [nodamage] + imls
                add_zero_value = True
            if steps_per_interval:
                gen_imls = scientific.fine_graining(imls, steps_per_interval)
            else:
                gen_imls = imls
        else:  # continuous:
            if min_iml is None:
                raise InvalidFile(
                    'Missing attribute minIML, line %d' % ffs.IML.lineno)
            elif max_iml is None:
                raise InvalidFile(
                    'Missing attribute maxIML, line %d' % ffs.IML.lineno)
            gen_imls = numpy.linspace(min_iml, max_iml,
                                      continuous_fragility_discretization)
        fragility_functions[taxonomy] = scientific.FragilityFunctionList(
            [], imt=imt_str, imls=list(gen_imls),
            no_damage_limit=nodamage,
            continuous_fragility_discretization=
            continuous_fragility_discretization,
            steps_per_interval=steps_per_interval)
        lstates = []
        for ff in ffs.getnodes(tag):
            ls = ff['ls']  # limit state
            lstates.append(ls)
            if tag == 'ffc':
                with context(fname, ff):
                    mean_stddev = ~ff.params
                fragility_functions[taxonomy].append(
                    scientific.FragilityFunctionContinuous(ls, *mean_stddev))
            else:  # discrete
                with context(fname, ff):
                    poes = ~ff.poEs
                if add_zero_value:
                    poes = [0.] + poes

                fragility_functions[taxonomy].append(
                    scientific.FragilityFunctionDiscrete(
                        ls, imls, poes, nodamage))

        if lstates != limit_states:
            raise InvalidFile("Expected limit states %s, got %s in %s" %
                             (limit_states, lstates, fname))

    fragility_functions.damage_states = ['no_damage'] + limit_states
    return fragility_functions
