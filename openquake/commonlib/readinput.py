import collections
import ConfigParser
import os
from lxml import etree

import numpy

from openquake.hazardlib import geo, site, gsim, correlation, imt
from openquake.nrmllib.node import read_nodes, LiteralNode, context
from openquake.risklib.workflows import Asset
from openquake import nrmllib
from openquake.commonlib.oqvalidation import OqParam

from openquake.commonlib import valid
from openquake.commonlib.oqvalidation import \
    fragility_files, vulnerability_files
from openquake.commonlib.riskmodels import \
    get_fragility_functions, get_imtls_from_vulnerabilities, get_vfs
from openquake.commonlib.source import ValidNode, RuptureConverter

GSIM = gsim.get_available_gsims()


def _collect_source_model_paths(smlt):
    """
    Given a path to a source model logic tree or a file-like, collect all of
    the soft-linked path names to the source models it contains and return them
    as a uniquified list (no duplicates).
    """
    src_paths = []
    tree = etree.parse(smlt)
    for branch_set in tree.xpath('//nrml:logicTreeBranchSet',
                                 namespaces=nrmllib.PARSE_NS_MAP):

        if branch_set.get('uncertaintyType') == 'sourceModel':
            for branch in branch_set.xpath(
                    './nrml:logicTreeBranch/nrml:uncertaintyModel',
                    namespaces=nrmllib.PARSE_NS_MAP):
                src_paths.append(branch.text)
    return sorted(set(src_paths))


def get_oqparam(source, hazard_calculation_id=None, hazard_output_id=None):
    """
    Parse a dictionary of parameters from an INI-style config file.

    :param source:
        File-like object containing the config parameters.
    :param hazard_job_id:
        The ID of a previous calculation (or None)
    :param hazard_ouput_id:
        The output of a previous job (or None)
    :returns:
        An :class:`openquake.commonlib.oqvalidation.OqParam` instance
        containing the validate and casted parameters/values parsed from
        the job.ini file as well as a subdictionary 'inputs' containing
        absolute paths to all of the files referenced in the job.ini, keyed by
        the parameter name.
    """
    cp = ConfigParser.ConfigParser()
    cp.readfp(source)

    base_path = os.path.dirname(
        os.path.join(os.path.abspath('.'), source.name))
    params = dict(base_path=base_path, inputs={},
                  hazard_calculation_id=hazard_calculation_id,
                  hazard_output_id=hazard_output_id)

    # Directory containing the config file we're parsing.
    base_path = os.path.dirname(os.path.abspath(source.name))

    for sect in cp.sections():
        for key, value in cp.items(sect):
            if key == 'sites_csv' or key.endswith('_file'):
                input_type = key[:-5]
                path = value if os.path.isabs(value) else os.path.join(
                    base_path, value)
                params['inputs'][input_type] = path
            else:
                params[key] = value

    # load source inputs (the paths are the source_model_logic_tree)
    smlt = params['inputs'].get('source_model_logic_tree')
    if smlt:
        params['inputs']['source'] = [
            os.path.join(base_path, src_path)
            for src_path in _collect_source_model_paths(smlt)]

    # check for obsolete calculation_mode
    is_risk = hazard_calculation_id or hazard_output_id
    cmode = params['calculation_mode']
    if is_risk and cmode in ('classical', 'event_based', 'scenario'):
        raise ValueError('Please change calculation_mode=%s into %s_risk '
                         'in the .ini file' % (cmode, cmode))

    oqparam = OqParam(**params)

    # define the parameter `intensity measure types and levels` always
    oqparam.intensity_measure_types_and_levels = get_imtls(oqparam)

    return oqparam


