import logging
import collections

from openquake.nrmllib.node import read_nodes, LiteralNode, context
from openquake.nrmllib import InvalidFile
from openquake.commonlib import valid

from openquake.commonlib.oqvalidation import vulnerability_files


############################ vulnerability ##################################

class VulnerabilityNode(LiteralNode):
    """
    Literal Node class used to validate discrete vulnerability functions
    """
    validators = valid.parameters(
        vulnerabilitySetID=valid.name,
        vulnerabilityFunctionID=valid.name_with_dashes,
        assetCategory=str,
        lossCategory=valid.name,
        IML=valid.IML,
        lossRatio=valid.positivefloats,
        coefficientsVariation=valid.positivefloats,
    )

VSet = collections.namedtuple(
    'VSet', 'imt imls vfunctions'.split())

VFunction = collections.namedtuple(
    'VFunction', 'id lossRatio coefficientsVariation'.split())


def filter_vset(elem):
    return elem.tag.endswith('discreteVulnerabilitySet')


def get_vulnerability_sets(fname):
    """
    Yields VSet namedtuples, each containing imt, imls and
    vulnerability functions.

    :param fname:
        path of the vulnerability filter
    """
    imts = set()
    for vset in read_nodes(fname, filter_vset, VulnerabilityNode):
        imt_str, imls, min_iml, max_iml = ~vset.IML
        if imt_str in imts:
            raise InvalidFile('Duplicated IMT %s: %s, line %d' %
                              (imt_str, fname, vset.imt.lineno))
        imts.add(imt_str)
        vfuns = []
        for vfun in vset.getnodes('discreteVulnerability'):
            with context(fname, vfun):
                vf = VFunction(vfun['vulnerabilityFunctionID'],
                               ~vfun.lossRatio, ~vfun.coefficientsVariation)
            if len(vf.lossRatio) != len(imls):
                raise InvalidFile(
                    'There are %d loss ratios, but %d imls: %s, line %d' %
                    (len(vf.lossRatio), len(imls), fname, vf.lossRatio.lineno))
            elif len(vf.coefficientsVariation) != len(imls):
                raise InvalidFile(
                    'There are %d coefficients, but %d imls: %s, line %d' %
                    (len(vf.coefficientsVariation), len(imls), fname,
                     vf.coefficientsVariation.lineno))
            vfuns.append(vf)
        yield VSet(imt_str, imls, vfuns)


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
    for loss_type, fname in vulnerability_files(inputs):
        for vset in get_vulnerability_sets(fname):
            imt = vset.imt
            if imt in imtls and imtls[imt] != vset.imls:
                logging.warn(
                    'Different levels for IMT %s: got %s, expected %s in %s',
                    imt, vset.imls, imtls[imt], fname)
                imtls[imt] = sorted(set(vset.imls + imtls[imt]))
            else:
                imtls[imt] = vset.imls
    return imtls


############################ fragility ##################################

class FragilityNode(LiteralNode):
    validators = valid.parameters(
        format=valid.Choice('discrete', 'continuous'),
        lossCategory=valid.name,
        IML=valid.IML,
        params=valid.fragilityparams,
        limitStates=valid.namelist,
        description=valid.utf8,
        type=valid.Choice('lognormal'),
        poEs=valid.probabilities,
        noDamageLimit=valid.positivefloat,
    )


FSet = collections.namedtuple(
    'FSet', ['imt', 'imls', 'min_iml', 'max_iml', 'taxonomy', 'nodamagelimit',
             'limit_states', 'ffunctions'])

FFunction = collections.namedtuple(
    'FFunction', 'limit_state params poes'.split())


def get_fragility_sets(fname):
    """
    :param fname:
        path of the fragility file
    """
    [fmodel] = read_nodes(
        fname, lambda el: el.tag.endswith('fragilityModel'), FragilityNode)
    # ~fmodel.description is ignored
    limit_states = ~fmodel.limitStates
    tag = 'ffc' if fmodel['format'] == 'continuous' else 'ffd'
    for ffs in fmodel.getnodes('ffs'):
        nodamage = ffs.attrib.get('noDamageLimit')
        taxonomy = ~ffs.taxonomy
        imt_str, imls, min_iml, max_iml = ~ffs.IML
        fset = []
        lstates = []
        for ff in ffs.getnodes(tag):
            lstates.append(ff['ls'])
            if tag == 'ffc':
                fset.append(FFunction(ff['ls'], ~ff.params, None))
            else:
                fset.append(FFunction(ff['ls'], None, ~ff.poEs))
        if lstates != limit_states:
            raise InvalidFile("Expected limit states %s, got %s in %s" %
                             (limit_states, lstates, fname))
        yield FSet(imt_str, imls, min_iml, max_iml, taxonomy, nodamage,
                   limit_states, fset)
