# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import configparser
import numpy
from openquake.baselib import hdf5, general, InvalidFile
from openquake.hazardlib import (
    geo, site, nrml, sourceconverter, gsim_lt, logictree, contexts, valid)
from openquake.hazardlib.source.rupture import EBRupture, get_ruptures, get_ebr
from openquake.hazardlib.calc.filters import IntegrationDistance
from openquake.hazardlib.source_reader import get_csm


bytrt = operator.attrgetter('tectonic_region_type')


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
    inputs = hparams['inputs']
    if 'sites' in hparams:
        sm = contexts.Oq(**hparams)
        mesh = geo.Mesh.from_coords(hparams['sites'])
    elif 'sites' in inputs:
        data = open(inputs['sites']).read().replace(',', ' ').strip()
        coords = valid.coordinates(','.join(data.split('\n')))
        dic = {site.param[p]: hparams[site.param[p]] for p in req_site_params}
        if 'reference_vs30_type' not in dic:
            dic['reference_vs30_type'] = 'measured'
        sm = type('FakeSM', (), dic)
        mesh = geo.Mesh.from_coords(coords)
    elif 'site_model' in inputs:
        sm = _get_site_model(inputs['site_model'], req_site_params)
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


# used in hazardlib/tests/gsim/can15/nbcc_aa13_test.py
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
        ebrs = [EBRupture(rup, 0, 0, id=0)]
        ebrs[0].seed = ses_seed
        return ebrs

    assert fname.endswith('.csv'), fname
    aw = get_ruptures(fname)
    ebrs = []
    for i, rec in enumerate(aw.array):
        ebr = get_ebr(rec, aw.geoms[i], aw.trts[rec['trt_smr']])
        ebr.seed = ebr.id + ses_seed
        ebrs.append(ebr)
    return ebrs


def read_hparams(job_ini):
    """
    :param job_ini: path to a job.ini file
    :returns: dictionary of hazard parameters
    """
    jobdir = os.path.dirname(job_ini)
    cp = configparser.ConfigParser(interpolation=None)
    cp.read([job_ini], encoding='utf8')
    params = {'inputs': {}}
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
            if key.endswith('_file'):
                params['inputs'][key[:-5]] = val
            else:
                params[key] = val
    params['imtls'] = general.DictArray(params['imtls'])
    if 'poes' in params:
        params['poes'] = valid.probabilities(params['poes'])
    return params


def get_smlt(hparams, sourceID=''):
    """
    :param hparams:
        dictionary of hazard parameters
    :returns:
        :class:`openquake.hazardlib.logictree.SourceModelLogicTree` object
    """
    args = (hparams['inputs']['source_model_logic_tree'],
            hparams.get('random_seed', 42),
            hparams.get('number_of_logic_tree_samples', 0),
            hparams.get('sampling_method', 'early_weights'),
            False,
            hparams.get('smlt_branch', ''),
            sourceID)
    smlt = logictree.SourceModelLogicTree(*args)
    if 'discard_trts' in hparams:
        discard_trts = {s.strip() for s in hparams['discard_trts'].split(',')}
        # smlt.tectonic_region_types comes from applyToTectonicRegionType
        smlt.tectonic_region_types = smlt.tectonic_region_types - discard_trts
    return smlt


def get_flt(hparams, branchID=''):
    """
    :param hparams:
        dictionary of hazard parameters
    :param branchID:
        used to read a single sourceModel branch (if given)
    :returns:
        :class:`openquake.hazardlib.logictree.FullLogicTree` object
    """
    inputs = hparams['inputs']
    if 'source_model_logic_tree' not in hparams['inputs']:
        smlt = logictree.SourceModelLogicTree.fake()
        if 'source_model' in inputs:
            smpath = inputs['source_model']
            smlt.basepath = os.path.dirname(smpath)
            smlt.collect_source_model_data('b0', smpath)  # populate trts
        else:  # rupture model
            smlt.tectonic_region_types = ['*']
    else:
        smlt = get_smlt(hparams, branchID)
    if 'gsim' in hparams:
        gslt = gsim_lt.GsimLogicTree.from_(hparams['gsim'])
    else:
        gslt = gsim_lt.GsimLogicTree(
            inputs['gsim_logic_tree'], smlt.tectonic_region_types)
    return logictree.FullLogicTree(smlt, gslt)


