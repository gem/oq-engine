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
import itertools
import collections

import numpy

from openquake.commonlib.node import context, LiteralNode
from openquake.commonlib import InvalidFile, nrml, valid
from openquake.risklib import scientific
from openquake.commonlib.sourcewriter import obj_to_node

F64 = numpy.float64

LOSS_TYPE_KEY = re.compile(
    '(structural|nonstructural|contents|business_interruption|'
    'occupants|fragility)_([\w_]+)')


def get_risk_files(inputs):
    """
    :param inputs: a dictionary key -> path name
    :returns: a pair (file_type, {cost_type: path})
    """
    vfs = {}
    names = set()
    for key in inputs:
        if key == 'fragility':
            # backward compatibily for .ini files with key fragility_file
            # instead of structural_fragility_file
            vfs['structural'] = inputs['structural_fragility'] = inputs[key]
            names.add('fragility')
            del inputs['fragility']
            continue
        match = LOSS_TYPE_KEY.match(key)
        if match and 'retrofitted' not in key and 'consequence' not in key:
            vfs[match.group(1)] = inputs[key]
            names.add(match.group(2))
    if not names:
        return None, {}
    elif len(names) > 1:
        raise ValueError('Found inconsistent keys %s in the .ini file'
                         % ', '.join(names))
    return names.pop(), vfs


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
    for cost_type in get_risk_files(inputs)[1]:
        key = '%s_vulnerability%s' % (cost_type, retro)
        if key not in inputs:
            continue
        vf_dict = nrml.parse(inputs[key])
        for (imt, tax), vf in vf_dict.items():
            vulnerability_functions[imt, tax][
                cost_type_to_loss_type(cost_type)] = vf
    return vulnerability_functions


def get_ffs(file_by_ct, continuous_fragility_discretization,
            steps_per_interval=None):
    """
    Given a dictionary {key: pathname}, look for keys with name
    <cost_type>__fragility, parse them and returns a dictionary
    imt, taxonomy -> ff_by_loss_type.

    :param file_by_ct: a dictionary cost_type -> pathname
    :param continuous_fragility_discretization: parameter from the .ini file
    :param steps_per_interval: steps_per_interval parameter
    """
    ffs = collections.defaultdict(dict)
    for cost_type in file_by_ct:
        ff_dict = nrml.parse(
            file_by_ct[cost_type],
            continuous_fragility_discretization, steps_per_interval)
        for tax, ff in ff_dict.items():
            ffs[ff.imt, tax][cost_type_to_loss_type(cost_type)] = ff
    return ffs, ff_dict.damage_states


# ########################### vulnerability ############################## #

def filter_vset(elem):
    return elem.tag.endswith('discreteVulnerabilitySet')


@obj_to_node.add('VulnerabilityFunction')
def build_vf_node(vf):
    """
    Convert a VulnerabilityFunction object into a LiteralNode suitable
    for XML conversion.
    """
    nodes = [LiteralNode('imls', {'imt': vf.imt}, vf.imls),
             LiteralNode('meanLRs', {}, vf.mean_loss_ratios),
             LiteralNode('covLRs', {}, vf.covs)]
    return LiteralNode(
        'vulnerabilityFunction',
        {'id': vf.id, 'dist': vf.distribution_name}, nodes=nodes)


def get_risk_models(kind, inputs):
    """
    :param kind: the string 'fragility', 'consequence'
    :param inputs: a dictionary key -> path name
    :returns: a dictionary loss_type -> ConsequenceModel instance
    """
    rmodels = {}
    for key in inputs:
        mo = re.match(
            '(structural|nonstructural|contents|business_interruption)'
            '_' + kind, key)
        if mo:
            rmodel = nrml.parse(inputs[key])
            expected_loss_type = mo.group(1)  # the loss type in the key
            if rmodel.lossCategory != expected_loss_type:
                raise ValueError(
                    'Error in the .ini file: "%s_file=%s" is of type "%s", '
                    'expected "%s"' % (key, inputs[key], rmodel.lossCategory,
                                       expected_loss_type))
            rmodels[rmodel.lossCategory] = rmodel
    return rmodels


@nrml.build.add(('vulnerabilityModel', 'nrml/0.4'))
def get_vulnerability_functions_04(node, fname):
    """
    :param node:
        a vulnerabilityModel node
    :param fname:
        path to the vulnerability file
    :returns:
        a dictionary imt, taxonomy -> vulnerability function
    """
    logging.warn('Please upgrade %s to NRML 0.5', fname)
    # NB: the IMTs can be duplicated and with different levels, each
    # vulnerability function in a set will get its own levels
    imts = set()
    taxonomies = set()
    vf_dict = {}  # imt, taxonomy -> vulnerability function
    for vset in node:
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


