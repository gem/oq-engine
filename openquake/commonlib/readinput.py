# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
import copy
import zlib
import shutil
import zipfile
import pathlib
import logging
import tempfile
import functools
import configparser
import collections
import itertools

import numpy
import pandas
import requests

from openquake.baselib import config, hdf5, parallel, InvalidFile
from openquake.baselib.general import (
    random_filter, countby, group_array, get_duplicates, gettemp)
from openquake.baselib.python3compat import zip, decode
from openquake.baselib.node import Node
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.calc.filters import SourceFilter, getdefault
from openquake.hazardlib.calc.gmf import CorrelationButNoInterIntraStdDevs
from openquake.hazardlib import (
    source, geo, site, imt, valid, sourceconverter, source_reader, nrml,
    pmf, logictree, gsim_lt, get_smlt)
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.utils import BBoxError, cross_idl
from openquake.risklib import asset, riskmodels, scientific, reinsurance
from openquake.risklib.riskmodels import get_risk_functions
from openquake.commonlib.oqvalidation import OqParam

F32 = numpy.float32
F64 = numpy.float64
U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
Site = collections.namedtuple('Site', 'sid lon lat')


class Global:
    """
    Global variables to be reset at the end of each calculation/test
    """
    pmap = None
    # set as side effect when the user reads hazard_curves from a file
    # the hazard curves format does not split the site locations from the data
    # (an unhappy legacy design choice that I fixed in the GMFs CSV format
    # only) thus this hack is necessary, otherwise we would have to parse the
    # file twice

    exposure = None
    # set as side effect when the user reads the site mesh; this hack is
    # necessary, otherwise we would have to parse the exposure twice

    gsim_lt_cache = {}  # fname, trt1, ..., trtN -> GsimLogicTree instance
    # populated when reading the gsim_logic_tree file; otherwise we would
    # have to parse the file multiple times

    @classmethod
    def reset(cls):
        cls.pmap = None
        cls.exposure = None
        cls.gsim_lt_cache.clear()


class DuplicatedPoint(Exception):
    """
    Raised when reading a CSV file with duplicated (lon, lat) pairs
    """


# used in extract_from_zip
def collect_files(dirpath, cond=lambda fullname: True):
    """
    Recursively collect the files contained inside dirpath.

    :param dirpath: path to a readable directory
    :param cond: condition on the path to collect the file
    """
    files = set()
    for fname in os.listdir(dirpath):
        fullname = os.path.join(dirpath, fname)
        if os.path.isdir(fullname):  # navigate inside
            files.update(collect_files(fullname))
        else:  # collect files
            if cond(fullname):
                files.add(fullname)
    return sorted(files)  # job_haz before job_risk


