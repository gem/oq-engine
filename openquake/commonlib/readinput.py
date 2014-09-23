import logging
import collections
import decimal

import numpy

from openquake.hazardlib import geo, site, imt
from openquake.nrmllib.node import read_nodes, LiteralNode
from openquake.commonlib import valid
from openquake.commonlib.readini import parse_config
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
        assetCategory=valid.Choice('buildings', 'population'),
        lossCategory=valid.name,
        IML=valid.positivefloats,
        IMT=valid.intensity_measure_types,
        lossRatio=valid.positivefloats,
        coefficientsVariation=valid.positivefloats,
    )

VSet = collections.namedtuple(
    'VSet', 'imt imls vfunctions'.split())

VFunction = collections.namedtuple(
    'VFunction', 'id lossRatio coefficientsVariation'.split())


def get_vulnerability_sets(oqparam):
    """
    Yields VSet namedtuples, each containing imt, imls and
    vulnerability functions.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    def filter(elem):
        return elem.tag.endswith('discreteVulnerabilitySet')

    imts = set()
    fname = oqparam.inputs['fragility']
    for vset in read_nodes(fname, filter, VulnerabilityNode):
        imt_str = str(imt.from_string(vset.imt['IMT']))
        if imt_str in imts:
            raise ValueError('Duplicated IMT in %s: %s' % (fname, imt_str))
        imts.add(imt_str)
        imls = ~vset
        vfuns = []
        for vfun in vset:
            vf = VFunction(vfun['vulnerabilityFunctionID'],
                           ~vfun.lossRatio, ~vfun.coefficientsVariation)
            if len(vf.lossRatio) != len(imls):
                raise ValueError('There are %d loss ratios, but %d imls' %
                                 (len(vf.lossRatio), len(imls)))
            elif len(vf.coefficientsVariation) != len(imls):
                raise ValueError('There are %d coefficients, but %d imls' %
                                 (len(vf.coefficientsVariation), len(imls)))
            vfuns.append(vf)
        yield VSet(imt, imls, vfuns)


class FragilityNode(LiteralNode):
    validators = valid.parameters(
        vulnerabilitySetID=valid.name,
        vulnerabilityFunctionID=valid.name,
        format=valid.Choice('discrete', 'continuous'),
        lossCategory=valid.name,
        IML=valid.positivefloats,
        IMT=valid.intensity_measure_types,
        lossRatio=valid.positivefloats,
        coefficientsVariation=valid.positivefloats,
    )


def get_fragility_sets(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    fmodel = read_nodes(oqparam.inputs['fragility'],
                        lambda el: el.tag.endswith('fragilityModel'),
                        FragilityNode).next()
    if fmodel['format'] == 'discrete':
        pass
    if fmodel['format'] == 'continuous':
        pass


def get_imtls(oqparam):
    """
    Return a dictionary {imt_str: intensity_measure_levels}

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if hasattr(oqparam, 'intensity_measure_types_and_levels'):
        return oqparam.intensity_measure_types_and_levels
    elif 'vulnerability' in oqparam.inputs:
        return {str(vset.imt): vset.imls
                for vset in get_vulnerability_sets(oqparam)}
    elif 'fragility' in oqparam.inputs:
        return {str(fset.imt): fset.imls
                for fset in get_fragility_sets(oqparam)}
    else:
        raise ValueError('Missing intensity_measure_types_and_levels, '
                         'vulnerability file and fragility file')


# used for debugging
if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as ini:
        oqparam = parse_config(ini)
    #print get_site_collection(oqparam)
    #site_model = get_site_model(oqparam)
    #for x in site_model:
    #    print x
    print list(get_gsim_lt(oqparam))

    print list(get_source_model_lt(oqparam))
