# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
import re
import ast
import csv
import copy
import json
import zlib
import pickle
import shutil
import zipfile
import logging
import tempfile
import functools
import configparser
import collections

import numpy
import pandas
import requests

from openquake.baselib import hdf5, parallel
from openquake.baselib.general import (
    random_filter, countby, group_array, get_duplicates, gettemp)
from openquake.baselib.python3compat import zip
from openquake.baselib.node import Node
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.gmf import CorrelationButNoInterIntraStdDevs
from openquake.hazardlib import (
    source, geo, site, imt, valid, sourceconverter, nrml, InvalidFile, pmf)
from openquake.hazardlib.source import rupture
from openquake.hazardlib.calc.stochastic import rupture_dt
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.utils import BBoxError, cross_idl
from openquake.risklib import asset, riskmodels
from openquake.risklib.riskmodels import get_risk_functions
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib.source_reader import get_csm
from openquake.commonlib import logictree

F32 = numpy.float32
F64 = numpy.float64
U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
Site = collections.namedtuple('Site', 'sid lon lat')
gsim_lt_cache = {}  # fname, trt1, ..., trtN -> GsimLogicTree instance
smlt_cache = {}  # fname, seed, samples, meth -> SourceModelLogicTree instance

source_info_dt = numpy.dtype([
    ('source_id', hdf5.vstr),          # 0
    ('grp_id', numpy.uint16),          # 1
    ('code', (numpy.string_, 1)),      # 2
    ('calc_time', numpy.float32),      # 3
    ('num_sites', numpy.uint32),       # 4
    ('eff_ruptures', numpy.uint32),    # 5
    ('trti', numpy.uint8),             # 6
    ('task_no', numpy.uint16),         # 7
])


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


def extract_from_zip(path, ext='.ini'):
    """
    Given a zip archive and a function to detect the presence of a given
    filename, unzip the archive into a temporary directory and return the
    full path of the file. Raise an IOError if the file cannot be found
    within the archive.

    :param path: pathname of the archive
    :param ext: file extension to search for
    """
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(path) as archive:
        archive.extractall(temp_dir)
    return [f for f in collect_files(temp_dir)
            if os.path.basename(f).endswith(ext)]


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
                params['inputs'][input_type] = dict(zip(dic, fnames))
                params[input_type] = ' '.join(dic)
            elif value:
                input_type, [fname] = normalize(key, [value], base_path)
                params['inputs'][input_type] = fname
        elif isinstance(value, str) and value.endswith('.hdf5'):
            logging.warning('The [reqv] syntax has been deprecated, see '
                            'https://github.com/gem/oq-engine/blob/master/doc/'
                            'adv-manual/equivalent-distance-app for the new '
                            'syntax')
            fname = os.path.normpath(os.path.join(base_path, value))
            try:
                reqv = params['inputs']['reqv']
            except KeyError:
                params['inputs']['reqv'] = {key: fname}
            else:
                reqv.update({key: fname})
        else:
            params[key] = value

    if 'reqv' in params['inputs']:
        params['pointsource_distance'] = '0'


# NB: this function must NOT log, since it is called when the logging
# is not configured yet
def get_params(job_ini, kw={}):
    """
    Parse a .ini file or a .zip archive

    :param job_ini:
        Configuration file | zip archive | URL
    :param kw:
        Optionally override some parameters
    :returns:
        A dictionary of parameters
    """
    if job_ini.startswith(('http://', 'https://')):
        resp = requests.get(job_ini)
        job_ini = gettemp(suffix='.zip')
        with open(job_ini, 'wb') as f:
            f.write(resp.content)
    # directory containing the config files we're parsing
    job_ini = os.path.abspath(job_ini)
    base_path = os.path.dirname(job_ini)
    params = dict(base_path=base_path, inputs={'job_ini': job_ini})
    input_zip = None
    if job_ini.endswith('.zip'):
        input_zip = job_ini
        job_inis = extract_from_zip(job_ini)
        if not job_inis:
            raise NameError('Could not find job.ini inside %s' % input_zip)
        job_ini = job_inis[0]

    if not os.path.exists(job_ini):
        raise IOError('File not found: %s' % job_ini)

    base_path = os.path.dirname(job_ini)
    params = dict(base_path=base_path, inputs={'job_ini': job_ini})
    cp = configparser.ConfigParser()
    cp.read([job_ini], encoding='utf8')
    for sect in cp.sections():
        _update(params, cp.items(sect), base_path)

    if input_zip:
        params['inputs']['input_zip'] = os.path.abspath(input_zip)
    _update(params, kw.items(), base_path)  # override on demand

    return params