class Input(object):
    """
    An Input object has attributes

    oq, sitecol, full_lt, gsim_lt, groups, cmakers
    """
    def __init__(self, hparams, extra, read_all=True):
        if isinstance(hparams, str):  # path to job.ini
            hparams = read_hparams(hparams)
        if extra:
            hparams = hparams.copy()
            hparams.update(extra)
        M = len(hparams['imtls'])
        assert isinstance(hparams['maximum_distance'], IntegrationDistance)
        hparams.setdefault('cross_correl', None)
        hparams.setdefault('number_of_logic_tree_samples', 0)
        hparams.setdefault('random_seed', 42)
        hparams.setdefault('ses_seed', 42)
        hparams.setdefault('reference_vs30_type', 600)
        hparams.setdefault('split_sources', True)
        hparams.setdefault('disagg_by_src', False)
        hparams.setdefault('reqv', {})
        hparams.setdefault('min_iml', numpy.zeros(M))
        hparams.setdefault('rupture_mesh_spacing', 5.),
        hparams.setdefault('complex_fault_mesh_spacing', 5.)
        hparams.setdefault('width_of_mfd_bin', 1.0),
        hparams.setdefault('area_source_discretization', 10.)
        hparams.setdefault('minimum_magnitude', {'default': 0})
        hparams.setdefault('source_id', None)
        hparams.setdefault('discard_trts', '')
        hparams.setdefault('floating_x_step', 0)
        hparams.setdefault('floating_y_step', 0)
        hparams.setdefault('source_nodes', '')
        hparams.setdefault('infer_occur_rates', False)
        hparams.setdefault('rlz_index', None)
        hparams.setdefault('disagg_bin_edges', {})
        hparams.setdefault('epsilon_star', False)
        self.oq = contexts.Oq(**hparams)
        self.full_lt = get_flt(hparams)
        self.sitecol = _get_sitecol(
            hparams, self.full_lt.gsim_lt.req_site_params)
        self.srcstring = hparams.get('source_string')
        self.converter = sourceconverter.SourceConverter(
            hparams.get('investigation_time'),
            hparams['rupture_mesh_spacing'],
            hparams['complex_fault_mesh_spacing'],
            hparams['width_of_mfd_bin'],
            hparams['area_source_discretization'],
            hparams['minimum_magnitude'],
            hparams['source_id'],
            hparams['discard_trts'],
            hparams['floating_x_step'],
            hparams['floating_y_step'],
            hparams['source_nodes'],
            hparams['infer_occur_rates'],
        )
        if read_all:
            self.groups, self.cmakers = self.get_groups_cmakers()

    def get_groups_cmakers(self):
        smfname = self.oq.inputs.get('source_model')
        rmfname = self.oq.inputs.get('rupture_model')
        if rmfname:
            ngmfs = self.oq.number_of_ground_motion_fields
            ses_seed = self.oq.ses_seed
        if smfname:
            [sm] = nrml.read_source_models([smfname], self.converter)
            groups = sm.src_groups
        elif rmfname:
            ebrs = _get_ebruptures(rmfname, self.converter, ses_seed)
            groups = _rupture_groups(ebrs)
        elif self.srcstring:
            c = self.converter
            src = nrml.get(self.srcstring, c.investigation_time,
                           c.rupture_mesh_spacing, c.width_of_mfd_bin,
                           c.area_source_discretization)
            grp = sourceconverter.SourceGroup(src.tectonic_region_type)
            grp.sources = list(src)
            groups = [grp]
        elif 'source_model_logic_tree' in self.oq.inputs:
            groups = get_csm(self.oq, self.full_lt).src_groups
        else:
            raise KeyError('Missing source model or rupture')

        # fix source attributes
        idx = 0
        num_rlzs = self.full_lt.get_num_paths()
        mags_by_trt = general.AccumDict(accum=set())
        trt_smrs = []
        for grp_id, sg in enumerate(groups):
            assert len(sg)  # sanity check
            for src in sg:
                # src can a source or an EBRupture (for scenarios)
                if hasattr(src, 'rupture'):
                    mags_by_trt[sg.trt].add('%.2f' % src.rupture.mag)
                else:
                    mags_by_trt[sg.trt].update(src.get_magstrs())
                src.id = idx
                src.grp_id = grp_id
                src.trt_smr = grp_id
                src.samples = num_rlzs
                src.smweight = 1. / num_rlzs
                idx += 1
                if hasattr(src, 'trt_smrs'):
                    trt_smrs.append(src.trt_smrs)
                else:  # scenario
                    trt_smrs.append([grp_id])
        self.oq.mags_by_trt = {
            trt: sorted(mags) for trt, mags in mags_by_trt.items()}
        if rmfname:
            # for instance, for 2 TRTs with 5x2 GSIMs and ngmfs=10, the
            # number of occupation is 100 for each rupture, for a total
            # of 200 events, see scenario/case_13
            for grp in groups:
                for ebr in grp:
                    ebr.n_occ = ngmfs * num_rlzs
                    ebr.trt_smrs = (ebr.trt_smr,)

        return groups, contexts.get_cmakers(groups, self.full_lt, self.oq)

    @property
    def cmaker(self):
        if len(self.cmakers) == 1:
            return self.cmakers[0]
        raise ValueError('There are multiple cmakers inside %s' % self.cmakers)

    @property
    def group(self):
        if len(self.groups) == 1:
            return self.groups[0]
        raise ValueError('There are multiple groups inside %s' % self.groups)


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
    return Input(hparams, extra)
