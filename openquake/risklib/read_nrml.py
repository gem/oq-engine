#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014-2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import logging
import itertools
import numpy

from openquake.baselib.node import Node, context
from openquake.hazardlib.nrml import node_to_obj, validators
from openquake.hazardlib import InvalidFile, valid
from openquake.risklib import scientific

F64 = numpy.float64


# ######################## node_to_obj definitions ######################### #

@node_to_obj.add(('vulnerabilityModel', 'nrml/0.4'))
def get_vulnerability_functions_04(node, fname):
    """
    :param node:
        a vulnerabilityModel node
    :param fname:
        path to the vulnerability file
    :returns:
        a dictionary imt, taxonomy -> vulnerability function
    """
    # NB: the fname below can contain non-ASCII characters
    logging.warn(u'Please upgrade %s to NRML 0.5', fname)
    # NB: the IMTs can be duplicated and with different levels, each
    # vulnerability function in a set will get its own levels
    imts = set()
    taxonomies = set()
    # imt, taxonomy -> vulnerability function
    vmodel = scientific.VulnerabilityModel(**node.attrib)
    for vset in node:
        imt_str = vset.IML['IMT']
        imls = ~vset.IML
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


@node_to_obj.add(('vulnerabilityModel', 'nrml/0.5'))
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
        attrs['imls'] = ~imls
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


@node_to_obj.add(('fragilityModel', 'nrml/0.5'))
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

@node_to_obj.add(('consequenceModel', 'nrml/0.5'))
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
                        raise ValueError("Expected '%s', got '%s'" %
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
        an :class:`openquake.commonib.node.Node` in NRML 0.4
    :param fname:
        path of the fragility file
    :returns:
        an :class:`openquake.commonib.node.Node` in NRML 0.5
    """
    convert_type = {"lognormal": "logncdf"}
    new = Node('fragilityModel',
               dict(assetCategory='building',
                    lossCategory='structural',
                    id='fm_%d_converted_from_NRML_04' %
                    next(fmcounter)))
    with context(fname, node):
        fmt = node['format']
        descr = ~node.description
        limit_states = ~node.limitStates
    new.append(Node('description', {}, descr))
    new.append((Node('limitStates', {}, ' '.join(limit_states))))
    for ffs in node[2:]:
        IML = ffs.IML
        # NB: noDamageLimit = None is different than zero
        nodamage = ffs.attrib.get('noDamageLimit')
        ff = Node('fragilityFunction', {'format': fmt})
        ff['id'] = ~ffs.taxonomy
        ff['shape'] = convert_type[ffs.attrib.get('type', 'lognormal')]
        if fmt == 'continuous':
            with context(fname, IML):
                attr = dict(imt=IML['IMT'],
                            minIML=IML['minIML'],
                            maxIML=IML['maxIML'])
                if nodamage is not None:
                    attr['noDamageLimit'] = nodamage
                ff.append(Node('imls', attr))
            for ffc in ffs[2:]:
                with context(fname, ffc):
                    ls = ffc['ls']
                    param = ffc.params
                with context(fname, param):
                    m, s = param['mean'], param['stddev']
                ff.append(Node('params', dict(ls=ls, mean=m, stddev=s)))
        else:  # discrete
            with context(fname, IML):
                imls = ' '.join(map(str, (~IML)[1]))
                attr = dict(imt=IML['IMT'])
            if nodamage is not None:
                attr['noDamageLimit'] = nodamage
            ff.append(Node('imls', attr, imls))
            for ffd in ffs[2:]:
                ls = ffd['ls']
                with context(fname, ffd):
                    poes = ' '.join(map(str, ~ffd.poEs))
                ff.append(Node('poes', dict(ls=ls), poes))
        new.append(ff)
    return new


@node_to_obj.add(('fragilityModel', 'nrml/0.4'))
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

# ######################## validators ######################## #


valid_loss_types = valid.Choice('structural', 'nonstructural', 'contents',
                                'business_interruption', 'occupants')


def asset_mean_stddev(value, assetRef, mean, stdDev):
    return assetRef, valid.positivefloat(mean), valid.positivefloat(stdDev)


def damage_triple(value, ds, mean, stddev):
    return ds, valid.positivefloat(mean), valid.positivefloat(stddev)


def update_validators():
    """
    Call this to updade the global nrml.validators
    """
    validators.update({
        'fragilityFunction.id': valid.utf8,  # taxonomy
        'vulnerabilityFunction.id': valid.utf8,  # taxonomy
        'consequenceFunction.id': valid.utf8,  # taxonomy
        'asset.id': valid.asset_id,
        'costType.name': valid.cost_type,
        'costType.type': valid.cost_type_type,
        'cost.type': valid.cost_type,
        'area.type': valid.name,
        'isAbsolute': valid.boolean,
        'insuranceLimit': valid.positivefloat,
        'deductible': valid.positivefloat,
        'occupants': valid.positivefloat,
        'value': valid.positivefloat,
        'retrofitted': valid.positivefloat,
        'number': valid.compose(valid.positivefloat, valid.nonzero),
        'vulnerabilitySetID': str,  # any ASCII string is fine
        'vulnerabilityFunctionID': str,  # any ASCII string is fine
        'lossCategory': valid.utf8,  # a description field
        'lr': valid.probability,
        'lossRatio': valid.positivefloats,
        'coefficientsVariation': valid.positivefloats,
        'probabilisticDistribution': valid.Choice('LN', 'BT'),
        'dist': valid.Choice('LN', 'BT', 'PM'),
        'meanLRs': valid.positivefloats,
        'covLRs': valid.positivefloats,
        'format': valid.ChoiceCI('discrete', 'continuous'),
        'mean': valid.positivefloat,
        'stddev': valid.positivefloat,
        'minIML': valid.positivefloat,
        'maxIML': valid.positivefloat,
        'limitStates': valid.namelist,
        'noDamageLimit': valid.NoneOr(valid.positivefloat),
        'loss_type': valid_loss_types,
        'losses': valid.positivefloats,
        'averageLoss': valid.positivefloat,
        'stdDevLoss': valid.positivefloat,
        'ffs.type': valid.ChoiceCI('lognormal'),
        'assetLifeExpectancy': valid.positivefloat,
        'interestRate': valid.positivefloat,
        'lossCategory': valid.utf8,
        'lossType': valid_loss_types,
        'aalOrig': valid.positivefloat,
        'aalRetr': valid.positivefloat,
        'ratio': valid.positivefloat,
        'cf': asset_mean_stddev,
        'damage': damage_triple,
        'damageStates': valid.namelist,
    })
