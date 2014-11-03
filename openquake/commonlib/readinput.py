#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import csv
import collections
import ConfigParser
from lxml import etree

import numpy

from openquake.hazardlib import geo, site, gsim, correlation, imt
from openquake.risklib import workflows

from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib.node import read_nodes, LiteralNode, context
from openquake.commonlib import nrml, valid
from openquake.commonlib.oqvalidation import \
    fragility_files, vulnerability_files
from openquake.commonlib.riskmodels import \
    get_fragility_functions, get_imtls_from_vulnerabilities, get_vfs
from openquake.commonlib.general import groupby, AccumDict
from openquake.commonlib import source
from openquake.commonlib.nrml import nodefactory, PARSE_NS_MAP

GSIM = gsim.get_available_gsims()


class DuplicatedPoint(Exception):
    """
    Raised when reading a CSV file with duplicated (lon, lat) pairs
    """


def _collect_source_model_paths(smlt):
    """
    Given a path to a source model logic tree or a file-like, collect all of
    the soft-linked path names to the source models it contains and return them
    as a uniquified list (no duplicates).
    """
    src_paths = []
    tree = etree.parse(smlt)
    for branch_set in tree.xpath('//nrml:logicTreeBranchSet',
                                 namespaces=PARSE_NS_MAP):

        if branch_set.get('uncertaintyType') == 'sourceModel':
            for branch in branch_set.xpath(
                    './nrml:logicTreeBranch/nrml:uncertaintyModel',
                    namespaces=PARSE_NS_MAP):
                src_paths.append(branch.text)
    return sorted(set(src_paths))


def get_oqparam(job_ini, calculators=None):
    """
    Parse a dictionary of parameters from one or more INI-style config file.

    :param job_ini:
        Configuration file or list of configuration files
    :returns:
        An :class:`openquake.commonlib.oqvalidation.OqParam` instance
        containing the validate and casted parameters/values parsed from
        the job.ini file as well as a subdictionary 'inputs' containing
        absolute paths to all of the files referenced in the job.ini, keyed by
        the parameter name.
    """
    if calculators is None:
        from openquake.commonlib.calculators import calculators
        OqParam.params['calculation_mode'].choices = tuple(calculators)

    job_inis = [job_ini] if isinstance(job_ini, basestring) else job_ini
    cp = ConfigParser.ConfigParser()
    cp.read(job_inis)

    # Directory containing the config files we're parsing
    base_path = os.path.dirname(
        os.path.join(os.path.abspath('.'), job_inis[0]))
    params = dict(base_path=base_path, inputs={})

    for sect in cp.sections():
        for key, value in cp.items(sect):
            if key.endswith(('_file', '_csv')):
                input_type, _ext = key.rsplit('_', 1)
                path = value if os.path.isabs(value) else os.path.join(
                    base_path, value)
                params['inputs'][input_type] = path
            else:
                params[key] = value

    # load job_ini inputs (the paths are the job_ini_model_logic_tree)
    smlt = params['inputs'].get('source_model_logic_tree')
    if smlt:
        params['inputs']['source'] = [
            os.path.join(base_path, src_path)
            for src_path in _collect_source_model_paths(smlt)]
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
    elif 'sites' in oqparam.inputs:
        csv_data = open(oqparam.inputs['sites'], 'U').read()
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
        raise RuntimeError('You can extract the site collection from the '
                           'exposure with get_sitecol_assets')


