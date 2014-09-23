import logging
import collections
import decimal

import numpy

from openquake.hazardlib import geo, site
from openquake.nrmllib.node import read_nodes, LiteralNode, context
from openquake.nrmllib import InvalidFile
from openquake.commonlib import valid
from openquake.commonlib.oqvalidation import fragility_files, vulnerability_files
from openquake.commonlib.converter import Converter
from openquake.commonlib.source import ValidNode, RuptureConverter


def get_mesh(oqparam):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, the region or the exposure.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if getattr(oqparam, 'sites', None):
        lons, lats = zip(*oqparam.sites)
        return geo.Mesh(numpy.array(lons), numpy.array(lats))
    elif 'site' in oqparam.inputs:
        csv_data = open(oqparam.inputs['site'], 'U').read()
        coords = valid.coordinates(
            csv_data.strip().replace(',', ' ').replace('\n', ','))
        lons, lats = zip(*coords)
        return geo.Mesh(numpy.array(lons), numpy.array(lats))
    elif getattr(oqparam, 'region', None):
        # close the linear polygon ring by appending the first
        # point to the end
        firstpoint = geo.Point(*oqparam.region[0])
        points = [geo.Point(*xy) for xy in oqparam.region] + [firstpoint]
        return geo.Polygon(points).discretize(oqparam.region_grid_spacing)
    elif 'exposure' in oqparam.inputs:
        exposure = Converter.from_nrml(oqparam.inputs['exposure'])
        coords = sorted(set((s.lon, s.lat)
                            for s in exposure.tableset.tableLocation))
        lons, lats = zip(*coords)
        return geo.Mesh(numpy.array(lons), numpy.array(lats))


class SiteModelNode(LiteralNode):
    validators = valid.parameters(site=valid.site_param)


def get_site_model(oqparam):
    """
    Convert the NRML file into an iterator over 6-tuple of the form
    (z1pt0, z2pt5, measured, vs30, lon, lat)

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    for node in read_nodes(oqparam.inputs['site_model'],
                           lambda el: el.tag.endswith('site'),
                           SiteModelNode):
        yield ~node


def get_site_collection(oqparam, mesh=None, site_ids=None,
                        site_model_params=None):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param mesh:
        a mesh of hazardlib points; if None the mesh is
        determined by invoking get_mesh
    :param site_ids:
        a list of integers to identify the points; if None, a
        range(1, len(points) + 1) is used
    :param site_model_params:
        object with a method ,get_closest returning the closest site
        model parameters and their distance from each point
    """
    mesh = mesh or get_mesh(oqparam)
    site_ids = site_ids or range(1, len(mesh) + 1)
    if oqparam.inputs.get('site_model'):
        sitecol = []
        exact_matches = 0
        for i, pt in zip(site_ids, mesh):
            param, dist = site_model_params.\
                get_closest(pt.longitude, pt.latitude)
            exact_matches += dist is 0
            sitecol.append(site.Site(pt, param.vs30, param.measured,
                                     param.z1pt0, param.z2pt5, i))
        if exact_matches:
            msg = ('Found %d site model parameters exactly at the hazard '
                   'sites, out of %d total sites' %
                   (exact_matches, len(sitecol)))
            logging.info(msg)
        return site.SiteCollection(sitecol)

    # else use the default site params
    return site.SiteCollection.from_points(
        mesh.lons, mesh.lats, site_ids, oqparam)


def get_rupture(oqparam):
    """
    Returns a hazardlib rupture by reading the `rupture_model` file.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    conv = RuptureConverter(oqparam.rupture_mesh_spacing)
    rup_model = oqparam.inputs['rupture_model']
    rup_node, = read_nodes(rup_model, lambda el: 'Rupture' in el.tag,
                           ValidNode)
    return conv.convert_node(rup_node)


def get_source_models(oqparam):
    """
    Read all the source models specified in oqparam.
    Yield pairs (fname, sources).

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    for fname in oqparam.inputs['source']:
        srcs = read_nodes(fname, lambda elem: 'Source' in elem.tag, ValidNode)
        yield fname, srcs


class GsimLtNode(LiteralNode):
    """GSIM Logic Tree Node"""

    validators = valid.parameters(
        branchSetID=valid.name,
        uncertaintyType=valid.Choice('gmpeModel'),
        uncertaintyWeight=decimal.Decimal,
    )

BranchSet = collections.namedtuple('BranchSet', 'id type attrib branches')

Branch = collections.namedtuple('Branch', 'id value weight')


uncertaintytype2validator = dict(
    sourceModel=valid.utf8,
    gmpeModel=valid.gsim,
    maxMagGRAbsolute=valid.positivefloat,
    bGRRelative=float,
    abGRAbsolute=valid.ab_values)


