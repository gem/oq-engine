# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
import ast
import csv
import copy
import zlib
import shutil
import zipfile
import logging
import tempfile
import functools
import configparser
import collections
import numpy
import requests

from openquake.baselib import performance, hdf5
from openquake.baselib.general import random_filter
from openquake.baselib.python3compat import decode, zip
from openquake.baselib.node import Node
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.gmf import CorrelationButNoInterIntraStdDevs
from openquake.hazardlib import (
    geo, site, imt, valid, sourceconverter, nrml, InvalidFile)
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.risklib import asset, riskinput
from openquake.risklib.riskmodels import get_risk_models
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib.source_model_factory import SourceModelFactory
from openquake.commonlib import logictree, source

# the following is quite arbitrary, it gives output weights that I like (MS)
NORMALIZATION_FACTOR = 1E-2
F32 = numpy.float32
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
Site = collections.namedtuple('Site', 'sid lon lat')


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


def unzip_rename(zpath, name):
    """
    :param zpath: full path to a .zip archive
    :param name: exposure.xml or ssmLT.xml
    :returns: path to an .xml file with the same name of the archive
    """
    xpath = zpath[:-4] + '.xml'
    if os.path.exists(xpath):
        # already unzipped
        return xpath
    dpath = os.path.dirname(zpath)
    with zipfile.ZipFile(zpath) as archive:
        for nam in archive.namelist():
            fname = os.path.join(dpath, nam)
            if os.path.exists(fname):  # already unzipped
                os.rename(fname, fname + '.bak')
                logging.warning('Overriding %s with the file in %s',
                                fname, zpath)
        logging.info('Unzipping %s', zpath)
        archive.extractall(dpath)
    xname = os.path.join(dpath, name)
    if os.path.exists(xname):
        os.rename(xname, xpath)
    return xpath


def normalize(key, fnames, base_path):
    input_type, _ext = key.rsplit('_', 1)
    filenames = []
    for val in fnames:
        if '://' in val:
            # get the data from an URL
            resp = requests.get(val)
            _, val = val.rsplit('/', 1)
            with open(os.path.join(base_path, val), 'wb') as f:
                f.write(resp.content)
        elif os.path.isabs(val):
            raise ValueError('%s=%s is an absolute path' % (key, val))
        if val.endswith('.zip'):
            zpath = os.path.normpath(os.path.join(base_path, val))
            if key == 'exposure_file':
                name = 'exposure.xml'
            elif key == 'source_model_logic_tree_file':
                name = 'ssmLT.xml'
            else:
                raise KeyError('Unknown key %s' % key)
            val = unzip_rename(zpath, name)
        else:
            val = os.path.normpath(os.path.join(base_path, val))
        if not os.path.exists(val):
            # tested in archive_err_2
            raise OSError('No such file: %s' % val)
        filenames.append(val)
    return input_type, filenames


def _update(params, items, base_path):
    for key, value in items:
        if key in ('hazard_curves_csv', 'site_model_file', 'exposure_file'):
            input_type, fnames = normalize(key, value.split(), base_path)
            params['inputs'][input_type] = fnames
        elif key.endswith(('_file', '_csv', '_hdf5')):
            if value.startswith('{'):
                dic = ast.literal_eval(value)  # name -> relpath
                input_type, fnames = normalize(key, dic.values(), base_path)
                params['inputs'][input_type] = fnames
                params[input_type] = ' '.join(dic)
            elif value:
                input_type, [fname] = normalize(key, [value], base_path)
                params['inputs'][input_type] = fname
        elif isinstance(value, str) and value.endswith('.hdf5'):
            # for the reqv feature
            fname = os.path.normpath(os.path.join(base_path, value))
            try:
                reqv = params['inputs']['reqv']
            except KeyError:
                params['inputs']['reqv'] = {key: fname}
            else:
                reqv.update({key: fname})
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

    if params['inputs'].get('reqv'):
        # using pointsource_distance=0 because of the reqv approximation
        params['pointsource_distance'] = '0'
    return params


