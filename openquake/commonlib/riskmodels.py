# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

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

COST_TYPE_REGEX = '|'.join(valid.cost_type.choices)

LOSS_TYPE_KEY = re.compile(
    '(%s|occupants|fragility)_([\w_]+)' % COST_TYPE_REGEX)


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


# ########################### vulnerability ############################## #

def filter_vset(elem):
    return elem.etag.endswith('discreteVulnerabilitySet')


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


def get_risk_models(oqparam, kind=None):
    """
    :param oqparam:
        an OqParam instance
    :param kind:
        vulnerability|vulnerability_retrofitted|fragility|consequence;
        if None it is extracted from the oqparam.file_type attribute
    :returns:
        a dictionary taxonomy -> loss_type -> function
    """
    kind = kind or oqparam.file_type
    rmodels = {}
    for key in oqparam.inputs:
        mo = re.match('(occupants|%s)_%s$' % (COST_TYPE_REGEX, kind), key)
        if mo:
            key_type = mo.group(1)  # the cost_type in the key
            # can be occupants, structural, nonstructural, ...
            rmodel = nrml.parse(oqparam.inputs[key])
            rmodels[key_type] = rmodel
            if rmodel.lossCategory is None:  # NRML 0.4
                continue
            cost_type = str(rmodel.lossCategory)
            rmodel_kind = rmodel.__class__.__name__
            kind_ = kind.replace('_retrofitted', '')  # strip retrofitted
            if not rmodel_kind.lower().startswith(kind_):
                raise ValueError(
                    'Error in the file "%s_file=%s": is '
                    'of kind %s, expected %s' % (
                        key, oqparam.inputs[key], rmodel_kind,
                        kind.capitalize() + 'Model'))
            if cost_type != key_type:
                raise ValueError(
                    'Error in the file "%s_file=%s": lossCategory is of type '
                    '"%s", expected "%s"' % (key, oqparam.inputs[key],
                                             rmodel.lossCategory, key_type))
    rdict = collections.defaultdict(dict)
    if kind == 'fragility':
        limit_states = []
        for loss_type, fm in sorted(rmodels.items()):
            # build a copy of the FragilityModel with different IM levels
            newfm = fm.build(oqparam.continuous_fragility_discretization,
                             oqparam.steps_per_interval)
            for (imt, taxo), ffl in newfm.items():
                if not limit_states:
                    limit_states.extend(fm.limitStates)
                # we are rejecting the case of loss types with different
                # limit states; this may change in the future
                assert limit_states == fm.limitStates, (
                    limit_states, fm.limitStates)
                rdict[taxo][loss_type] = ffl
                # TODO: see if it is possible to remove the attribute
                # below, used in classical_damage
                ffl.steps_per_interval = oqparam.steps_per_interval
        oqparam.limit_states = limit_states
    elif kind == 'consequence':
        rdict = rmodels
    else:  # vulnerability
        cl_risk = oqparam.calculation_mode in ('classical', 'classical_risk')
        # only for classical_risk reduce the loss_ratios
        # to make sure they are strictly increasing
        for loss_type, rm in rmodels.items():
            for (imt, taxo), rf in rm.items():
                rdict[taxo][loss_type] = (
                    rf.strictly_increasing() if cl_risk else rf)
    return rdict


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
    # imt, taxonomy -> vulnerability function
    vmodel = scientific.VulnerabilityModel(**node.attrib)
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
                vmodel[imt_str, taxonomy] = scientific.VulnerabilityFunction(
                    taxonomy, imt_str, imls, loss_ratios, coefficients,
                    vfun['probabilisticDistribution'])
    return vmodel


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
    vmodel = scientific.VulnerabilityModel(**node.attrib)
    # imt, taxonomy -> vulnerability function
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
            vmodel[imt, taxonomy] = (
                scientific.VulnerabilityFunctionWithPMF(
                    taxonomy, imt, imls, numpy.array(loss_ratios),
                    probs))  # the seed will be set by readinput.get_risk_model
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
                vmodel[imt, taxonomy] = scientific.VulnerabilityFunction(
                    taxonomy, imt, imls, loss_ratios, coefficients,
                    vfun['dist'])
    return vmodel


# ########################### fragility ############################### #


def ffconvert(fname, limit_states, ff, min_iml=1E-10):
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
    nodamage = imls.attrib.get('noDamageLimit')
    if nodamage == 0:
        # use a cutoff to avoid log(0) in GMPE.to_distribution_values
        logging.warn('Found a noDamageLimit=0 in %s, line %s, '
                     'using %g instead', fname, ff.lineno, min_iml)
        nodamage = min_iml
    with context(fname, imls):
        attrs = dict(format=ff['format'],
                     imt=imls['imt'],
                     nodamage=nodamage)

    LS = len(limit_states)
    if LS != len(ffs):
        with context(fname, ff):
            raise InvalidFile('expected %d limit states, found %d' %
                              (LS, len(ffs)))
    if ff['format'] == 'continuous':
        minIML = float(imls['minIML'])
        if minIML == 0:
            # use a cutoff to avoid log(0) in GMPE.to_distribution_values
            logging.warn('Found minIML=0 in %s, line %s, using %g instead',
                         fname, imls.lineno, min_iml)
            minIML = min_iml
        attrs['minIML'] = minIML
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


# utility to convert the old, deprecated format
def convert_fragility_model_04(node, fname, fmcounter=itertools.count(1)):
    """
    :param node:
        an :class:`openquake.commonib.node.LiteralNode` in NRML 0.4
    :param fname:
        path of the fragility file
    :returns:
        an :class:`openquake.commonib.node.LiteralNode` in NRML 0.5
    """
    convert_type = {"lognormal": "logncdf"}
    new = LiteralNode('fragilityModel',
                      dict(assetCategory='building',
                           lossCategory='structural',
                           id='fm_%d_converted_from_NRML_04' %
                           next(fmcounter)))
    with context(fname, node):
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
            with context(fname, IML):
                attr = dict(imt=IML['IMT'],
                            minIML=IML['minIML'],
                            maxIML=IML['maxIML'])
                if nodamage is not None:
                    attr['noDamageLimit'] = nodamage
                ff.append(LiteralNode('imls', attr))
            for ffc in ffs[2:]:
                with context(fname, ffc):
                    ls = ffc['ls']
                    param = ffc.params
                with context(fname, param):
                    m, s = param['mean'], param['stddev']
                ff.append(LiteralNode('params', dict(ls=ls, mean=m, stddev=s)))
        else:  # discrete
            with context(fname, IML):
                imls = ' '.join(map(str, (~IML)[1]))
                attr = dict(imt=IML['IMT'])
            if nodamage is not None:
                attr['noDamageLimit'] = nodamage
            ff.append(LiteralNode('imls', attr, imls))
            for ffd in ffs[2:]:
                ls = ffd['ls']
                with context(fname, ffd):
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
    node05 = convert_fragility_model_04(fmodel, fname)
    node05.limitStates.text = node05.limitStates.text.split()
    return get_fragility_model(node05, fname)
