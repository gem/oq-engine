# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
import os
import csv
import copy
import zlib
import shutil
import zipfile
import logging
import tempfile
import configparser
import collections
import numpy

from openquake.baselib.general import (
    AccumDict, DictArray, deprecated, random_filter)
from openquake.baselib.python3compat import decode, zip
from openquake.baselib.node import Node
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.calc.gmf import CorrelationButNoInterIntraStdDevs
from openquake.hazardlib import (
    geo, site, imt, valid, sourceconverter, nrml, InvalidFile)
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.risklib import asset, riskinput
from openquake.risklib.riskmodels import get_risk_models
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import logictree, source, writers

# the following is quite arbitrary, it gives output weights that I like (MS)
NORMALIZATION_FACTOR = 1E-2
TWO16 = 2 ** 16  # 65,536
F32 = numpy.float32
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64

Site = collections.namedtuple('Site', 'sid lon lat')
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
    input_zip = None
    if len(job_inis) == 1 and job_inis[0].endswith('.zip'):
        input_zip = job_inis[0]
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
    if input_zip:
        params['inputs']['input_zip'] = os.path.abspath(input_zip)

    for sect in cp.sections():
        _update(params, cp.items(sect), base_path)
    _update(params, kw.items(), base_path)  # override on demand

    # populate the 'source' list
    inputs = params['inputs']
    smlt = inputs.get('source_model_logic_tree')
    if smlt:
        inputs['source'] = []
        for paths in gen_sm_paths(smlt):
            inputs['source'].extend(paths)
    elif 'source_model' in inputs:
        inputs['source'] = [inputs['source_model']]
    return params


def gen_sm_paths(smlt):
    """
    Yields the path names for the source models listed in the smlt file,
    a block at the time.
    """
    base_path = os.path.dirname(smlt)
    for model in source.collect_source_model_paths(smlt):
        paths = []
        for name in model.split():
            if os.path.isabs(name):
                raise InvalidFile('%s: %s must be a relative path' %
                                  (smlt, name))
            fname = os.path.abspath(os.path.join(base_path, name))
            if os.path.exists(fname):  # consider only real paths
                paths.append(fname)
        yield paths


def get_oqparam(job_ini, pkg=None, calculators=None, hc_id=None, validate=1):
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
    :param validate:
        Flag. By default it is true and the parameters are validated
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
    if validate:
        oqparam.validate()
    return oqparam


pmap = None  # set as side effect when the user reads hazard_curves from a file
# the hazard curves format does not split the site locations from the data (an
# unhappy legacy design choice that I fixed in the GMFs CSV format only) thus
# this hack is necessary, otherwise we would have to parse the file twice

exposure = None  # set as side effect when the user reads the site mesh
# this hack is necessary, otherwise we would have to parse the exposure twice

gmfs, eids = None, None  # set as a sided effect when reading gmfs.xml
# this hack is necessary, otherwise we would have to parse the file twice


def get_mesh(oqparam):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, or the region.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    global pmap, exposure, gmfs, eids
    if 'exposure' in oqparam.inputs and exposure is None:
        # read it only once
        exposure = get_exposure(oqparam)
    if oqparam.sites:
        return geo.Mesh.from_coords(oqparam.sites)
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
        # TODO: sort=True below would break a lot of tests :-(
        return geo.Mesh.from_coords(c, sort=False)
    elif 'hazard_curves' in oqparam.inputs:
        fname = oqparam.inputs['hazard_curves']
        if fname.endswith('.csv'):
            mesh, pmap = get_pmap_from_csv(oqparam, fname)
        elif fname.endswith('.xml'):
            mesh, pmap = get_pmap_from_nrml(oqparam, fname)
        else:
            raise NotImplementedError('Reading from %s' % fname)
        return mesh
    elif 'gmfs' in oqparam.inputs:
        eids, gmfs = _get_gmfs(oqparam)  # sets oqparam.sites
        return geo.Mesh.from_coords(oqparam.sites)
    elif oqparam.region and oqparam.region_grid_spacing:
        poly = geo.Polygon.from_wkt(oqparam.region)
        try:
            mesh = poly.discretize(oqparam.region_grid_spacing)
            return geo.Mesh.from_coords(zip(mesh.lons, mesh.lats))
        except Exception:
            raise ValueError(
                'Could not discretize region %(region)s with grid spacing '
                '%(region_grid_spacing)s' % vars(oqparam))
    elif 'exposure' in oqparam.inputs:
        return exposure.mesh