def get_oqparam(job_ini, pkg=None, calculators=None, hc_id=None, validate=1,
                **kw):
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
    :param kw:
        String-valued keyword arguments used to override the job.ini parameters
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
    job_ini.update(kw)
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


def get_csv_header(fname, sep=','):
    """
    :param fname: a CSV file
    :param sep: the separator (default comma)
    :returns: the first line of fname
    """
    with open(fname, encoding='utf-8-sig') as f:
        return next(f).split(sep)


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
        fname = oqparam.inputs['sites']
        header = get_csv_header(fname)
        if 'lon' in header:
            data = []
            for i, row in enumerate(
                    csv.DictReader(open(fname, encoding='utf-8-sig'))):
                if header[0] == 'site_id' and row['site_id'] != str(i):
                    raise InvalidFile('%s: expected site_id=%d, got %s' % (
                        fname, i, row['site_id']))
                data.append(' '.join([row['lon'], row['lat']]))
        elif 'gmfs' in oqparam.inputs:
            raise InvalidFile('Missing header in %(sites)s' % oqparam.inputs)
        else:
            data = [line.replace(',', ' ')
                    for line in open(fname, encoding='utf-8-sig')]
        coords = valid.coordinates(','.join(data))
        start, stop = oqparam.sites_slice
        c = (coords[start:stop] if header[0] == 'site_id'
             else sorted(coords[start:stop]))
        return geo.Mesh.from_coords(c)
    elif 'hazard_curves' in oqparam.inputs:
        fname = oqparam.inputs['hazard_curves']
        if isinstance(fname, list):  # for csv
            mesh, pmap = get_pmap_from_csv(oqparam, fname)
        else:
            raise NotImplementedError('Reading from %s' % fname)
        return mesh
    elif oqparam.region_grid_spacing:
        if oqparam.region:
            poly = geo.Polygon.from_wkt(oqparam.region)
        elif 'site_model' in oqparam.inputs:
            sm = get_site_model(oqparam)
            poly = geo.Mesh(sm['lon'], sm['lat']).get_convex_hull()
        elif exposure:
            poly = exposure.mesh.get_convex_hull()
        else:
            raise InvalidFile('There is a grid spacing but not a region, '
                              'nor a site model, nor an exposure in %s' %
                              oqparam.inputs['job_ini'])
        try:
            mesh = poly.dilate(oqparam.region_grid_spacing).discretize(
                oqparam.region_grid_spacing)
            return geo.Mesh.from_coords(zip(mesh.lons, mesh.lats))
        except Exception:
            raise ValueError(
                'Could not discretize region with grid spacing '
                '%(region_grid_spacing)s' % vars(oqparam))
    elif 'exposure' in oqparam.inputs:
        return exposure.mesh


def get_site_model(oqparam):
    """
    Convert the NRML file into an array of site parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an array with fields lon, lat, vs30, ...
    """
    req_site_params = get_gsim_lt(oqparam).req_site_params
    arrays = []
    for fname in oqparam.inputs['site_model']:
        if isinstance(fname, str) and fname.endswith('.csv'):
            sm = hdf5.read_csv(
                 fname, {None: float, 'vs30measured': numpy.uint8}).array
            if 'site_id' in sm.dtype.names:
                raise InvalidFile('%s: you passed a sites.csv file instead of '
                                  'a site_model.csv file!' % fname)
            z = numpy.zeros(len(sm), sorted(sm.dtype.descr))
            for name in z.dtype.names:  # reorder the fields
                z[name] = sm[name]
            arrays.append(z)
            continue
        nodes = nrml.read(fname).siteModel
        params = [valid.site_param(node.attrib) for node in nodes]
        missing = req_site_params - set(params[0])
        if 'vs30measured' in missing:  # use a default of False
            missing -= {'vs30measured'}
            for param in params:
                param['vs30measured'] = False
        if 'backarc' in missing:  # use a default of False
            missing -= {'backarc'}
            for param in params:
                param['backarc'] = False
        if missing:
            raise InvalidFile('%s: missing parameter %s' %
                              (oqparam.inputs['site_model'],
                               ', '.join(missing)))
        # NB: the sorted in sorted(params[0]) is essential, otherwise there is
        # an heisenbug in scenario/test_case_4
        site_model_dt = numpy.dtype([(p, site.site_param_dt[p])
                                     for p in sorted(params[0])])
        sm = numpy.array([tuple(param[name] for name in site_model_dt.names)
                          for param in params], site_model_dt)
        arrays.append(sm)
    return numpy.concatenate(arrays)