def get_oqparam(job_ini, pkg=None, calculators=None, kw={}, validate=1):
    """
    Parse a dictionary of parameters from an INI-style config file.

    :param job_ini:
        Path to configuration file/archive or dictionary of parameters
    :param pkg:
        Python package where to find the configuration file (optional)
    :param calculators:
        Sequence of calculator names (optional) used to restrict the
        valid choices for `calculation_mode`
    :param kw:
        Dictionary of strings to override the job parameters
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
        job_ini = get_params(os.path.join(basedir, job_ini), kw)
    re = os.environ.get('OQ_REDUCE')  # debugging facility
    if re:
        # reduce the imtls to the first imt
        # reduce the logic tree to one random realization
        # reduce the sites by a factor of `re`
        # reduce the ses by a factor of `re`
        # set save_disk_space = true
        os.environ['OQ_SAMPLE_SITES'] = re
        job_ini['number_of_logic_tree_samples'] = '1'
        ses = job_ini.get('ses_per_logic_tree_path')
        if ses:
            ses = str(int(numpy.ceil(int(ses) * float(re))))
            job_ini['ses_per_logic_tree_path'] = ses
        imtls = job_ini.get('intensity_measure_types_and_levels')
        if imtls:
            imtls = valid.intensity_measure_types_and_levels(imtls)
            imt = next(iter(imtls))
            job_ini['intensity_measure_types_and_levels'] = repr(
                {imt: imtls[imt]})
        job_ini['save_disk_space'] = 'true'
    oqparam = OqParam(**job_ini)
    if validate and '_job_id' not in job_ini:
        oqparam.check_source_model()
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


def get_mesh(oqparam, h5=None):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, the region, the site model, the exposure in this order.

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
        # NB: Notice the sort=False below
        # Calculations starting from ground motion fields input by the user
        # require at least two input files related to the gmf data:
        #   1. A sites.csv file, listing {site_id, lon, lat} tuples
        #   2. A gmfs.csv file, listing {event_id, site_id, gmv[IMT1],
        #      gmv[IMT2], ...} tuples
        # The site coordinates defined in the sites file do not need to be in
        # sorted order.
        # We must only ensure uniqueness of the provided site_ids and
        # coordinates.
        # When creating the site mesh from the site coordinates read from
        # the csv file, the sort=False flag maintains the user-specified
        # site_ids instead of reassigning them after sorting.
        return geo.Mesh.from_coords(c, sort=False)
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
        elif exposure:
            # in case of implicit grid the exposure takes precedence over
            # the site model
            poly = exposure.mesh.get_convex_hull()
        elif 'site_model' in oqparam.inputs:
            # this happens in event_based/case_19, where there is an implicit
            # grid over the site model
            sm = get_site_model(oqparam)  # do not store in h5!
            poly = geo.Mesh(sm['lon'], sm['lat']).get_convex_hull()
        else:
            raise InvalidFile('There is a grid spacing but not a region, '
                              'nor a site model, nor an exposure in %s' %
                              oqparam.inputs['job_ini'])
        try:
            logging.info('Inferring the hazard grid')
            mesh = poly.dilate(oqparam.region_grid_spacing).discretize(
                oqparam.region_grid_spacing)
            return geo.Mesh.from_coords(zip(mesh.lons, mesh.lats))
        except Exception:
            raise ValueError(
                'Could not discretize region with grid spacing '
                '%(region_grid_spacing)s' % vars(oqparam))
    # the site model has the precedence over the exposure, see the
    # discussion in https://github.com/gem/oq-engine/pull/5217
    elif 'site_model' in oqparam.inputs:
        logging.info('Extracting the hazard sites from the site model')
        sm = get_site_model(oqparam)
        if h5:
            h5['site_model'] = sm
        mesh = geo.Mesh(sm['lon'], sm['lat'])
        return mesh
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
    if 'amplification' in oqparam.inputs:
        req_site_params.add('ampcode')
    arrays = []
    for fname in oqparam.inputs['site_model']:
        if isinstance(fname, str) and fname.endswith('.csv'):
            sm = hdf5.read_csv(fname, site.site_param_dt).array
            sm['lon'] = numpy.round(sm['lon'], 5)
            sm['lat'] = numpy.round(sm['lat'], 5)
            dupl = get_duplicates(sm, 'lon', 'lat')
            if dupl:
                raise InvalidFile(
                    'Found duplicate sites %s in %s' % (dupl, fname))
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
        if 'ampcode' in missing:  # use a default of b''
            missing -= {'ampcode'}
            for param in params:
                param['ampcode'] = b''
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
        dupl = "\n".join(
            '%s %s' % loc for loc, n in countby(sm, 'lon', 'lat').items()
            if n > 1)
        if dupl:
            raise InvalidFile('There are duplicated sites in %s:\n%s' %
                              (fname, dupl))
        arrays.append(sm)
    return numpy.concatenate(arrays)


def get_site_collection(oqparam, h5=None):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if h5 and 'sitecol' in h5:
        return h5['sitecol']
    mesh = get_mesh(oqparam, h5)
    if mesh is None and oqparam.ground_motion_fields:
        raise InvalidFile('You are missing sites.csv or site_model.csv in %s'
                          % oqparam.inputs['job_ini'])
    elif mesh is None:
        # a None sitecol is okay when computing the ruptures only
        return
    else:  # use the default site params
        req_site_params = get_gsim_lt(oqparam).req_site_params
        if 'amplification' in oqparam.inputs:
            req_site_params.add('ampcode')
        if h5 and 'site_model' in h5:  # comes from a site_model.csv
            sm = h5['site_model'][:]
        else:
            sm = oqparam
        sitecol = site.SiteCollection.from_points(
            mesh.lons, mesh.lats, mesh.depths, sm, req_site_params)
    ss = os.environ.get('OQ_SAMPLE_SITES')
    if ss:
        # debugging tip to reduce the size of a calculation
        # OQ_SAMPLE_SITES=.1 oq engine --run job.ini
        # will run a computation with 10 times less sites
        sitecol.array = numpy.array(random_filter(sitecol.array, float(ss)))
        sitecol.make_complete()
    if h5:
        h5['sitecol'] = sitecol
    return sitecol


def get_gsim_lt(oqparam, trts=('*',)):
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
    key = (gsim_file,) + tuple(sorted(trts))
    if key in gsim_lt_cache:
        return gsim_lt_cache[key]
    gsim_lt = logictree.GsimLogicTree(gsim_file, trts)
    gmfcorr = oqparam.correl_model
    for trt, gsims in gsim_lt.values.items():
        for gsim in gsims:
            if gmfcorr and (gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES ==
                            {StdDev.TOTAL}):
                raise CorrelationButNoInterIntraStdDevs(gmfcorr, gsim)
    imt_dep_w = any(len(branch.weight.dic) > 1 for branch in gsim_lt.branches)
    if oqparam.number_of_logic_tree_samples and imt_dep_w:
        logging.error('IMT-dependent weights in the logic tree cannot work '
                      'with sampling, because they would produce different '
                      'GMPE paths for each IMT that cannot be combined, so '
                      'I am using the default weights')
        for branch in gsim_lt.branches:
            for k, w in sorted(branch.weight.dic.items()):
                if k != 'weight':
                    logging.warning(
                        'Using weight=%s instead of %s for %s %s',
                        branch.weight.dic['weight'], w, branch.gsim, k)
                    del branch.weight.dic[k]
    if oqparam.collapse_gsim_logic_tree:
        logging.info('Collapsing the gsim logic tree')
        gsim_lt = gsim_lt.collapse(oqparam.collapse_gsim_logic_tree)
    gsim_lt_cache[key] = gsim_lt
    return gsim_lt


def get_ruptures(fname_csv):
    """
    Read ruptures in CSV format and return an ArrayWrapper
    """
    if not rupture.BaseRupture._code:
        rupture.BaseRupture.init()  # initialize rupture codes
    code = rupture.BaseRupture.str2code
    aw = hdf5.read_csv(fname_csv, rupture.rupture_dt)
    trts = aw.trts
    rups = []
    geoms = []
    n_occ = 1
    for u, row in enumerate(aw.array):
        hypo = row['lon'], row['lat'], row['dep']
        dic = json.loads(row['extra'])
        mesh = F32(json.loads(row['mesh']))
        s1, s2 = mesh.shape[1:]
        rec = numpy.zeros(1, rupture_dt)[0]
        rec['seed'] = row['seed']
        rec['minlon'] = minlon = mesh[0].min()
        rec['minlat'] = minlat = mesh[1].min()
        rec['maxlon'] = maxlon = mesh[0].max()
        rec['maxlat'] = maxlat = mesh[1].max()
        rec['mag'] = row['mag']
        rec['hypo'] = hypo
        rate = dic.get('occurrence_rate', numpy.nan)
        tup = (u, row['seed'], 'no-source', trts.index(row['trt']),
               code[row['kind']], n_occ, row['mag'], row['rake'], rate,
               minlon, minlat, maxlon, maxlat, hypo, u, 0, 0)
        rups.append(tup)
        points = mesh.flatten()  # lons + lats + deps
        # FIXME: extend to MultiSurfaces
        geoms.append(numpy.concatenate([[1], [s1, s2], points]))
    if not rups:
        return ()
    dic = dict(geom=numpy.array(geoms, object))
    # NB: PMFs for nonparametric ruptures are missing
    return hdf5.ArrayWrapper(numpy.array(rups, rupture_dt), dic)


def get_rupture(oqparam):
    """
    Read the `rupture_model` file and by filter the site collection

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an hazardlib rupture
    """
    rup_model = oqparam.inputs['rupture_model']
    if rup_model.endswith('.csv'):
        return rupture.from_array(hdf5.read_csv(rup_model))
    if rup_model.endswith('.xml'):
        [rup_node] = nrml.read(rup_model)
        conv = sourceconverter.RuptureConverter(
            oqparam.rupture_mesh_spacing, oqparam.complex_fault_mesh_spacing)
        rup = conv.convert_node(rup_node)
    else:
        raise ValueError('Unrecognized ruptures model %s' % rup_model)
    rup.tectonic_region_type = '*'  # there is not TRT for scenario ruptures
    rup.rup_id = oqparam.ses_seed
    return rup


def get_source_model_lt(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        a :class:`openquake.commonlib.logictree.SourceModelLogicTree`
        instance
    """
    fname = oqparam.inputs['source_model_logic_tree']
    args = (fname, oqparam.random_seed, oqparam.number_of_logic_tree_samples,
            oqparam.sampling_method)
    try:
        smlt = smlt_cache[args]
    except KeyError:
        smlt = smlt_cache[args] = logictree.SourceModelLogicTree(*args)
    if oqparam.discard_trts:
        trts = set(trt.strip() for trt in oqparam.discard_trts.split(','))
        # smlt.tectonic_region_types comes from applyToTectonicRegionType
        smlt.tectonic_region_types = smlt.tectonic_region_types - trts
    if 'ucerf' in oqparam.calculation_mode:
        smlt.tectonic_region_types = {'Active Shallow Crust'}
    return smlt