site_model_dt = numpy.dtype([
    ('lon', numpy.float64),
    ('lat', numpy.float64),
    ('vs30', numpy.float64),
    ('vs30measured', numpy.bool),
    ('z1pt0', numpy.float64),
    ('z2pt5', numpy.float64),
    ('backarc', numpy.bool),
])


def get_site_model(oqparam):
    """
    Convert the NRML file into an array of site parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an array with fields lon, lat, vs30, measured, z1pt0, z2pt5, backarc
    """
    nodes = nrml.read(oqparam.inputs['site_model']).siteModel
    params = sorted(valid.site_param(**node.attrib) for node in nodes)
    array = numpy.zeros(len(params), site_model_dt)
    for i, param in enumerate(params):
        rec = array[i]
        for name in site_model_dt.names:
            rec[name] = getattr(param, name)
    return array


def get_site_collection(oqparam):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    mesh = get_mesh(oqparam)
    if oqparam.inputs.get('site_model'):
        sm = get_site_model(oqparam)
        try:
            # in the future we could have elevation in the site model
            depth = sm['depth']
        except ValueError:
            # this is the normal case
            depth = None
        if mesh is None:
            # extract the site collection directly from the site model
            sitecol = site.SiteCollection.from_points(
                sm['lon'], sm['lat'], depth, sm)
        else:
            # associate the site parameters to the mesh
            sitecol = site.SiteCollection.from_points(
                mesh.lons, mesh.lats, mesh.depths)
            sc, params = geo.utils.assoc(
                sm, sitecol, oqparam.max_site_model_distance, 'warn')
            for sid, param in zip(sc.sids, params):
                for name in site_model_dt.names[2:]:  # except lon, lat
                    sitecol.array[sid][name] = param[name]
    else:  # use the default site params
        sitecol = site.SiteCollection.from_points(
            mesh.lons, mesh.lats, mesh.depths, oqparam)
    ss = os.environ.get('OQ_SAMPLE_SITES')
    if ss:
        # debugging tip to reduce the size of a calculation
        # OQ_SAMPLE_SITES=.1 oq engine --run job.ini
        # will run a computation with 10 times less sites
        sitecol.array = numpy.array(random_filter(sitecol.array, float(ss)))
        sitecol.make_complete()
    return sitecol


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
    gmfcorr = oqparam.get_correl_model()
    for trt, gsims in gsim_lt.values.items():
        for gsim in gsims:
            if gmfcorr and (gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES ==
                            set([StdDev.TOTAL])):
                raise CorrelationButNoInterIntraStdDevs(gmfcorr, gsim)
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
    Return an ordered dictionary gsim -> [realization index]. Work for
    gsim logic trees with a single tectonic region type.
    """
    cinfo = source.CompositionInfo.fake(get_gsim_lt(oqparam))
    ra = cinfo.get_rlzs_assoc()
    dic = collections.OrderedDict()
    for rlzi, gsim_by_trt in enumerate(ra.gsim_by_trt):
        dic[gsim_by_trt['*']] = [rlzi]
    return dic


def get_rupture(oqparam):
    """
    Read the `rupture_model` file and by filter the site collection

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an hazardlib rupture
    """
    rup_model = oqparam.inputs['rupture_model']
    [rup_node] = nrml.read(rup_model)
    conv = sourceconverter.RuptureConverter(
        oqparam.rupture_mesh_spacing, oqparam.complex_fault_mesh_spacing)
    rup = conv.convert_node(rup_node)
    rup.tectonic_region_type = '*'  # there is not TRT for scenario ruptures
    rup.seed = oqparam.random_seed
    return rup


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
        an iterator over :class:`openquake.commonlib.logictree.LtSourceModel`
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
                logging.info('Reading %s', fname)
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

    # check investigation_time
    psr.check_nonparametric_sources(oqparam.investigation_time)

    # log if some source file is being used more than once
    dupl = 0
    for fname, hits in psr.fname_hits.items():
        if hits > 1:
            logging.info('%s has been considered %d times', fname, hits)
            if not psr.changed_sources:
                dupl += hits
    if dupl and not oqparam.optimize_same_id_sources:
        logging.warn('You are doing redundant calculations: please make sure '
                     'that different sources have different IDs and set '
                     'optimize_same_id_sources=true in your .ini file')


def getid(src):
    try:
        return src.source_id
    except AttributeError:
        return src['id']


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
    csm = source.CompositeSourceModel(gsim_lt, source_model_lt, smodels,
                                      oqparam.optimize_same_id_sources)
    for sm in csm.source_models:
        counter = collections.Counter()
        for sg in sm.src_groups:
            for srcid in map(getid, sg):
                counter[srcid] += 1
        dupl = [srcid for srcid in counter if counter[srcid] > 1]
        if dupl:
            raise nrml.DuplicatedID('Found duplicated source IDs in %s: %s'
                                    % (sm, dupl))
    return csm


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


def get_cost_calculator(oqparam):
    """
    Read the first lines of the exposure file and infers the cost calculator
    """
    exposure = asset._get_exposure(oqparam.inputs['exposure'], stop='assets')
    return exposure[0].cost_calculator


def get_exposure(oqparam):
    """
    Read the full exposure in memory and build a list of
    :class:`openquake.risklib.asset.Asset` instances.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an :class:`Exposure` instance or a compatible AssetCollection
    """
    logging.info('Reading the exposure')
    exposure = asset.Exposure.read(
        oqparam.inputs['exposure'], oqparam.calculation_mode,
        oqparam.region, oqparam.ignore_missing_costs)
    exposure.mesh, exposure.assets_by_site = exposure.get_mesh_assets_by_site()
    return exposure


def get_sitecol_assetcol(oqparam, haz_sitecol):
    """
    :param oqparam: calculation parameters
    :param haz_sitecol: the hazard site collection
    :returns: (site collection, asset collection) instances
    """
    global exposure
    if exposure is None:
        # haz_sitecol not extracted from the exposure
        exposure = get_exposure(oqparam)
    if oqparam.region_grid_spacing and not oqparam.region:
        # extract the hazard grid from the exposure
        exposure.mesh = exposure.mesh.get_convex_hull().dilate(
            oqparam.region_grid_spacing).discretize(
                oqparam.region_grid_spacing)
        haz_sitecol = get_site_collection(oqparam)
        haz_distance = oqparam.region_grid_spacing
        if haz_distance != oqparam.asset_hazard_distance:
            logging.info('Using asset_hazard_distance=%d km instead of %d km',
                         haz_distance, oqparam.asset_hazard_distance)
    else:
        haz_distance = oqparam.asset_hazard_distance

    if haz_sitecol.mesh != exposure.mesh:
        # associate the assets to the hazard sites
        tot_assets = sum(len(assets) for assets in exposure.assets_by_site)
        mode = 'strict' if oqparam.region_grid_spacing else 'filter'
        sitecol, assets_by = geo.utils.assoc(
            exposure.assets_by_site, haz_sitecol, haz_distance, mode)
        assets_by_site = [[] for _ in sitecol.complete.sids]
        num_assets = 0
        for sid, assets in zip(sitecol.sids, assets_by):
            assets_by_site[sid] = assets
            num_assets += len(assets)
        logging.info(
            'Associated %d assets to %d sites', num_assets, len(sitecol))
        if num_assets < tot_assets:
            logging.warn('Discarded %d assets outside the '
                         'asset_hazard_distance of %d km',
                         tot_assets - num_assets, haz_distance)
    else:
        # asset sites and hazard sites are the same
        sitecol = haz_sitecol
        assets_by_site = exposure.assets_by_site

    asset_refs = [exposure.asset_refs[asset.ordinal]
                  for assets in assets_by_site for asset in assets]
    assetcol = asset.AssetCollection(
        asset_refs, assets_by_site, exposure.tagcol, exposure.cost_calculator,
        oqparam.time_event, exposure.occupancy_periods)

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


def _get_gmfs(oqparam):
    M = len(oqparam.imtls)
    assert M, ('oqparam.imtls is empty, did you call '
               'oqparam.set_risk_imtls(get_risk_models(oqparam))?')
    fname = oqparam.inputs['gmfs']
    if fname.endswith('.csv'):
        array = writers.read_composite_array(fname).array
        R = len(numpy.unique(array['rlzi']))
        if R > 1:
            raise InvalidFile('%s: found %d realizations, currently only one '
                              'realization is supported' % (fname, R))
        # the array has the structure rlzi, sid, eid, gmv_PGA, gmv_...
        dtlist = [(name, array.dtype[name]) for name in array.dtype.names[:3]]
        required_imts = list(oqparam.imtls)
        imts = [name[4:] for name in array.dtype.names[3:]]
        if imts != required_imts:
            raise ValueError('Required %s, but %s contains %s' % (
                required_imts, fname, imts))
        dtlist.append(('gmv', (F32, M)))
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


@deprecated('Reading hazard curves from CSV may change in the future')
def get_pmap_from_csv(oqparam, fname):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fname:
        a .txt file with format `IMT lon lat poe1 ... poeN`
    :returns:
        the site mesh and the hazard curves read by the .txt file
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
    array = numpy.zeros((len(mesh), sum(num_values)))
    for imt_ in hcurves:
        array[:, oqparam.imtls.slicedic[imt_]] = hcurves[imt_]
    return mesh, ProbabilityMap.from_array(array, range(len(mesh)))


def get_pmap_from_nrml(oqparam, fname):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fname:
        an XML file containing hazard curves
    :returns:
        site mesh, curve array
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
    num_levels = sum(len(v) for v in imtls.values())
    array = numpy.zeros((len(mesh), num_levels))
    imtls = DictArray(imtls)
    for imt_ in hcurves_by_imt:
        array[:, imtls.slicedic[imt_]] = hcurves_by_imt[imt_]
    return mesh, ProbabilityMap.from_array(array, range(len(mesh)))


# used in get_scenario_from_nrml
def _extract_eids_sitecounts(gmfset):
    eids = set()
    counter = collections.Counter()
    for gmf in gmfset:
        eids.add(gmf['ruptureId'])
        for node in gmf:
            counter[node['lon'], node['lat']] += 1
    eids = numpy.array(sorted(eids), numpy.uint64)
    if (eids != numpy.arange(len(eids), dtype=numpy.uint64)).any():
        raise ValueError('There are ruptureIds in the gmfs_file not in the '
                         'range [0, %d)' % len(eids))
    return eids, counter


@deprecated('Use the .csv format for the GMFs instead')
def get_scenario_from_nrml(oqparam, fname):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fname:
        the NRML files containing the GMFs
    :returns:
        a pair (eids, gmf array)
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


# used in utils/reduce_sm and utils/extract_source
def reduce_source_model(smlt_file, source_ids):
    """
    Extract sources from the composite source model
    """
    for paths in gen_sm_paths(smlt_file):
        for path in paths:
            root = nrml.read(path)
            model = Node('sourceModel', root[0].attrib)
            origmodel = root[0]
            if root['xmlns'] == 'http://openquake.org/xmlns/nrml/0.4':
                for src_node in origmodel:
                    if src_node['id'] in source_ids:
                        model.nodes.append(src_node)
            else:  # nrml/0.5
                for src_group in origmodel:
                    sg = copy.copy(src_group)
                    sg.nodes = []
                    for src_node in src_group:
                        if src_node['id'] in source_ids:
                            sg.nodes.append(src_node)
                    if sg.nodes:
                        model.nodes.append(sg)
            if model:
                shutil.copy(path, path + '.bak')
                with open(path, 'wb') as f:
                    nrml.write([model], f, xmlns=root['xmlns'])
                    logging.warn('Reduced %s' % path)


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