def get_site_collection(oqparam):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    mesh = get_mesh(oqparam)
    req_site_params = get_gsim_lt(oqparam).req_site_params
    grid_spacing = oqparam.region_grid_spacing
    if oqparam.inputs.get('site_model'):
        sm = get_site_model(oqparam)
        try:
            # in the future we could have elevation in the site model
            depth = sm['depth']
        except ValueError:
            # this is the normal case
            depth = None
        if grid_spacing:
            grid = mesh.get_convex_hull().dilate(
                grid_spacing).discretize(grid_spacing)
            grid_sites = site.SiteCollection.from_points(
                grid.lons, grid.lats, req_site_params=req_site_params)
            sitecol, params, _ = geo.utils.assoc(
                sm, grid_sites, oqparam.region_grid_spacing * 1.414, 'filter')
            logging.info('Associating %d site model sites to %d grid sites',
                         len(sm), len(sitecol))
            sitecol.make_complete()
        else:
            sitecol = site.SiteCollection.from_points(
                sm['lon'], sm['lat'], depth, sm, req_site_params)
            params = sm
        for name in req_site_params:
            if name in ('vs30measured', 'backarc') \
                   and name not in params.dtype.names:
                sitecol._set(name, 0)  # the default
            else:
                sitecol._set(name, params[name])
    elif mesh is None and oqparam.ground_motion_fields:
        raise InvalidFile('You are missing sites.csv or site_model.csv in %s'
                          % oqparam.inputs['job_ini'])
    elif mesh is None:
        # a None sitecol is okay when computing the ruptures only
        return
    else:  # use the default site params
        sitecol = site.SiteCollection.from_points(
            mesh.lons, mesh.lats, mesh.depths, oqparam, req_site_params)
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
    gmfcorr = oqparam.correl_model
    for trt, gsims in gsim_lt.values.items():
        for gsim in gsims:
            if gmfcorr and (gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES ==
                            {StdDev.TOTAL}):
                raise CorrelationButNoInterIntraStdDevs(gmfcorr, gsim)
    trts = set(oqparam.minimum_magnitude) - {'default'}
    expected_trts = set(gsim_lt.values)
    assert trts <= expected_trts, (trts, expected_trts)
    imt_dep_w = any(len(branch.weight.dic) > 1 for branch in gsim_lt.branches)
    if oqparam.number_of_logic_tree_samples and imt_dep_w:
        raise NotImplementedError('IMT-dependent weights in the logic tree '
                                  'do not work with sampling!')
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
    dic = {}
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
    rup.serial = oqparam.random_seed
    return rup


def get_source_model_lt(oqparam, validate=True):
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
        smlt = logictree.SourceModelLogicTree(
            fname, validate, seed=int(oqparam.random_seed),
            num_samples=oqparam.number_of_logic_tree_samples)
    else:
        smlt = logictree.FakeSmlt(oqparam.inputs['source_model'],
                                  int(oqparam.random_seed),
                                  oqparam.number_of_logic_tree_samples)
    return smlt


def getid(src):
    try:
        return src.source_id
    except AttributeError:
        return src['id']


