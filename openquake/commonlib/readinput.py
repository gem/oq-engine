# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from __future__ import division
import os
import csv
import zlib
import zipfile
import logging
import operator
import tempfile
import collections
import numpy
from shapely import wkt, geometry

from openquake.baselib.general import groupby, AccumDict, DictArray, deprecated
from openquake.baselib.python3compat import configparser, decode
from openquake.baselib.node import Node, context
from openquake.baselib import hdf5
from openquake.hazardlib import (
    calc, geo, site, imt, valid, sourceconverter, nrml, InvalidFile)
from openquake.hazardlib.source.rupture import EBRupture
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.risklib import asset, riskinput, read_nrml
from openquake.baselib import datastore
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import logictree, source, writers
from openquake.commonlib.riskmodels import get_risk_models

read_nrml.update_validators()


# the following is quite arbitrary, it gives output weights that I like (MS)
NORMALIZATION_FACTOR = 1E-2
TWO16 = 2 ** 16  # 65,536
F32 = numpy.float32
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64

stored_event_dt = numpy.dtype([
    ('eid', U64), ('rup_id', U32), ('grp_id', U16), ('year', U32),
    ('ses', U32), ('sample', U32)])


class DuplicatedPoint(Exception):
    """
    Raised when reading a CSV file with duplicated (lon, lat) pairs
    """


def collect_files(dirpath, cond=lambda fullname: True):
    """
    Recursively collect the files contained inside dirpath.

    :param dirpath: path to a readable directory
    :param cond: condition on the path to collect the file
    """
    files = []
    for fname in os.listdir(dirpath):
        fullname = os.path.join(dirpath, fname)
        if os.path.isdir(fullname):  # navigate inside
            files.extend(collect_files(fullname))
        else:  # collect files
            if cond(fullname):
                files.append(fullname)
    return files


def extract_from_zip(path, candidates):
    """
    Given a zip archive and a function to detect the presence of a given
    filename, unzip the archive into a temporary directory and return the
    full path of the file. Raise an IOError if the file cannot be found
    within the archive.

    :param path: pathname of the archive
    :param candidates: list of names to search for
    """
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(path) as archive:
        archive.extractall(temp_dir)
    return [f for f in collect_files(temp_dir)
            if os.path.basename(f) in candidates]


def _update(params, items, base_path):
    for key, value in items:
        if key.endswith(('_file', '_csv')):
            if os.path.isabs(value):
                raise ValueError('%s=%s is an absolute path' % (key, value))
            input_type, _ext = key.rsplit('_', 1)
            params['inputs'][input_type] = (
                os.path.join(base_path, value) if value else '')
        else:
            params[key] = value


def get_params(job_inis, **kw):
    """
    Parse one or more INI-style config files.

    :param job_inis:
        List of configuration files (or list containing a single zip archive)
    :param kw:
        Optionally override some parameters
    :returns:
        A dictionary of parameters
    """
    if len(job_inis) == 1 and job_inis[0].endswith('.zip'):
        job_inis = extract_from_zip(
            job_inis[0], ['job_hazard.ini', 'job_haz.ini',
                          'job.ini', 'job_risk.ini'])

    not_found = [ini for ini in job_inis if not os.path.exists(ini)]
    if not_found:  # something was not found
        raise IOError('File not found: %s' % not_found[0])

    cp = configparser.ConfigParser()
    cp.read(job_inis)

    # directory containing the config files we're parsing
    job_ini = os.path.abspath(job_inis[0])
    base_path = decode(os.path.dirname(job_ini))
    params = dict(base_path=base_path, inputs={'job_ini': job_ini})

    for sect in cp.sections():
        _update(params, cp.items(sect), base_path)
    _update(params, kw.items(), base_path)  # override on demand

    # populate the 'source' list
    inputs = params['inputs']
    smlt = inputs.get('source_model_logic_tree')
    if smlt:
        inputs['source'] = sorted(_get_paths(smlt))
    elif 'source_model' in inputs:
        inputs['source'] = [inputs['source_model']]
    return params


def _get_paths(smlt):
    # extract the path names for the source models listed in the smlt file
    base_path = os.path.dirname(smlt)
    for model in source.collect_source_model_paths(smlt):
        for name in model.split():
            if os.path.isabs(name):
                raise InvalidFile('%s: %s must be a relative path' %
                                  (smlt, name))
            fname = os.path.abspath(os.path.join(base_path, name))
            if os.path.exists(fname):  # consider only real paths
                yield fname


def get_oqparam(job_ini, pkg=None, calculators=None, hc_id=None):
    """
    Parse a dictionary of parameters from an INI-style config file.

    :param job_ini:
        Path to configuration file/archive or dictionary of parameters
    :param pkg:
        Python package where to find the configuration file (optional)
    :param calculators:
        Sequence of calculator names (optional) used to restrict the
        valid choices for `calculation_mode`
    :param hc_id:
        Not None only when called from a post calculation
    :returns:
        An :class:`openquake.commonlib.oqvalidation.OqParam` instance
        containing the validate and casted parameters/values parsed from
        the job.ini file as well as a subdictionary 'inputs' containing
        absolute paths to all of the files referenced in the job.ini, keyed by
        the parameter name.
    """
    # UGLY: this is here to avoid circular imports
    from openquake.calculators import base

    OqParam.calculation_mode.validator.choices = tuple(
        calculators or base.calculators)
    if not isinstance(job_ini, dict):
        basedir = os.path.dirname(pkg.__file__) if pkg else ''
        job_ini = get_params([os.path.join(basedir, job_ini)])
    if hc_id:
        job_ini.update(hazard_calculation_id=str(hc_id))
    oqparam = OqParam(**job_ini)
    oqparam.validate()
    return oqparam