@nrml.build.add(('vulnerabilityModel', 'nrml/0.5'))
def get_vulnerability_functions_05(node, fname):
    """
    :param node:
        a vulnerabilityModel node
    :param fname:
        path of the vulnerability filter
    :returns:
        a dictionary imt, taxonomy -> vulnerability function
    """
    # NB: the IMTs can be duplicated and with different levels, each
    # vulnerability function in a set will get its own levels
    taxonomies = set()
    vf_dict = {}  # imt, taxonomy -> vulnerability function
    for vfun in node.getnodes('vulnerabilityFunction'):
        with context(fname, vfun):
            imt = vfun.imls['imt']
            imls = numpy.array(~vfun.imls)
            taxonomy = vfun['id']
        if taxonomy in taxonomies:
            raise InvalidFile(
                'Duplicated vulnerabilityFunctionID: %s: %s, line %d' %
                (taxonomy, fname, vfun.lineno))
        if vfun['dist'] == 'PM':
            loss_ratios, probs = [], []
            for probabilities in vfun[1:]:
                loss_ratios.append(probabilities['lr'])
                probs.append(valid.probabilities(~probabilities))
            probs = numpy.array(probs)
            assert probs.shape == (len(loss_ratios), len(imls))
            vf_dict[imt, taxonomy] = (
                scientific.VulnerabilityFunctionWithPMF(
                    taxonomy, imt, imls, numpy.array(loss_ratios),
                    probs, seed=42))  # it is fine to hard-code it
        else:
            with context(fname, vfun):
                loss_ratios = ~vfun.meanLRs
                coefficients = ~vfun.covLRs
            if len(loss_ratios) != len(imls):
                raise InvalidFile(
                    'There are %d loss ratios, but %d imls: %s, line %d' %
                    (len(loss_ratios), len(imls), fname,
                     vfun.meanLRs.lineno))
            if len(coefficients) != len(imls):
                raise InvalidFile(
                    'There are %d coefficients, but %d imls: %s, '
                    'line %d' % (len(coefficients), len(imls), fname,
                                 vfun.covLRs.lineno))
            with context(fname, vfun):
                vf_dict[imt, taxonomy] = scientific.VulnerabilityFunction(
                    taxonomy, imt, imls, loss_ratios, coefficients,
                    vfun['dist'])
    return vf_dict


def get_imtls(ddict):
    """
    :param ddict:
        a dictionary (imt, taxo) -> loss_type -> risk_function
    :returns:
        a dictionary imt_str -> imls
    """
    # NB: different loss types may have different IMLs for the same IMT
    # in that case we merge the IMLs
    imtls = {}
    for (imt, taxonomy), dic in ddict.items():
        for loss_type, rf in dic.items():
            if hasattr(rf, 'orig_imls'):
                imls = list(rf.orig_imls)
            else:
                imls = list(rf.imls)
            if imt in imtls and imtls[imt] != imls:
                logging.info(
                    'Different levels for IMT %s: got %s, expected %s',
                    imt, imls, imtls[imt])
                imtls[imt] = sorted(set(imls + imtls[imt]))
            else:
                imtls[imt] = imls
    return imtls


# ########################### fragility ############################### #

def ffconvert(fname, limit_states, ff):
    """
    Convert a fragility function into a numpy array plus a bunch
    of attributes.

    :param fname: path to the fragility model file
    :param limit_states: expected limit states
    :param ff: fragility function node
    :returns: a pair (array, dictionary)
    """
    with context(fname, ff):
        ffs = ff[1:]
        imls = ff.imls
    with context(fname, imls):
        attrs = dict(format=ff['format'],
                     imt=imls['imt'],
                     nodamage=imls.attrib.get('noDamageLimit'))

    LS = len(limit_states)
    if LS != len(ffs):
        with context(fname, ff):
            raise InvalidFile('expected %d limit states, found %d' %
                              (LS, len(ffs)))
    if ff['format'] == 'continuous':
        attrs['minIML'] = float(imls['minIML'])
        attrs['maxIML'] = float(imls['maxIML'])
        array = numpy.zeros(LS, [('mean', F64), ('stddev', F64)])
        for i, ls, node in zip(range(LS), limit_states, ff[1:]):
            if ls != node['ls']:
                with context(fname, node):
                    raise InvalidFile('expected %s, found' %
                                      (ls, node['ls']))
            array['mean'][i] = node['mean']
            array['stddev'][i] = node['stddev']
    elif ff['format'] == 'discrete':
        attrs['imls'] = valid.positivefloats(~imls)
        valid.check_levels(attrs['imls'], attrs['imt'])
        num_poes = len(attrs['imls'])
        array = numpy.zeros((LS, num_poes))
        for i, ls, node in zip(range(LS), limit_states, ff[1:]):
            with context(fname, node):
                if ls != node['ls']:
                    raise InvalidFile('expected %s, found' %
                                      (ls, node['ls']))
                poes = (~node if isinstance(~node, list)
                        else valid.probabilities(~node))
                if len(poes) != num_poes:
                    raise InvalidFile('expected %s, found' %
                                      (num_poes, len(poes)))
                array[i, :] = poes
    # NB: the format is constrained in nrml.FragilityNode to be either
    # discrete or continuous, there is no third option
    return array, attrs