def get_composite_source_model(oqparam, monitor=None, in_memory=True,
                               srcfilter=SourceFilter(None, {})):
    """
    Parse the XML and build a complete composite source model in memory.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param monitor:
         a `openquake.baselib.performance.Monitor` instance
    :param in_memory:
        if False, just parse the XML without instantiating the sources
    :param srcfilter:
        if not None, use it to prefilter the sources
    """
    ucerf = oqparam.calculation_mode.startswith('ucerf')
    source_model_lt = get_source_model_lt(oqparam, validate=not ucerf)
    trts = source_model_lt.tectonic_region_types
    trts_lower = {trt.lower() for trt in trts}
    reqv = oqparam.inputs.get('reqv', {})
    for trt in reqv:  # these are lowercase because they come from the job.ini
        if trt not in trts_lower:
            raise ValueError('Unknown TRT=%s in %s [reqv]' %
                             (trt, oqparam.inputs['job_ini']))
    gsim_lt = get_gsim_lt(oqparam, trts or ['*'])
    p = source_model_lt.num_paths * gsim_lt.get_num_paths()
    if oqparam.number_of_logic_tree_samples:
        logging.info('Considering {:,d} logic tree paths out of {:,d}'.format(
            oqparam.number_of_logic_tree_samples, p))
    else:  # full enumeration
        if (oqparam.is_event_based() and
            (oqparam.ground_motion_fields or oqparam.hazard_curves_from_gmfs)
                and p > oqparam.max_potential_paths):
            raise ValueError(
                'There are too many potential logic tree paths (%d):'
                'use sampling instead of full enumeration or reduce the '
                'source model with oq reduce_sm' % p)
        logging.info('Potential number of logic tree paths = {:,d}'.format(p))

    if source_model_lt.on_each_source:
        logging.info('There is a logic tree on each source')
    if monitor is None:
        monitor = performance.Monitor()
    smodels = []
    factory = SourceModelFactory(oqparam, gsim_lt, source_model_lt, monitor,
                                 in_memory, srcfilter)
    for source_model in factory.get_models():
        for src_group in source_model.src_groups:
            src_group.sources = sorted(src_group, key=getid)
            for src in src_group:
                # there are two cases depending on the flag in_memory:
                # 1) src is a hazardlib source and has a src_group_id
                #    attribute; in that case the source has to be numbered
                # 2) src is a Node object, then nothing must be done
                if isinstance(src, Node):
                    continue
        smodels.append(source_model)
    csm = source.CompositeSourceModel(gsim_lt, source_model_lt, smodels)
    for sm in csm.source_models:
        counter = collections.Counter()
        for sg in sm.src_groups:
            for srcid in map(getid, sg):
                counter[srcid] += 1
        dupl = [srcid for srcid in counter if counter[srcid] > 1]
        if dupl:
            raise nrml.DuplicatedID('Found duplicated source IDs in %s: %s'
                                    % (sm, dupl))
    if not in_memory:
        return csm

    if oqparam.is_event_based():
        # initialize the rupture serial numbers before splitting/filtering; in
        # this way the serials are independent from the site collection
        csm.init_serials(oqparam.ses_seed)

    if oqparam.disagg_by_src:
        csm = csm.grp_by_src()  # one group per source

    csm.info.gsim_lt.check_imts(oqparam.imtls)
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
    riskdict = get_risk_models(oqparam)
    oqparam.set_risk_imtls(riskdict)
    crm = riskinput.CompositeRiskModel(oqparam, riskdict)
    return crm


def get_exposure(oqparam):
    """
    Read the full exposure in memory and build a list of
    :class:`openquake.risklib.asset.Asset` instances.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an :class:`Exposure` instance or a compatible AssetCollection
    """
    exposure = asset.Exposure.read(
        oqparam.inputs['exposure'], oqparam.calculation_mode,
        oqparam.region, oqparam.ignore_missing_costs,
        by_country='country' in oqparam.aggregate_by)
    exposure.mesh, exposure.assets_by_site = exposure.get_mesh_assets_by_site()
    return exposure