def get_full_lt(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        a :class:`openquake.commonlib.logictree.FullLogicTree`
        instance
    """
    source_model_lt = get_source_model_lt(oqparam)
    trts = source_model_lt.tectonic_region_types
    trts_lower = {trt.lower() for trt in trts}
    reqv = oqparam.inputs.get('reqv', {})
    for trt in reqv:
        if trt in oqparam.discard_trts:
            continue
        elif trt.lower() not in trts_lower:
            raise ValueError('Unknown TRT=%s in %s [reqv]' %
                             (trt, oqparam.inputs['job_ini']))
    gsim_lt = get_gsim_lt(oqparam, trts or ['*'])
    p = source_model_lt.num_paths * gsim_lt.get_num_paths()
    if oqparam.number_of_logic_tree_samples:
        logging.info('Considering {:_d} logic tree paths out of {:_d}'.format(
            oqparam.number_of_logic_tree_samples, p))
    else:  # full enumeration
        if (oqparam.is_event_based() and
            (oqparam.ground_motion_fields or oqparam.hazard_curves_from_gmfs)
                and p > oqparam.max_potential_paths):
            raise ValueError(
                'There are too many potential logic tree paths (%d):'
                'use sampling instead of full enumeration or reduce the '
                'source model with oq reduce_sm' % p)
        logging.info('Total number of logic tree paths = {:_d}'.format(p))
    if source_model_lt.on_each_source:
        logging.info('There is a logic tree on each source')
    full_lt = logictree.FullLogicTree(source_model_lt, gsim_lt)
    return full_lt


def save_source_info(csm, h5):
    data = {}  # src_id -> row
    wkts = []
    lens = []
    for sg in csm.src_groups:
        for src in sg:
            lens.append(len(src.et_ids))
            row = [src.source_id, src.grp_id, src.code,
                   0, 0, 0, csm.full_lt.trti[src.tectonic_region_type], 0]
            wkts.append(src._wkt)
            data[src.id] = row
    logging.info('There are %d groups and %d sources with len(et_ids)=%.2f',
                 len(csm.src_groups), sum(len(sg) for sg in csm.src_groups),
                 numpy.mean(lens))
    csm.source_info = data  # src_id -> row
    if h5:
        attrs = dict(atomic=any(grp.atomic for grp in csm.src_groups))
        # avoid hdf5 damned bug by creating source_info in advance
        hdf5.create(h5, 'source_info', source_info_dt, attrs=attrs)
        h5['source_wkt'] = numpy.array(wkts, hdf5.vstr)
        h5['et_ids'] = csm.get_et_ids()


def _check_csm(csm, oqparam, h5):
    # checks
    csm.gsim_lt.check_imts(oqparam.imtls)

    srcs = csm.get_sources()
    if not srcs:
        raise RuntimeError('All sources were discarded!?')

    if os.environ.get('OQ_CHECK_INPUT'):
        source.check_complex_faults(srcs)

    # build a smart SourceFilter
    sitecol = get_site_collection(oqparam, h5)
    srcfilter = SourceFilter(sitecol, oqparam.maximum_distance)

    if sitecol:  # missing in test_case_1_ruptures
        logging.info('Checking the sources bounding box')
        lons = []
        lats = []
        for src in srcs:
            try:
                box = srcfilter.get_enlarged_box(src)
            except BBoxError as exc:
                logging.error(exc)
                continue
            lons.append(box[0])
            lats.append(box[1])
            lons.append(box[2])
            lats.append(box[3])
        if cross_idl(*(list(sitecol.lons) + lons)):
            lons = numpy.array(lons) % 360
        else:
            lons = numpy.array(lons)
        bbox = (lons.min(), min(lats), lons.max(), max(lats))
        if bbox[2] - bbox[0] > 180:
            raise BBoxError(
                'The bounding box of the sources is larger than half '
                'the globe: %d degrees' % (bbox[2] - bbox[0]))
        sids = sitecol.within_bbox(bbox)
        if len(sids) == 0:
            raise RuntimeError('All sources were discarded!?')

    csm.sitecol = sitecol


def get_composite_source_model(oqparam, h5=None):
    """
    Parse the XML and build a complete composite source model in memory.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param h5:
         an open hdf5.File where to store the source info
    """
    # first read the logic tree
    full_lt = get_full_lt(oqparam)

    # then read the composite source model from the cache if possible
    if oqparam.cachedir and not os.path.exists(oqparam.cachedir):
        os.makedirs(oqparam.cachedir)
    if oqparam.cachedir and not oqparam.is_ucerf():
        # for UCERF pickling the csm is slower
        checksum = get_checksum32(oqparam, h5)
        fname = os.path.join(oqparam.cachedir, 'csm_%s.pik' % checksum)
        if os.path.exists(fname):
            logging.info('Reading %s', fname)
            with open(fname, 'rb') as f:
                csm = pickle.load(f)
                csm.full_lt = full_lt
            if h5:
                # avoid errors with --reuse_hazard
                h5['et_ids'] = csm.get_et_ids()
                hdf5.create(h5, 'source_info', source_info_dt)
            _check_csm(csm, oqparam, h5)
            return csm

    # read and process the composite source model from the input files
    csm = get_csm(oqparam, full_lt,  h5)
    save_source_info(csm, h5)
    if oqparam.cachedir and not oqparam.is_ucerf():
        logging.info('Saving %s', fname)
        with open(fname, 'wb') as f:
            pickle.dump(csm, f)

    _check_csm(csm, oqparam, h5)
    return csm


def get_imts(oqparam):
    """
    Return a sorted list of IMTs as hazardlib objects
    """
    return list(map(imt.from_string, sorted(oqparam.imtls)))


def get_amplification(oqparam):
    """
    :returns: a DataFrame (ampcode, level, PGA, SA() ...)
    """
    fname = oqparam.inputs['amplification']
    df = hdf5.read_csv(fname, {'ampcode': site.ampcode_dt, None: F64},
                       index='ampcode')
    df.fname = fname
    return df


def _cons_coeffs(records, limit_states):
    dtlist = [(lt, F32) for lt in records['loss_type']]
    coeffs = numpy.zeros(len(limit_states), dtlist)
    for rec in records:
        coeffs[rec['loss_type']] = [rec[ds] for ds in limit_states]
    return coeffs


def get_crmodel(oqparam):
    """
    Return a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance

   :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    risklist = get_risk_functions(oqparam)
    consdict = {}
    if 'consequence' in oqparam.inputs:
        # build consdict of the form cname_by_tagname -> tag -> array
        for by, fname in oqparam.inputs['consequence'].items():
            dtypedict = {
                by: str, 'cname': str, 'loss_type': str, None: float}
            dic = group_array(
                hdf5.read_csv(fname, dtypedict).array, 'cname')
            for cname, group in dic.items():
                bytag = {tag: _cons_coeffs(grp, risklist.limit_states)
                         for tag, grp in group_array(group, by).items()}
                consdict['%s_by_%s' % (cname, by)] = bytag
    crm = riskmodels.CompositeRiskModel(oqparam, risklist, consdict)
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
    if oqparam.cachedir and not os.path.exists(oqparam.cachedir):
        os.makedirs(oqparam.cachedir)
    checksum = _checksum(oqparam.inputs['exposure'])
    fname = os.path.join(oqparam.cachedir, 'exp_%s.pik' % checksum)
    if os.path.exists(fname):
        logging.info('Reading %s', fname)
        with open(fname, 'rb') as f:
            return pickle.load(f)
    exposure = asset.Exposure.read(
        oqparam.inputs['exposure'], oqparam.calculation_mode,
        oqparam.region, oqparam.ignore_missing_costs,
        by_country='country' in oqparam.aggregate_by)
    exposure.mesh, exposure.assets_by_site = exposure.get_mesh_assets_by_site()
    if oqparam.cachedir:
        logging.info('Saving %s', fname)
        with open(fname, 'wb') as f:
            pickle.dump(exposure, f)
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
            exposure.assets_by_site, haz_sitecol, haz_distance, 'filter')
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
        exposure, assets_by_site, oqparam.time_event, oqparam.aggregate_by)
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
        # for predefined hazard you cannot reduce the site collection; instead
        # you can in other cases, typically with a grid which is mostly empty
        # (i.e. there are many hazard sites with no assets)
        assetcol.reduce_also(sitecol)
    return sitecol, assetcol, discarded