def get_mesh(oqparam):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, or the region.

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
        model parameters
    """
    mesh = mesh or get_mesh(oqparam)
    site_ids = site_ids or range(1, len(mesh) + 1)
    if oqparam.inputs.get('site_model'):
        sitecol = []
        for i, pt in zip(site_ids, mesh):
            param = site_model_params.\
                get_closest(pt.longitude, pt.latitude)
            sitecol.append(
                site.Site(pt, param.vs30, param.vs30_type == 'measured',
                          param.z1pt0, param.z2pt5, i))
        return site.SiteCollection(sitecol)

    # else use the default site params
    return site.SiteCollection.from_points(
        mesh.lons, mesh.lats, site_ids, oqparam)


def get_gsim(oqparam):
    """
    Return a GSIM instance from the gsim name in the configuration
    file (defined for scenario computations).
    """
    return GSIM[oqparam.gsim]()


def get_correl_model(oqparam):
    """
    Return a correlation object. See :mod:`openquake.hazardlib.correlation`
    for more info.
    """
    correl_name = getattr(oqparam, 'ground_motion_correlation_model', None)
    if correl_name is None:  # no correlation model
        return
    correl_model_cls = getattr(correlation, '%sCorrelationModel' % correl_name)
    return correl_model_cls(**oqparam.ground_motion_correlation_params)


def get_rupture(oqparam):
    """
    Returns a hazardlib rupture by reading the `rupture_model` file.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    rup_model = oqparam.inputs['rupture_model']
    rup_node, = read_nodes(rup_model, lambda el: 'Rupture' in el.tag,
                           ValidNode)
    conv = RuptureConverter(oqparam.rupture_mesh_spacing)
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


def get_imtls(oqparam):
    """
    Return a dictionary {imt_str: intensity_measure_levels}

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if hasattr(oqparam, 'intensity_measure_types'):
        imtls = dict.fromkeys(oqparam.intensity_measure_types)
        # remove the now redundant parameter
        delattr(oqparam, 'intensity_measure_types')
    elif hasattr(oqparam, 'intensity_measure_types_and_levels'):
        imtls = oqparam.intensity_measure_types_and_levels
    elif vulnerability_files(oqparam.inputs):
        imtls = get_imtls_from_vulnerabilities(oqparam.inputs)
    elif fragility_files(oqparam.inputs):
        fname = oqparam.inputs['fragility']
        ffs = get_fragility_functions(fname)
        imtls = {fset.imt: fset.imls for fset in ffs.itervalues()}
    else:
        raise ValueError('Missing intensity_measure_types_and_levels, '
                         'vulnerability file and fragility file')
    return imtls


def get_imts(oqparam):
    """
    Return a sorted list of IMTs as hazardlib objects
    """
    return map(imt.from_string,
               sorted(oqparam.intensity_measure_types_and_levels))


def get_vulnerability_functions(oqparam):
    """Return a dict (imt, taxonomy) -> vf"""
    return get_vfs(oqparam.inputs)


############################ exposure #############################


class ExposureNode(LiteralNode):
    validators = valid.parameters(
        occupants=valid.positivefloat,
        value=valid.positivefloat,
        deductible=valid.positivefloat,
        insuranceLimit=valid.positivefloat,
        number=valid.positivefloat,
        location=valid.point2d,
    )


def get_exposure(oqparam):
    """
    Read the exposure and yields :class:`openquake.risklib.workflows.Asset`
    instances.
    """
    relevant_cost_types = set(vulnerability_files(oqparam.inputs))
    fname = oqparam.inputs['exposure']
    time_event = getattr(oqparam, 'time_event', None)
    for asset in read_nodes(fname,
                            lambda node: node.tag.endswith('asset'),
                            ExposureNode):
        values = {}
        deductibles = {}
        insurance_limits = {}
        retrofitting_values = {}

        with context(fname, asset):
            asset_id = asset['id']
            taxonomy = asset['taxonomy']
            number = asset['number']
            location = ~asset.location
        with context(fname, asset.costs):
            for cost in asset.costs:
                cost_type = cost['type']
                if cost_type not in relevant_cost_types:
                    continue
                values[cost_type] = cost['value']
                deductibles[cost_type] = cost.attrib.get('deductible')
                insurance_limits[cost_type] = cost.attrib.get('insuranceLimit')
            # check we are not missing a cost type
            assert set(values) == relevant_cost_types

        if time_event:
            for occupancy in asset.occupancies:
                with context(fname, occupancy):
                    if occupancy['period'] == time_event:
                        values['fatalities'] = occupancy['occupants']
                        break

        yield Asset(asset_id, taxonomy, number, location,
                    values, deductibles, insurance_limits, retrofitting_values)


def get_sitecol_assets(oqparam):
    """
    Returns two sequences of the same length: a list with the assets
    per each site and the site collection.
    """
    assets_by_loc = collections.defaultdict(list)
    for asset in get_exposure(oqparam):
        assets_by_loc[asset.location].append(asset)
    lons, lats = zip(*sorted(assets_by_loc))
    mesh = geo.Mesh(numpy.array(lons), numpy.array(lats))
    sitecol = get_site_collection(oqparam, mesh)
    return sitecol, [
        assets_by_loc[site.location.longitude, site.location.latitude]
        for site in sitecol]