def get_sitecol_assetcol(oqparam, haz_sitecol=None, cost_types=()):
    """
    :param oqparam: calculation parameters
    :param haz_sitecol: the hazard site collection
    :param cost_types: the expected cost types
    :returns: (site collection, asset collection, discarded)
    """
    global exposure
    asset_hazard_distance = oqparam.asset_hazard_distance['default']
    if exposure is None:
        # haz_sitecol not extracted from the exposure
        exposure = get_exposure(oqparam)
    if haz_sitecol is None:
        haz_sitecol = get_site_collection(oqparam)
    if oqparam.region_grid_spacing:
        haz_distance = oqparam.region_grid_spacing * 1.414
        if haz_distance != asset_hazard_distance:
            logging.info('Using asset_hazard_distance=%d km instead of %d km',
                         haz_distance, asset_hazard_distance)
    else:
        haz_distance = asset_hazard_distance

    if haz_sitecol.mesh != exposure.mesh:
        # associate the assets to the hazard sites
        sitecol, assets_by, discarded = geo.utils.assoc(
            exposure.assets_by_site, haz_sitecol,
            haz_distance, 'filter', exposure.asset_refs)
        assets_by_site = [[] for _ in sitecol.complete.sids]
        num_assets = 0
        for sid, assets in zip(sitecol.sids, assets_by):
            assets_by_site[sid] = assets
            num_assets += len(assets)
        logging.info(
            'Associated %d assets to %d sites', num_assets, len(sitecol))
    else:
        # asset sites and hazard sites are the same
        sitecol = haz_sitecol
        assets_by_site = exposure.assets_by_site
        discarded = []
        logging.info('Read %d sites and %d assets from the exposure',
                     len(sitecol), sum(len(a) for a in assets_by_site))
    assetcol = asset.AssetCollection(
        exposure, assets_by_site, oqparam.time_event)
    if assetcol.occupancy_periods:
        missing = set(cost_types) - set(exposure.cost_types['name']) - set(
            ['occupants'])
    else:
        missing = set(cost_types) - set(exposure.cost_types['name'])
    if missing and not oqparam.calculation_mode.endswith('damage'):
        raise InvalidFile('The exposure %s is missing %s' %
                          (oqparam.inputs['exposure'], missing))
    if (not oqparam.hazard_calculation_id and 'gmfs' not in oqparam.inputs
            and 'hazard_curves' not in oqparam.inputs
            and sitecol is not sitecol.complete):
        assetcol.reduce_also(sitecol)
    return sitecol, assetcol, discarded


def levels_from(header):
    levels = []
    for field in header:
        if field.startswith('poe-'):
            levels.append(float(field[4:]))
    return levels