def levels_from(header):
    levels = []
    for field in header:
        if field.startswith('poe-'):
            levels.append(float(field[4:]))
    return levels


def taxonomy_mapping(oqparam, taxonomies):
    """
    :param oqparam: OqParam instance
    :param taxonomies: array of strings tagcol.taxonomy
    :returns: a dictionary loss_type -> [[(taxonomy, weight), ...], ...]
    """
    if 'taxonomy_mapping' not in oqparam.inputs:  # trivial mapping
        lst = [[(taxo, 1)] for taxo in taxonomies]
        return {lt: lst for lt in oqparam.loss_names}
    dic = oqparam.inputs['taxonomy_mapping']
    if isinstance(dic, str):  # filename
        dic = {lt: dic for lt in oqparam.loss_names}
    return {lt: _taxonomy_mapping(dic[lt], taxonomies)
            for lt in oqparam.loss_names}


def _taxonomy_mapping(filename, taxonomies):
    tmap_df = pandas.read_csv(filename)
    if 'weight' not in tmap_df:
        tmap_df['weight'] = 1.

    assert set(tmap_df) == {'taxonomy', 'conversion', 'weight'}
    dic = dict(list(tmap_df.groupby('taxonomy')))
    taxonomies = taxonomies[1:]  # strip '?'
    missing = set(taxonomies) - set(dic)
    if missing:
        raise InvalidFile('The taxonomies %s are in the exposure but not in '
                          'the taxonomy mapping %s' % (missing, filename))
    lst = [[("?", 1)]]
    for taxo in taxonomies:
        recs = dic[taxo]
        if abs(recs['weight'].sum() - 1.) > pmf.PRECISION:
            raise InvalidFile('%s: the weights do not sum up to 1 for %s' %
                              (filename, taxo))
        lst.append([(rec['conversion'], rec['weight'])
                    for r, rec in recs.iterrows()])
    return lst


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
    oqparam.set_risk_imts(get_risk_functions(oqparam))
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