@nrml.build.add(('fragilityModel', 'nrml/0.5'))
def get_fragility_model(node, fname):
    """
    :param node:
        a vulnerabilityModel node
    :param fname:
        path to the vulnerability file
    :returns:
        a dictionary imt, taxonomy -> fragility function list
    """
    with context(fname, node):
        fid = node['id']
        asset_category = node['assetCategory']
        loss_type = node['lossCategory']
        description = ~node.description
        limit_states = ~node.limitStates
        ffs = node[2:]
    fmodel = scientific.FragilityModel(
        fid, asset_category, loss_type, description, limit_states)
    for ff in ffs:
        imt_taxo = ff.imls['imt'], ff['id']
        array, attrs = ffconvert(fname, limit_states, ff)
        ffl = scientific.FragilityFunctionList(array)
        vars(ffl).update(attrs)
        fmodel[imt_taxo] = ffl
    return fmodel


# ################################## consequences ########################## #

@nrml.build.add(('consequenceModel', 'nrml/0.5'))
def get_consequence_model(node, fname):
    with context(fname, node):
        description = ~node.description  # make sure it is there
        limitStates = ~node.limitStates  # make sure it is there
        # ASK: is the 'id' mandatory?
        node['assetCategory']  # make sure it is there
        node['lossCategory']  # make sure it is there
        cfs = node[2:]
    functions = {}
    for cf in cfs:
        with context(fname, cf):
            params = []
            if len(limitStates) != len(cf):
                raise ValueError(
                    'Expected %d limit states, got %d' %
                    (len(limitStates), len(cf)))
            for ls, param in zip(limitStates, cf):
                with context(fname, param):
                    if param['ls'] != ls:
                        raise ValueError('Expected %r, got %r' %
                                         (ls, param['ls']))
                    params.append((param['mean'], param['stddev']))
            functions[cf['id']] = scientific.ConsequenceFunction(
                cf['id'], cf['dist'], params)
    attrs = node.attrib.copy()
    attrs.update(description=description, limitStates=limitStates)
    cmodel = scientific.ConsequenceModel(**attrs)
    cmodel.update(functions)
    return cmodel


# deprecated

def convert_fragility_model_04(node, fmcounter=itertools.count(1)):
    """
    :param node:
        an :class:`openquake.commonib.node.LiteralNode` in NRML 0.4
    :returns:
        an :class:`openquake.commonib.node.LiteralNode` in NRML 0.5
    """
    convert_type = {"lognormal": "logncdf"}
    new = LiteralNode('fragilityModel',
                      dict(assetCategory='building',
                           lossCategory='structural',
                           id='fm_%d_converted_from_NRML_04' %
                           next(fmcounter)))
    fmt = node['format']
    descr = ~node.description
    limit_states = ~node.limitStates
    new.append(LiteralNode('description', {}, descr))
    new.append((LiteralNode('limitStates', {}, ' '.join(limit_states))))
    for ffs in node[2:]:
        IML = ffs.IML
        # NB: noDamageLimit = None is different than zero
        nodamage = ffs.attrib.get('noDamageLimit')
        ff = LiteralNode('fragilityFunction', {'format': fmt})
        ff['id'] = ~ffs.taxonomy
        ff['shape'] = convert_type[ffs.attrib.get('type', 'lognormal')]
        if fmt == 'continuous':
            ff.append(LiteralNode('imls', dict(imt=IML['IMT'],
                                               minIML=IML['minIML'],
                                               maxIML=IML['maxIML'],
                                               noDamageLimit=nodamage)))
            for ffc in ffs[2:]:
                ls = ffc['ls']
                param = ffc.params
                ff.append(LiteralNode('params', dict(ls=ls,
                                                     mean=param['mean'],
                                                     stddev=param['stddev'])))
        else:  # discrete
            imls = ' '.join(map(str, (~IML)[1]))
            attr = dict(imt=IML['IMT'])
            if nodamage is not None:
                attr['noDamageLimit'] = nodamage
            ff.append(LiteralNode('imls', attr, imls))
            for ffd in ffs[2:]:
                ls = ffd['ls']
                poes = ' '.join(map(str, ~ffd.poEs))
                ff.append(LiteralNode('poes', dict(ls=ls), poes))
        new.append(ff)
    return new


@nrml.build.add(('fragilityModel', 'nrml/0.4'))
def get_fragility_model_04(fmodel, fname):
    """
    :param fmodel:
        a fragilityModel node
    :param fname:
        path of the fragility file
    :returns:
        an :class:`openquake.risklib.scientific.FragilityModel` instance
    """
    logging.warn('Please upgrade %s to NRML 0.5', fname)
    node05 = convert_fragility_model_04(fmodel)
    node05.limitStates.text = node05.limitStates.text.split()
    return get_fragility_model(node05, fname)