def extract_from_zip(path, ext='.ini', targetdir=None):
    """
    Given a zip archive and an extension (by default .ini), unzip the archive
    into the target directory and the files with the given extension.

    :param path: pathname of the archive
    :param ext: file extension to search for
    :returns: filenames
    """
    targetdir = targetdir or tempfile.mkdtemp(
        dir=config.directory.custom_tmp or None)
    with zipfile.ZipFile(path) as archive:
        archive.extractall(targetdir)
    return [f for f in collect_files(targetdir)
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


def normpath(fnames, base_path):
    vals = []
    for fname in fnames:
        val = os.path.normpath(os.path.join(base_path, fname))
        if not os.path.exists(val):
            raise OSError('No such file: %s' % val)
        vals.append(val)
    return vals


def normalize(key, fnames, base_path):
    input_type, _ext = key.rsplit('_', 1)
    filenames = []
    for val in fnames:
        if isinstance(val, list):
            val = normpath(val, base_path)
        elif os.path.isabs(val):
            raise ValueError('%s=%s is an absolute path' % (key, val))
        elif val.endswith('.zip'):
            zpath = os.path.normpath(os.path.join(base_path, val))
            if key == 'exposure_file':
                name = 'exposure.xml'
            elif key == 'source_model_logic_tree_file':
                name = 'ssmLT.xml'
            else:
                raise KeyError('Unknown key %s' % key)
            val = unzip_rename(zpath, name)
        elif val.startswith('${mosaic}/'):
            if 'mosaic' in config.directory:
                # support ${mosaic}/XXX/in/ssmLT.xml
                val = val.format(**config.directory)[1:]  # strip initial "$"
            else:
                continue
        else:
            val = os.path.normpath(os.path.join(base_path, val))
        if isinstance(val, str) and not os.path.exists(val):
            # tested in archive_err_2
            raise OSError('No such file: %s' % val)
        filenames.append(val)
    return input_type, filenames


def _update(params, items, base_path):
    for key, value in items:
        if key in ('hazard_curves_csv', 'hazard_curves_file',
                   'site_model_csv', 'site_model_file',
                   'exposure_csv', 'exposure_file'):
            input_type, fnames = normalize(key, value.split(), base_path)
            params['inputs'][input_type] = fnames
        elif key.endswith(('_file', '_csv', '_hdf5')):
            if value.startswith('{'):
                dic = ast.literal_eval(value)  # name -> relpath
                input_type, fnames = normalize(key, dic.values(), base_path)
                params['inputs'][input_type] = dict(zip(dic, fnames))
                params[input_type] = ' '.join(dic)
            elif value:
                input_type, fnames = normalize(key, [value], base_path)
                assert len(fnames) in (0, 1)
                for fname in fnames:
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


def _warn_about_duplicates(cp):
    params_sets = [
        set(cp.options(section)) for section in cp.sections()]
    for pair in itertools.combinations(params_sets, 2):
        params_intersection = sorted(set.intersection(*pair))
        if params_intersection:
            logging.warning(
                f'Parameter(s) {params_intersection} is(are) defined in'
                f' multiple sections')


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
    if isinstance(job_ini, pathlib.Path):
        job_ini = str(job_ini)
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
    cp.read([job_ini], encoding='utf-8-sig')  # skip BOM on Windows
    _warn_about_duplicates(cp)
    dic = {}
    for sect in cp.sections():
        dic.update(cp.items(sect))

    # put source_model_logic_tree_file on top of the items so that
    # oq-risk-tests alaska, which has a smmLT.zip file works, since
    # it is unzipped before and therefore the files can be read later
    if 'source_model_logic_tree_file' in dic:
        fname = dic.pop('source_model_logic_tree_file')
        items = [('source_model_logic_tree_file', fname)] + list(dic.items())
    else:
        items = list(dic.items())
    _update(params, items, base_path)

    if input_zip:
        params['inputs']['input_zip'] = os.path.abspath(input_zip)
    _update(params, kw.items(), base_path)  # override on demand

    return params


def get_oqparam(job_ini, pkg=None, kw={}, validate=True):
    """
    Parse a dictionary of parameters from an INI-style config file.

    :param job_ini:
        Path to configuration file/archive or
        dictionary of parameters with a key "calculation_mode"
    :param pkg:
        Python package where to find the configuration file (optional)
    :param kw:
        Dictionary of strings to override the job parameters
    :returns:
        An :class:`openquake.commonlib.oqvalidation.OqParam` instance
        containing the validated and casted parameters/values parsed from
        the job.ini file as well as a subdictionary 'inputs' containing
        absolute paths to all of the files referenced in the job.ini, keyed by
        the parameter name.
    """
    if not isinstance(job_ini, dict):
        basedir = os.path.dirname(pkg.__file__) if pkg else ''
        job_ini = get_params(os.path.join(basedir, job_ini), kw)
    re = os.environ.get('OQ_REDUCE')  # debugging facility
    if re:
        # reduce the imtls to the first imt
        # reduce the logic tree to one random realization
        # reduce the sites by a factor of `re`
        # reduce the ses by a factor of `re`
        os.environ['OQ_SAMPLE_SITES'] = re
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
    oqparam = OqParam(**job_ini)
    oqparam._input_files = get_input_files(oqparam)
    if validate:  # always true except from oqzip
        oqparam.validate()
    return oqparam


def get_csv_header(fname, sep=','):
    """
    :param fname: a CSV file
    :param sep: the separator (default comma)
    :returns: the first non-commented line of fname and the file object
    """
    f = open(fname, encoding='utf-8-sig')
    first = next(f).strip().split(sep)
    while first[0].startswith('#'):
        first = next(f).strip().split(sep)
    return first, f


def get_mesh(oqparam, h5=None):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, the region, the site model, the exposure in this order.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if 'exposure' in oqparam.inputs and Global.exposure is None:
        # read it only once
        Global.exposure = get_exposure(oqparam)
    if oqparam.sites:
        return geo.Mesh.from_coords(oqparam.sites)
    elif 'hazard_curves' in oqparam.inputs:
        fname = oqparam.inputs['hazard_curves']
        if isinstance(fname, list):  # for csv
            mesh, Global.pmap = get_pmap_from_csv(oqparam, fname)
        else:
            raise NotImplementedError('Reading from %s' % fname)
        return mesh
    elif oqparam.region_grid_spacing:
        if oqparam.region:
            poly = geo.Polygon.from_wkt(oqparam.region)
        elif Global.exposure:
            # in case of implicit grid the exposure takes precedence over
            # the site model
            poly = Global.exposure.mesh.get_convex_hull()
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
        return Global.exposure.mesh


def get_poor_site_model(fname):
    """
    :returns: a poor site model with only lon, lat fields
    """
    data = [ln.replace(',', ' ') for ln in open(fname, encoding='utf-8-sig')]
    coords = sorted(valid.coordinates(','.join(data)))
    # sorting the coordinates so that event_based do not depend on the order
    dt = [('lon', float), ('lat', float), ('depth', float)]
    return numpy.array(coords, dt)


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
        if isinstance(fname, str) and not fname.endswith('.xml'):

            # check if the file is a list of lon,lat without header
            with open(fname, encoding='utf-8-sig') as f:
                lon, *rest = next(f).split(',')
                try:
                    valid.longitude(lon)
                except ValueError:  # has a header
                    sm = hdf5.read_csv(fname, site.site_param_dt).array
                else:
                    sm = get_poor_site_model(fname)

            # make sure site_id starts from 0, if given
            if 'site_id' in sm.dtype.names:
                if (sm['site_id'] != numpy.arange(len(sm))).any():
                    raise InvalidFile('%s: site_id not sequential from zero'
                                      % fname)

            # round coordinates and check for duplicate points
            sm['lon'] = numpy.round(sm['lon'], 5)
            sm['lat'] = numpy.round(sm['lat'], 5)
            dupl = get_duplicates(sm, 'lon', 'lat')
            if dupl:
                raise InvalidFile(
                    'Found duplicate sites %s in %s' % (dupl, fname))

            # used global parameters is local ones are missing
            params = sorted(set(sm.dtype.names) | req_site_params)
            z = numpy.zeros(
                len(sm), [(p, site.site_param_dt[p]) for p in params])
            for name in z.dtype.names:
                try:
                    z[name] = sm[name]
                except ValueError:  # missing, use the global parameter
                    # exercised in the test classical/case_28
                    value = getattr(oqparam, site.param[name])
                    if isinstance(value, float) and numpy.isnan(value):
                        raise InvalidFile(
                            f"{oqparam.inputs['job_ini']}: "
                            f"{site.param[name]} not specified")
                    if name == 'vs30measured':  # special case
                        value = value == 'measured'
                    z[name] = value
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


def get_no_vect(gsim_lt):
    """
    :returns: the names of the non-vectorized GMPEs
    """
    names = set()
    for gsims in gsim_lt.values.values():
        for gsim in gsims:
            compute = getattr(gsim.__class__, 'compute')
            if 'ctx' not in compute.__annotations__:
                names.add(gsim.__class__.__name__)
    return names


def get_site_collection(oqparam, h5=None):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if oqparam.calculation_mode == 'aftershock':
        return
    ss = oqparam.sites_slice  # can be None or (start, stop)
    if h5 and 'sitecol' in h5 and not ss:
        return h5['sitecol']

    mesh = get_mesh(oqparam, h5)
    if mesh is None and oqparam.ground_motion_fields:
        raise InvalidFile('You are missing sites.csv or site_model.csv in %s'
                          % oqparam.inputs['job_ini'])
    elif mesh is None:
        # a None sitecol is okay when computing the ruptures only
        return
    else:  # use the default site params
        if ('gmfs' in oqparam.inputs or 'hazard_curves' in oqparam.inputs
                or 'shakemap' in oqparam.inputs):
            req_site_params = set()   # no parameters are required
        else:
            req_site_params = get_gsim_lt(oqparam).req_site_params
        if 'amplification' in oqparam.inputs:
            req_site_params.add('ampcode')
        if h5 and 'site_model' in h5:  # comes from a site_model.csv
            sm = h5['site_model'][:]
        elif (not h5 and 'site_model' in oqparam.inputs and
              'exposure' not in oqparam.inputs):
            # tested in test_with_site_model
            sm = get_site_model(oqparam)
            if len(sm) > len(mesh):  # the association will happen in base.py
                sm = oqparam
        else:
            sm = oqparam
        sitecol = site.SiteCollection.from_points(
            mesh.lons, mesh.lats, mesh.depths, sm, req_site_params)
    if ss:
        if 'custom_site_id' not in sitecol.array.dtype.names:
            gh = sitecol.geohash(6)
            assert len(numpy.unique(gh)) == len(gh), 'geohashes are not unique'
            sitecol.add_col('custom_site_id', 'S6', gh)
        mask = (sitecol.sids >= ss[0]) & (sitecol.sids < ss[1])
        sitecol = sitecol.filter(mask)
        assert sitecol is not None, 'No sites in the slice %d:%d' % ss
        sitecol.make_complete()

    ss = os.environ.get('OQ_SAMPLE_SITES')
    if ss:
        # debugging tip to reduce the size of a calculation
        # OQ_SAMPLE_SITES=.1 oq engine --run job.ini
        # will run a computation with 10 times less sites
        sitecol.array = numpy.array(random_filter(sitecol.array, float(ss)))
        sitecol.make_complete()
    if h5:
        h5['sitecol'] = sitecol
    if ('vs30' in sitecol.array.dtype.names and
            not numpy.isnan(sitecol.vs30).any()):
        assert sitecol.vs30.max() < 32767, sitecol.vs30.max()
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
    if key in Global.gsim_lt_cache:
        return Global.gsim_lt_cache[key]
    gsim_lt = logictree.GsimLogicTree(gsim_file, trts)
    gmfcorr = oqparam.correl_model
    for trt, gsims in gsim_lt.values.items():
        for gsim in gsims:
            # NB: gsim.DEFINED_FOR_TECTONIC_REGION_TYPE can be != trt,
            # but it is not an error, it is actually the most common case!
            if gmfcorr and (gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES ==
                            {StdDev.TOTAL}):
                modifications = list(gsim.kwargs.keys())
                if not (type(gsim).__name__ == 'ModifiableGMPE' and
                        'add_between_within_stds' in modifications):
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
                    logging.debug(
                        'Using weight=%s instead of %s for %s %s',
                        branch.weight.dic['weight'], w, branch.gsim, k)
                    del branch.weight.dic[k]
    if oqparam.collapse_gsim_logic_tree:
        logging.info('Collapsing the gsim logic tree')
        gsim_lt = gsim_lt.collapse(oqparam.collapse_gsim_logic_tree)
    Global.gsim_lt_cache[key] = gsim_lt
    if trts != ('*',):  # not in get_input_files
        no_vect = get_no_vect(gsim_lt)
        if no_vect:
            logging.info('The following GMPEs are not vectorized: %s', no_vect)
    return gsim_lt


def get_rupture(oqparam):
    """
    Read the `rupture_model` XML file and by filter the site collection

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an hazardlib rupture
    """
    [rup_node] = nrml.read(oqparam.inputs['rupture_model'])
    conv = sourceconverter.RuptureConverter(oqparam.rupture_mesh_spacing)
    rup = conv.convert_node(rup_node)
    rup.tectonic_region_type = '*'  # there is not TRT for scenario ruptures
    return rup


def get_source_model_lt(oqparam, branchID=''):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        a :class:`openquake.hazardlib.logictree.SourceModelLogicTree`
        instance
    """
    smlt = get_smlt(vars(oqparam), branchID)
    srcids = set(smlt.source_data['source'])
    for src in oqparam.reqv_ignore_sources:
        if src not in srcids:
            raise NameError('The source %r in reqv_ignore_sources does '
                            'not exist in the source model(s)' % src)
    if len(oqparam.source_id) == 1:  # reduce to a single source
        return smlt.reduce(oqparam.source_id[0])
    return smlt


def get_full_lt(oqparam, branchID=''):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param branchID:
        used to read a single sourceModel branch (if given)
    :returns:
        a :class:`openquake.hazardlib.logictree.FullLogicTree`
        instance
    """
    source_model_lt = get_source_model_lt(oqparam, branchID)
    trts = source_model_lt.tectonic_region_types
    trts_lower = {trt.lower() for trt in trts}
    reqv = oqparam.inputs.get('reqv', {})
    for trt in reqv:
        if trt in oqparam.discard_trts.split(','):
            continue
        elif trt.lower() not in trts_lower:
            logging.warning('Unknown TRT=%s in [reqv] section' % trt)
    gsim_lt = get_gsim_lt(oqparam, trts or ['*'])
    if len(oqparam.source_id) == 1:
        oversampling = 'reduce-rlzs'
    else:
        oversampling = oqparam.oversampling
    full_lt = logictree.FullLogicTree(source_model_lt, gsim_lt, oversampling)
    p = full_lt.source_model_lt.num_paths * gsim_lt.get_num_paths()
    if oqparam.number_of_logic_tree_samples:
        if (oqparam.oversampling == 'forbid' and
                oqparam.number_of_logic_tree_samples >= p
                and 'event' not in oqparam.calculation_mode):
            raise ValueError('Use full enumeration since there are only '
                             '{:_d} realizations'.format(p))
        unique = numpy.unique(full_lt.rlzs['branch_path'])
        logging.info('Considering {:_d} logic tree paths out of {:_d}, unique'
                     ' {:_d}'.format(oqparam.number_of_logic_tree_samples, p,
                                     len(unique)))
    else:  # full enumeration
        logging.info('There are {:_d} logic tree paths(s)'.format(p))
        if oqparam.hazard_curves and p > oqparam.max_potential_paths:
            raise ValueError(
                'There are too many potential logic tree paths (%d):'
                'raise `max_potential_paths`, use sampling instead of '
                'full enumeration, or set hazard_curves=false ' % p)
        elif (oqparam.is_event_based() and
              (oqparam.ground_motion_fields or oqparam.hazard_curves_from_gmfs)
                and p > oqparam.max_potential_paths / 100):
            logging.warning(
                'There are many potential logic tree paths (%d): '
                'try to use sampling or reduce the source model' % p)
    if source_model_lt.is_source_specific:
        logging.info('There is a source specific logic tree')
    return full_lt


def get_logic_tree(oqparam):
    """
    :returns: a CompositeLogicTree instance
    """
    flt = get_full_lt(oqparam)
    return logictree.compose(flt.source_model_lt, flt.gsim_lt)


def check_min_mag(sources, minimum_magnitude):
    """
    Raise an error if all sources are below the minimum_magnitude
    """
    ok = 0
    for src in sources:
        min_mag = getdefault(minimum_magnitude, src.tectonic_region_type)
        maxmag = src.get_min_max_mag()[1]
        if min_mag <= maxmag:
            ok += 1
    if not ok:
        raise RuntimeError('All sources were discarded by minimum_magnitude')


def _check_csm(csm, oqparam, h5):
    # checks
    csm.gsim_lt.check_imts(oqparam.imtls)

    srcs = csm.get_sources()
    check_min_mag(srcs, oqparam.minimum_magnitude)

    if os.environ.get('OQ_CHECK_INPUT'):
        source.check_complex_faults(srcs)

    # build a smart SourceFilter
    if h5 and 'sitecol' in h5:
        csm.sitecol = h5['sitecol']
    else:
        csm.sitecol = get_site_collection(oqparam, h5)
    if csm.sitecol is None:  # missing sites.csv (test_case_1_ruptures)
        return
    srcfilter = SourceFilter(csm.sitecol, oqparam.maximum_distance)
    logging.info('Checking sources bounding box using %s', csm.sitecol)
    lons = []
    lats = []
    for src in srcs:
        if hasattr(src, 'location'):
            lons.append(src.location.x)
            lats.append(src.location.y)
            continue
        try:
            box = srcfilter.get_enlarged_box(src)
        except BBoxError as exc:
            logging.error(exc)
            continue
        lons.append(box[0])
        lats.append(box[1])
        lons.append(box[2])
        lats.append(box[3])
    if cross_idl(*(list(csm.sitecol.lons) + lons)):
        lons = numpy.array(lons) % 360
    else:
        lons = numpy.array(lons)
    bbox = (lons.min(), min(lats), lons.max(), max(lats))
    if bbox[2] - bbox[0] > 180:
        raise BBoxError(
            'The bounding box of the sources is larger than half '
            'the globe: %d degrees' % (bbox[2] - bbox[0]))


# tested in test_mosaic
def get_cache_path(oqparam, h5=None):
    """
    :returns: cache path of the form OQ_DATA/csm_<checksum>.hdf5
    """
    if oqparam.cachedir:
        checksum = get_checksum32(oqparam, h5)
        return os.path.join(oqparam.cachedir, 'csm_%d.hdf5' % checksum)
    return ''


def get_composite_source_model(oqparam, dstore=None, branchID=''):
    """
    Parse the XML and build a complete composite source model in memory.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param dstore:
         an open datastore where to save the source info
    """
    logging.info('Reading %s', oqparam.inputs['source_model_logic_tree'])
    full_lt = get_full_lt(oqparam, branchID)
    path = get_cache_path(oqparam, dstore.hdf5 if dstore else None)
    if os.path.exists(path):
        from openquake.commonlib import datastore  # avoid circular import
        with datastore.read(os.path.realpath(path)) as ds:
            csm = ds['_csm']
            csm.init(full_lt)
    else:
        csm = source_reader.get_csm(oqparam, full_lt, dstore)
        _check_csm(csm, oqparam, dstore)
    return csm


def get_imts(oqparam):
    """
    Return a sorted list of IMTs as hazardlib objects
    """
    return list(map(imt.from_string, sorted(oqparam.imtls)))


def _cons_coeffs(records, loss_types, limit_states):
    dtlist = [(lt, F32) for lt in loss_types]
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
    if not oqparam.limit_states and risklist.limit_states:
        oqparam.limit_states = risklist.limit_states
    elif 'damage' in oqparam.calculation_mode and risklist.limit_states:
        assert oqparam.limit_states == risklist.limit_states
    loss_types = oqparam.loss_dt().names
    consdict = {}
    if 'consequence' in oqparam.inputs:
        if not risklist.limit_states:
            raise InvalidFile('Missing fragility functions in %s' %
                              oqparam.inputs['job_ini'])
        # build consdict of the form consequence_by_tagname -> tag -> array
        for by, fnames in oqparam.inputs['consequence'].items():
            if isinstance(fnames, str):  # single file
                fnames = [fnames]
            dtypedict = {
                by: str, 'consequence': str, 'loss_type': str, None: float}

            # i.e. files collapsed.csv, fatalities.csv, ... with headers
            # taxonomy,consequence,loss_type,slight,moderate,extensive
            arrays = []
            for fname in fnames:
                arr = hdf5.read_csv(fname, dtypedict).array
                arrays.append(arr)
                for no, row in enumerate(arr, 2):
                    if row['loss_type'] not in loss_types:
                        msg = '%s: %s is not a recognized loss type, line=%d'
                        raise InvalidFile(msg % (fname, row['loss_type'], no))

            array = numpy.concatenate(arrays)
            dic = group_array(array, 'consequence')
            for consequence, group in dic.items():
                if consequence not in scientific.KNOWN_CONSEQUENCES:
                    raise InvalidFile('Unknown consequence %s in %s' %
                                      (consequence, fnames))
                bytag = {
                    tag: _cons_coeffs(grp, loss_types, risklist.limit_states)
                    for tag, grp in group_array(group, by).items()}
                consdict['%s_by_%s' % (consequence, by)] = bytag
    # for instance consdict['collapsed_by_taxonomy']['W_LFM-DUM_H3']
    # is [(0.05,), (0.2 ,), (0.6 ,), (1.  ,)] for damage state and structural
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
    exposure = Global.exposure = asset.Exposure.read(
        oqparam.inputs['exposure'], oqparam.calculation_mode,
        oqparam.region, oqparam.ignore_missing_costs,
        by_country='country' in asset.tagset(oqparam.aggregate_by),
        errors='ignore' if oqparam.ignore_encoding_errors else None)
    exposure.mesh, exposure.assets_by_site = exposure.get_mesh_assets_by_site()
    return exposure


def get_station_data(oqparam):
    """
    Read the station data input file and build a list of
    ground motion stations and recorded ground motion values
    along with their uncertainty estimates

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns sd:
        a Pandas dataframe with station ids and coordinates as the index and
        IMT names as the first level of column headers and
        mean, std as the second level of column headers
    :returns imts:
        a list of observed intensity measure types
    """
    if 'station_data' in oqparam.inputs:
        fname = oqparam.inputs['station_data']
        sdata = pandas.read_csv(fname)

        # Identify the columns with IM values
        # Replace replace() with removesuffix() for pandas ≥ 1.4
        imt_candidates = sdata.filter(regex="_VALUE$").columns.str.replace(
            "_VALUE", "")
        imts = [valid.intensity_measure_type(imt) for imt in imt_candidates]
        im_cols = [imt + '_' + stat
                   for imt in imts for stat in ["mean", "std"]]
        station_cols = ["STATION_ID", "LONGITUDE", "LATITUDE"]
        cols = []
        for im in imts:
            stddev_str = "STDDEV" if im == "MMI" else "LN_SIGMA"
            cols.append(im + '_VALUE')
            cols.append(im + '_' + stddev_str)
        station_data = pandas.DataFrame(sdata[cols].values, columns=im_cols)
        station_sites = pandas.DataFrame(
            sdata[station_cols].values, columns=["station_id", "lon", "lat"]
        ).astype({"station_id": str, "lon": F64, "lat": F64})
    return station_data, station_sites, imts


def get_sitecol_assetcol(oqparam, haz_sitecol=None, exp_types=()):
    """
    :param oqparam: calculation parameters
    :param haz_sitecol: the hazard site collection
    :param exp_types: the expected loss types
    :returns: (site collection, asset collection, discarded)
    """
    asset_hazard_distance = max(oqparam.asset_hazard_distance.values())
    if Global.exposure is None:
        # haz_sitecol not extracted from the exposure
        Global.exposure = get_exposure(oqparam)
    if haz_sitecol is None:
        haz_sitecol = get_site_collection(oqparam)
    if oqparam.region_grid_spacing:
        haz_distance = oqparam.region_grid_spacing * 1.414
        if haz_distance != asset_hazard_distance:
            logging.debug('Using asset_hazard_distance=%d km instead of %d km',
                          haz_distance, asset_hazard_distance)
    else:
        haz_distance = asset_hazard_distance

    if haz_sitecol.mesh != Global.exposure.mesh:
        # associate the assets to the hazard sites
        sitecol, assets_by, discarded = geo.utils.assoc(
            Global.exposure.assets_by_site, haz_sitecol, haz_distance,
            'filter')
        assets_by_site = [[] for _ in sitecol.complete.sids]
        num_assets = 0
        for sid, assets in zip(sitecol.sids, assets_by):
            assets_by_site[sid] = assets
            num_assets += len(assets)
        logging.info('Associated {:_d} assets to {:_d} sites'.
                     format(num_assets, len(sitecol)))
    else:
        # asset sites and hazard sites are the same
        sitecol = haz_sitecol
        assets_by_site = Global.exposure.assets_by_site
        discarded = []
        logging.info('Read {:_d} sites and {:_d} assets from the exposure'.
                     format(len(sitecol), sum(len(a) for a in assets_by_site)))

    assetcol = asset.AssetCollection(
        Global.exposure, assets_by_site, oqparam.time_event,
        oqparam.aggregate_by)

    # check on missing fields in the exposure
    if 'risk' in oqparam.calculation_mode:
        for exp_type in exp_types:
            if not any(exp_type in name for name in assetcol.array.dtype.names):
                raise InvalidFile('The exposure %s is missing %s' %
                                  (oqparam.inputs['exposure'], exp_type))

    if (not oqparam.hazard_calculation_id and 'gmfs' not in oqparam.inputs
            and 'hazard_curves' not in oqparam.inputs
            and sitecol is not sitecol.complete):
        # for predefined hazard you cannot reduce the site collection; instead
        # you can in other cases, typically with a grid which is mostly empty
        # (i.e. there are many hazard sites with no assets)
        assetcol.reduce_also(sitecol)
    if 'custom_site_id' not in sitecol.array.dtype.names:
        gh = sitecol.geohash(8)
        if len(numpy.unique(gh)) < len(gh):
            logging.error('geohashes are not unique')
        sitecol.add_col('custom_site_id', 'S8', gh)
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
        return {lt: lst for lt in oqparam.loss_types}
    dic = oqparam.inputs['taxonomy_mapping']
    if isinstance(dic, str):  # same file for all loss_types
        dic = {lt: dic for lt in oqparam.loss_types}
    return {lt: _taxonomy_mapping(dic[lt], taxonomies)
            for lt in oqparam.loss_types}


def _taxonomy_mapping(filename, taxonomies):
    try:
        tmap_df = pandas.read_csv(filename, converters=dict(weight=float))
    except Exception as e:
        raise e.__class__('%s while reading %s' % (e, filename))
    if 'weight' not in tmap_df:
        tmap_df['weight'] = 1.

    assert set(tmap_df) in ({'taxonomy', 'conversion', 'weight'},
                            {'taxonomy', 'risk_id', 'weight'})
    # NB: conversion was the old name in the header for engine <= 3.12
    risk_id = 'risk_id' if 'risk_id' in tmap_df.columns else 'conversion'
    dic = dict(list(tmap_df.groupby('taxonomy')))
    taxonomies = taxonomies[1:]  # strip '?'
    missing = set(taxonomies) - set(dic)
    if missing:
        raise InvalidFile(
            'The taxonomy strings %s are in the exposure but not in '
            'the taxonomy mapping file %s' % (missing, filename))
    lst = [[("?", 1)]]
    for taxo in taxonomies:
        recs = dic[taxo]
        if abs(recs['weight'].sum() - 1.) > pmf.PRECISION:
            raise InvalidFile('%s: the weights do not sum up to 1 for %s' %
                              (filename, taxo))
        lst.append([(rec[risk_id], rec['weight'])
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
    oqparam.investigation_time = wrapper.investigation_time
    oqparam.set_risk_imts(get_risk_functions(oqparam))
    array = wrapper.array
    mesh = geo.Mesh(array['lon'], array['lat'])
    N = len(mesh)
    L = sum(len(imls) for imls in oqparam.imtls.values())
    data = numpy.zeros((N, L))
    level = 0
    for im in oqparam.imtls:
        arr = dic[im]
        for poe in arr.dtype.names[3:]:
            data[:, level] = arr[poe]
            level += 1
        for field in ('lon', 'lat', 'depth'):  # sanity check
            numpy.testing.assert_equal(arr[field], array[field])
    Global.pmap = ProbabilityMap(numpy.arange(N, dtype=U32), len(data), 1)
    Global.pmap.array = data.reshape(N, L, 1)
    return mesh, Global.pmap


tag2code = {'multiFaultSource': b'F',
            'areaSource': b'A',
            'multiPointSource': b'M',
            'pointSource': b'P',
            'simpleFaultSource': b'S',
            'complexFaultSource': b'C',
            'characteristicSource': b'X',
            'nonParametricSource': b'N'}


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
            if src_node.tag.endswith('Surface'):  # in geometrySections
                return True
            code = tag2code[re.search(r'\}(\w+)', src_node.tag).group(1)]
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
    if isinstance(source_ids, dict):
        source_ids = {decode(k): v for k, v in source_ids.items()}
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


def get_shapefiles(dirname):
    """
    :param dirname: directory containing the shapefiles
    :returns: list of shapefiles
    """
    out = []
    extensions = ('.shp', '.dbf', '.prj', '.shx')
    for fname in os.listdir(dirname):
        if fname.endswith(extensions):
            out.append(os.path.join(dirname, fname))
    return out


def get_reinsurance(oqparam, assetcol=None):
    """
    :returns: (policy_df, treaty_df, field_map)
    """
    if assetcol is None:
        sitecol, assetcol, discarded = get_sitecol_assetcol(oqparam)
    [(loss_type, fname)] = oqparam.inputs['reinsurance'].items()
    # make sure the first aggregate by is policy
    if oqparam.aggregate_by[0] != ['policy']:
        raise InvalidFile('%s: aggregate_by=%s' %
                          (fname, oqparam.aggregate_by))
    [(key, fname)] = oqparam.inputs['reinsurance'].items()
    p, t, f = reinsurance.parse(fname, assetcol.tagcol.policy_idx)

    # check ideductible
    arr = assetcol.array
    for pol_no, deduc in zip(p.policy, p.deductible):
        if deduc:
            ideduc = arr[arr['policy'] == pol_no]['ideductible']
            if ideduc.any():
                pol = assetcol.tagcol.policy[pol_no]
                raise InvalidFile('%s: for policy %s there is a deductible '
                                  'also in the exposure!' % (fname, pol))
    return p, t, f


def get_input_files(oqparam):
    """
    :param oqparam: an OqParam instance
    :param hazard: if True, consider only the hazard files
    :returns: input path names in a specific order
    """
    fnames = set()  # files entering in the checksum
    uri = oqparam.shakemap_uri
    if isinstance(uri, dict) and uri:
        # local files
        for key, val in uri.items():
            if key == 'fname' or key.endswith('_url'):
                val = val.replace('file://', '')
                fname = os.path.join(oqparam.base_path, val)
                if os.path.exists(fname):
                    uri[key] = fname
                    fnames.add(fname)
        # additional separate shapefiles
        if uri['kind'] == 'shapefile' and not uri['fname'].endswith('.zip'):
            fnames.update(get_shapefiles(os.path.dirname(fname)))

    for key in oqparam.inputs:
        fname = oqparam.inputs[key]
        # collect .hdf5 tables for the GSIMs, if any
        if key == 'gsim_logic_tree':
            fnames.update(gsim_lt.collect_files(fname))
            fnames.add(fname)
        elif key == 'source_model':
            fnames.add(oqparam.inputs['source_model'])
        elif key == 'exposure':  # fname is a list
            for exp in asset.Exposure.read_headers(fname):
                fnames.update(exp.datafiles)
            fnames.update(fname)
        elif key == 'reinsurance':
            [xml] = fname.values()
            node = nrml.read(xml)
            csv = ~node.reinsuranceModel.policies
            fnames.add(xml)
            fnames.add(os.path.join(os.path.dirname(xml), csv))
        elif isinstance(fname, dict):
            for key, val in fname.items():
                if isinstance(val, list):  # list of files
                    fnames.update(val)
                else:
                    fnames.add(val)
        elif isinstance(fname, list):
            for f in fname:
                if f == oqparam.input_dir:
                    raise InvalidFile('%s there is an empty path in %s' %
                                      (oqparam.inputs['job_ini'], key))
            fnames.update(fname)
        elif key == 'source_model_logic_tree':
            info = logictree.collect_info(fname)
            fnames.update(info.smpaths)
            fnames.update(info.h5paths)
            fnames.add(fname)
        else:
            fnames.add(fname)
    return sorted(fnames)


def _checksum(fnames, checksum=0):
    """
    :returns: the 32 bit checksum of a list of files
    """
    for fname in fnames:
        if fname == '<in-memory>':
            pass
        elif not os.path.exists(fname):
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
    checksum = _checksum(oqparam._input_files)
    hazard_params = []
    for key, val in sorted(vars(oqparam).items()):
        if key in ('rupture_mesh_spacing', 'complex_fault_mesh_spacing',
                   'width_of_mfd_bin', 'area_source_discretization',
                   'random_seed', 'number_of_logic_tree_samples',
                   'minimum_magnitude', 'source_id', 'sites',
                   'floating_x_step', 'floating_y_step'):
            hazard_params.append('%s = %s' % (key, val))
    data = '\n'.join(hazard_params).encode('utf8')
    checksum = zlib.adler32(data, checksum)
    if h5:
        h5.attrs['checksum32'] = checksum
    return checksum
