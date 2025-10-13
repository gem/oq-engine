# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

"""
Utilities to read the input files recognized by the OpenQuake engine.
"""

import io
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
import traceback
import configparser
import collections
import itertools

import numpy
import pandas
import requests
from shapely import wkt, geometry

from openquake.baselib import config, hdf5, parallel, InvalidFile
from openquake.baselib.performance import Monitor
from openquake.baselib.general import (
    random_filter, countby, get_duplicates, check_extension, gettemp, AccumDict)
from openquake.baselib.python3compat import zip, decode
from openquake.baselib.node import Node
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.geo.packager import fiona
from openquake.hazardlib.shakemap.maps import get_sitecol_shakemap
from openquake.hazardlib.calc.filters import getdefault, RuptureFilter
from openquake.hazardlib.calc.gmf import CorrelationButNoInterIntraStdDevs
from openquake.hazardlib import (
    source, geo, site, imt, valid, sourceconverter, source_reader, nrml,
    pmf, logictree, gsim_lt, get_smlt)
from openquake.hazardlib.source.rupture import build_planar_rupture_from_dict
from openquake.hazardlib.map_array import MapArray
from openquake.hazardlib.geo.utils import hex6
from openquake.hazardlib.shakemap.parsers import convert_to_oq_xml
from openquake.risklib import asset, riskmodels, scientific, reinsurance
from openquake.risklib.riskmodels import get_risk_functions
from openquake.commonlib import logs
from openquake.commonlib.oqvalidation import OqParam
from openquake.qa_tests_data import mosaic, global_risk

F32 = numpy.float32
F64 = numpy.float64
U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
Site = collections.namedtuple('Site', 'sid lon lat')


class DuplicatedPoint(Exception):
    """
    Raised when reading a CSV file with duplicated (lon, lat) pairs
    """


# used in extract_fom_zip
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
            if os.path.basename(f).endswith(ext)
            and '__MACOSX' not in f]


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


def _normalize(key, fnames, base_path):
    # returns (input_type, filenames)

    # check that all the fnames have the same extension
    # NB: for consequences fnames is a list of lists
    flatten = []
    for fname in fnames:
        if isinstance(fname, list):
            flatten.extend(fname)
        else:
            flatten.append(fname)
    check_extension(flatten)
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
            elif key == 'mmi_file':
                filenames.append(os.path.join(base_path, val))
                continue
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


def update(params, items, base_path):
    """
    Update a dictionary of string parameters with new parameters. Manages
    correctly file parameters.
    """
    for key, value in items:
        if key in ('hazard_curves_csv', 'hazard_curves_file',
                   'gmfs_csv', 'gmfs_file',
                   'site_model_csv', 'site_model_file', 'source_model_file',
                   'exposure_csv', 'exposure_file'):
            input_type, fnames = _normalize(key, value.split(), base_path)
            params['inputs'][input_type] = fnames
        elif key.endswith(('_file', '_csv', '_hdf5')):
            if value.startswith('{'):
                dic = ast.literal_eval(value)  # name -> relpath
                input_type, fnames = _normalize(key, dic.values(), base_path)
                params['inputs'][input_type] = dict(zip(dic, fnames))
                params[input_type] = ' '.join(dic)
            elif value:
                input_type, fnames = _normalize(key, [value], base_path)
                assert len(fnames) in (0, 1)
                for fname in fnames:
                    params['inputs'][input_type] = fname
            else:
                # remove the key if the value is empty
                basekey, _file = key.rsplit('_', 1)
                params['inputs'].pop(basekey, None)
        elif (isinstance(value, str) and value.endswith('.hdf5')
              and key != 'description'):
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


def check_params(cp, fname):
    params_sets = [
        set(cp.options(section)) for section in cp.sections()]
    for pair in itertools.combinations(params_sets, 2):
        params_intersection = sorted(set.intersection(*pair))
        if params_intersection:
            raise InvalidFile(
                f'{fname}: parameter(s) {params_intersection} is(are) defined'
                ' in multiple sections')


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
    cp = configparser.ConfigParser(interpolation=None)
    cp.read([job_ini], encoding='utf-8-sig')  # skip BOM on Windows
    check_params(cp, job_ini)
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
        items = dic.items()
    update(params, items, base_path)

    if input_zip:
        params['inputs']['input_zip'] = os.path.abspath(input_zip)
    update(params, kw.items(), base_path)  # override on demand
    return params


def is_fraction(string):
    """
    :returns: True if the string can be converted to a probability
    """
    try:
        f = float(string)
    except (ValueError, TypeError):
        return
    return 0 < f < 1


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
    if is_fraction(re):
        # reduce the imtls to the first imt
        # reduce the logic tree to one random realization
        # reduce the sites by a factor of `re`
        # reduce the ses by a factor of `re`
        os.environ['OQ_SAMPLE_SITES'] = re
        ses = job_ini.get('ses_per_logic_tree_path')
        if ses:
            ses = int(numpy.ceil(int(ses) * float(re)))
            job_ini['ses_per_logic_tree_path'] = str(ses)
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


def get_mesh_exp(oqparam, h5=None):
    """
    Extract the mesh of points to compute from the sites,
    the sites_csv, the region, the site model, the exposure in this order.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        a pair (mesh, exposure) both of which can be None
    """
    exposure = get_exposure(oqparam, h5)
    if oqparam.impact:
        sm = get_site_model(oqparam, h5)
        mesh = geo.Mesh(sm['lon'], sm['lat'])
        return mesh, exposure
    if oqparam.sites:
        mesh = geo.Mesh.from_coords(oqparam.sites)
        return mesh, exposure
    elif 'hazard_curves' in oqparam.inputs:
        fname = oqparam.inputs['hazard_curves']
        if isinstance(fname, list):  # for csv
            mesh, _pmap = get_pmap_from_csv(oqparam, fname)
            return mesh, exposure
        raise NotImplementedError('Reading from %s' % fname)
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
            return geo.Mesh.from_coords(zip(mesh.lons, mesh.lats)), exposure
        except Exception:
            raise ValueError(
                'Could not discretize region with grid spacing '
                '%(region_grid_spacing)s' % vars(oqparam))
    # the site model has the precedence over the exposure, see the
    # discussion in https://github.com/gem/oq-engine/pull/5217
    elif 'site_model' in oqparam.inputs:
        logging.info('Extracting the hazard sites from the site model')
        sm = get_site_model(oqparam, h5)
        mesh = geo.Mesh(sm['lon'], sm['lat'])
    elif 'exposure' in oqparam.inputs:
        mesh = exposure.mesh
    else:
        mesh = None
    return mesh, exposure


