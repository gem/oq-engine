import operator
import collections
import decimal

import numpy

from openquake.hazardlib import geo, site
from openquake.nrmllib.node import read_nodes, LiteralNode
from openquake.commonlib import valid
from openquake.commonlib.readini import parse_config
from openquake.commonlib.converter import Converter
from openquake.commonlib.source import ValidNode, RuptureConverter


class GeographicObjects(object):
    EARTH_DIAMETER = 12742.0
    """
    Store a collection of geographic points, i.e. objects with longitudes
    and latitudes. By default extracts them from the attributes .lon and .lat,
    but you can provide your own getters.

    NB: lons and lats of the objects are converted into radians at
    instantiation time, so the computation of distances is faster.
    """
    def __init__(self, objects, getlon=operator.attrgetter('lon'),
                 getlat=operator.attrgetter('lat')):
        self.objects = collections.OrderedDict()
        for obj in objects:
            lon = getlon(obj)
            lat = getlat(obj)
            self.objects[lon, lat] = obj
        lons, lats = zip(*self.objects.keys())
        self.lons = numpy.radians(lons)
        self.lats = numpy.radians(lats)

    def get_closest(self, lon, lat):
        """
        Get the closest object to the given longitude and latitude.

        :returns: a pair (object, distance)

        A special case is made for objects which are exactly at the
        given location. In such case the returned distance is zero.
        """
        try:
            return self.objects[lon, lat], 0
        except KeyError:
            pass  # search for the closest object
        obj_dist = zip(self.objects.itervalues(), self.get_distances(lon, lat))
        obj_dist.sort(key=operator.itemgetter(1))
        return obj_dist[0]

    def get_distances(self, lon, lat):
        """
        Return an array of distances from the given longitude and latitude,
        with size = len(objects).
        """
        lon, lat = numpy.radians(lon), numpy.radians(lat)
        return self.EARTH_DIAMETER * numpy.arcsin(
            numpy.sqrt(
                numpy.sin((lat - self.lats) / 2.0) ** 2.0
                + numpy.cos(lat) * numpy.cos(self.lats)
                * numpy.sin((lon - self.lons) / 2.0) ** 2.0
                ).clip(-1., 1.))


def get_points(oqparam):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, the region or the exposure.
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


vs30_type = valid.Choice('measured', 'inferred')

SiteParam = collections.namedtuple(
    'SiteParam', 'z1pt0 z2pt5 measured vs30 lon lat'.split())


def site_param(value, z1pt0, z2pt5, vs30Type, vs30, lon, lat):
    """
    Used to convert a node like

       <site lon="24.7125" lat="42.779167" vs30="462" vs30Type="inferred"
       z1pt0="100" z2pt5="5" />

    into a 6-tuple (z1pt0, z2pt5, measured, vs30, lon, lat)
    """
    return SiteParam(valid.positivefloat(z1pt0),
                     valid.positivefloat(z2pt5),
                     vs30_type(vs30Type) == 'measured',
                     valid.positivefloat(vs30),
                     valid.longitude(lon),
                     valid.latitude(lat))


class SiteModelNode(LiteralNode):
    validators = valid.parameters(site=site_param)


def get_site_model(oqparam):
    """
    Convert the NRML file into an iterator over 6-tuple of the form
    (z1pt0, z2pt5, measured, vs30, lon, lat)
    """
    for node in read_nodes(oqparam.inputs['site_model'],
                           lambda el: el.tag.endswith('site'),
                           SiteModelNode):
        yield ~node


def get_site_collection(oqparam, points=None, site_ids=None):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.
    """
    points = points or get_points(oqparam)
    site_ids = site_ids or range(1, len(points) + 1)
    if oqparam.inputs.get('site_model'):
        sitecol = []
        site_model_param = GeographicObjects(
            get_site_model(oqparam),
            getlon=operator.itemgetter(4),
            getlat=operator.itemgetter(5))
        for i, pt in zip(site_ids, points):
            param, _dist = site_model_param.\
                get_closest(pt.longitude, pt.latitude)
            sitecol.append(site.Site(pt, param.vs30, param.measured,
                                     param.z1pt0, param.z2pt5, i))
        return site.SiteCollection(sitecol)

    # else use the default site params
    return site.SiteCollection.from_points(
        points.lons, points.lats, site_ids, oqparam)


def get_rupture(oqparam):
    """
    Returns a hazardlib rupture
    """
    conv = RuptureConverter(oqparam.rupture_mesh_spacing)
    rup_model = oqparam.inputs['rupture_model']
    rup_node, = read_nodes(rup_model, lambda el: 'Rupture' in el.tag,
                           ValidNode)
    return conv.convert_node(rup_node)


def get_source_models(oqparam):
    """
    Read all the source models specified. Yield pairs (fname, sources).
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


def ab_values(value):
    a, b = value.split()
    return valid.positivefloat(a), float(b)

utype2validator = dict(
    sourceModel=valid.utf8,
    gmpeModel=valid.gsim,
    maxMagGRAbsolute=valid.positivefloat,
    bGRRelative=float,
    abGRAbsolute=ab_values)


def _branches(branchset, known_attribs):
    attrib = branchset.attrib.copy()
    del attrib['branchSetID']
    utype = attrib.pop('uncertaintyType')
    validator = utype2validator[utype]
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


def get_gsim_lt(oqparam):
    """
    """
    fname = oqparam.inputs['gsim_logic_tree']
    known_attribs = set(['applyToTectonicRegionType'])

    def is_branchset(elem):
        return elem.tag.endswith('logicTreeBranchSet')
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


def get_source_model_lt(oqparam):
    """
    """
    fname = oqparam.inputs['source_model_logic_tree']

    def is_branchlevel(elem):
        return elem.tag.endswith('logicTreeBranchingLevel')
    known_attribs = set(['applyToSources', 'applyToTectonicRegionType',
                         'applyToBranch'])
    for branchlevel in read_nodes(fname, is_branchlevel, SourceModelLtNode):
        yield branchlevel['branchingLevelID'], [
            _branches(branchset, known_attribs)
            for branchset in branchlevel]


class VulnerabilityNode(LiteralNode):
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
    def filter(elem):
        return elem.tag.endswith('discreteVulnerabilitySet')

    for vset in read_nodes(oqparam.inputs['fragility'],
                           filter, VulnerabilityNode):
        imt = vset.imt['IMT']
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
    fmodel = read_nodes(oqparam.inputs['fragility'],
                        lambda el: el.tag.endswith('fragilityModel'),
                        FragilityNode).next()
    if fmodel['format'] == 'discrete':
        pass
    if fmodel['format'] == 'continuous':
        pass


def get_imtls(oqparam):
    """
    """
    if hasattr(oqparam, 'intensity_measure_types_and_levels'):
        return oqparam.intensity_measure_types_and_levels
    if 'vulnerability' in oqparam.inputs:
        return {str(vset.imt): vset.imls
                for vset in get_vulnerability_sets(oqparam)}
    elif 'fragility' in oqparam.inputs:
        return {str(fset.imt): fset.imls
                for fset in get_fragility_sets(oqparam)}
    else:
        raise ValueError('Missing intensity_measure_types_and_levels, '
                         'vulnerability file and fragility file')


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