tag2code = {'ar': b'A',
            'mu': b'M',
            'po': b'P',
            'si': b'S',
            'co': b'C',
            'ch': b'X',
            'no': b'N'}


# tested in commands_test
def reduce_sm(paths, source_ids):
    """
    :param paths: list of source_model.xml files
    :param source_ids: dictionary src_id -> array[src_id, code]
    :returns: dictionary with keys good, total, model, path, xmlns

    NB: duplicate sources are not removed from the XML
    """
    if isinstance(source_ids, dict):  # in oq reduce_sm
        def ok(src_node):
            code = tag2code[re.search(r'\}(\w\w)', src_node.tag).group(1)]
            arr = source_ids.get(src_node['id'])
            if arr is None:
                return False
            return (arr['code'] == code).any()
    else:  # list of source IDs, in extract_source
        def ok(src_node):
            return src_node['id'] in source_ids
    for path in paths:
        good = 0
        total = 0
        logging.info('Reading %s', path)
        root = nrml.read(path)
        model = Node('sourceModel', root[0].attrib)
        origmodel = root[0]
        if root['xmlns'] == 'http://openquake.org/xmlns/nrml/0.4':
            for src_node in origmodel:
                total += 1
                if ok(src_node):
                    good += 1
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
                reduced_weigths = []
                for src_node, weight in zip(src_group, weights):
                    total += 1
                    if ok(src_node):
                        good += 1
                        sg.nodes.append(src_node)
                        reduced_weigths.append(weight)
                        src_node.attrib.pop('tectonicRegion', None)
                src_group['srcs_weights'] = reduced_weigths
                if sg.nodes:
                    model.nodes.append(sg)
        yield dict(good=good, total=total, model=model, path=path,
                   xmlns=root['xmlns'])