def get_poor_site_model(fname):
    """
    :returns: a poor site model with only lon, lat fields
    """
    with open(fname, encoding='utf-8-sig') as f:
        data = [ln.replace(',', ' ') for ln in f]
    coords = sorted(valid.coordinates(','.join(data)))
    # sorting the coordinates so that event_based do not depend on the order
    dt = [('lon', float), ('lat', float), ('depth', float)]
    return numpy.array(coords, dt)


def get_site_model_around(site_model_hdf5, rup, dist):
    """
    :param site_model_hdf5: path to an HDF5 file containing a 'site_model'
    :param rup: a rupture object
    :param dist: integration distance in km
    :returns: site model close to the rupture
    """
    with hdf5.File(site_model_hdf5) as f:
        sm = f['site_model'][:]
    return RuptureFilter(rup, dist)(sm)


def _smparse(fname, oqparam, arrays, sm_fieldsets):
    # check if the file is a list of lon,lat without header
    with open(fname, encoding='utf-8-sig') as f:
        lon, _rest = next(f).split(',', 1)
        try:
            valid.longitude(lon)
        except ValueError:  # has a header
            sm = hdf5.read_csv(fname, site.site_param_dt).array
        else:
            sm = get_poor_site_model(fname)

    sm_fieldsets[fname] = set(sm.dtype.names)

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

    # used global parameters if local ones are missing
    params = sorted(set(sm.dtype.names) | set(oqparam.req_site_params))
    z = numpy.zeros(
        len(sm), [(p, site.site_param_dt[p]) for p in params])
    for name in z.dtype.names:
        if name in sm.dtype.names:
            vals = sm[name]
            # Get param from site model and if "core"
            # then validate the associated values
            if name in ['lon', 'lat']:
                coos = ','.join(str(x) for x in vals)
                if name == "lat":
                    z[name] = valid.latitudes(coos)
                else:
                    z[name] = valid.longitudes(coos)
            elif name in ["vs30", "z1pt0", "z2pt5"]:
                pars = ' '.join(str(x) for x in vals)
                if name == 'vs30' and not oqparam.override_vs30:
                    # if override_vs30 is set, then we can have vs30=-999
                    z[name] = valid.positivefloats(pars)
                else:
                    z[name] = valid.positivefloatsorsentinels(pars)
            else:
                z[name] = vals  # None-core site parameter

        else:
            # If missing use the global parameter
            if name != 'backarc':  # backarc has default zero
                # exercised in the test classical/case_28_bis
                z[name] = check_site_param(oqparam, name)

    arrays.append(z)


def check_site_param(oqparam, name):
    """
    Extract the value of the given parameter
    """
    longname = site.param[name]  # vs30 -> reference_vs30_value
    value = getattr(oqparam, longname, None)
    if value is None:
        raise InvalidFile('Missing site_model_file specifying the parameter %s'
                          % name)
    if isinstance(value, float) and numpy.isnan(value):
        raise InvalidFile(
            f"{oqparam.inputs['job_ini']}: "
            f"{site.param[name]} not specified")
    elif name == 'vs30measured':  # special case
        value = value == 'measured'
    return value