def get_mesh(oqparam):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, or the region.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if oqparam.sites:
        return geo.Mesh.from_coords(sorted(oqparam.sites))
    elif 'sites' in oqparam.inputs:
        csv_data = open(oqparam.inputs['sites'], 'U').readlines()
        has_header = csv_data[0].startswith('site_id')
        if has_header:  # strip site_id
            data = []
            for i, line in enumerate(csv_data[1:]):
                row = line.replace(',', ' ').split()
                sid = row[0]
                if sid != str(i):
                    raise InvalidFile('%s: expected site_id=%d, got %s' % (
                        oqparam.inputs['sites'], i, sid))
                data.append(' '.join(row[1:]))
        elif 'gmfs' in oqparam.inputs:
            raise InvalidFile('Missing header in %(sites)s' % oqparam.inputs)
        else:
            data = [line.replace(',', ' ') for line in csv_data]
        coords = valid.coordinates(','.join(data))
        start, stop = oqparam.sites_slice
        c = coords[start:stop] if has_header else sorted(coords[start:stop])
        return geo.Mesh.from_coords(c)
    elif oqparam.region:
        # close the linear polygon ring by appending the first
        # point to the end
        firstpoint = geo.Point(*oqparam.region[0])
        points = [geo.Point(*xy) for xy in oqparam.region] + [firstpoint]
        try:
            mesh = geo.Polygon(points).discretize(oqparam.region_grid_spacing)
            lons, lats = zip(*sorted(zip(mesh.lons, mesh.lats)))
            return geo.Mesh(numpy.array(lons), numpy.array(lats))
        except:
            raise ValueError(
                'Could not discretize region %(region)s with grid spacing '
                '%(region_grid_spacing)s' % vars(oqparam))
    elif oqparam.hazard_calculation_id:
        sitecol = datastore.read(oqparam.hazard_calculation_id)['sitecol']
        return geo.Mesh(sitecol.lons, sitecol.lats, sitecol.depths)
    elif 'exposure' in oqparam.inputs:
        # the mesh is extracted from get_sitecol_assetcol
        return
    elif 'site_model' in oqparam.inputs:
        coords = [(param.lon, param.lat, param.depth)
                  for param in get_site_model(oqparam)]
        mesh = geo.Mesh.from_coords(sorted(coords))
        mesh.from_site_model = True
        return mesh


def get_site_model(oqparam):
    """
    Convert the NRML file into an iterator over 6-tuple of the form
    (z1pt0, z2pt5, measured, vs30, lon, lat)

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    for node in nrml.read(oqparam.inputs['site_model']).siteModel:
        yield valid.site_param(**node.attrib)


def get_site_collection(oqparam, mesh=None):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param mesh:
        a mesh of hazardlib points; if None the mesh is
        determined by invoking get_mesh
    """
    if mesh is None:
        mesh = get_mesh(oqparam)
    if mesh is None:
        return
    if oqparam.inputs.get('site_model'):
        sitecol = []
        if getattr(mesh, 'from_site_model', False):
            for param in sorted(get_site_model(oqparam)):
                pt = geo.Point(param.lon, param.lat, param.depth)
                sitecol.append(site.Site(
                    pt, param.vs30, param.measured,
                    param.z1pt0, param.z2pt5, param.backarc))
            return site.SiteCollection(sitecol)
        # read the parameters directly from their file
        site_model_params = geo.utils.GeographicObjects(
            get_site_model(oqparam))
        for pt in mesh:
            # attach the closest site model params to each site
            param, dist = site_model_params.get_closest(
                pt.longitude, pt.latitude)
            if dist >= oqparam.max_site_model_distance:
                logging.warn('The site parameter associated to %s came from a '
                             'distance of %d km!' % (pt, dist))
            sitecol.append(
                site.Site(pt, param.vs30, param.measured,
                          param.z1pt0, param.z2pt5, param.backarc))
        if len(sitecol) == 1 and oqparam.hazard_maps:
            logging.warn('There is a single site, hazard_maps=true '
                         'has little sense')
        return site.SiteCollection(sitecol)

    # else use the default site params
    return site.SiteCollection.from_points(
        mesh.lons, mesh.lats, mesh.depths, oqparam)


def get_gsim_lt(oqparam, trts=['*']):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param trts:
        a sequence of tectonic region types as strings; trts=['*']
        means that there is no filtering
    :returns:
        a GsimLogicTree instance obtained by filtering on the provided
        tectonic region types.
    """
    if 'gsim_logic_tree' not in oqparam.inputs:
        return logictree.GsimLogicTree.from_(oqparam.gsim)
    gsim_file = os.path.join(
        oqparam.base_path, oqparam.inputs['gsim_logic_tree'])
    gsim_lt = logictree.GsimLogicTree(gsim_file, trts)
    return gsim_lt


def get_gsims(oqparam):
    """
    Return an ordered list of GSIM instances from the gsim name in the
    configuration file or from the gsim logic tree file.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    return [rlz.value[0] for rlz in get_gsim_lt(oqparam)]


def get_rlzs_by_gsim(oqparam):
    """
    Return an ordered dictionary gsim -> [realization]. Work for
    gsim logic trees with a single tectonic region type.
    """
    cinfo = source.CompositionInfo.fake(get_gsim_lt(oqparam))
    return cinfo.get_rlzs_assoc().rlzs_by_gsim[0]