# used in oq reduce_sm and utils/extract_source
def reduce_source_model(smlt_file, source_ids, remove=True):
    """
    Extract sources from the composite source model.

    :param smlt_file: path to a source model logic tree file
    :param source_ids: dictionary source_id -> records (src_id, code)
    :param remove: if True, remove sm.xml files containing no sources
    :returns: the number of sources satisfying the filter vs the total
    """
    total = good = 0
    to_remove = set()
    paths = logictree.collect_info(smlt_file).smpaths
    for dic in parallel.Starmap.apply(reduce_sm, (paths, source_ids)):
        path = dic['path']
        model = dic['model']
        good += dic['good']
        total += dic['total']
        shutil.copy(path, path + '.bak')
        if model:
            with open(path, 'wb') as f:
                nrml.write([model], f, xmlns=dic['xmlns'])
        elif remove:  # remove the files completely reduced
            to_remove.add(path)
    if good:
        for path in to_remove:
            os.remove(path)
    parallel.Starmap.shutdown()
    return good, total


def get_input_files(oqparam, hazard=False):
    """
    :param oqparam: an OqParam instance
    :param hazard: if True, consider only the hazard files
    :returns: input path names in a specific order
    """
    fnames = set()  # files entering in the checksum
    for key in oqparam.inputs:
        fname = oqparam.inputs[key]
        if hazard and key not in ('source_model_logic_tree',
                                  'gsim_logic_tree', 'source'):
            continue
        # collect .hdf5 tables for the GSIMs, if any
        elif key == 'gsim_logic_tree':
            gsim_lt = get_gsim_lt(oqparam)
            for gsims in gsim_lt.values.values():
                for gsim in gsims:
                    for k, v in gsim.kwargs.items():
                        if k.endswith(('_file', '_table')):
                            fnames.add(v)
            fnames.add(fname)
        elif key == 'source_model':  # UCERF
            f = oqparam.inputs['source_model']
            fnames.add(f)
            fname = nrml.read(f).sourceModel.UCERFSource['filename']
            fnames.add(os.path.join(os.path.dirname(f), fname))
        elif key == 'exposure':  # fname is a list
            for exp in asset.Exposure.read_headers(fname):
                fnames.update(exp.datafiles)
            fnames.update(fname)
        elif isinstance(fname, dict):
            fnames.update(fname.values())
        elif isinstance(fname, list):
            for f in fname:
                if f == oqparam.input_dir:
                    raise InvalidFile('%s there is an empty path in %s' %
                                      (oqparam.inputs['job_ini'], key))
            fnames.update(fname)
        elif key == 'source_model_logic_tree':
            args = (fname, oqparam.random_seed,
                    oqparam.number_of_logic_tree_samples,
                    oqparam.sampling_method)
            try:
                smlt = smlt_cache[args]
            except KeyError:
                smlt = smlt_cache[args] = logictree.SourceModelLogicTree(*args)
            fnames.update(smlt.hdf5_files)
            fnames.update(smlt.info.smpaths)
            fnames.add(fname)
        else:
            fnames.add(fname)
    return sorted(fnames)