def get_site_model(oqparam, h5=None):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an array with fields lon, lat, vs30, ...
    """
    if h5 and 'site_model' in h5:
        return h5['site_model'][:]

    if oqparam.impact:
        # read the site model close to the rupture
        rup = get_rupture(oqparam)
        dist = oqparam.maximum_distance('*')(rup.mag)
        sm = get_site_model_around(oqparam.inputs['exposure'][0], rup, dist)
        if h5:
            h5['site_model'] = sm
        return sm

    arrays = []
    sm_fieldsets = {}
    for fname in oqparam.inputs['site_model']:
        if isinstance(fname, str) and not fname.endswith('.xml'):
            # parsing site_model.csv and populating arrays
            _smparse(fname, oqparam, arrays, sm_fieldsets)
            continue

        # parsing site_model.xml
        nodes = nrml.read(fname).siteModel
        params = [valid.site_param(node.attrib) for node in nodes]
        missing = set(oqparam.req_site_params) - set(params[0])
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

    # all source model input files must have the same fields
    for this_sm_fname in sm_fieldsets:
        for other_sm_fname in sm_fieldsets:
            if other_sm_fname == this_sm_fname:
                continue
            this_fieldset = sm_fieldsets[this_sm_fname]
            other_fieldset = sm_fieldsets[other_sm_fname]
            fieldsets_diff = this_fieldset - other_fieldset
            if fieldsets_diff:
                raise InvalidFile(
                    f'Fields {fieldsets_diff} present in'
                    f' {this_sm_fname} were not found in {other_sm_fname}')

    sm = numpy.concatenate(arrays, dtype=arrays[0].dtype)
    if oqparam.site_labels:
        assert 'ilabel' in sm.dtype.names, 'Missing ilabel in site_model.csv'
        ilabels = set(sm['ilabel']) - {0}  # 0 means no label
        for ilabel in ilabels:
            if ilabel not in oqparam.site_labels.values():
                raise KeyError(
                    f'{oqparam.inputs["job_ini"]}: Unknown {ilabel=}')
    if h5:
        h5['site_model'] = sm

    return sm


def debug_site(oqparam, haz_sitecol):
    """
    Reduce the site collection to the custom_site_id specified in
    OQ_DEBUG_SITE. For conditioned GMFs, keep the stations.
    """
    siteid = os.environ.get('OQ_DEBUG_SITE')
    if siteid:
        complete = copy.copy(haz_sitecol.complete)
        ok = haz_sitecol['custom_site_id'] == siteid.encode('ascii')
        if not ok.any():
            raise ValueError('There is no custom_site_id=%s', siteid)
        if 'station_data' in oqparam.inputs:
            # keep the stations while restricting to the specified site
            sdata, _imts = get_station_data(oqparam, haz_sitecol)
            ok |= numpy.isin(haz_sitecol.sids, sdata.site_id.to_numpy())
        haz_sitecol.array = haz_sitecol[ok]
        haz_sitecol.complete = complete
        oqparam.concurrent_tasks = 0


def _vs30(dic):
    # dic is a dictionary key -> pathnames
    if 'site_model' in dic:
        files = hdf5.sniff(dic['site_model'])
        return any('vs30' in csv.fields for csv in files)


def get_site_collection(oqparam, h5=None):
    """
    Returns a SiteCollection instance by looking at the points and the
    site model defined by the configuration parameters.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if h5 and 'sitecol' in h5:
        return h5['sitecol']
    if oqparam.ruptures_hdf5:
        with hdf5.File(oqparam.ruptures_hdf5) as r:
            rup_sitecol = r['sitecol']
    mesh, exp = get_mesh_exp(oqparam, h5)
    if mesh is None and oqparam.ground_motion_fields:
        if oqparam.calculation_mode != 'preclassical':
            raise InvalidFile(
                'You are missing sites.csv or site_model.csv in %s'
                % oqparam.inputs['job_ini'])
        return None
    elif mesh is None:
        # a None sitecol is okay when computing the ruptures only
        return None
    else:  # use the default site params
        if ('gmfs' in oqparam.inputs or 'hazard_curves' in oqparam.inputs
                or 'shakemap' in oqparam.inputs):
            req_site_params = set()   # no parameters are required
        else:
            req_site_params = oqparam.req_site_params
        if oqparam.ruptures_hdf5 and not _vs30(oqparam.inputs):
            assoc_dist = (oqparam.region_grid_spacing * 1.414
                          if oqparam.region_grid_spacing else 10)
            # 10 km is around the grid spacing used in the mosaic
            sc = site.SiteCollection.from_points(
                mesh.lons, mesh.lats, mesh.depths, oqparam, req_site_params)
            logging.info('Associating the mesh to the site parameters')
            sitecol, _array, _discarded = geo.utils.assoc(
                sc, rup_sitecol, assoc_dist, 'filter')
            sitecol.make_complete()
            return _get_sitecol(sitecol, exp, oqparam, h5)
        elif h5 and 'site_model' in h5:
            sm = h5['site_model'][:]
        elif oqparam.impact and (
                    not oqparam.infrastructure_connectivity_analysis):
            # filter the far away sites
            rup = get_rupture(oqparam)
            dist = oqparam.maximum_distance('*')(rup.mag)
            [expo_hdf5] = oqparam.inputs['exposure']
            sm = get_site_model_around(expo_hdf5, rup, dist)
        elif (not h5 and 'site_model' in oqparam.inputs and
              'exposure' not in oqparam.inputs):
            # tested in test_with_site_model
            sm = get_site_model(oqparam, h5)
            if len(sm) > len(mesh):  # the association will happen in base.py
                sm = oqparam
        elif 'site_model' not in oqparam.inputs:
            # check the required site parameters are not NaN
            sm = oqparam
            for req_site_param in req_site_params:
                if req_site_param in site.param:
                    check_site_param(oqparam, req_site_param)
        else:
            sm = oqparam
        sitecol = site.SiteCollection.from_points(
            mesh.lons, mesh.lats, mesh.depths, sm, req_site_params)
        return _get_sitecol(sitecol, exp, oqparam, h5)


def _get_sitecol(sitecol, exp, oqparam, h5):
    if ('vs30' in sitecol.array.dtype.names and
            not numpy.isnan(sitecol.vs30).any()):
        assert sitecol.vs30.max() < 32767, sitecol.vs30.max()

    if oqparam.tile_spec:
        if 'custom_site_id' not in sitecol.array.dtype.names:
            gh = sitecol.geohash(6)
            assert len(numpy.unique(gh)) == len(gh), 'geohashes are not unique'
            sitecol.add_col('custom_site_id', 'S6', gh)
        tileno, ntiles = oqparam.tile_spec
        assert len(sitecol) > ntiles, (len(sitecol), ntiles)
        mask = sitecol.sids % ntiles == tileno - 1
        oqparam.max_sites_disagg = 1
        sitecol = sitecol.filter(mask)
        sitecol.make_complete()

    ss = os.environ.get('OQ_SAMPLE_SITES')
    if ss:
        # debugging tip to reduce the size of a calculation
        # OQ_SAMPLE_SITES=.1 oq engine --run job.ini
        # will run a computation with 10 times less sites
        sitecol.array = numpy.array(random_filter(sitecol.array, float(ss)))
        sitecol.make_complete()

    sitecol.array['lon'] = numpy.round(sitecol.lons, 5)
    sitecol.array['lat'] = numpy.round(sitecol.lats, 5)
    sitecol.exposure = exp

    # add custom_site_id in risk calculations (or GMF calculations)
    custom_site_id = any(x in oqparam.calculation_mode
                         for x in ('scenario', 'event_based',
                                   'risk', 'damage'))
    if custom_site_id and 'custom_site_id' not in sitecol.array.dtype.names:
        gh = sitecol.geohash(8)
        if len(numpy.unique(gh)) < len(gh):
            logging.error('geohashes are not unique')
        sitecol.add_col('custom_site_id', 'S8', gh)
        if sitecol is not sitecol.complete:
            # tested in scenario_risk/test_case_8
            gh = sitecol.complete.geohash(8)
            sitecol.complete.add_col('custom_site_id', 'S8', gh)

    debug_site(oqparam, sitecol)
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
        return logictree.GsimLogicTree.from_(
            oqparam.gsim, oqparam.inputs['job_ini'])
    gsim_file = os.path.join(
        oqparam.base_path, oqparam.inputs['gsim_logic_tree'])
    if len(oqparam.site_labels) > 1:
        logictree.GsimLogicTree.check_multiple(gsim_file, trts)
    gsim_lt = logictree.GsimLogicTree(gsim_file, trts)
    gmfcorr = oqparam.correl_model
    for trt, gsims in gsim_lt.values.items():
        for gsim in gsims:
            # NB: gsim.DEFINED_FOR_TECTONIC_REGION_TYPE can be != trt,
            # but it is not an error, it is actually the most common case!
            if gmfcorr and (gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES ==
                            {StdDev.TOTAL}) and not oqparam.with_betw_ratio:
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
    return gsim_lt