def get_rupture_sitecol(oqparam, sitecol):
    """
    Read the `rupture_model` file and by filter the site collection

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :returns:
        a pair (EBRupture, SiteCollection)
    """
    rup_model = oqparam.inputs['rupture_model']
    [rup_node] = nrml.read(rup_model)
    conv = sourceconverter.RuptureConverter(
        oqparam.rupture_mesh_spacing, oqparam.complex_fault_mesh_spacing)
    rup = conv.convert_node(rup_node)
    rup.tectonic_region_type = '*'  # there is not TRT for scenario ruptures
    rup.seed = oqparam.random_seed
    maxdist = oqparam.maximum_distance['default']
    sc = calc.filters.filter_sites_by_distance_to_rupture(
        rup, maxdist, sitecol)
    if sc is None:
        raise RuntimeError(
            'All sites were filtered out! maximum_distance=%s km' %
            maxdist)
    n = oqparam.number_of_ground_motion_fields
    events = numpy.zeros(n, stored_event_dt)
    events['eid'] = numpy.arange(n)
    ebr = EBRupture(rup, sc.sids, events)
    return ebr, sc


def get_source_model_lt(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        a :class:`openquake.commonlib.logictree.SourceModelLogicTree`
        instance
    """
    fname = oqparam.inputs.get('source_model_logic_tree')
    if fname:
        # NB: converting the random_seed into an integer is needed on Windows
        return logictree.SourceModelLogicTree(
            fname, validate=False, seed=int(oqparam.random_seed),
            num_samples=oqparam.number_of_logic_tree_samples)
    return logictree.FakeSmlt(oqparam.inputs['source_model'],
                              int(oqparam.random_seed),
                              oqparam.number_of_logic_tree_samples)


def get_source_models(oqparam, gsim_lt, source_model_lt, in_memory=True):
    """
    Build all the source models generated by the logic tree.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param gsim_lt:
        a :class:`openquake.commonlib.logictree.GsimLogicTree` instance
    :param source_model_lt:
        a :class:`openquake.commonlib.logictree.SourceModelLogicTree` instance
    :param in_memory:
        if True, keep in memory the sources, else just collect the TRTs
    :returns:
        an iterator over :class:`openquake.commonlib.logictree.SourceModel`
        tuples
    """
    converter = sourceconverter.SourceConverter(
        oqparam.investigation_time,
        oqparam.rupture_mesh_spacing,
        oqparam.complex_fault_mesh_spacing,
        oqparam.width_of_mfd_bin,
        oqparam.area_source_discretization)
    psr = nrml.SourceModelParser(converter)

    # consider only the effective realizations
    smlt_dir = os.path.dirname(source_model_lt.filename)
    for sm in source_model_lt.gen_source_models(gsim_lt):
        src_groups = []
        for name in sm.names.split():
            fname = os.path.abspath(os.path.join(smlt_dir, name))
            if in_memory:
                apply_unc = source_model_lt.make_apply_uncertainties(sm.path)
                logging.info('Parsing %s', fname)
                src_groups.extend(psr.parse_src_groups(fname, apply_unc))
            else:  # just collect the TRT models
                smodel = nrml.read(fname).sourceModel
                if smodel[0].tag.endswith('sourceGroup'):  # NRML 0.5 format
                    for sg_node in smodel:
                        sg = sourceconverter.SourceGroup(
                            sg_node['tectonicRegion'])
                        sg.sources = sg_node.nodes
                        src_groups.append(sg)
                else:  # NRML 0.4 format: smodel is a list of source nodes
                    src_groups.extend(
                        sourceconverter.SourceGroup.collect(smodel))
        num_sources = sum(len(sg.sources) for sg in src_groups)
        sm.src_groups = src_groups
        trts = [mod.trt for mod in src_groups]
        source_model_lt.tectonic_region_types.update(trts)
        logging.info(
            'Processed source model %d with %d potential gsim path(s) and %d '
            'sources', sm.ordinal + 1, sm.num_gsim_paths, num_sources)

        gsim_file = oqparam.inputs.get('gsim_logic_tree')
        if gsim_file:  # check TRTs
            for src_group in src_groups:
                if src_group.trt not in gsim_lt.values:
                    raise ValueError(
                        "Found in %r a tectonic region type %r inconsistent "
                        "with the ones in %r" % (sm, src_group.trt, gsim_file))
        yield sm

    # log if some source file is being used more than once
    for fname, hits in psr.fname_hits.items():
        if hits > 1:
            logging.info('%s has been considered %d times', fname, hits)


def get_composite_source_model(oqparam, in_memory=True):
    """
    Parse the XML and build a complete composite source model in memory.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param in_memory:
        if False, just parse the XML without instantiating the sources
    """
    smodels = []
    grp_id = 0
    idx = 0

    def getid(src):
        try:
            return src.source_id
        except AttributeError:
            return src['id']
    gsim_lt = get_gsim_lt(oqparam)
    source_model_lt = get_source_model_lt(oqparam)
    for source_model in get_source_models(
            oqparam, gsim_lt, source_model_lt, in_memory=in_memory):
        for src_group in source_model.src_groups:
            src_group.sources = sorted(src_group, key=getid)
            src_group.id = grp_id
            for src in src_group:
                # there are two cases depending on the flag in_memory:
                # 1) src is a hazardlib source and has a src_group_id
                #    attribute; in that case the source has to be numbered
                # 2) src is a Node object, then nothing must be done
                if isinstance(src, Node):
                    continue
                src.src_group_id = grp_id
                src.id = idx
                idx += 1
            grp_id += 1
            if grp_id >= TWO16:
                # the limit is really needed only for event based calculations
                raise ValueError('There is a limit of %d src groups!' % TWO16)
        smodels.append(source_model)
    csm = source.CompositeSourceModel(gsim_lt, source_model_lt, smodels)
    return csm


def get_job_info(oqparam, csm, sitecol):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param csm:
        a :class:`openquake.commonlib.source.CompositeSourceModel` instance
    :param sitecol:
        a :class:`openquake.hazardlib.site.SiteCollection` instance
    :returns:
        a dictionary with same parameters of the computation, in particular
        the input and output weights
    """
    info = {}
    # The input weight is given by the number of ruptures generated
    # by the sources; for point sources however a corrective factor
    # given by the parameter `point_source_weight` is applied
    input_weight = sum((src.weight or 0) * src_model.samples
                       for src_model in csm
                       for src_group in src_model.src_groups
                       for src in src_group)
    imtls = oqparam.imtls
    n_sites = len(sitecol) if sitecol else 0

    # the imtls object has values [NaN] when the levels are unknown
    # (this is a valid case for the event based hazard calculator)
    n_imts = len(imtls)
    n_levels = len(oqparam.imtls.array)

    n_realizations = oqparam.number_of_logic_tree_samples or sum(
        sm.num_gsim_paths for sm in csm)
    # NB: in the event based case `n_realizations` can be over-estimated,
    # if the method is called in the pre_execute phase, because
    # some tectonic region types may have no occurrencies.

    # The output weight is a pure number which is proportional to the size
    # of the expected output of the calculator. For classical and disagg
    # calculators it is given by
    # n_sites * n_imts * n_levels * n_statistics;
    # for the event based calculator is given by n_sites * n_realizations
    # * n_levels * n_imts * (n_ses * investigation_time) * NORMALIZATION_FACTOR
    n_stats = len(oqparam.hazard_stats()) or 1
    output_weight = n_sites * n_imts * n_stats
    if oqparam.calculation_mode == 'event_based':
        total_time = (oqparam.investigation_time *
                      oqparam.ses_per_logic_tree_path)
        output_weight *= total_time * NORMALIZATION_FACTOR
    else:
        output_weight *= n_levels / n_imts

    n_sources = csm.get_num_sources()
    info['hazard'] = dict(input_weight=input_weight,
                          output_weight=output_weight,
                          n_imts=n_imts,
                          n_levels=n_levels,
                          n_sites=n_sites,
                          n_sources=n_sources,
                          n_realizations=n_realizations)
    return info


def get_imts(oqparam):
    """
    Return a sorted list of IMTs as hazardlib objects
    """
    return list(map(imt.from_string, sorted(oqparam.imtls)))


def get_risk_model(oqparam):
    """
    Return a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance

   :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    rmdict = get_risk_models(oqparam)
    oqparam.set_risk_imtls(rmdict)
    if oqparam.calculation_mode.endswith('_bcr'):
        retro = get_risk_models(oqparam, 'vulnerability_retrofitted')
    else:
        retro = {}
    return riskinput.CompositeRiskModel(oqparam, rmdict, retro)

# ########################### exposure ############################ #

cost_type_dt = numpy.dtype([('name', hdf5.vstr),
                            ('type', hdf5.vstr),
                            ('unit', hdf5.vstr)])


def _get_exposure(fname, ok_cost_types, stop=None):
    """
    :param fname:
        path of the XML file containing the exposure
    :param ok_cost_types:
        a set of cost types (as strings)
    :param stop:
        node at which to stop parsing (or None)
    :returns:
        a pair (Exposure instance, list of asset nodes)
    """
    [exposure] = nrml.read(fname, stop=stop)
    if not exposure.tag.endswith('exposureModel'):
        raise InvalidFile('%s: expected exposureModel, got %s' %
                          (fname, exposure.tag))
    description = exposure.description
    try:
        conversions = exposure.conversions
    except AttributeError:
        conversions = Node('conversions', nodes=[Node('costTypes', [])])
    try:
        inslimit = conversions.insuranceLimit
    except AttributeError:
        inslimit = Node('insuranceLimit', text=True)
    try:
        deductible = conversions.deductible
    except AttributeError:
        deductible = Node('deductible', text=True)
    try:
        area = conversions.area
    except AttributeError:
        # NB: the area type cannot be an empty string because when sending
        # around the CostCalculator object we would run into this numpy bug
        # about pickling dictionaries with empty strings:
        # https://github.com/numpy/numpy/pull/5475
        area = Node('area', dict(type='?'))
    try:
        occupancy_periods = ~exposure.occupancyPeriods or ''
    except AttributeError:
        occupancy_periods = 'day night transit'
    try:
        tagNames = exposure.tagNames
    except AttributeError:
        tagNames = Node('tagNames', text='')
    tagnames = ~tagNames or []
    tagnames.insert(0, 'taxonomy')

    # read the cost types and make some check
    cost_types = []
    retrofitted = False
    for ct in conversions.costTypes:
        if not ok_cost_types or ct['name'] in ok_cost_types:
            with context(fname, ct):
                ctname = ct['name']
                if ctname == 'structural' and 'retrofittedType' in ct.attrib:
                    if ct['retrofittedType'] != ct['type']:
                        raise ValueError(
                            'The retrofittedType %s is different from the type'
                            '%s' % (ct['retrofittedType'], ct['type']))
                    if ct['retrofittedUnit'] != ct['unit']:
                        raise ValueError(
                            'The retrofittedUnit %s is different from the unit'
                            '%s' % (ct['retrofittedUnit'], ct['unit']))
                    retrofitted = True
                cost_types.append(
                    (ctname, valid.cost_type_type(ct['type']), ct['unit']))
    if 'occupants' in ok_cost_types:
        cost_types.append(('occupants', 'per_area', 'people'))
    cost_types.sort(key=operator.itemgetter(0))
    cost_types = numpy.array(cost_types, cost_type_dt)
    insurance_limit_is_absolute = il = inslimit.get('isAbsolute')
    deductible_is_absolute = de = deductible.get('isAbsolute')
    cc = asset.CostCalculator(
        {}, {}, {},
        True if de is None else de,
        True if il is None else il,
        {name: i for i, name in enumerate(tagnames)},
    )
    for ct in cost_types:
        name = ct['name']  # structural, nonstructural, ...
        cc.cost_types[name] = ct['type']  # aggregated, per_asset, per_area
        cc.area_types[name] = area['type']
        cc.units[name] = ct['unit']
    assets = []
    asset_refs = []
    exp = Exposure(
        exposure['id'], exposure['category'],
        ~description, cost_types, occupancy_periods.split(),
        insurance_limit_is_absolute, deductible_is_absolute, retrofitted,
        area.attrib, assets, asset_refs, cc, asset.TagCollection(tagnames))
    return exp, exposure.assets


def get_cost_calculator(oqparam):
    """
    Read the first lines of the exposure file and infers the cost calculator
    """
    return _get_exposure(oqparam.inputs['exposure'],
                         set(oqparam.all_cost_types),
                         stop='assets')[0].cost_calculator


def get_exposure(oqparam):
    """
    Read the full exposure in memory and build a list of
    :class:`openquake.risklib.asset.Asset` instances.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an :class:`Exposure` instance
    """
    return Exposure.read(
        oqparam.inputs['exposure'], oqparam.calculation_mode,
        oqparam.insured_losses, oqparam.region_constraint,
        oqparam.all_cost_types, oqparam.ignore_missing_costs)


class Exposure(object):
    """
    A class to read the exposure from XML/CSV files
    """
    fields = ['id', 'category', 'description', 'cost_types',
              'occupancy_periods', 'insurance_limit_is_absolute',
              'deductible_is_absolute', 'retrofitted',
              'area', 'assets', 'asset_refs',
              'cost_calculator', 'tagcol']

    @classmethod
    def read(cls, fname, calculation_mode='', insured_losses=False,
             region_constraint='', all_cost_types=(), ignore_missing_costs=(),
             asset_nodes=False):
        """
        Call `Exposure.read(fname)` to get an :class:`Exposure` instance
        keeping all the assets in memory or
        `Exposure.read(fname, asset_nodes=True)` to get an iterator over
        Node objects (one Node for each asset).
        """
        param = {'calculation_mode': calculation_mode}
        param['out_of_region'] = 0
        param['insured_losses'] = insured_losses
        if region_constraint:
            param['region'] = wkt.loads(region_constraint)
        else:
            param['region'] = None
        param['all_cost_types'] = set(all_cost_types)
        param['fname'] = fname
        param['relevant_cost_types'] = param['all_cost_types'] - set(
            ['occupants'])
        param['ignore_missing_costs'] = set(ignore_missing_costs)
        exposure, assets = _get_exposure(
            param['fname'], param['all_cost_types'])
        nodes = assets if assets else exposure._read_csv(
            assets.text, os.path.dirname(param['fname']))
        if asset_nodes:  # this is useful for the GED4ALL import script
            return nodes
        exposure._populate_from(nodes, param)
        if param['region'] and param['out_of_region']:
            logging.info('Discarded %d assets outside the region',
                         param['out_of_region'])
        if len(exposure.assets) == 0:
            raise RuntimeError('Could not find any asset within the region!')
        # sanity checks
        values = any(len(ass.values) + ass.number for ass in exposure.assets)
        assert values, 'Could not find any value??'
        return exposure

    def __init__(self, *values):
        assert len(values) == len(self.fields)
        for field, value in zip(self.fields, values):
            setattr(self, field, value)

    def _csv_header(self):
        """
        Extract the expected CSV header from the exposure metadata
        """
        fields = ['id', 'number', 'taxonomy', 'lon', 'lat']
        for name in self.cost_types['name']:
            fields.append(name)
        if 'per_area' in self.cost_types['type']:
            fields.append('area')
        fields.extend(self.occupancy_periods)
        fields.extend(self.tagcol.tagnames)
        return set(fields)

    def _read_csv(self, csvnames, dirname):
        """
        :param csvnames: names of csv files, space separated
        :param dirname: the directory where the csv files are
        :yields: asset nodes
        """
        expected_header = self._csv_header()
        fnames = [os.path.join(dirname, f) for f in csvnames.split()]
        for fname in fnames:
            with open(fname) as f:
                header = set(next(csv.reader(f)))
                if expected_header - header:
                    raise InvalidFile(
                        'Unexpected header in %s\nExpected: %s\nGot: %s' %
                        (fname, expected_header, header))
        for fname in fnames:
            with open(fname) as f:
                for i, dic in enumerate(csv.DictReader(f), 1):
                    asset = Node('asset', lineno=i)
                    with context(fname, asset):
                        asset['id'] = dic['id']
                        asset['number'] = float(dic['number'])
                        asset['taxonomy'] = dic['taxonomy']
                        if 'area' in dic:  # optional attribute
                            asset['area'] = dic['area']
                        loc = Node('location',
                                   dict(lon=valid.longitude(dic['lon']),
                                        lat=valid.latitude(dic['lat'])))
                        costs = Node('costs')
                        for cost in self.cost_types['name']:
                            a = dict(type=cost, value=dic[cost])
                            costs.append(Node('cost', a))
                        occupancies = Node('occupancies')
                        for period in self.occupancy_periods:
                            a = dict(occupants=dic[period], period=period)
                            occupancies.append(Node('occupancy', a))
                        tags = Node('tags')
                        for tagname in self.tagcol.tagnames:
                            if tagname != 'taxonomy':
                                tags.attrib[tagname] = dic[tagname]
                        asset.nodes.extend([loc, costs, occupancies, tags])
                        if i % 100000 == 0:
                            logging.info('Read %d assets', i)
                    yield asset

    def _populate_from(self, asset_nodes, param):
        asset_refs = set()
        for idx, asset_node in enumerate(asset_nodes):
            asset_id = asset_node['id']
            if asset_id in asset_refs:
                raise nrml.DuplicatedID(asset_id)
            asset_refs.add(asset_id)
            self._add_asset(idx, asset_node, param)

    def _add_asset(self, idx, asset_node, param):
        values = {}
        deductibles = {}
        insurance_limits = {}
        retrofitted = None
        asset_id = asset_node['id'].encode('utf8')
        with context(param['fname'], asset_node):
            self.asset_refs.append(asset_id)
            taxonomy = asset_node['taxonomy']
            if 'damage' in param['calculation_mode']:
                # calculators of 'damage' kind require the 'number'
                # if it is missing a KeyError is raised
                number = asset_node['number']
            else:
                # some calculators ignore the 'number' attribute;
                # if it is missing it is considered 1, since we are going
                # to multiply by it
                try:
                    number = asset_node['number']
                except KeyError:
                    number = 1
                else:
                    if 'occupants' in param['all_cost_types']:
                        values['occupants_None'] = number
            location = asset_node.location['lon'], asset_node.location['lat']
            if param['region'] and not geometry.Point(*location).within(
                    param['region']):
                param['out_of_region'] += 1
                return
            tagnode = getattr(asset_node, 'tags', None)
            dic = {} if tagnode is None else tagnode.attrib.copy()
            with context(param['fname'], tagnode):
                dic['taxonomy'] = taxonomy
                idxs = self.tagcol.add_tags(dic)
        try:
            costs = asset_node.costs
        except AttributeError:
            costs = Node('costs', [])
        try:
            occupancies = asset_node.occupancies
        except AttributeError:
            occupancies = Node('occupancies', [])
        for cost in costs:
            with context(param['fname'], cost):
                cost_type = cost['type']
                if cost_type == 'structural':
                    # retrofitted is defined only for structural
                    retrofitted = cost.get('retrofitted')
                if cost_type in param['relevant_cost_types']:
                    values[cost_type] = cost['value']
                    if param['insured_losses']:
                        deductibles[cost_type] = cost['deductible']
                        insurance_limits[cost_type] = cost['insuranceLimit']

        # check we are not missing a cost type
        missing = param['relevant_cost_types'] - set(values)
        if missing and missing <= param['ignore_missing_costs']:
            logging.warn(
                'Ignoring asset %s, missing cost type(s): %s',
                asset_id, ', '.join(missing))
            for cost_type in missing:
                values[cost_type] = None
        elif missing and 'damage' not in param['calculation_mode']:
            # missing the costs is okay for damage calculators
            with context(param['fname'], asset_node):
                raise ValueError("Invalid Exposure. "
                                 "Missing cost %s for asset %s" % (
                                     missing, asset_id))
        tot_occupants = 0
        for occupancy in occupancies:
            with context(param['fname'], occupancy):
                occupants = 'occupants_%s' % occupancy['period']
                values[occupants] = occupancy['occupants']
                tot_occupants += values[occupants]
        if occupancies:  # store average occupants
            values['occupants_None'] = tot_occupants / len(occupancies)
        area = float(asset_node.get('area', 1))
        ass = asset.Asset(idx, idxs, number, location, values, area,
                          deductibles, insurance_limits, retrofitted,
                          self.cost_calculator)
        self.assets.append(ass)

    def __repr__(self):
        return '<%s with %s assets>' % (self.__class__.__name__,
                                        len(self.assets))


def get_sitecol_assetcol(oqparam, exposure):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        the site collection and the asset collection
    """
    assets_by_loc = groupby(exposure.assets, key=lambda a: a.location)
    lons, lats = zip(*sorted(assets_by_loc))
    mesh = geo.Mesh(numpy.array(lons), numpy.array(lats))
    sitecol = get_site_collection(oqparam, mesh)
    assets_by_site = []
    for lonlat in zip(sitecol.lons, sitecol.lats):
        assets = assets_by_loc[lonlat]
        assets_by_site.append(sorted(assets, key=operator.attrgetter('idx')))
    assetcol = asset.AssetCollection(
        assets_by_site, exposure.tagcol, exposure.cost_calculator,
        oqparam.time_event, occupancy_periods=hdf5.array_of_vstr(
            sorted(exposure.occupancy_periods)))
    return sitecol, assetcol


def get_mesh_csvdata(csvfile, imts, num_values, validvalues):
    """
    Read CSV data in the format `IMT lon lat value1 ... valueN`.

    :param csvfile:
        a file or file-like object with the CSV data
    :param imts:
        a list of intensity measure types
    :param num_values:
        dictionary with the number of expected values per IMT
    :param validvalues:
        validation function for the values
    :returns:
        the mesh of points and the data as a dictionary
        imt -> array of curves for each site
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
            values = validvalues(' '.join(row[3:]))
            if len(values) != number_of_values[imt]:
                raise ValueError('Found %d values, expected %d' %
                                 (len(values), number_of_values[imt]))
        except (ValueError, DuplicatedPoint) as err:
            raise err.__class__('%s: file %s, line %d' % (err, csvfile, line))
        data += {imt: [numpy.array(values)]}
    points = lon_lats.pop(imts[0])
    for other_imt, other_points in lon_lats.items():
        if points != other_points:
            raise ValueError('Inconsistent locations between %s and %s' %
                             (imts[0], other_imt))
    lons, lats = zip(*sorted(points))
    mesh = geo.Mesh(numpy.array(lons), numpy.array(lats))
    return mesh, {imt: numpy.array(lst) for imt, lst in data.items()}


def get_gmfs(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        sitecol, eids, gmf array of shape (R, N, E, M)
    """
    M = len(oqparam.imtls)
    fname = oqparam.inputs['gmfs']
    if fname.endswith('.csv'):
        array = writers.read_composite_array(fname)
        R = len(numpy.unique(array['rlzi']))
        # the array has the structure rlzi, sid, eid, gmv_PGA, gmv_...
        dtlist = [(name, array.dtype[name]) for name in array.dtype.names[:3]]
        num_gmv = len(array.dtype.names[3:])
        assert num_gmv == M, (num_gmv, M)
        dtlist.append(('gmv', (F32, num_gmv)))
        eids = numpy.unique(array['eid'])
        E = len(eids)
        found_eids = set(eids)
        expected_eids = set(range(E))  # expected incremental eids
        missing_eids = expected_eids - found_eids
        if missing_eids:
            raise InvalidFile('Missing eids in the gmfs.csv file: %s'
                              % missing_eids)
        assert expected_eids == found_eids, (expected_eids, found_eids)
        eidx = {eid: e for e, eid in enumerate(eids)}
        sitecol = get_site_collection(oqparam)
        expected_sids = set(sitecol.sids)
        found_sids = set(numpy.unique(array['sid']))
        missing_sids = found_sids - expected_sids
        if missing_sids:
            raise InvalidFile(
                'Found site IDs missing in the sites.csv file: %s' %
                missing_sids)
        N = len(sitecol)
        gmfs = numpy.zeros((R, N, E, M), F32)
        counter = collections.Counter()
        for row in array.view(dtlist):
            key = row['rlzi'], row['sid'], eidx[row['eid']]
            gmfs[key] = row['gmv']
            counter[key] += 1
        dupl = [key for key in counter if counter[key] > 1]
        if dupl:
            raise InvalidFile('Duplicated (rlzi, sid, eid) in the GMFs file: '
                              '%s' % dupl)
    elif fname.endswith('.xml'):
        eids, gmfs_by_imt = get_scenario_from_nrml(oqparam, fname)
        N, E = gmfs_by_imt.shape
        gmfs = numpy.zeros((1, N, E, M), F32)
        for imti, imtstr in enumerate(oqparam.imtls):
            gmfs[0, :, :, imti] = gmfs_by_imt[imtstr]
    else:
        raise NotImplemented('Reading from %s' % fname)
    return eids, gmfs


def get_pmap(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        sitecol, probability map
    """
    fname = oqparam.inputs['hazard_curves']
    if fname.endswith('.csv'):
        return get_pmap_from_csv(oqparam, fname)
    elif fname.endswith('.xml'):
        return get_pmap_from_nrml(oqparam, fname)
    else:
        raise NotImplementedError('Reading from %s' % fname)


@deprecated('Reading hazard curves from CSV may change in the future')
def get_pmap_from_csv(oqparam, fname):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fname:
        a .txt file with format `IMT lon lat poe1 ... poeN`
    :returns:
        the site collection and the hazard curves read by the .txt file
    """
    if not oqparam.imtls:
        oqparam.set_risk_imtls(get_risk_models(oqparam))
    if not oqparam.imtls:
        raise ValueError('Missing intensity_measure_types_and_levels in %s'
                         % oqparam.inputs['job_ini'])
    num_values = list(map(len, list(oqparam.imtls.values())))
    with open(oqparam.inputs['hazard_curves']) as csvfile:
        mesh, hcurves = get_mesh_csvdata(
            csvfile, list(oqparam.imtls), num_values,
            valid.decreasing_probabilities)
    sitecol = get_site_collection(oqparam, mesh)
    array = numpy.zeros((len(sitecol), sum(num_values)))
    for imt_ in hcurves:
        array[:, oqparam.imtls.slicedic[imt_]] = hcurves[imt_]
    return sitecol, ProbabilityMap.from_array(array, sitecol.sids)


def get_pmap_from_nrml(oqparam, fname):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fname:
        an XML file containing hazard curves
    :returns:
        sitecol, curve array
    """
    hcurves_by_imt = {}
    oqparam.hazard_imtls = imtls = collections.OrderedDict()
    for hcurves in nrml.read(fname):
        imt = hcurves['IMT']
        oqparam.investigation_time = hcurves['investigationTime']
        if imt == 'SA':
            imt += '(%s)' % hcurves['saPeriod']
        imtls[imt] = ~hcurves.IMLs
        data = sorted((~node.Point.pos, ~node.poEs) for node in hcurves[1:])
        hcurves_by_imt[imt] = numpy.array([d[1] for d in data])
    lons, lats = [], []
    for xy, poes in data:
        lons.append(xy[0])
        lats.append(xy[1])
    mesh = geo.Mesh(numpy.array(lons), numpy.array(lats))
    sitecol = get_site_collection(oqparam, mesh)
    num_levels = sum(len(v) for v in imtls.values())
    array = numpy.zeros((len(sitecol), num_levels))
    imtls = DictArray(imtls)
    for imt_ in hcurves_by_imt:
        array[:, imtls.slicedic[imt_]] = hcurves_by_imt[imt_]
    return sitecol, ProbabilityMap.from_array(array, sitecol.sids)


# used in get_scenario_from_nrml
def _extract_eids_sitecounts(gmfset):
    eids = set()
    counter = collections.Counter()
    for gmf in gmfset:
        eids.add(gmf['ruptureId'])
        for node in gmf:
            counter[node['lon'], node['lat']] += 1
    return numpy.array(sorted(eids), numpy.uint64), counter


@deprecated('Use the .csv format for the GMFs instead')
def get_scenario_from_nrml(oqparam, fname):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fname:
        the NRML files containing the GMFs
    :returns:
        a triple (sitecol, eids, gmf array)
    """
    if not oqparam.imtls:
        oqparam.set_risk_imtls(get_risk_models(oqparam))
    imts = sorted(oqparam.imtls)
    num_imts = len(imts)
    imt_dt = numpy.dtype([(imt, F32) for imt in imts])
    gmfset = nrml.read(fname).gmfCollection.gmfSet
    eids, sitecounts = _extract_eids_sitecounts(gmfset)
    coords = sorted(sitecounts)
    oqparam.sites = [(lon, lat, 0) for lon, lat in coords]
    site_idx = {lonlat: i for i, lonlat in enumerate(coords)}
    oqparam.number_of_ground_motion_fields = num_events = len(eids)
    num_sites = len(oqparam.sites)
    gmf_by_imt = numpy.zeros((num_events, num_sites), imt_dt)
    counts = collections.Counter()
    for i, gmf in enumerate(gmfset):
        if len(gmf) != num_sites:  # there must be one node per site
            raise InvalidFile('Expected %d sites, got %d nodes in %s, line %d'
                              % (num_sites, len(gmf), fname, gmf.lineno))
        counts[gmf['ruptureId']] += 1
        imt = gmf['IMT']
        if imt == 'SA':
            imt = 'SA(%s)' % gmf['saPeriod']
        for node in gmf:
            sid = site_idx[node['lon'], node['lat']]
            gmf_by_imt[imt][i % num_events, sid] = node['gmv']

    for rupid, count in sorted(counts.items()):
        if count < num_imts:
            raise InvalidFile("Found a missing ruptureId %d in %s" %
                              (rupid, fname))
        elif count > num_imts:
            raise InvalidFile("Found a duplicated ruptureId '%s' in %s" %
                              (rupid, fname))
    expected_gmvs_per_site = num_imts * len(eids)
    for lonlat, counts in sitecounts.items():
        if counts != expected_gmvs_per_site:
            raise InvalidFile(
                '%s: expected %d gmvs at location %s, found %d' %
                (fname, expected_gmvs_per_site, lonlat, counts))
    return eids, gmf_by_imt.T


def get_mesh_hcurves(oqparam):
    """
    Read CSV data in the format `lon lat, v1-vN, w1-wN, ...`.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        the mesh of points and the data as a dictionary
        imt -> array of curves for each site
    """
    imtls = oqparam.imtls
    lon_lats = set()
    data = AccumDict()  # imt -> list of arrays
    ncols = len(imtls) + 1  # lon_lat + curve_per_imt ...
    csvfile = oqparam.inputs['hazard_curves']
    for line, row in enumerate(csv.reader(csvfile), 1):
        try:
            if len(row) != ncols:
                raise ValueError('Expected %d columns, found %d' %
                                 ncols, len(row))
            x, y = row[0].split()
            lon_lat = valid.longitude(x), valid.latitude(y)
            if lon_lat in lon_lats:
                raise DuplicatedPoint(lon_lat)
            lon_lats.add(lon_lat)
            for i, imt_ in enumerate(imtls, 1):
                values = valid.decreasing_probabilities(row[i])
                if len(values) != len(imtls[imt_]):
                    raise ValueError('Found %d values, expected %d' %
                                     (len(values), len(imtls([imt_]))))
                data += {imt_: [numpy.array(values)]}
        except (ValueError, DuplicatedPoint) as err:
            raise err.__class__('%s: file %s, line %d' % (err, csvfile, line))
    lons, lats = zip(*sorted(lon_lats))
    mesh = geo.Mesh(numpy.array(lons), numpy.array(lats))
    return mesh, {imt: numpy.array(lst) for imt, lst in data.items()}


def get_checksum32(oqparam):
    """
    Build an unsigned 32 bit integer from the input files of the calculation
    """
    # NB: using adler32 & 0xffffffff is the documented way to get a checksum
    # which is the same between Python 2 and Python 3
    checksum = 0
    for key in sorted(oqparam.inputs):
        fname = oqparam.inputs[key]
        if not fname:
            continue
        elif key == 'source':  # list of fnames and/or strings
            for f in fname:
                data = open(f, 'rb').read()
                checksum = zlib.adler32(data, checksum) & 0xffffffff
        elif os.path.exists(fname):
            data = open(fname, 'rb').read()
            checksum = zlib.adler32(data, checksum) & 0xffffffff
        else:
            raise ValueError('%s does not exist or is not a file' % fname)
    return checksum