def _checksum(fnames, checksum=0):
    """
    :returns: the 32 bit checksum of a list of files
    """
    for fname in fnames:
        if not os.path.exists(fname):
            zpath = os.path.splitext(fname)[0] + '.zip'
            if not os.path.exists(zpath):
                raise OSError('No such file: %s or %s' % (fname, zpath))
            with open(zpath, 'rb') as f:
                data = f.read()
        else:
            with open(fname, 'rb') as f:
                data = f.read()
        checksum = zlib.adler32(data, checksum)
    return checksum


def get_checksum32(oqparam, h5=None):
    """
    Build an unsigned 32 bit integer from the hazard input files

    :param oqparam: an OqParam instance
    """
    checksum = _checksum(get_input_files(oqparam, hazard=True))
    hazard_params = []
    for key, val in sorted(vars(oqparam).items()):
        if key in ('rupture_mesh_spacing', 'complex_fault_mesh_spacing',
                   'width_of_mfd_bin', 'area_source_discretization',
                   'random_seed', 'number_of_logic_tree_samples',
                   'minimum_magnitude', 'source_id'):
            hazard_params.append('%s = %s' % (key, val))
    data = '\n'.join(hazard_params).encode('utf8')
    checksum = zlib.adler32(data, checksum)
    if h5:
        h5.attrs['checksum32'] = checksum
    return checksum
