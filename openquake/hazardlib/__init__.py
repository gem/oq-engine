# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
hazardlib stands for Hazard Library.
"""
import os
import ast
import operator
import itertools
import unittest
import collections
import configparser
import numpy
from openquake.baselib import hdf5, general, InvalidFile
from openquake.hazardlib import (
    geo, site, nrml, sourceconverter, gsim_lt, contexts, valid)
from openquake.hazardlib.source.rupture import (
    EBRupture, get_ruptures, _get_rupture)
from openquake.hazardlib.calc.filters import IntegrationDistance


@property
def cmaker(self):
    if len(self.cmakerdict) == 1:
        return list(self.cmakerdict.values())[0]
    raise TypeError('There are multiple cmakers inside %s' % self.cmakerdict)


@property
def group(self):
    if len(self.groups) == 1:
        return self.groups[0]
    raise TypeError('There are multiple groups inside %s' % self.groups)


bytrt = operator.attrgetter('tectonic_region_type')
Input = collections.namedtuple('Input', 'groups sitecol gsim_lt cmakerdict')
Input.cmaker = cmaker
Input.group = group


def _get_site_model(fname, req_site_params):
    sm = hdf5.read_csv(fname, site.site_param_dt).array
    sm['lon'] = numpy.round(sm['lon'], 5)
    sm['lat'] = numpy.round(sm['lat'], 5)
    dupl = general.get_duplicates(sm, 'lon', 'lat')
    if dupl:
        raise InvalidFile(
            'Found duplicate sites %s in %s' % (dupl, fname))
    z = numpy.zeros(len(sm), sorted(sm.dtype.descr))
    for name in z.dtype.names:
        z[name] = sm[name]
    return z


def _get_sitecol(hparams, req_site_params):
    """
    :param hparams: a dictionary of hazard parameters
    """
    if 'sites' in hparams:
        sm = unittest.mock.Mock(**hparams)
        mesh = geo.Mesh.from_coords(hparams['sites'])
    elif 'sites_csv' in hparams:
        data = open(hparams['sites_csv']).read().replace(',', ' ').strip()
        coords = valid.coordinates(','.join(data.split('\n')))
        dic = {site.param[p]: hparams[site.param[p]] for p in req_site_params}
        if 'reference_vs30_type' not in dic:
            dic['reference_vs30_type'] = 'measured'
        sm = type('FakeSM', (), dic)
        mesh = geo.Mesh.from_coords(coords)
    elif 'site_model_file' in hparams:
        sm = _get_site_model(hparams['site_model_file'], req_site_params)
        mesh = geo.Mesh(sm['lon'], sm['lat'])
    else:
        raise KeyError('Missing sites or site_model_file')
    return site.SiteCollection.from_points(
        mesh.lons, mesh.lats, mesh.depths, sm, req_site_params)


def _rupture_groups(ebruptures):
    ebruptures.sort(key=bytrt)
    rup_groups = []
    for trt, ebrs in itertools.groupby(ebruptures, bytrt):
        grp = sourceconverter.SourceGroup(trt)
        grp.sources = list(ebrs)
        rup_groups.append(grp)
    return rup_groups


def _get_ebruptures(fname, conv=None, ses_seed=None):
    """
    :param fname: path to a rupture file (XML or CSV)
    :param conv: RuptureConverter instanc, used for XML ruptures
    :param ses_seed: used for XML ruptures
    :returns: a list of one or more EBRuptures
    """
    if fname.endswith('.xml'):
        [rup_node] = nrml.read(fname)
        rup = conv.convert_node(rup_node)
        rup.tectonic_region_type = '*'  # no TRT for scenario ruptures
        rup.seed = ses_seed
        ebrs = [EBRupture(rup, 'NA', 0, id=rup.seed, scenario=True)]
        return ebrs

    assert fname.endswith('.csv'), fname
    aw = get_ruptures(fname)
    ebrs = []
    for i, rec in enumerate(aw.array):
        rupture = _get_rupture(rec, aw.geoms[i], aw.trts[rec['trt_smr']])
        ebr = EBRupture(rupture, rec['source_id'], rec['trt_smr'],
                        rec['n_occ'], rec['id'], rec['e0'])
        ebrs.append(ebr)
    return ebrs


def read_hparams(job_ini):
    """
    :param job_ini: path to a job.ini file
    :returns: dictionary of hazard parameters
    """
    jobdir = os.path.dirname(job_ini)
    cp = configparser.ConfigParser()
    cp.read([job_ini], encoding='utf8')
    params = {}
    for sect in cp.sections():
        for key, val in cp.items(sect):
            if key == 'intensity_measure_types_and_levels':
                key = 'imtls'
                val = valid.intensity_measure_types_and_levels(val)
            elif key == 'maximum_distance':
                val = IntegrationDistance.new(val)
            elif key == 'sites':
                val = valid.coordinates(val)
            elif key.endswith('_file'):
                val = os.path.join(jobdir, val)
            else:
                try:
                    val = ast.literal_eval(val)
                except (SyntaxError, ValueError):
                    if val == 'true':
                        val = True
                    elif val == 'false':
                        val = False
            params[key] = val
    return params


def read_input(hparams, **extra):
    """
    :param hparams: path to a job.ini file or dictionary of hazard parameters
    :returns: an Input namedtuple (groups, sitecol, gsim_lt, cmakerdict)

    The dictionary hparams must contain the keys

    - "maximum_distance"
    - "imtls"
    - "source_model_file" or "rupture_model_file" or "source_string"
    - "sites" or "site_model_file"
    - "gsim" or "gsim_logic_tree_file"

    Moreover:

    - if "source_model_file" is given, then "investigation_time" is mandatory
    - if "rupture_model_file" is given, the "number_of_ground_motion_fields"
      and "ses_seed" are mandatory
    - if there is an area source, then "area_source_discretization" is needed
    - if  "site_model_file" is missing, then global site parameters are needed

    The optional keys include

    - "rupture_mesh_spacing" (default 5.)
    - "complex_fault_mesh_spacing" (default rupture_mesh_spacing)
    - "width_of_mfd_bin" (default 1.)
    - "minimum_magnitude"
    - "discard_trts" (default "")
    - "number_of_logic_tree_samples" (default 0)
    - "ses_per_logic_tree_path" (default 1)
    """
    if isinstance(hparams, str):
        hparams = read_hparams(hparams)
    if extra:
        hparams = hparams.copy()
        hparams.update(extra)
    assert 'imts' in hparams or 'imtls' in hparams
    assert isinstance(hparams['maximum_distance'], IntegrationDistance)
    smfname = hparams.get('source_model_file')
    srcstring = hparams.get('source_string')
    if smfname:  # nonscenario
        itime = hparams['investigation_time']
    else:
        itime = 50.  # ignored in scenario
    rmfname = hparams.get('rupture_model_file')
    if rmfname:
        ngmfs = hparams["number_of_ground_motion_fields"]
        ses_seed = hparams["ses_seed"]
    converter = c = sourceconverter.SourceConverter(
        itime,
        hparams.get('rupture_mesh_spacing', 5.),
        hparams.get('complex_fault_mesh_spacing'),
        hparams.get('width_of_mfd_bin', 1.0),
        hparams.get('area_source_discretization'),
        hparams.get('minimum_magnitude', {'default': 0}),
        hparams.get('source_id'),
        discard_trts=hparams.get('discard_trts', ''))
    if smfname:
        [sm] = nrml.read_source_models([smfname], converter)
        groups = sm.src_groups
    elif rmfname:
        ebrs = _get_ebruptures(rmfname, converter, ses_seed)
        groups = _rupture_groups(ebrs)
    elif srcstring:
        src = nrml.get(srcstring, c.investigation_time, c.rupture_mesh_spacing,
                       c.width_of_mfd_bin, c.area_source_discretization)
        grp = sourceconverter.SourceGroup(src.tectonic_region_type)
        grp.sources = list(src)
        groups = [grp]
    else:
        raise KeyError('Missing source_model_file or rupture_file')
    trts = set(grp.trt for grp in groups)
    if 'gsim' in hparams:
        gslt = gsim_lt.GsimLogicTree.from_(hparams['gsim'])
    else:
        gslt = gsim_lt.GsimLogicTree(hparams['gsim_logic_tree_file'], trts)

    # fix source attributes
    idx = 0
    num_rlzs = gslt.get_num_paths()
    mags_by_trt = general.AccumDict(accum=set())
    for grp_id, sg in enumerate(groups):
        assert len(sg)  # sanity check
        for src in sg:
            if hasattr(src, 'rupture'):
                mags_by_trt[sg.trt].add('%.2f' % src.rupture.mag)
            src.id = idx
            src.grp_id = grp_id
            src.trt_smr = grp_id
            src.samples = num_rlzs
            src.smweight = 1. / num_rlzs
            idx += 1

    cmakerdict = {}  # trt => cmaker
    start = 0
    n = hparams.get('number_of_logic_tree_samples', 0)
    s = hparams.get('random_seed', 42)
    for trt, rlzs_by_gsim in gslt.get_rlzs_by_gsim_trt(n, s).items():
        hparams['mags'] = sorted(mags_by_trt[trt] or mags_by_trt['*'])
        cmakerdict[trt] = contexts.ContextMaker(trt, rlzs_by_gsim, hparams)
        cmakerdict[trt].gidx = numpy.arange(start, start + len(rlzs_by_gsim))
        start += len(rlzs_by_gsim)
    if rmfname:
        # for instance, for 2 TRTs with 5x2 GSIMs and ngmfs=10, the
        # number of occupation is 100 for each rupture, for a total
        # of 200 events, see scenario/case_13
        nrlzs = gslt.get_num_paths()
        for grp in groups:
            for ebr in grp:
                ebr.n_occ = ngmfs * nrlzs

    sitecol = _get_sitecol(hparams, gslt.req_site_params)
    return Input(groups, sitecol, gslt, cmakerdict)