def get_rupture(oqparam):
    """
    Read the `rupture_model` XML file or the `rupture_dict` dictionary

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an hazardlib rupture
    """
    rupture_model = oqparam.inputs.get('rupture_model')
    rup = None

    if rupture_model and rupture_model.endswith('.json'):
        # converting rupture_model from json to an oq-compatible xml
        rupture_model = convert_to_oq_xml(rupture_model, rupture_model)
    if rupture_model and rupture_model.endswith('.xml'):
        [rup_node] = nrml.read(rupture_model)
        conv = sourceconverter.RuptureConverter(oqparam.rupture_mesh_spacing)
        rup = conv.convert_node(rup_node)
        rup.tectonic_region_type = '*'  # there is no TRT for scenario ruptures
    if rup is None:  # assume rupture_dict
        rup = build_planar_rupture_from_dict(oqparam.rupture_dict)
    return rup


def get_source_model_lt(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        a :class:`openquake.hazardlib.logictree.SourceModelLogicTree`
        instance
    """
    smlt = get_smlt(vars(oqparam))
    for bset in smlt.branchsets:
        bset.check_duplicates(smlt.filename)
    srcids = set(smlt.source_data['source'])
    for src in oqparam.reqv_ignore_sources:
        if src not in srcids:
            raise NameError('The source %r in reqv_ignore_sources does '
                            'not exist in the source model(s)' % src)
    if len(oqparam.source_id) == 1:  # reduce to a single source
        return smlt.reduce(oqparam.source_id[0])
    return smlt


def get_full_lt(oqparam):
    """
    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        a :class:`openquake.hazardlib.logictree.FullLogicTree`
        instance
    """
    source_model_lt = get_source_model_lt(oqparam)
    trts = source_model_lt.tectonic_region_types
    trts_lower = {trt.lower() for trt in trts}
    reqv = oqparam.inputs.get('reqv', {})
    for trt in reqv:
        if trt in oqparam.discard_trts.split(','):
            continue
        elif trt.lower() not in trts_lower:
            logging.warning('Unknown TRT=%s in [reqv] section' % trt)
    gsim_lt = get_gsim_lt(oqparam, trts or ['*'])
    oversampling = oqparam.oversampling
    full_lt = logictree.FullLogicTree(source_model_lt, gsim_lt, oversampling)
    p = full_lt.source_model_lt.num_paths * gsim_lt.get_num_paths()

    if full_lt.gsim_lt.has_imt_weights() and oqparam.use_rates:
        raise ValueError('use_rates=true cannot be used with imtWeight')

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
        if not oqparam.fastmean and p > oqparam.max_potential_paths:
            raise ValueError(
                'There are too many potential logic tree paths (%d):'
                'raise `max_potential_paths`, use sampling instead of '
                'full enumeration, or set use_rates=true ' % p)
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

    if h5 and 'sitecol' in h5:
        csm.sitecol = h5['sitecol']
    else:
        csm.sitecol = get_site_collection(oqparam, h5)
    if csm.sitecol is None:  # missing sites.csv (test_case_1_ruptures)
        return

    if os.environ.get('OQ_CHECK_INPUT'):
        # slow checks
        source.check_complex_faults(srcs)


def get_composite_source_model(oqparam, dstore=None):
    """
    Parse the XML and build a complete composite source model in memory.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param dstore:
         an open datastore where to save the source info
    """
    if 'source_model_logic_tree' in oqparam.inputs:
        logging.info('Reading %s', oqparam.inputs['source_model_logic_tree'])
    elif 'source_model' in oqparam.inputs:
        logging.info('Reading %s', oqparam.inputs['source_model'])
    h5 = dstore.hdf5 if dstore else None
    with Monitor('building full_lt', measuremem=True, h5=h5):
        full_lt = get_full_lt(oqparam)  # builds the weights
    csm = source_reader.get_csm(oqparam, full_lt, dstore)
    _check_csm(csm, oqparam, dstore)
    oqparam.mags_by_trt = csm.get_mags_by_trt(oqparam.maximum_distance)
    return csm


def get_imts(oqparam):
    """
    Return a sorted list of IMTs as hazardlib objects
    """
    return list(map(imt.from_string, sorted(oqparam.imtls)))


def _cons_coeffs(df, perils, loss_dt, limit_states):
    # returns composite array peril -> loss_type -> coeffs
    dtlist = [(peril, loss_dt) for peril in perils]
    coeffs = numpy.zeros(len(limit_states), dtlist)
    for loss_type in loss_dt.names:
        for peril in perils:
            the_df = df[(df.peril == peril) & (df.loss_type == loss_type)]
            if len(the_df) == 1:
                coeffs[peril][loss_type] = the_df[limit_states].to_numpy()[0]
            elif len(the_df) > 1:
                raise ValueError(
                    f'Multiple consequences for {loss_type=}, {peril=}\n%s' %
                    the_df)
    return coeffs


def get_crmodel(oqparam):
    """
    Return a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance

   :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    """
    if oqparam.impact:
        with hdf5.File(oqparam.inputs['exposure'][0], 'r') as exp:
            try:
                crm = riskmodels.CompositeRiskModel.read(exp, oqparam)
            except KeyError:
                pass  # missing crm in exposure.hdf5 in mosaic/case_01
            else:
                return crm

    risklist = get_risk_functions(oqparam)
    limit_states = risklist.limit_states
    perils = numpy.array(sorted(set(rf.peril for rf in risklist)))
    if not oqparam.limit_states and limit_states:
        oqparam.limit_states = limit_states
    elif 'damage' in oqparam.calculation_mode and limit_states:
        assert oqparam.limit_states == limit_states
    consdict = {}
    if 'consequence' in oqparam.inputs:
        if not limit_states:
            raise InvalidFile('Missing fragility functions in %s' %
                              oqparam.inputs['job_ini'])
        # build consdict of the form consequence_by_tagname -> tag -> array
        loss_dt = oqparam.loss_dt()
        for by, fnames in oqparam.inputs['consequence'].items():
            if by == 'taxonomy':  # obsolete name
                by = 'risk_id'
            if isinstance(fnames, str):  # single file
                fnames = [fnames]
            # i.e. files collapsed.csv, fatalities.csv, ... with headers like
            # taxonomy,consequence,slight,moderate,extensive
            df = pandas.concat([pandas.read_csv(fname) for fname in fnames])
            # NB: consequence files depend on loss_type, unlike fragility files
            if 'taxonomy' in df.columns:  # obsolete name
                df['risk_id'] = df['taxonomy']
                del df['taxonomy']
            if 'loss_type' not in df.columns:
                df['loss_type'] = 'structural'
            if 'peril' not in df.columns:
                df['peril'] = 'groundshaking'
            for consequence, group in df.groupby('consequence'):
                if consequence not in scientific.KNOWN_CONSEQUENCES:
                    raise InvalidFile('Unknown consequence %s in %s' %
                                      (consequence, fnames))
                bytag = {
                    tag: _cons_coeffs(grp, perils, loss_dt, limit_states)
                    for tag, grp in group.groupby(by)}
                consdict['%s_by_%s' % (consequence, by)] = bytag
    # for instance consdict['collapsed_by_taxonomy']['W_LFM-DUM_H3']
    # is [(0.05,), (0.2 ,), (0.6 ,), (1.  ,)] for damage state and structural
    crm = riskmodels.CompositeRiskModel(oqparam, risklist, consdict)
    return crm


def get_exposure(oqparam, h5=None):
    """
    Read the full exposure in memory and build a list of
    :class:`openquake.risklib.asset.Asset` instances.

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :returns:
        an :class:`Exposure` instance or a compatible AssetCollection
    """
    oq = oqparam
    if 'exposure' not in oq.inputs:
        return
    fnames = oq.inputs['exposure']
    if oqparam.rupture_xml or oqparam.rupture_dict:
        rup = get_rupture(oqparam)
        dist = oqparam.maximum_distance('*')(rup.mag)
        rupfilter = RuptureFilter(rup, dist)
    else:
        rupfilter = None
    with Monitor('reading exposure', measuremem=True, h5=h5):
        if oqparam.impact:
            sm = get_site_model(oq, h5)  # the site model around the rupture
            h6 = [x.encode('ascii') for x in sorted(set(
                hex6(sm['lon'], sm['lat'])))]
            exposure = asset.Exposure.read_around(fnames[0], h6, rupfilter)
            with hdf5.File(fnames[0]) as f:
                if 'crm' in f:
                    loss_types = f['crm'].attrs['loss_types']
                    oq.all_cost_types = loss_types
                    oq.minimum_asset_loss = {lt: 0 for lt in loss_types}
        else:
            exposure = asset.Exposure.read_all(
                oq.inputs['exposure'], oq.calculation_mode,
                oq.ignore_missing_costs,
                errors='ignore' if oq.ignore_encoding_errors else None,
                infr_conn_analysis=oq.infrastructure_connectivity_analysis,
                aggregate_by=oq.aggregate_by, rupfilter=rupfilter)
    return exposure


def concat_if_different(values):
    unique_values = values.dropna().unique().astype(str)
    # If all values are identical, return the single unique value,
    # otherwise join with "|"
    return '|'.join(unique_values)


def read_df(fname, lon, lat, id, duplicates_strategy='error'):
    """
    Read a DataFrame containing lon-lat-id fields.
    In case of rows having the same coordinates, duplicates_strategy
    determines how to manage duplicates:

    - 'error': raise an error (default)
    - 'keep_first': keep the first occurrence
    - 'keep_last': keep the last occurrence
    - 'avg': calculate the average numeric values
    """
    assert duplicates_strategy in (
        'error', 'keep_first', 'keep_last', 'avg'), duplicates_strategy
    # NOTE: the id field has to be treated as a string even if contains numbers
    dframe = pandas.read_csv(fname, dtype={id: str})
    dframe[lon] = numpy.round(dframe[lon].to_numpy(), 5)
    dframe[lat] = numpy.round(dframe[lat].to_numpy(), 5)
    duplicates = dframe[dframe.duplicated(subset=[lon, lat], keep=False)]
    if not duplicates.empty:
        msg = '%s: has duplicate sites %s' % (fname, list(duplicates[id]))
        if duplicates_strategy == 'error':
            raise InvalidFile(msg)
        msg += f' (duplicates_strategy: {duplicates_strategy})'
        logging.warning(msg)
        if duplicates_strategy == 'keep_first':
            dframe = dframe.drop_duplicates(subset=[lon, lat], keep='first')
        elif duplicates_strategy == 'keep_last':
            dframe = dframe.drop_duplicates(subset=[lon, lat], keep='last')
        elif duplicates_strategy == 'avg':
            string_columns = dframe.select_dtypes(include='object').columns
            numeric_columns = dframe.select_dtypes(include='number').columns
            # group by lon-lat, averaging columns and concatenating by "|"
            # the different contents of string columns
            dframe = dframe.groupby([lon, lat], as_index=False).agg(
                {**{col: concat_if_different for col in string_columns},
                 **{col: 'mean' for col in numeric_columns}})
    return dframe


def get_station_data(oqparam, sitecol, duplicates_strategy='error'):
    """
    Read the station data input file and build a list of
    ground motion stations and recorded ground motion values
    along with their uncertainty estimates

    :param oqparam:
        an :class:`openquake.commonlib.oqvalidation.OqParam` instance
    :param sitecol:
        the hazard site collection
    :param duplicates_strategy: either 'error', 'keep_first', 'keep_last', 'avg'
    :returns: station_data, observed_imts
    """
    if parallel.oq_distribute() == 'zmq':
        logging.error('Conditioned scenarios are not meant to be run '
                      ' on a cluster')
    # Read the station data and associate the site ID from longitude, latitude
    df = read_df(oqparam.inputs['station_data'], 'LONGITUDE', 'LATITUDE',
                 'STATION_ID', duplicates_strategy=duplicates_strategy)
    lons = df['LONGITUDE'].to_numpy()
    lats = df['LATITUDE'].to_numpy()
    nsites = len(sitecol.complete)
    sitecol.extend(lons, lats)
    logging.info('Extended complete site collection from %d to %d sites',
                 nsites, len(sitecol.complete))
    dic = {(lo, la): sid
           for lo, la, sid in sitecol.complete[['lon', 'lat', 'sids']]}
    sids = U32([dic[lon, lat] for lon, lat in zip(lons, lats)])

    # Identify the columns with IM values
    # Replace replace() with removesuffix() for pandas ≥ 1.4
    imt_candidates = df.filter(regex="_VALUE$").columns.str.replace(
        "_VALUE", "")
    imts = [valid.intensity_measure_type(imt) for imt in imt_candidates]
    im_cols = [imt + '_' + stat for imt in imts for stat in ["mean", "std"]]
    cols = []
    for im in imts:
        stddev_str = "STDDEV" if im == "MMI" else "LN_SIGMA"
        cols.append(im + '_VALUE')
        cols.append(im + '_' + stddev_str)
    for im_value_col in [im + '_VALUE' for im in imts]:
        if (df[im_value_col] == 0).any():
            file_basename = os.path.basename(oqparam.inputs['station_data'])
            wrong_rows = df[['STATION_ID', im_value_col]].loc[
                df.index[df[im_value_col] == 0]]
            raise InvalidFile(
                f"Please remove station data with zero intensity value from"
                f" {file_basename}:\n"
                f" {wrong_rows}")
    station_data = pandas.DataFrame(df[cols].values, columns=im_cols)
    station_data['site_id'] = sids
    return station_data, imts


def assoc_to_shakemap(oq, haz_sitecol, assetcol):
    """
    Download the shakemap, reduce the assetcol and returns a reduced sitecol
    """
    oq.risk_imtls = {imt: list(imls) for imt, imls in oq.imtls.items()}
    logging.info('Getting/reducing shakemap, sitecol, assetcol')
    # for instance for the test case_shakemap the haz_sitecol
    # has sids in range(0, 26) while sitecol.sids is
    # [8, 9, 10, 11, 13, 15, 16, 17, 18];
    # the total assetcol has 26 assets on the total sites
    # and the reduced assetcol has 9 assets on the reduced sites
    if oq.shakemap_id:
        uridict = {'kind': 'usgs_id', 'id': oq.shakemap_id}
    elif 'shakemap' in oq.inputs:
        uridict = {'kind': 'file_npy', 'fname': oq.inputs['shakemap']}
    else:
        uridict = oq.shakemap_uri
    sitecol, shakemap, discarded = get_sitecol_shakemap(
        uridict, oq.risk_imtls, haz_sitecol,
        oq.asset_hazard_distance['default'])
    assetcol.reduce_also(sitecol)
    logging.info('Extracted %d assets', len(assetcol))
    return sitecol, shakemap


def assoc_exposure(exp, haz_sitecol, oqparam, h5):
    """
    Associate the assets to the hazard sites
    """
    # this is absurdely fast: 10 million assets can be associated in <10s
    A = len(exp.assets)
    N = len(haz_sitecol)
    with Monitor('associating exposure', measuremem=True, h5=h5):
        region = wkt.loads(oqparam.region) if oqparam.region else None
        sitecol, discarded = exp.associate(
            haz_sitecol, oqparam.get_haz_distance(), region)
        logging.info(
            'Associated {:_d} assets (of {:_d}) to {:_d} sites'
            ' (of {:_d})'.format(len(exp.assets), A, len(sitecol), N))
    return sitecol, discarded


def get_sitecol_assetcol(oqparam, haz_sitecol=None, inp_types=(), h5=None):
    """
    :param oqparam: calculation parameters
    :param haz_sitecol: the hazard site collection
    :param inp_types: the input loss types
    :returns: (site collection, asset collection, discarded, exposure)
    """
    if haz_sitecol is None:
        # read the sites from the sites/site_model/region
        haz_sitecol = get_site_collection(oqparam, h5)
    try:
        exp = haz_sitecol.exposure
    except AttributeError:
        # in scenario_risk test_case_6a
        exp = get_exposure(oqparam, h5)
    sitecol, discarded = assoc_exposure(exp, haz_sitecol, oqparam, h5)

    assetcol = asset.AssetCollection(
        exp, sitecol, oqparam.time_event, oqparam.aggregate_by)
    if oqparam.aggregate_exposure:
        A = len(assetcol)
        assetcol = assetcol.agg_by_site()
        logging.info(f'Aggregated {A} assets -> {len(assetcol)} assets')

    u, c = numpy.unique(assetcol['taxonomy'], return_counts=True)
    idx = c.argmax()  # index of the most common taxonomy
    tax = assetcol.tagcol.taxonomy[u[idx]]
    logging.info('Found %d taxonomies with ~%.1f assets each',
                 len(u), len(assetcol) / len(u))
    logging.info('The most common taxonomy is %s with %d assets', tax, c[idx])

    # check on missing fields in the exposure
    if 'risk' in oqparam.calculation_mode:
        for exp_type in inp_types:
            if not any(exp_type in name
                       for name in assetcol.array.dtype.names):
                raise InvalidFile('The exposure %s is missing %s' %
                                  (oqparam.inputs['exposure'], exp_type))

    if (not oqparam.hazard_calculation_id and 'gmfs' not in oqparam.inputs
            and 'hazard_curves' not in oqparam.inputs
            and 'station_data' not in oqparam.inputs
            and not oqparam.rupture_dict  # and not oqparam.rupture_xml
            and sitecol is not sitecol.complete):
        # for predefined hazard you cannot reduce the site collection; instead
        # you can in other cases, typically with a grid which is mostly empty
        # (i.e. there are many hazard sites with no assets)
        assetcol.reduce_also(sitecol)
    return sitecol, assetcol, discarded, exp


def levels_from(header):
    levels = []
    for field in header:
        if field.startswith('poe-'):
            levels.append(float(field[4:]))
    return levels


def impact_tmap(oqparam, taxidx):
    """
    :returns: a taxonomy mapping dframe
    """
    acc = AccumDict(accum=[])  # loss_type, taxi, risk_id, weight
    with hdf5.File(oqparam.inputs['exposure'][0], 'r') as exp:
        for key in exp['tmap']:
            # tmap has fields conversion, taxonomy, weight
            df = exp.read_df('tmap/' + key)
            for taxo, risk_id, weight in zip(
                    df.taxonomy, df.conversion, df.weight):
                if taxo in taxidx:
                    acc['country'].append(key)
                    acc['peril'].append('groundshaking')
                    acc['taxi'].append(taxidx[taxo])
                    acc['risk_id'].append(risk_id)
                    acc['weight'].append(weight)
    return pandas.DataFrame(acc)


# tested in TaxonomyMappingTestCase
def taxonomy_mapping(oqparam, taxidx):
    """
    :param oqparam: OqParam instance
    :param taxidx: dictionary taxo:str -> taxi:int
    :returns: a dictionary loss_type -> [[(riskid, weight), ...], ...]
    """
    if oqparam.impact:
        return impact_tmap(oqparam, taxidx)
    elif 'taxonomy_mapping' not in oqparam.inputs:  # trivial mapping
        nt = len(taxidx)  # number of taxonomies
        df = pandas.DataFrame(dict(weight=numpy.ones(nt),
                                   taxi=taxidx.values(),
                                   risk_id=list(taxidx),
                                   peril=['*']*nt,
                                   country=['?']*nt))
        return df
    fname = oqparam.inputs['taxonomy_mapping']
    return _taxonomy_mapping(fname, taxidx)


def _taxonomy_mapping(filename, taxidx):
    try:
        tmap_df = pandas.read_csv(filename, converters=dict(weight=float))
    except Exception as e:
        raise e.__class__('%s while reading %s' % (e, filename))
    if 'weight' not in tmap_df:
        tmap_df['weight'] = 1.
    if 'peril' not in tmap_df:
        tmap_df['peril'] = '*'
    if 'country' not in tmap_df:
        tmap_df['country'] = '?'
    if 'conversion' in tmap_df.columns:
        # conversion was the old name in the header for engine <= 3.12
        tmap_df = tmap_df.rename(columns={'conversion': 'risk_id'})
    assert set(tmap_df) == {'country', 'peril', 'taxonomy',
                            'risk_id', 'weight'}, set(tmap_df)
    taxos = set()
    for (taxo, country, per), df in tmap_df.groupby(
            ['taxonomy', 'country', 'peril']):
        taxos.add(taxo)
        if abs(df.weight.sum() - 1.) > pmf.PRECISION:
            raise InvalidFile('%s: the weights do not sum up to 1 for %s' %
                              (filename, taxo))
    missing = set(taxidx) - taxos
    if missing:
        raise InvalidFile(
            'The taxonomy strings %s are in the exposure but not in '
            'the taxonomy mapping file %s' % (missing, filename))
    tmap_df['taxi'] = [taxidx.get(taxo, -1) for taxo in tmap_df.taxonomy]
    del tmap_df['taxonomy']
    # NB: we are ignoring the taxonomies in the mapping but not in the exposure
    # for instance in EventBasedRiskTestCase::test_case_5
    return tmap_df[tmap_df.taxi != -1]


def assert_probabilities(array, fname):
    """
    Check that the array contains valid probabilities
    """
    for poe_field in (f for f in array.dtype.names if f.startswith('poe-')):
        arr = array[poe_field]
        if (arr > 1).any():
            raise InvalidFile('%s: contains probabilities > 1: %s' %
                              (fname, arr[arr > 1]))
        if (arr < 0).any():
            raise InvalidFile('%s: contains probabilities < 0: %s' %
                              (fname, arr[arr < 0]))


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
    for fname in fnames:
        wrapper = read(fname)
        assert_probabilities(wrapper.array, fname)
        dic[wrapper.imt] = wrapper.array
        imtls[wrapper.imt] = levels_from(wrapper.dtype.names)
    oqparam.hazard_imtls = imtls
    oqparam.investigation_time = wrapper.investigation_time
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
    pmap = MapArray(numpy.arange(N, dtype=U32), len(data), 1)
    pmap.array = data.reshape(N, L, 1)
    return mesh, pmap


tag2code = {'multiFaultSource': b'F',
            'areaSource': b'A',
            'multiPointSource': b'M',
            'pointSource': b'P',
            'simpleFaultSource': b'S',
            'complexFaultSource': b'C',
            'characteristicFaultSource': b'X',
            'nonParametricSeismicSource': b'N'}


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


def read_delta_rates(fname, idx_nr):
    """
    :param fname:
        path to a CSV file with fields (source_id, rup_id, delta)
    :param idx_nr:
        dictionary source_id -> (src_id, num_ruptures) with Ns sources
    :returns:
        list of Ns floating point arrays of different lenghts
    """
    delta_df = pandas.read_csv(fname, converters=dict(
        source_id=str, rup_id=int, delta=float), index_col=0)
    assert list(delta_df.columns) == ['rup_id', 'delta']
    delta = [numpy.zeros(0) for _ in idx_nr]
    for src, df in delta_df.groupby(delta_df.index):
        idx, nr = idx_nr[src]
        rupids = df.rup_id.to_numpy()
        if len(numpy.unique(rupids)) < len(rupids):
            raise InvalidFile('%s: duplicated rup_id for %s' % (fname, src))
        drates = numpy.zeros(nr)
        drates[rupids] = df.delta.to_numpy()
        delta[idx] = drates
    return delta


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
        _sitecol, assetcol, _discarded, _exp = get_sitecol_assetcol(oqparam)
    [(_loss_type, fname)] = oqparam.inputs['reinsurance'].items()
    # make sure the first aggregate by is policy
    if oqparam.aggregate_by[0] != ['policy']:
        raise InvalidFile('%s: aggregate_by=%s' %
                          (fname, oqparam.aggregate_by))
    [(_key, fname)] = oqparam.inputs['reinsurance'].items()
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
        # local files, like .npy arrays
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
            fnames.update(oqparam.inputs['source_model'])
        elif key == 'exposure':  # fname is a list
            fnames.update(fname)
            if any(f.endswith(('.xml', '.nrml')) for f in fnames):
                for exp in asset.Exposure.read_headers(fname):
                    fnames.update(exp.datafiles)
        elif key == 'reinsurance':
            [xml] = fname.values()
            node = nrml.read(xml)
            csv = ~node.reinsuranceModel.policies
            fnames.add(xml)
            fnames.add(os.path.join(os.path.dirname(xml), csv))
        elif key == 'geometry':
            fnames.add(fname)
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
    for fname in (f for f in fnames if f != '<in-memory>'):
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


# NOTE: we expect to call this for mosaic or global_risk, with buffer 0 or 0.1
@functools.lru_cache(maxsize=4)
def read_geometries(fname, name, buffer=0):
    """
    :param fname: path of the file containing the geometries
    :param name: name of the primary key field
    :param buffer: shapely buffer in degrees
    :returns: data frame with codes and geometries
    """
    with fiona.open(fname) as f:
        codes = []
        geoms = []
        for feature in f:
            props = feature['properties']
            geom = feature['geometry']
            code = props[name]
            if code and geom:
                codes.append(code)
                geoms.append(geometry.shape(geom).buffer(buffer))
            else:
                logging.error(f'{code=}, {geom=} in {fname}')
    return pandas.DataFrame(dict(code=codes, geom=geoms))


@functools.lru_cache()
def read_cities(fname, lon_name, lat_name, label_name):
    """
    Reading coordinates and names of populated places from a CSV file

    :returns: a Pandas DataFrame
    """
    data = pandas.read_csv(fname)
    expected_colnames_set = {lon_name, lat_name, label_name}
    if not expected_colnames_set.issubset(data.columns):
        raise ValueError(
            f"CSV file must contain {expected_colnames_set} columns.")
    return data


def read_mosaic_df(buffer):
    """
    :returns: a DataFrame of geometries for the mosaic models
    """
    mosaic_boundaries_file = config.directory.mosaic_boundaries_file
    if not mosaic_boundaries_file:
        mosaic_boundaries_file = os.path.join(
            os.path.dirname(mosaic.__file__), 'mosaic.gpkg')
    return read_geometries(mosaic_boundaries_file, 'name', buffer)


def read_countries_df(buffer=0.1):
    """
    :returns: a DataFrame of geometries for the world countries
    """
    logging.info('Reading geoBoundariesCGAZ_ADM0.gpkg')  # slow
    fname = os.path.join(os.path.dirname(global_risk.__file__),
                         'geoBoundariesCGAZ_ADM0.gpkg')
    return read_geometries(fname, 'shapeGroup', buffer)


def read_cities_df(lon_field='longitude', lat_field='latitude',
                             label_field='name'):
    """
    Reading from a 'worldcities.csv' file in the mosaic_dir, if present,
    or returning None otherwise

    :returns: a DataFrame of coordinates and names of populated places
    """
    fname = os.path.join(os.path.dirname(mosaic.__file__), 'worldcities.csv')
    return read_cities(fname, lon_field, lat_field, label_field)


def read_source_models(fnames, hdf5path='', **converterparams):
    """
    :param fnames: a list of source model files
    :param hdf5path: auxiliary .hdf5 file used to store the multifault sources
    :param converterparams: a dictionary of parameters like rupture_mesh_spacing
    :returns: a list of SourceModel instances
    """
    converter = sourceconverter.SourceConverter()
    vars(converter).update(converterparams)
    smodels = list(nrml.read_source_models(fnames, converter))
    smdict = dict(zip(fnames, smodels))
    src_groups = [sg for sm in smdict.values() for sg in sm.src_groups]
    secparams = source_reader.fix_geometry_sections(
        smdict, src_groups, hdf5path)
    for smodel in smodels:
        for sg in smodel.src_groups:
            for src in sg:
                if src.code == b'F':  # multifault
                    src.set_msparams(secparams)
    return smodels


def loadnpz(resp):
    """
    Get an .npz file from the WebUI
    """
    if hasattr(resp, 'content'):
        # there was an error and we got an HTTP response from Django
        raise RuntimeError(resp.content.decode('utf-8'))
    bio = io.BytesIO(b''.join(ln for ln in resp))
    return numpy.load(bio)


# tested in commands_test
def jobs_from_inis(inis):
    """
    :param inis: list of pathnames
    :returns:
        {'success': jids or [], 'error': '' or traceback string}
    """
    jids = []
    try:
        for ini in inis:
            oq = get_oqparam(ini)
            checksum = get_checksum32(oq)
            jobs = logs.dbcmd('SELECT job_id FROM checksum '
                              'WHERE hazard_checksum=?x', checksum)
            if jobs:
                jids.append(jobs[0].job_id)
            else:
                jids.append(0)
    except Exception:
        return {'success': [], 'error': traceback.format_exc()}
    return {'success': jids, 'error': ''}