def get_pmap_from_csv(oqparam, fnames):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param fnames:
        a space-separated list of .csv relative filenames
    :returns:
        the site mesh and the hazard curves read by the .csv files
    """
    read = functools.partial(hdf5.read_csv, dtypedict={None: float})
    imtls = {}
    dic = {}
    for wrapper in map(read, fnames):
        dic[wrapper.imt] = wrapper.array
        imtls[wrapper.imt] = levels_from(wrapper.dtype.names)
    oqparam.hazard_imtls = imtls
    oqparam.set_risk_imtls(get_risk_models(oqparam))
    array = wrapper.array
    mesh = geo.Mesh(array['lon'], array['lat'])
    num_levels = sum(len(imls) for imls in oqparam.imtls.values())
    data = numpy.zeros((len(mesh), num_levels))
    level = 0
    for im in oqparam.imtls:
        arr = dic[im]
        for poe in arr.dtype.names[3:]:
            data[:, level] = arr[poe]
            level += 1
        for field in ('lon', 'lat', 'depth'):  # sanity check
            numpy.testing.assert_equal(arr[field], array[field])
    return mesh, ProbabilityMap.from_array(data, range(len(mesh)))


# used in utils/reduce_sm and utils/extract_source
def reduce_source_model(smlt_file, source_ids, remove=True):
    """
    Extract sources from the composite source model
    """
    found = 0
    to_remove = set()
    for paths in logictree.collect_info(smlt_file).smpaths.values():
        for path in paths:
            logging.info('Reading %s', path)
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
                    weights = src_group.get('srcs_weights')
                    if weights:
                        assert len(weights) == len(src_group.nodes)
                    else:
                        weights = [1] * len(src_group.nodes)
                    src_group['srcs_weights'] = reduced_weigths = []
                    for src_node, weight in zip(src_group, weights):
                        if src_node['id'] in source_ids:
                            found += 1
                            sg.nodes.append(src_node)
                            reduced_weigths.append(weight)
                    if sg.nodes:
                        model.nodes.append(sg)
            shutil.copy(path, path + '.bak')
            if model:
                with open(path, 'wb') as f:
                    nrml.write([model], f, xmlns=root['xmlns'])
            elif remove:  # remove the files completely reduced
                to_remove.add(path)
    if found:
        for path in to_remove:
            os.remove(path)


def get_input_files(oqparam, hazard=False):
    """
    :param oqparam: an OqParam instance
    :param hazard: if True, consider only the hazard files
    :returns: input path names in a specific order
    """
    fnames = []  # files entering in the checksum
    for key in oqparam.inputs:
        fname = oqparam.inputs[key]
        if hazard and key not in ('site_model', 'source_model_logic_tree',
                                  'gsim_logic_tree', 'source'):
            continue
        # collect .hdf5 tables for the GSIMs, if any
        elif key == 'gsim_logic_tree':
            gsim_lt = get_gsim_lt(oqparam)
            for gsims in gsim_lt.values.values():
                for gsim in gsims:
                    table = getattr(gsim, 'GMPE_TABLE', None)
                    if table:
                        fnames.append(table)
            fnames.append(fname)
        elif key == 'source_model':  # UCERF
            f = oqparam.inputs['source_model']
            fnames.append(f)
            fname = nrml.read(f).sourceModel.UCERFSource['filename']
            fnames.append(os.path.join(os.path.dirname(f), fname))
        elif key == 'exposure':  # fname is a list
            for exp in asset.Exposure.read_headers(fname):
                fnames.extend(exp.datafiles)
            fnames.extend(fname)
        elif isinstance(fname, dict):
            fnames.extend(fname.values())
        elif isinstance(fname, list):
            for f in fname:
                if f == oqparam.input_dir:
                    raise InvalidFile('%s there is an empty path in %s' %
                                      (oqparam.inputs['job_ini'], key))
            fnames.extend(fname)
        elif key == 'source_model_logic_tree':
            for smpaths in logictree.collect_info(fname).smpaths.values():
                fnames.extend(smpaths)
            fnames.append(fname)
        else:
            fnames.append(fname)
    return sorted(fnames)


def _checksum(fname, checksum):
    if not os.path.exists(fname):
        zpath = os.path.splitext(fname)[0] + '.zip'
        if not os.path.exists(zpath):
            raise OSError('No such file: %s or %s' % (fname, zpath))
        with open(zpath, 'rb') as f:
            data = f.read()
    else:
        with open(fname, 'rb') as f:
            data = f.read()
    return zlib.adler32(data, checksum)


def get_checksum32(oqparam, hazard=False):
    """
    Build an unsigned 32 bit integer from the input files of a calculation.

    :param oqparam: an OqParam instance
    :param hazard: if True, consider only the hazard files
    :returns: the checkume
    """
    # NB: using adler32 & 0xffffffff is the documented way to get a checksum
    # which is the same between Python 2 and Python 3
    checksum = 0
    for fname in get_input_files(oqparam, hazard):
        checksum = _checksum(fname, checksum)
    if hazard:
        hazard_params = []
        for key, val in vars(oqparam).items():
            if key in ('rupture_mesh_spacing', 'complex_fault_mesh_spacing',
                       'width_of_mfd_bin', 'area_source_discretization',
                       'random_seed', 'ses_seed', 'truncation_level',
                       'maximum_distance', 'investigation_time',
                       'number_of_logic_tree_samples', 'imtls',
                       'ses_per_logic_tree_path', 'minimum_magnitude',
                       'sites', 'pointsource_distance', 'filter_distance'):
                hazard_params.append('%s = %s' % (key, val))
        data = '\n'.join(hazard_params).encode('utf8')
        checksum = zlib.adler32(data, checksum) & 0xffffffff
    return checksum