def _branches(branchset, known_attribs):
    attrib = branchset.attrib.copy()
    del attrib['branchSetID']
    utype = attrib.pop('uncertaintyType')
    validator = uncertaintytype2validator[utype]
    assert set(attrib) <= known_attribs, attrib

    weight = 0
    branches = []
    for branch in branchset:
        weight += ~branch.uncertaintyWeight
        branches.append(
            Branch(branch['branchID'],
                   validator(~branch.uncertaintyModel),
                   float(~branch.uncertaintyWeight)))
    assert weight == 1, weight
    return BranchSet(branchset['branchSetID'],
                     branchset['uncertaintyType'],
                     attrib, branches)


def is_branchset(elem):
    return elem.tag.endswith('logicTreeBranchSet')


def get_gsim_lt(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    fname = oqparam.inputs['gsim_logic_tree']
    known_attribs = set(['applyToTectonicRegionType'])
    for branchset in read_nodes(fname, is_branchset, GsimLtNode):
        yield _branches(branchset, known_attribs)


class SourceModelLtNode(LiteralNode):
    """Source Model Logic Tree Node"""

    validators = valid.parameters(
        branchingLevelID=valid.name,
        branchSetID=valid.name,
        uncertaintyType=valid.Choice('sourceModel', 'abGRAbsolute',
                                     'bGRRelative', 'maxMagGRAbsolute'),
        uncertaintyWeight=decimal.Decimal,
    )


def is_branchlevel(elem):
    return elem.tag.endswith('logicTreeBranchingLevel')


def get_source_model_lt(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    fname = oqparam.inputs['source_model_logic_tree']
    known_attribs = set(['applyToSources', 'applyToTectonicRegionType',
                         'applyToBranch'])
    for branchlevel in read_nodes(fname, is_branchlevel, SourceModelLtNode):
        yield branchlevel['branchingLevelID'], [
            _branches(branchset, known_attribs)
            for branchset in branchlevel]


class VulnerabilityNode(LiteralNode):
    """
    Literal Node class used to validate discrete vulnerability functions
    """
    validators = valid.parameters(
        vulnerabilitySetID=valid.name,
        vulnerabilityFunctionID=valid.name,
        assetCategory=valid.Choice('buildings', 'population', 'single_asset'),
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


class FragilityNode(LiteralNode):
    validators = valid.parameters(
        vulnerabilitySetID=valid.name,
        vulnerabilityFunctionID=valid.name,
        format=valid.Choice('discrete', 'continuous'),
        lossCategory=valid.name,
        IML=valid.IML,
        params=valid.fragilityparams,
        lossRatio=valid.positivefloats,
        coefficientsVariation=valid.positivefloats,
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


def _get_imtls_from_vulnerabilities(inputs):
    # return a dictionary imt_str -> imls
    imtls = {}
    for fname in vulnerability_files(inputs):
        for vset in get_vulnerability_sets(fname):
            imt = vset.imt
            if imt in imtls and imtls[imt] != vset.imls:
                raise RuntimeError(
                    'Inconsistent levels for IMT %s: got %s, expected %s in %s'
                    % (imt, vset.imls, imtls[imt], fname))
            imtls[imt] = vset.imls
    return imtls


def get_imtls(oqparam):
    """
    Return a dictionary {imt_str: intensity_measure_levels}

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if hasattr(oqparam, 'intensity_measure_types'):
        imtls = dict.fromkeys(oqparam.intensity_measure_types)
    elif hasattr(oqparam, 'intensity_measure_types_and_levels'):
        imtls = oqparam.intensity_measure_types_and_levels
    elif vulnerability_files(oqparam.inputs):
        imtls = _get_imtls_from_vulnerabilities(oqparam.inputs)
    elif fragility_files(oqparam.inputs):
        imtls = {str(fset.imt): fset.imls
                 for fset in get_fragility_sets(oqparam.inputs['fragility'])}
    else:
        raise ValueError('Missing intensity_measure_types_and_levels, '
                         'vulnerability file and fragility file')
    return imtls


# used for debugging
if __name__ == '__main__':
    import sys
    from openquake.commonlib.readini import parse_config
    with open(sys.argv[1]) as ini:
        oqparam = parse_config(ini)
    #print get_site_collection(oqparam)
    #site_model = get_site_model(oqparam)
    #for x in site_model:
    #    print x
    #print list(get_gsim_lt(oqparam))
    #print list(get_source_model_lt(oqparam))
    for x in get_fragility_sets(oqparam.inputs['fragility']):
        print x