def get_site_model(oqparam):
    """
    Convert the NRML file into an iterator over 6-tuple of the form
    (z1pt0, z2pt5, measured, vs30, lon, lat)

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    for node in read_nodes(oqparam.inputs['site_model'],
                           lambda el: el.tag.endswith('site'),
                           nodefactory['siteModel']):
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
        object with a method .get_closest returning the closest site
        model parameters
    """
    mesh = mesh or get_mesh(oqparam)
    site_ids = site_ids or range(1, len(mesh) + 1)
    if oqparam.inputs.get('site_model'):
        if site_model_params is None:
            # read the parameters directly from their file
            site_model_params = geo.geodetic.GeographicObjects(
                get_site_model(oqparam))
        sitecol = []
        for i, pt in zip(site_ids, mesh):
            param = site_model_params.\
                get_closest(pt.longitude, pt.latitude)
            sitecol.append(
                site.Site(pt, param.vs30, param.measured,
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
                           nodefactory['sourceModel'])
    conv = source.RuptureConverter(oqparam.rupture_mesh_spacing)
    return conv.convert_node(rup_node)


def get_trt_models(oqparam, fname):
    """
    Read all the source models specified in oqparam and yield
    :class:`openquake.commonlib.source.TrtModel` instances
    ordered by tectonic region type.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    converter = source.SourceConverter(
        oqparam.investigation_time,
        oqparam.rupture_mesh_spacing,
        oqparam.width_of_mfd_bin,
        oqparam.area_source_discretization)
    for trt_model in source.parse_source_model(fname, converter):
        for src in trt_model.sources:
            trt_model.update_num_ruptures(src)
        yield trt_model


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
        cfd = getattr(oqparam, 'continuous_fragility_discretization', None)
        ffs = get_fragility_functions(fname, cfd)
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


def get_risk_model(oqparam):
    """
    Return a :class:`openquake.risklib.workflows.RiskModel` instance

   :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    risk_models = {}  # (imt, taxonomy) -> workflow
    riskmodel = workflows.RiskModel(risk_models)

    rit = getattr(oqparam, 'risk_investigation_time', None)
    if rit:  # defined for event based calculations
        oqparam.time_span = oqparam.tses = rit

    if oqparam.calculation_mode.endswith('_damage'):
        # scenario damage calculator
        fragility_functions = get_fragility_functions(
            oqparam.inputs['fragility'],
            getattr(oqparam, 'continuous_fragility_discretization', None))
        riskmodel.damage_states = fragility_functions.damage_states
        for taxonomy, ffs in fragility_functions.iteritems():
            risk_models[ffs.imt, taxonomy] = workflows.get_workflow(
                oqparam, fragility_functions=dict(damage=ffs))
    elif oqparam.calculation_mode.endswith('_bcr'):
        # bcr calculators
        vfs_orig = get_vfs(oqparam.inputs, retrofitted=False).items()
        vfs_retro = get_vfs(oqparam.inputs, retrofitted=True).items()
        for (imt_taxo, vf_orig), (imt_taxo_, vf_retro) in \
                zip(vfs_orig, vfs_retro):
            assert imt_taxo == imt_taxo_  # same imt and taxonomy
            risk_models[imt_taxo] = workflows.get_workflow(
                oqparam,
                vulnerability_functions_orig=vf_orig,
                vulnerability_functions_retro=vf_retro)
    else:
        # classical, event based and scenario calculators
        oqparam.__dict__.setdefault('insured_losses', False)
        for imt_taxo, vfs in get_vfs(oqparam.inputs).iteritems():
            risk_models[imt_taxo] = workflows.get_workflow(
                oqparam, vulnerability_functions=vfs)

    return riskmodel

############################ exposure #############################


class DuplicateID(Exception):
    """
    Raised when two assets with the same ID are found in an exposure model
    """


def get_exposure_lazy(fname):
    """
    :returns: a pair (Exposure instance, list of asset nodes)
    """
    [exposure] = nrml.read_lazy(fname, ['assets'])
    description = exposure.description
    conversions = exposure.conversions
    try:
        inslimit = conversions.insuranceLimit
    except NameError:
        inslimit = LiteralNode('insuranceLimit')
    try:
        deductible = conversions.deductible
    except NameError:
        deductible = LiteralNode('deductible')
    return Exposure(
        exposure['id'], exposure['category'],
        ~description, [ct.attrib for ct in conversions.costTypes],
        ~inslimit, ~deductible, [], set()), exposure.assets


def get_exposure(oqparam):
    """
    Read the full exposure in memory and build a list of
    :class:`openquake.risklib.workflows.Asset` instances.
    If you don't want to keep everything in memory, use
    get_exposure_lazy instead (for experts only).

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an :class:`Exposure` instance
    """
    fname = oqparam.inputs['exposure']
    exposure, assets_node = get_exposure_lazy(fname)
    relevant_cost_types = set(vulnerability_files(oqparam.inputs)) - \
        set(['occupants'])
    asset_refs = set()
    time_event = getattr(oqparam, 'time_event', None)
    for asset in assets_node:
        values = {}
        deductibles = {}
        insurance_limits = {}
        retrofitting_values = {}
        with context(fname, asset):
            asset_id = asset['id']
            if asset_id in asset_refs:
                raise DuplicateID(asset_id)
            asset_refs.add(asset_id)
            taxonomy = asset['taxonomy']
            number = asset['number']
            location = asset.location['lon'], asset.location['lat']
        with context(fname, asset.costs):
            for cost in asset.costs:
                cost_type = cost['type']
                if cost_type not in relevant_cost_types:
                    continue
                values[cost_type] = cost['value']
                deductibles[cost_type] = cost.attrib.get('deductible')
                insurance_limits[cost_type] = cost.attrib.get('insuranceLimit')
            if exposure.category == 'population':
                values['fatalities'] = number
            # check we are not missing a cost type
            missing = relevant_cost_types - set(values)
            if missing:
                raise RuntimeError(
                    'Missing cost types: %s' % ', '.join(missing))

        if time_event:
            for occupancy in asset.occupancies:
                with context(fname, occupancy):
                    if occupancy['period'] == time_event:
                        values['fatalities'] = occupancy['occupants']
                        break

        ass = workflows.Asset(
            asset_id, taxonomy, number, location, values, deductibles,
            insurance_limits, retrofitting_values)
        exposure.assets.append(ass)
        exposure.taxonomies.add(taxonomy)
    return exposure


Exposure = collections.namedtuple(
    'Exposure', ['id', 'category', 'description', 'cost_types',
                 'insurance_limit_is_absolute',
                 'deductible_is_absolute', 'assets', 'taxonomies'])


def get_specific_assets(oqparam):
    """
    Get the assets from the parameters specific_assets or specific_assets_csv

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    try:
        return set(oqparam.specific_assets)
    except AttributeError:
        if 'specific_assets' not in oqparam.inputs:
            return set()
        return set(open(oqparam.inputs['specific_assets']).read().split())


def get_sitecol_assets(oqparam, exposure):
    """
    Returns two sequences of the same length: the site collection and an
    array with the assets per each site, collected by taxonomy.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    assets_by_loc = groupby(exposure.assets, key=lambda a: a.location)
    lons, lats = zip(*sorted(assets_by_loc))
    mesh = geo.Mesh(numpy.array(lons), numpy.array(lats))
    sitecol = get_site_collection(oqparam, mesh)
    return sitecol, numpy.array([
        assets_by_loc[site.location.longitude, site.location.latitude]
        for site in sitecol])


def get_mesh_csvdata(csvfile, imts, num_values, validvalue):
    """
    Read CSV data in the format `IMT lon lat value1 ... valueN`.
    Return the mesh of points and the data as a dictionary
    imt -> list of arrays.
    """
    number_of_values = dict(zip(imts, num_values))
    lon_lats = {imt: set() for imt in imts}
    data = AccumDict()  # imt -> list of arrays
    check_imt = valid.Choice(*imts)
    for line, row in enumerate(csv.reader(csvfile, delimiter=' '), 1):
        try:
            imt = check_imt(row[0])
            lon_lat = valid.longitude(row[1]), valid.latitude(row[2])
            if lon_lat in lon_lats[imt]:
                raise DuplicatedPoint(lon_lat)
            lon_lats[imt].add(lon_lat)
            values = map(validvalue, row[3:])
            if len(values) != number_of_values[imt]:
                raise ValueError('Found %d values, expected %d' %
                                 (len(values), number_of_values[imt]))
        except (ValueError, DuplicatedPoint) as err:
            raise err.__class__('%s: file %s, line %d' % (err, csvfile, line))
        data += {imt: [numpy.array(values)]}
    points = lon_lats.pop(imts[0])
    for other_points in lon_lats.values():
        if points != other_points:
            raise ValueError('Inconsistent locations between %s and %s' %
                             (imts[0], ', '.join(imts[1:])))
    lons, lats = zip(*sorted(points))
    mesh = geo.Mesh(numpy.array(lons), numpy.array(lats))
    return mesh, {imt: numpy.array(lst) for imt, lst in data.iteritems()}


def get_sitecol_hcurves(oqparam):
    """
    Returns the site collection and the hazard curves, by reading
    a CSV file with format `IMT lon lat poe1 ... poeN`

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    imts = oqparam.intensity_measure_types_and_levels.keys()
    num_values = map(len, oqparam.intensity_measure_types_and_levels.values())
    with open(oqparam.inputs['hazard_curves']) as csvfile:
        mesh, hcurves_by_imt = get_mesh_csvdata(
            csvfile, imts, num_values, valid.probability)
    sitecol = get_site_collection(oqparam, mesh)
    return sitecol, hcurves_by_imt


def get_sitecol_gmfs(oqparam):
    """
    Returns the site collection and the GMFs as a dictionary, by reading
    a CSV file with format `IMT lon lat gmv1 ... gmvN`

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    imts = oqparam.intensity_measure_types_and_levels.keys()
    num_values = [oqparam.number_of_ground_motion_fields] * len(imts)
    with open(oqparam.inputs['gmvs']) as csvfile:
        mesh, gmfs_by_imt = get_mesh_csvdata(
            csvfile, imts, num_values, valid.positivefloat)
    sitecol = get_site_collection(oqparam, mesh)
    return sitecol, gmfs_by_imt
