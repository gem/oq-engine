# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2022 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import re
import abc
import copy
import time
import logging
import warnings
import itertools
import collections
from unittest.mock import patch
import numpy
import shapely
from scipy.interpolate import interp1d

from openquake.baselib.general import (
    AccumDict, DictArray, RecordBuilder, gen_slices, block_splitter, sqrscale)
from openquake.baselib.performance import Monitor, split_array, kollapse
from openquake.baselib.python3compat import decode
from openquake.hazardlib import valid, imt as imt_module
from openquake.hazardlib.const import StdDev, OK_COMPONENTS
from openquake.hazardlib.tom import (
    registry, get_pnes, FatedTOM, NegativeBinomialTOM)
from openquake.hazardlib.stats import ndtr
from openquake.hazardlib.site import site_param_dt
from openquake.hazardlib.calc.filters import (
    SourceFilter, IntegrationDistance, magdepdist, get_distances, getdefault,
    MINMAG, MAXMAG)
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.surface.planar import (
    project, project_back, get_distances_planar)

U32 = numpy.uint32
F16 = numpy.float16
F64 = numpy.float64
TWO20 = 2**20  # used when collapsing
TWO16 = 2**16
TWO24 = 2**24
TWO32 = 2**32
STD_TYPES = (StdDev.TOTAL, StdDev.INTER_EVENT, StdDev.INTRA_EVENT)
MAX_MB = 200
KNOWN_DISTANCES = frozenset(
    'rrup rx ry0 rjb rhypo repi rcdpp azimuth azimuth_cp rvolc closest_point'
    .split())
DIST_BINS = sqrscale(1, 1000, 65536)
# the following is used in the collapse method
IGNORE_PARAMS = {'rup_id', 'src_id', 'weight', 'occurrence_rate', 'probs_occur',
                 'clon', 'clat', 'sids'}
MEA = 0
STD = 1

# These coordinates were provided by M Gerstenberger (personal
# communication, 10 August 2018)
cshm_polygon = shapely.geometry.Polygon([(171.6, -43.3), (173.2, -43.3),
                                         (173.2, -43.9), (171.6, -43.9)])


def is_modifiable(gsim):
    """
    :returns: True if it is a ModifiableGMPE
    """
    return hasattr(gsim, 'gmpe') and hasattr(gsim, 'params')


def concat(ctxs):
    """
    Concatenate context arrays.
    :returns: list with 0, 1 or 2 elements
    """
    out, poisson, nonpoisson, nonparam = [], [], [], []
    for ctx in ctxs:
        if numpy.isnan(ctx.occurrence_rate).all():
            nonparam.append(ctx)

        # If ctx has probs_occur and occur_rate is parametric non-poisson
        elif hasattr(ctx, 'probs_occur') and ctx.probs_occur.shape[1] >= 1:
            nonpoisson.append(ctx)
        else:
            poisson.append(ctx)
    if poisson:
        out.append(numpy.concatenate(poisson).view(numpy.recarray))
    if nonpoisson:
        # Ctxs with the same shape of prob_occur are concatenated
        # and different shape sets are appended separately
        for shp in set(ctx.probs_occur.shape[1] for ctx in nonpoisson):
            p_array = [p for p in nonpoisson
                       if p.probs_occur.shape[1] == shp]
            out.append(numpy.concatenate(p_array).view(numpy.recarray))
    if nonparam:
        out.append(numpy.concatenate(nonparam).view(numpy.recarray))
    return out


def get_maxsize(M, G):
    """
    :returns: an integer N such that arrays N*M*G fit in the CPU cache
    """
    maxs = TWO20 // (8*M*G)
    assert maxs > 1, maxs
    return maxs


def size(imtls):
    """
    :returns: size of the dictionary of arrays imtls
    """
    imls = imtls[next(iter(imtls))]
    return len(imls) * len(imtls)


def trivial(ctx, name):
    """
    :param ctx: a recarray
    :param name: name of a parameter
    :returns: True if the parameter is missing or single valued
    """
    if name not in ctx.dtype.names:
        return True
    return len(numpy.unique(numpy.float32(ctx[name]))) == 1


class DeltaRatesGetter(object):
    """
    Read the delta rates from an aftershock datastore
    """
    def __init__(self, dstore):
        self.dstore = dstore

    def __call__(self, src_id):
        with self.dstore.open('r') as dstore:
            return dstore['delta_rates'][src_id]


# same speed as performance.kround, round more
def kround(ctx, kfields):
    kdist = 5. * ctx.mag**2  # heuristic collapse distance from 80 to 500 km
    close = ctx.rrup < kdist
    far = ~close
    out = numpy.zeros(len(ctx), [(k, ctx.dtype[k]) for k in kfields])
    for kfield in kfields:
        kval = ctx[kfield]
        if kval.dtype == F64 and kfield != 'mag':
            out[kfield][close] = F16(kval[close])  # round less
            out[kfield][far] = numpy.round(kval[far])  # round more
        else:
            out[kfield] = ctx[kfield]
    return out


class Collapser(object):
    """
    Class managing the collapsing logic.
    """
    def __init__(self, collapse_level, kfields):
        self.collapse_level = collapse_level
        self.kfields = sorted(kfields)
        self.cfactor = numpy.zeros(2)

    def collapse(self, ctx, rup_indep, collapse_level=None):
        """
        Collapse a context recarray if possible.

        :param ctx: a recarray with "sids"
        :param rup_indep: False if the ruptures are mutually exclusive
        :param collapse_level: if None, use .collapse_level
        :returns: the collapsed array and a list of arrays with site IDs
        """
        clevel = (collapse_level if collapse_level is not None
                  else self.collapse_level)
        if not rup_indep or clevel < 0:
            # no collapse
            self.cfactor[0] += len(ctx)
            self.cfactor[1] += len(ctx)
            return ctx, ctx.sids.reshape(-1, 1)

        out, allsids = [], []
        kfields = [k for k in self.kfields if k != 'mag']
        for mag in numpy.unique(ctx.mag):
            ctxt = ctx[ctx.mag == mag]
            o, a = kollapse(ctxt, kfields, kround,
                            mfields=['mag', 'occurrence_rate', 'probs_occur'],
                            afield='sids')
            out.append(o)
            allsids.extend(a)
        out = numpy.concatenate(out).view(numpy.recarray)
        self.cfactor[0] += len(out)
        self.cfactor[1] += len(ctx)
        print(self.kfields, len(ctx), len(out), '(%.1f)' % (len(ctx)/len(out)))
        return out.view(numpy.recarray), allsids


class FarAwayRupture(Exception):
    """Raised if the rupture is outside the maximum distance for all sites"""


def basename(src):
    """
    :returns: the base name of a split source
    """
    src_id = src if isinstance(src, str) else src.source_id
    splits = re.split('[.:]', src_id, 1)
    if len(splits) == 2 and ';' in splits[1]:
        return splits[0] + ';' + splits[1].split(';')[1]
    return splits[0]


def get_num_distances(gsims):
    """
    :returns: the number of distances required for the given GSIMs
    """
    dists = set()
    for gsim in gsims:
        dists.update(gsim.REQUIRES_DISTANCES)
    return len(dists)


def _interp(param, name, trt):
    try:
        mdd = param[name]
    except KeyError:
        return magdepdist([(MINMAG, 1000), (MAXMAG, 1000)])
    if isinstance(mdd, IntegrationDistance):
        return mdd(trt)
    elif isinstance(mdd, dict):
        return magdepdist(getdefault(mdd, trt))
    return mdd


class ContextMaker(object):
    """
    A class to manage the creation of contexts and to compute mean/stddevs
    and possibly PoEs.

    :param trt: tectonic region type string
    :param gsims: list of GSIMs or a dictionary gsim -> rlz indices
    :param oq:
       dictionary of parameters like the maximum_distance, the IMTLs,
       the investigation time, etc, or an OqParam instance
    :param extraparams:
       additional site parameters to consider, used only in the tests

    NB: the trt can be different from the tectonic region type for which
    the underlying GSIMs are defined. This is intentional.
    """
    REQUIRES = ['DISTANCES', 'SITES_PARAMETERS', 'RUPTURE_PARAMETERS']
    deltagetter = None
    fewsites = False
    tom = None

    def __init__(self, trt, gsims, oq, monitor=Monitor(), extraparams=()):
        if isinstance(oq, dict):
            param = oq
            self.mags = param.get('mags', ())
            self.cross_correl = param.get('cross_correl')  # cond_spectra_test
        else:  # OqParam
            param = vars(oq)
            param['split_sources'] = oq.split_sources
            param['min_iml'] = oq.min_iml
            param['reqv'] = oq.get_reqv()
            param['af'] = getattr(oq, 'af', None)
            self.cross_correl = oq.cross_correl
            self.imtls = oq.imtls
            try:
                self.mags = oq.mags_by_trt[trt]
            except AttributeError:
                self.mags = ()
            except KeyError:  # missing TRT but there is only one
                [(_, self.mags)] = oq.mags_by_trt.items()
        if 'poes' in param:
            self.poes = param['poes']
        if 'imtls' in param:
            for imt in param['imtls']:
                if not isinstance(imt, str):
                    raise TypeError('Expected string, got %s' % type(imt))
            self.imtls = param['imtls']
        elif 'hazard_imtls' in param:
            self.imtls = DictArray(param['hazard_imtls'])
        elif not hasattr(self, 'imtls'):
            raise KeyError('Missing imtls in ContextMaker!')

        self.cache_distances = param.get('cache_distances', False)
        if self.cache_distances:
            # use a cache (surface ID, dist_type) for MultiFaultSources
            self.dcache = AccumDict()
            self.dcache.hit = 0
        else:
            self.dcache = None  # disabled
        self.af = param.get('af')
        self.max_sites_disagg = param.get('max_sites_disagg', 10)
        self.time_per_task = param.get('time_per_task', 60)
        self.disagg_by_src = param.get('disagg_by_src')
        self.collapse_level = int(param.get('collapse_level', -1))
        self.disagg_by_src = param.get('disagg_by_src', False)
        self.trt = trt
        self.gsims = gsims
        self.oq = oq
        for gsim in gsims:
            if hasattr(gsim, 'set_tables'):
                if not self.mags and not is_modifiable(gsim):
                    raise ValueError(
                        'You must supply a list of magnitudes as 2-digit '
                        'strings, like mags=["6.00", "6.10", "6.20"]')
                gsim.set_tables(self.mags, self.imtls)
        self.horiz_comp = param.get('horiz_comp_to_geom_mean', False)
        self.maximum_distance = _interp(param, 'maximum_distance', trt)
        if 'pointsource_distance' not in param:
            self.pointsource_distance = 1000.
        else:
            self.pointsource_distance = getdefault(
                param['pointsource_distance'], trt)
        self.minimum_distance = param.get('minimum_distance', 0)
        self.investigation_time = param.get('investigation_time')
        if self.investigation_time:
            self.tom = registry['PoissonTOM'](self.investigation_time)
        self.ses_seed = param.get('ses_seed', 42)
        self.ses_per_logic_tree_path = param.get('ses_per_logic_tree_path', 1)
        self.truncation_level = param.get('truncation_level', 99.)
        self.phi_b = ndtr(self.truncation_level)
        self.num_epsilon_bins = param.get('num_epsilon_bins', 1)
        self.disagg_bin_edges = param.get('disagg_bin_edges', {})
        self.ps_grid_spacing = param.get('ps_grid_spacing')
        self.split_sources = param.get('split_sources')
        self.effect = param.get('effect')
        for req in self.REQUIRES:
            reqset = set()
            for gsim in gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
                if self.af and req == 'SITES_PARAMETERS':
                    reqset.add('ampcode')
                if is_modifiable(gsim) and req == 'SITES_PARAMETERS':
                    reqset.add('vs30')  # required by the ModifiableGMPE
                    reqset.update(gsim.gmpe.REQUIRES_SITES_PARAMETERS)
                    if 'apply_swiss_amplification' in gsim.params:
                        reqset.add('amplfactor')
            setattr(self, 'REQUIRES_' + req, reqset)
        try:
            self.min_iml = param['min_iml']
        except KeyError:
            self.min_iml = [0. for imt in self.imtls]
        self.reqv = param.get('reqv')
        if self.reqv is not None:
            self.REQUIRES_DISTANCES.add('repi')
        # NB: REQUIRES_DISTANCES is empty when gsims = [FromFile]
        REQUIRES_DISTANCES = self.REQUIRES_DISTANCES | {'rrup'}
        reqs = (sorted(self.REQUIRES_RUPTURE_PARAMETERS) +
                sorted(self.REQUIRES_SITES_PARAMETERS | set(extraparams)) +
                sorted(REQUIRES_DISTANCES))
        dic = {}
        for req in reqs:
            if req in site_param_dt:
                dt = site_param_dt[req]
                if isinstance(dt, tuple):  # (string_, size)
                    dic[req] = b'X' * dt[1]
                else:
                    dic[req] = dt(0)
            else:
                dic[req] = 0.
        dic['src_id'] = U32(0)
        dic['rup_id'] = U32(0)
        dic['sids'] = U32(0)
        dic['rrup'] = numpy.float64(0)
        dic['weight'] = numpy.float64(0)
        dic['occurrence_rate'] = numpy.float64(0)
        self.defaultdict = dic
        kfields = (self.REQUIRES_DISTANCES |
                   self.REQUIRES_RUPTURE_PARAMETERS |
                   self.REQUIRES_SITES_PARAMETERS)
        self.collapser = Collapser(self.collapse_level, kfields)
        self.shift_hypo = param.get('shift_hypo')
        self.set_imts_conv()
        self.init_monitoring(monitor)

    def init_monitoring(self, monitor):
        # instantiating child monitors, may be called in the workers
        self.pla_mon = monitor('planar contexts', measuremem=False)
        self.ctx_mon = monitor('nonplanar contexts', measuremem=False)
        self.col_mon = monitor('collapsing contexts', measuremem=True)
        self.gmf_mon = monitor('computing mean_std', measuremem=False)
        self.poe_mon = monitor('get_poes', measuremem=False)
        self.pne_mon = monitor('composing pnes', measuremem=False)
        self.ir_mon = monitor('iter_ruptures', measuremem=True)
        self.delta_mon = monitor('getting delta_rates', measuremem=False)
        self.task_no = getattr(monitor, 'task_no', 0)
        self.out_no = getattr(monitor, 'out_no', self.task_no)

    def restrict(self, imts):
        """
        :param imts: a list of IMT strings subset of the full list
        :returns: a new ContextMaker involving less IMTs
        """
        new = copy.copy(self)
        new.imtls = DictArray({imt: self.imtls[imt] for imt in imts})
        new.set_imts_conv()
        return new

    def set_imts_conv(self):
        """
        Set the .imts list and .conv dictionary for the horizontal component
        conversion (if any).
        """
        self.loglevels = DictArray(self.imtls) if self.imtls else {}
        with warnings.catch_warnings():
            # avoid RuntimeWarning: divide by zero encountered in log
            warnings.simplefilter("ignore")
            for imt, imls in self.imtls.items():
                if imt != 'MMI':
                    self.loglevels[imt] = numpy.log(imls)
        self.imts = tuple(imt_module.from_string(im) for im in self.imtls)
        self.conv = {}  # gsim -> imt -> (conv_median, conv_sigma, rstd)
        if not self.horiz_comp:
            return  # do not convert
        for gsim in self.gsims:
            self.conv[gsim] = {}
            imc = gsim.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT
            if imc.name == 'GEOMETRIC_MEAN':
                pass  # nothing to do
            elif imc.name in OK_COMPONENTS:
                dic = {imt: imc.apply_conversion(imt) for imt in self.imts}
                self.conv[gsim].update(dic)
            else:
                logging.warning(f'Conversion from {imc.name} not applicable to '
                                f'{gsim.__class__.__name__}')

    def horiz_comp_to_geom_mean(self, mean_stds):
        """
        This function converts ground-motion obtained for a given description of
        horizontal component into ground-motion values for geometric_mean.

        The conversion equations used are from:
            - Beyer and Bommer (2006): for arithmetic mean, GMRot and random
            - Boore and Kishida (2017): for RotD50
        """
        for g, gsim in enumerate(self.gsims):
            if not self.conv[gsim]:
                continue
            for m, imt in enumerate(self.imts):
                me, si, ta, ph = mean_stds[:, g, m]
                conv_median, conv_sigma, rstd = self.conv[gsim][imt]
                me[:] = numpy.log(numpy.exp(me) / conv_median)
                si[:] = ((si**2 - conv_sigma**2) / rstd**2)**0.5

    @property
    def stop(self):
        return self.start + len(self.gsims)

    def dcache_size(self):
        """
        :returns: the size in bytes of the distance cache
        """
        if not self.dcache:
            return 0
        nbytes = 0
        for arr in self.dcache.values():
            if isinstance(arr, numpy.ndarray):
                nbytes += arr.nbytes
        return nbytes

    def read_ctxs(self, dstore, slc=None, magi=None):
        """
        :param dstore: a DataStore instance
        :param slice: a slice of contexts with the same grp_id
        :returns: a list of contexts
        """
        self.src_mutex, self.rup_mutex = dstore['mutex_by_grp'][self.grp_id]
        sitecol = dstore['sitecol'].complete.array
        if slc is None:
            slc = dstore['rup/grp_id'][:] == self.grp_id
        params = {n: dstore['rup/' + n][slc] for n in dstore['rup']}
        dtlist = []
        for par, val in params.items():
            if len(val) == 0:
                return []
            elif par == 'probs_occur':
                item = (par, object)
            elif par == 'occurrence_rate':
                item = (par, F64)
            else:
                item = (par, val[0].dtype)
            dtlist.append(item)
        for par in sitecol.dtype.names:
            if par != 'sids':
                dtlist.append((par, sitecol.dtype[par]))
        if magi is not None:
            dtlist.append(('magi', numpy.uint8))
        ctx = numpy.zeros(len(params['grp_id']), dtlist).view(numpy.recarray)
        for par, val in params.items():
            ctx[par] = val
        for par in sitecol.dtype.names:
            if par != 'sids':
                ctx[par] = sitecol[par][ctx['sids']]
        if magi is not None:
            ctx['magi'] = magi
        # NB: sorting the contexts break the disaggregation! (see case_1)

        # split parametric vs nonparametric contexts
        nans = numpy.isnan(ctx.occurrence_rate)
        if nans.sum() in (0, len(ctx)):  # no nans or all nans
            ctxs = [ctx]
        else:
            # happens in the oq-risk-tests for NZ
            ctxs = [ctx[nans], ctx[~nans]]
        return ctxs

    def new_ctx(self, size):
        """
        :returns: a recarray of the given size full of zeros
        """
        return RecordBuilder(**self.defaultdict).zeros(size)

    def recarray(self, ctxs, magi=None):
        """
        :params ctxs: a non-empty list of homogeneous contexts
        :returns: a recarray, possibly collapsed
        """
        assert ctxs
        dd = self.defaultdict.copy()
        if magi is not None:  # magnitude bin used in disaggregation
            dd['magi'] = numpy.uint8(0)

        if not hasattr(ctxs[0], 'probs_occur'):
            for ctx in ctxs:
                ctx.probs_occur = numpy.zeros(0)
            np = 0
        else:
            shps = [ctx.probs_occur.shape for ctx in ctxs]
            np = max(i[1] if len(i) > 1 else i[0] for i in shps)
        dd['probs_occur'] = numpy.zeros(np)
        if self.fewsites:  # must be at the end
            dd['clon'] = numpy.float64(0.)
            dd['clat'] = numpy.float64(0.)
        C = sum(len(ctx) for ctx in ctxs)
        ra = RecordBuilder(**dd).zeros(C)
        start = 0
        for ctx in ctxs:
            ctx = ctx.roundup(self.minimum_distance)
            slc = slice(start, start + len(ctx))
            for par in dd:
                if par == 'rup_id':
                    val = getattr(ctx, par)
                elif par == 'magi':  # in disaggregation
                    val = magi
                elif par == 'weight':
                    val = getattr(ctx, par, 0.)
                else:
                    val = getattr(ctx, par, numpy.nan)
                getattr(ra, par)[slc] = val
            ra.sids[slc] = ctx.sids
            start = slc.stop
        return ra

    def get_ctx_params(self):
        """
        :returns: the interesting attributes of the context
        """
        params = {'occurrence_rate', 'sids', 'src_id',
                  'probs_occur', 'clon', 'clat', 'rrup'}
        params.update(self.REQUIRES_RUPTURE_PARAMETERS)
        for dparam in self.REQUIRES_DISTANCES:
            params.add(dparam + '_')
        return params

    def from_srcs(self, srcs, sitecol):  # used in disagg.disaggregation
        """
        :param srcs: a list of Source objects
        :param sitecol: a SiteCollection instance
        :returns: a list of context arrays
        """
        ctxs = []
        srcfilter = SourceFilter(sitecol, self.maximum_distance)
        for i, src in enumerate(srcs):
            src.id = i
            sites = srcfilter.get_close_sites(src)
            if sites is not None:
                ctxs.extend(self.get_ctx_iter(src, sites))
        return concat(ctxs)

    def make_rctx(self, rup):
        """
        Add .REQUIRES_RUPTURE_PARAMETERS to the rupture
        """
        ctx = RuptureContext()
        vars(ctx).update(vars(rup))
        for param in self.REQUIRES_RUPTURE_PARAMETERS:
            if param == 'mag':
                value = numpy.round(rup.mag, 6)
            elif param == 'strike':
                value = rup.surface.get_strike()
            elif param == 'dip':
                value = rup.surface.get_dip()
            elif param == 'rake':
                value = rup.rake
            elif param == 'ztor':
                value = rup.surface.get_top_edge_depth()
            elif param == 'hypo_lon':
                value = rup.hypocenter.longitude
            elif param == 'hypo_lat':
                value = rup.hypocenter.latitude
            elif param == 'hypo_depth':
                value = rup.hypocenter.depth
            elif param == 'width':
                value = rup.surface.get_width()
            elif param == 'in_cshm':
                # used in McVerry and Bradley GMPEs
                if rup.surface:
                    lons = rup.surface.mesh.lons.flatten()
                    lats = rup.surface.mesh.lats.flatten()
                    points_in_polygon = (
                        shapely.geometry.Point(lon, lat).within(cshm_polygon)
                        for lon, lat in zip(lons, lats))
                    value = any(points_in_polygon)
                else:
                    value = False
            elif param == 'zbot':
                # needed for width estimation in CampbellBozorgnia2014
                if rup.surface:
                    value = rup.surface.mesh.depths.max()
                else:
                    value = rup.hypocenter.depth
            else:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (type(self).__name__, param))
            setattr(ctx, param, value)
        if not hasattr(ctx, 'occurrence_rate'):
            ctx.occurrence_rate = numpy.nan
        if hasattr(ctx, 'temporal_occurrence_model'):
            if isinstance(ctx.temporal_occurrence_model, NegativeBinomialTOM):
                ctx.probs_occur = ctx.temporal_occurrence_model.get_pmf(
                    ctx.occurrence_rate)

        return ctx

    def get_rctx(self, rup, sites, distances=None):
        """
        :returns: a RuptureContext (or None if filtered away)
        """
        ctx = self.make_rctx(rup)
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])

        if distances is None:
            distances = rup.surface.get_min_distance(sites.mesh)
        ctx.rrup = distances
        ctx.sites = sites
        for param in self.REQUIRES_DISTANCES - {'rrup'}:
            dists = get_distances(rup, sites, param, self.dcache)
            setattr(ctx, param, dists)

        # Equivalent distances
        reqv_obj = (self.reqv.get(self.trt) if self.reqv else None)
        if reqv_obj and not rup.surface:  # PointRuptures have no surface
            reqv = reqv_obj.get(ctx.repi, rup.mag)
            if 'rjb' in self.REQUIRES_DISTANCES:
                ctx.rjb = reqv
            if 'rrup' in self.REQUIRES_DISTANCES:
                ctx.rrup = numpy.sqrt(reqv**2 + rup.hypocenter.depth**2)

        return ctx

    def _get_ctx_planar(self, mag, planar, sites, src_id, start_stop, tom):
        # computing distances
        rrup, xx, yy = project(planar, sites.xyz)  # (3, U, N)
        if self.fewsites:
            # get the closest points on the surface
            closest = project_back(planar, xx, yy)  # (3, U, N)
        dists = {'rrup': rrup}
        for par in self.REQUIRES_DISTANCES - {'rrup'}:
            dists[par] = get_distances_planar(planar, sites, par)
        for par in dists:
            dst = dists[par]
            if self.minimum_distance:
                dst[dst < self.minimum_distance] = self.minimum_distance

        # building contexts; ctx has shape (U, N), ctxt (N, U)
        ctx = self.build_ctx((len(planar), len(sites)))
        ctxt = ctx.T  # smart trick taking advantage of numpy magic
        ctxt['src_id'] = src_id

        if self.fewsites:
            # the loop below is a bit slow
            for u, rup_id in enumerate(range(*start_stop)):
                ctx[u]['rup_id'] = rup_id

        # setting rupture parameters
        for par in self.ruptparams:
            if par == 'mag':
                ctxt[par] = mag
            elif par == 'occurrence_rate':
                ctxt[par] = planar.wlr[:, 2]  # shape U-> (N, U)
            elif par == 'width':
                ctxt[par] = planar.wlr[:, 0]
            elif par == 'strike':
                ctxt[par] = planar.sdr[:, 0]
            elif par == 'dip':
                ctxt[par] = planar.sdr[:, 1]
            elif par == 'rake':
                ctxt[par] = planar.sdr[:, 2]
            elif par == 'ztor':  # top edge depth
                ctxt[par] = planar.corners[:, 2, 0]
            elif par == 'zbot':  # bottom edge depth
                ctxt[par] = planar.corners[:, 2, 3]
            elif par == 'hypo_lon':
                ctxt[par] = planar.hypo[:, 0]
            elif par == 'hypo_lat':
                ctxt[par] = planar.hypo[:, 1]
            elif par == 'hypo_depth':
                ctxt[par] = planar.hypo[:, 2]

        # setting distance parameters
        for par in dists:
            ctx[par] = dists[par]
        if self.fewsites:
            ctx['clon'] = closest[0]
            ctx['clat'] = closest[1]

        # setting site parameters
        for par in self.siteparams:
            ctx[par] = sites.array[par]  # shape N-> (U, N)
        if hasattr(tom, 'get_pmf'):  # NegativeBinomialTOM
            # read Probability Mass Function from model and reshape it
            # into predetermined shape of probs_occur
            pmf = tom.get_pmf(planar.wlr[:, 2],
                              n_max=ctx['probs_occur'].shape[2])
            ctx['probs_occur'] = pmf[:, numpy.newaxis, :]

        return ctx

    def gen_ctxs_planar(self, src, sitecol):
        """
        :param src: a (Collapsed)PointSource
        :param sitecol: a filtered SiteCollection
        :yields: context arrays
        """
        dd = self.defaultdict.copy()
        tom = src.temporal_occurrence_model

        if isinstance(tom, NegativeBinomialTOM):
            if hasattr(src, 'pointsources'):  # CollapsedPointSource
                maxrate = max(max(ps.mfd.occurrence_rates)
                              for ps in src.pointsources)
            else:  # regular source
                maxrate = max(src.mfd.occurrence_rates)
            p_size = tom.get_pmf(maxrate).shape[1]
            dd['probs_occur'] = numpy.zeros(p_size)
        else:
            dd['probs_occur'] = numpy.zeros(0)

        if self.fewsites:
            dd['clon'] = numpy.float64(0.)
            dd['clat'] = numpy.float64(0.)

        self.build_ctx = RecordBuilder(**dd).zeros
        self.siteparams = [par for par in sitecol.array.dtype.names
                           if par in dd]
        self.ruptparams = (
            self.REQUIRES_RUPTURE_PARAMETERS | {'occurrence_rate'})

        with self.ir_mon:
            # building planar geometries
            planardict = src.get_planar(self.shift_hypo)

        magdist = {mag: self.maximum_distance(mag)
                   for mag, rate in src.get_annual_occurrence_rates()}
        # self.maximum_distance(mag) can be 0 if outside the mag range
        maxmag = max(mag for mag, dist in magdist.items() if dist > 0)
        maxdist = magdist[maxmag]
        cdist = sitecol.get_cdist(src.location)
        # NB: having a decent max_radius is essential for performance!
        mask = cdist <= maxdist + src.max_radius(maxdist)
        sitecol = sitecol.filter(mask)
        if sitecol is None:
            return []

        for magi, mag, planarlist, sites in self._quartets(
                src, sitecol, cdist[mask], magdist, planardict):
            if not planarlist:
                continue
            elif len(planarlist) > 1:  # when using ps_grid_spacing
                pla = numpy.concatenate(planarlist).view(numpy.recarray)
            else:
                pla = planarlist[0]

            offset = src.offset + magi * len(pla)
            start_stop = offset, offset + len(pla)
            ctx = self._get_ctx_planar(
                mag, pla, sites, src.id, start_stop, tom).flatten()
            ctxt = ctx[ctx.rrup < magdist[mag]]
            if len(ctxt):
                yield ctxt

    def _quartets(self, src, sitecol, cdist, magdist, planardict):
        minmag = self.maximum_distance.x[0]
        maxmag = self.maximum_distance.x[-1]
        # splitting by magnitude
        if src.count_nphc() == 1:
            # one rupture per magnitude
            for m, (mag, pla) in enumerate(planardict.items()):
                if minmag < mag < maxmag:
                    yield m, mag, pla, sitecol
        else:
            for m, rup in enumerate(src.iruptures()):
                mag = rup.mag
                if mag > maxmag or mag < minmag:
                    continue
                arr = [rup.surface.array.reshape(-1, 3)]
                pla = planardict[mag]
                # NB: having a good psdist is essential for performance!
                psdist = src.get_psdist(m, mag, self.pointsource_distance,
                                        magdist)
                close = sitecol.filter(cdist <= psdist)
                far = sitecol.filter(cdist > psdist)
                if self.fewsites:
                    if close is None:  # all is far, common for small mag
                        yield m, mag, arr, sitecol
                    else:  # something is close
                        yield m, mag, pla, sitecol
                else:  # many sites
                    if close is None:  # all is far
                        yield m, mag, arr, far
                    elif far is None:  # all is close
                        yield m, mag, pla, close
                    else:  # some sites are far, some are close
                        yield m, mag, arr, far
                        yield m, mag, pla, close

    # this is called for non-point sources (or point sources in preclassical)
    def gen_contexts(self, rups_sites, src_id):
        """
        :yields: the old-style RuptureContexts generated by the source
        """
        for rups, sites in rups_sites:  # ruptures with the same magnitude
            if len(rups) == 0:  # may happen in case of min_mag/max_mag
                continue
            magdist = self.maximum_distance(rups[0].mag)
            for u, rup in enumerate(rups):
                dist = get_distances(rup, sites, 'rrup', self.dcache)
                mask = dist <= magdist
                if mask.any():
                    r_sites = sites.filter(mask)
                    rctx = self.get_rctx(rup, r_sites, dist[mask])
                    rctx.src_id = src_id
                    rctx.rup_id = rup.rup_id
                    if self.fewsites:
                        c = rup.surface.get_closest_points(sites.complete)
                        rctx.clon = c.lons[rctx.sids]
                        rctx.clat = c.lats[rctx.sids]
                    yield rctx

    def get_ctx_iter(self, src, sitecol, src_id=0, step=1):
        """
        :param src:
            a source object (already split) or a list of ruptures
        :param sitecol:
            a (filtered) SiteCollection
        :param src_id:
            integer source ID used where src is actually a list
        :param step:
            > 1 only in preclassical
        :returns:
            iterator over recarrays
        """
        self.fewsites = len(sitecol.complete) <= self.max_sites_disagg
        if getattr(src, 'location', None) and step == 1:
            return self.pla_mon.iter(self.gen_ctxs_planar(src, sitecol))
        elif hasattr(src, 'source_id'):  # other source
            minmag = self.maximum_distance.x[0]
            maxmag = self.maximum_distance.x[-1]
            with self.ir_mon:
                allrups = [rup for rup in src.iter_ruptures(
                    shift_hypo=self.shift_hypo, step=step)
                           if minmag < rup.mag < maxmag]
                for i, rup in enumerate(allrups):
                    rup.rup_id = src.offset + i
                self.num_rups = len(allrups)
                # sorted by mag by construction
                u32mags = U32([rup.mag * 100 for rup in allrups])
                rups_sites = [(rups, sitecol) for rups in split_array(
                    numpy.array(allrups), u32mags)]
            src_id = src.id
        else:  # in event based we get a list with a single rupture
            rups_sites = [(src, sitecol)]
            src_id = 0
        rctxs = self.gen_contexts(rups_sites, src_id)
        blocks = block_splitter(rctxs, 10_000, weight=len)
        # the weight of 10_000 ensure less than 1MB per block (recarray)
        return self.ctx_mon.iter(map(self.recarray, blocks))

    def max_intensity(self, sitecol1, mags, dists):
        """
        :param sitecol1: a SiteCollection instance with a single site
        :param mags: a sequence of magnitudes
        :param dists: a sequence of distances
        :returns: an array of GMVs of shape (#mags, #dists)
        """
        assert len(sitecol1) == 1, sitecol1
        nmags, ndists = len(mags), len(dists)
        gmv = numpy.zeros((nmags, ndists))
        for m, d in itertools.product(range(nmags), range(ndists)):
            mag, dist = mags[m], dists[d]
            ctx = RuptureContext()
            for par in self.REQUIRES_RUPTURE_PARAMETERS:
                setattr(ctx, par, 0)
            for dst in self.REQUIRES_DISTANCES:
                setattr(ctx, dst, numpy.array([dist]))
            for par in self.REQUIRES_SITES_PARAMETERS:
                setattr(ctx, par, getattr(sitecol1, par))
            ctx.sids = sitecol1.sids
            ctx.mag = mag
            ctx.width = .01  # 10 meters to avoid warnings in abrahamson_2014
            try:
                maxmean = self.get_mean_stds([ctx])[0].max()
                # shape NM
            except ValueError:  # magnitude outside of supported range
                continue
            else:
                gmv[m, d] = numpy.exp(maxmean)
        return gmv

    # not used by the engine, is is meant for notebooks
    def get_poes(self, srcs, sitecol, rup_indep=True, collapse_level=-1):
        """
        :param srcs: a list of sources with the same TRT
        :param sitecol: a SiteCollection instance with N sites
        :returns: an array of PoEs of shape (N, L, G)
        """
        self.collapser.cfactor = numpy.zeros(2)
        ctxs = self.from_srcs(srcs, sitecol)
        with patch.object(self.collapser, 'collapse_level', collapse_level):
            return self.get_pmap(ctxs, rup_indep).array

    def get_pmap(self, ctxs, rup_indep=True):
        """
        :param ctxs: a list of context arrays (only one for poissonian ctxs)
        :param rup_indep: default True
        :returns: a ProbabilityMap
        """
        sids = numpy.unique(ctxs[0].sids)
        pmap = ProbabilityMap(sids, size(self.imtls), len(self.gsims))
        pmap.fill(rup_indep)
        self.update(pmap, ctxs, rup_indep)
        return ~pmap if rup_indep else pmap

    def update(self, pmap, ctxs, rup_indep=True):
        """
        :param pmap: probability map to update
        :param ctxs: a list of context arrays (only one for parametric ctxs)
        :param rup_indep: False for mutex ruptures, default True
        """
        if self.tom is None:
            itime = -1.  # test_hazard_curve_X _
        elif isinstance(self.tom, FatedTOM):
            itime = 0.
        else:
            itime = self.tom.time_span
        for ctx in ctxs:
            for poes, ctxt, slcsids in self.gen_poes(ctx, rup_indep):
                probs_occur = getattr(ctxt, 'probs_occur',
                                      numpy.zeros((len(ctxt), 0)))
                rates = ctxt.occurrence_rate
                with self.pne_mon:
                    if isinstance(slcsids, numpy.ndarray):
                        # no collapse: avoiding an inner loop can give a 25%
                        if rup_indep:
                            pmap.update_i(poes, rates, probs_occur,
                                          ctxt.sids, itime)
                        else:  # USAmodel, New Madrid cluster
                            pmap.update_m(poes, rates, probs_occur,
                                          ctxt.weight, ctxt.sids, itime)
                    else:  # collapse is possible only for rup_indep
                        allsids = []
                        sizes = []
                        for sids in slcsids:
                            allsids.extend(sids)
                            sizes.append(len(sids))
                        pmap.update_c(poes, rates, probs_occur,
                                      U32(allsids), U32(sizes), itime)

    # called by gen_poes and by the GmfComputer
    def get_mean_stds(self, ctxs):
        """
        :param ctxs: a list of contexts with N=sum(len(ctx) for ctx in ctxs)
        :returns: an array of shape (4, G, M, N) with mean and stddevs
        """
        N = sum(len(ctx) for ctx in ctxs)
        M = len(self.imtls)
        G = len(self.gsims)
        out = numpy.zeros((4, G, M, N))
        if all(isinstance(ctx, numpy.recarray) for ctx in ctxs):
            # contexts already vectorized
            recarrays = ctxs
        else:  # vectorize the contexts
            recarrays = [self.recarray(ctxs)]
        # split by magnitude in case of GMPETable gsims
        if any(hasattr(gsim, 'gmpe_table') for gsim in self.gsims):
            assert len(recarrays) == 1, len(recarrays)
            recarrays = split_array(recarrays[0], U32(recarrays[0].mag*100))
        self.adj = {gsim: [] for gsim in self.gsims}  # NSHM2014P adjustments
        for g, gsim in enumerate(self.gsims):
            compute = gsim.__class__.compute
            start = 0
            for ctx in recarrays:
                slc = slice(start, start + len(ctx))
                adj = compute(gsim, ctx, self.imts, *out[:, g, :, slc])
                if adj is not None:
                    self.adj[gsim].append(adj)
                start = slc.stop
            if self.adj[gsim]:
                self.adj[gsim] = numpy.concatenate(self.adj[gsim])
            if self.truncation_level not in (0, 99.) and (
                    out[1, g] == 0.).any():
                raise ValueError('Total StdDev is zero for %s' % gsim)
        if self.conv:  # apply horizontal component conversion
            self.horiz_comp_to_geom_mean(out)
        return out

    def gen_poes(self, ctx, rup_indep=True):
        """
        :param ctx: a vectorized context (recarray) of size N
        :yields: poes, ctxt, slcsids with poes of shape (N, L, G)
        """
        # NB: we are carefully trying to save memory here
        # see case_39
        from openquake.hazardlib.site_amplification import get_poes_site
        (M, L1), G = self.loglevels.array.shape, len(self.gsims)
        maxsize = get_maxsize(M, G)
        # L1 is the reduction factor such that the NLG arrays have
        # the same size as the GMN array and fit in the CPU cache

        # collapse if possible
        with self.col_mon:
            ctx, allsids = self.collapser.collapse(ctx, rup_indep)

        # split large context arrays to avoid filling the CPU cache
        if ctx.nbytes > maxsize:
            bigslices = gen_slices(0, len(ctx), maxsize)
        else:
            bigslices = [slice(0, len(ctx))]

        for bigslc in bigslices:
            s = bigslc.start
            with self.gmf_mon:
                mean_stdt = self.get_mean_stds([ctx[bigslc]])
            for slc in gen_slices(bigslc.start, bigslc.stop, maxsize // (4*L1)):
                slcsids = allsids[slc]
                ctxt = ctx[slc]
                self.slc = slice(slc.start - s, slc.stop - s)  # in set_poes
                with self.poe_mon:
                    # this is allocating at most 1MB of RAM
                    poes = numpy.zeros((len(ctxt), M*L1, G))
                    for g, gsim in enumerate(self.gsims):
                        ms = mean_stdt[:2, g, :, self.slc]
                        # builds poes of shape (n, L, G)
                        if self.af:  # kernel amplification method
                            poes[:, :, g] = get_poes_site(ms, self, ctxt)
                        else:  # regular case
                            gsim.set_poes(ms, self, ctxt, poes[:, :, g])
                yield poes, ctxt, slcsids

    def estimate_sites(self, src, sites):
        """
        :param src: a (Collapsed)PointSource
        :param sites: a filtered SiteCollection
        :returns: how many sites are impacted overall
        """
        magdist = {mag: self.maximum_distance(mag)
                   for mag, rate in src.get_annual_occurrence_rates()}
        nphc = src.count_nphc()
        dists = sites.get_cdist(src.location)
        planardict = src.get_planar(iruptures=True)
        esites = 0
        for m, (mag, [planar]) in enumerate(planardict.items()):
            rrup = dists[dists < magdist[mag]]
            nclose = (rrup < src.get_psdist(m, mag, self.pointsource_distance,
                                            magdist)).sum()
            nfar = len(rrup) - nclose
            esites += nclose * nphc + nfar
        return esites

    # tested in test_collapse_small
    def estimate_weight(self, src, srcfilter, multiplier=1):
        """
        :param src: a source object
        :param srcfilter: a SourceFilter instance
        :returns: (weight, estimate_sites)
        """
        sites = srcfilter.get_close_sites(src)
        if sites is None:
            # may happen for CollapsedPointSources
            return 0, 0
        src.nsites = len(sites)
        N = len(srcfilter.sitecol.complete)  # total sites
        if (hasattr(src, 'location') and src.count_nphc() > 1 and
                self.pointsource_distance < 1000):
            # cps or pointsource with nontrivial nphc
            esites = self.estimate_sites(src, sites) * multiplier
        else:
            ctxs = list(self.get_ctx_iter(src, sites, step=10))  # reduced
            if not ctxs:
                return src.num_ruptures if N == 1 else 0, 0
            esites = (sum(len(ctx) for ctx in ctxs) * src.num_ruptures /
                      self.num_rups * multiplier)  # num_rups from get_ctx_iter
        weight = esites / N  # the weight is the effective number of ruptures
        return weight, int(esites)

    def set_weight(self, sources, srcfilter, multiplier=1, mon=Monitor()):
        """
        Set the weight attribute on each prefiltered source
        """
        if hasattr(srcfilter, 'array'):  # a SiteCollection was passed
            srcfilter = SourceFilter(srcfilter, self.maximum_distance)
        G = len(self.gsims)
        N = len(srcfilter.sitecol)
        for src in sources:
            if src.nsites == 0:  # was discarded by the prefiltering
                src.esites = 0
            else:
                with mon:
                    src.weight, src.esites = self.estimate_weight(
                        src, srcfilter, multiplier)
                    src.weight *= G
                    if src.code == b'P':
                        src.weight += .1
                    elif src.code == b'C':
                        src.weight += 10.
                    elif src.code == b'F':
                        if N <= self.max_sites_disagg:
                            src.weight *= 100  # superheavy
                        else:
                            src.weight += 30.
                    else:
                        src.weight += 1.
                    
    def split_by_gsim(self):
        """
        Split the ContextMaker in multiple context makers, one per GSIM
        """
        if len(self.gsims) == 1:
            return [self]
        cmakers = []
        for g, gsim in enumerate(self.gsims):
            cm = self.__class__(self.trt, [gsim], self.oq)
            cm.start = self.start + g
            cm.gsim_idx = g
            cm.grp_id = self.grp_id
            cmakers.append(cm)
        return cmakers


# see contexts_tests.py for examples of collapse
# probs_occur = functools.reduce(combine_pmf, (r.probs_occur for r in rups))
def combine_pmf(o1, o2):
    """
    Combine probabilities of occurrence; used to collapse nonparametric
    ruptures.

    :param o1: probability distribution of length n1
    :param o2: probability distribution of length n2
    :returns: probability distribution of length n1 + n2 - 1

    >>> combine_pmf([.99, .01], [.98, .02])
    array([9.702e-01, 2.960e-02, 2.000e-04])
    """
    n1 = len(o1)
    n2 = len(o2)
    o = numpy.zeros(n1 + n2 - 1)
    for i in range(n1):
        for j in range(n2):
            o[i + j] += o1[i] * o2[j]
    return o


def print_finite_size(rups):
    """
    Used to print the number of finite-size ruptures
    """
    c = collections.Counter()
    for rup in rups:
        if rup.surface:
            c['%.2f' % rup.mag] += 1
    print(c)
    print('total finite size ruptures = ', sum(c.values()))


class PmapMaker(object):
    """
    A class to compute the PoEs from a given source
    """
    def __init__(self, cmaker, srcfilter, group):
        vars(self).update(vars(cmaker))
        self.cmaker = cmaker
        self.srcfilter = srcfilter
        self.N = len(self.srcfilter.sitecol.complete)
        try:
            self.sources = group.sources
        except AttributeError:  # already a list of sources
            self.sources = group
        self.src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
        self.rup_indep = getattr(group, 'rup_interdep', None) != 'mutex'
        self.fewsites = self.N <= cmaker.max_sites_disagg

    def count_bytes(self, ctxs):
        # # usuful for debugging memory issues
        rparams = len(self.cmaker.REQUIRES_RUPTURE_PARAMETERS)
        sparams = len(self.cmaker.REQUIRES_SITES_PARAMETERS) + 1
        dparams = len(self.cmaker.REQUIRES_DISTANCES)
        nbytes = 0
        for ctx in ctxs:
            nsites = len(ctx)
            nbytes += 8 * rparams
            nbytes += 8 * sparams * nsites
            nbytes += 8 * dparams * nsites
        return nbytes

    def gen_ctxs(self, src):
        sites = self.srcfilter.get_close_sites(src)
        if sites is None:
            return
        for ctx in self.cmaker.get_ctx_iter(src, sites):
            if self.cmaker.deltagetter:
                # adjust occurrence rates in case of aftershocks
                with self.cmaker.delta_mon:
                    delta = self.cmaker.deltagetter(src.id)
                    ctx.occurrence_rate += delta[ctx.rup_id]
            if hasattr(src, 'mutex_weight'):
                if ctx.weight.any():
                    ctx['weight'] *= src.mutex_weight
                else:
                    ctx['weight'] = src.mutex_weight
            if self.fewsites:  # keep rupdata in memory (before collapse)
                self.rupdata.append(ctx)
            yield ctx

    def _make_src_indep(self, pmap):
        # sources with the same ID
        cm = self.cmaker
        allctxs = []
        ctxs_mb = 0
        totlen = 0
        t0 = time.time()
        for src in self.sources:
            src.nsites = 0
            for ctx in self.gen_ctxs(src):
                ctxs_mb += ctx.nbytes / TWO20  # TWO20=1MB
                src.nsites += len(ctx)
                totlen += len(ctx)
                allctxs.append(ctx)
                if ctxs_mb > MAX_MB:
                    cm.update(pmap, concat(allctxs), self.rup_indep)
                    allctxs.clear()
                    ctxs_mb = 0
        if allctxs:
            cm.update(pmap, concat(allctxs), self.rup_indep)
            allctxs.clear()
        dt = time.time() - t0
        nsrcs = len(self.sources)
        for src in self.sources:
            self.source_data['src_id'].append(src.source_id)
            self.source_data['grp_id'].append(src.grp_id)
            self.source_data['nsites'].append(src.nsites)
            self.source_data['esites'].append(src.esites)
            self.source_data['nrupts'].append(src.num_ruptures)
            self.source_data['weight'].append(src.weight)
            self.source_data['ctimes'].append(
                dt * src.nsites / totlen if totlen else dt / nsrcs)
            self.source_data['taskno'].append(cm.task_no)
        return pmap

    def _make_src_mutex(self, pmap):
        # used in the Japan model, test case_27
        pmap_by_src = {}
        cm = self.cmaker
        for src in self.sources:
            t0 = time.time()
            pm = ProbabilityMap(pmap.sids, cm.imtls.size, len(cm.gsims))
            pm.fill(self.rup_indep)
            ctxs = list(self.gen_ctxs(src))
            nctxs = len(ctxs)
            nsites = sum(len(ctx) for ctx in ctxs)
            if nsites:
                cm.update(pm, ctxs, self.rup_indep)
            if hasattr(src, 'mutex_weight'):
                arr = 1. - pm.array if self.rup_indep else pm.array
                p = pm.new(arr * src.mutex_weight)
            else:
                p = pm
            if ':' in src.source_id:
                srcid = basename(src)
                if srcid in pmap_by_src:
                    pmap_by_src[srcid].array += p.array
                else:
                    pmap_by_src[srcid] = p
            else:
                pmap_by_src[src.source_id] = p
            dt = time.time() - t0
            self.source_data['src_id'].append(src.source_id)
            self.source_data['grp_id'].append(src.grp_id)
            self.source_data['nsites'].append(nsites)
            self.source_data['esites'].append(src.esites)
            self.source_data['nrupts'].append(nctxs)
            self.source_data['weight'].append(src.weight)
            self.source_data['ctimes'].append(dt)
            self.source_data['taskno'].append(cm.task_no)

        return pmap_by_src

    def make(self, pmap):
        dic = {}
        self.rupdata = []
        self.source_data = AccumDict(accum=[])
        grp_id = self.sources[0].grp_id
        if self.src_mutex or not self.rup_indep:
            pmap.fill(0)
            pmap_by_src = self._make_src_mutex(pmap)
            for source_id, pm in pmap_by_src.items():
                if self.src_mutex:
                    pmap.array += pm.array
                else:
                    pmap.array = 1. - (1-pmap.array) * (1-pm.array)
        else:
            self._make_src_indep(pmap)
        dic['cfactor'] = self.cmaker.collapser.cfactor
        dic['rup_data'] = concat(self.rupdata)
        dic['source_data'] = self.source_data
        dic['task_no'] = self.task_no
        dic['grp_id'] = grp_id
        if self.disagg_by_src and self.src_mutex:
            dic['pmap_by_src'] = pmap_by_src
        elif self.disagg_by_src:
            # all the sources in the group have the same source_id because
            # of the groupby(group, get_source_id) in classical.py
            srcid = basename(self.sources[0])
            dic['pmap_by_src'] = {srcid: pmap}
        return dic


class BaseContext(metaclass=abc.ABCMeta):
    """
    Base class for context object.
    """
    def __eq__(self, other):
        """
        Return True if ``other`` has same attributes with same values.
        """
        if isinstance(other, self.__class__):
            if self._slots_ == other._slots_:
                oks = []
                for s in self._slots_:
                    a, b = getattr(self, s, None), getattr(other, s, None)
                    if a is None and b is None:
                        ok = True
                    elif a is None and b is not None:
                        ok = False
                    elif a is not None and b is None:
                        ok = False
                    elif hasattr(a, 'shape') and hasattr(b, 'shape'):
                        if a.shape == b.shape:
                            ok = numpy.allclose(a, b)
                        else:
                            ok = False
                    else:
                        ok = a == b
                    oks.append(ok)
                return numpy.all(oks)
        return False


# mock of a site collection used in the tests and in the SMTK
class SitesContext(BaseContext):
    """
    Sites calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of the sites collection.
    Every GSIM class is required to declare what :attr:`sites parameters
    <GroundShakingIntensityModel.REQUIRES_SITES_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    # _slots_ is used in hazardlib check_gsim and in the SMTK
    def __init__(self, slots='vs30 vs30measured z1pt0 z2pt5'.split(),
                 sitecol=None):
        self._slots_ = slots
        if sitecol is not None:
            self.sids = sitecol.sids
            for slot in slots:
                setattr(self, slot, getattr(sitecol, slot))

    # used in the SMTK
    def __len__(self):
        return len(self.sids)


class DistancesContext(BaseContext):
    """
    Distances context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant distances between sites from the collection
    and the rupture. Every GSIM class is required to declare what
    :attr:`distance measures <GroundShakingIntensityModel.REQUIRES_DISTANCES>`
    does it need. Only those required values are calculated and made available
    in a result context object.
    """
    _slots_ = ('rrup', 'rx', 'rjb', 'rhypo', 'repi', 'ry0', 'rcdpp',
               'azimuth', 'hanging_wall', 'rvolc')

    def __init__(self, param_dist_pairs=()):
        for param, dist in param_dist_pairs:
            setattr(self, param, dist)

    def roundup(self, minimum_distance):
        """
        If the minimum_distance is nonzero, returns a copy of the
        DistancesContext with updated distances, i.e. the ones below
        minimum_distance are rounded up to the minimum_distance. Otherwise,
        returns the original DistancesContext unchanged.
        """
        if not minimum_distance:
            return self
        ctx = DistancesContext()
        for dist, array in vars(self).items():
            small_distances = array < minimum_distance
            if small_distances.any():
                array = numpy.array(array)  # make a copy first
                array[small_distances] = minimum_distance
                array.flags.writeable = False
            setattr(ctx, dist, array)
        return ctx


def get_dists(ctx):
    """
    Extract the distance parameters from a context.

    :returns: a dictionary dist_name -> distances
    """
    return {par: dist for par, dist in vars(ctx).items()
            if par in KNOWN_DISTANCES}


# used to produce a RuptureContext suitable for legacy code, i.e. for calls
# to .get_mean_and_stddevs, like for instance in the SMTK
def full_context(sites, rup, dctx=None):
    """
    :returns: a full RuptureContext with all the relevant attributes
    """
    self = RuptureContext()
    self.src_id = 0
    for par, val in vars(rup).items():
        setattr(self, par, val)
    if not hasattr(self, 'occurrence_rate'):
        self.occurrence_rate = numpy.nan
    if hasattr(sites, 'array'):  # is a SiteCollection
        for par in sites.array.dtype.names:
            setattr(self, par, sites[par])
    else:  # sites is a SitesContext
        for par, val in vars(sites).items():
            setattr(self, par, val)
    if dctx:
        for par, val in vars(dctx).items():
            setattr(self, par, val)
    return self


def get_mean_stds(gsim, ctx, imts, **kw):
    """
    :param gsim: a single GSIM or a a list of GSIMs
    :param ctx: a RuptureContext or a recarray of size N
    :param imts: a list of M IMTs
    :param kw: additional keyword arguments
    :returns:
        an array of shape (4, M, N) obtained by applying the
        given GSIM, ctx amd imts, or an array of shape (G, 4, M, N)
    """
    single = hasattr(gsim, 'compute')
    kw['imtls'] = {imt.string: [0] for imt in imts}
    cmaker = ContextMaker('*', [gsim] if single else gsim, kw)
    out = cmaker.get_mean_stds([ctx])  # (4, G, M, N)
    return out[:, 0] if single else out


# mock of a rupture used in the tests and in the SMTK
class RuptureContext(BaseContext):
    """
    Rupture calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of a single rupture. Every
    GSIM class is required to declare what :attr:`rupture parameters
    <GroundShakingIntensityModel.REQUIRES_RUPTURE_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    src_id = 0
    rup_id = 0
    _slots_ = (
        'mag', 'strike', 'dip', 'rake', 'ztor', 'hypo_lon', 'hypo_lat',
        'hypo_depth', 'width', 'hypo_loc', 'src_id', 'rup_id')

    def __init__(self, param_pairs=()):
        for param, value in param_pairs:
            setattr(self, param, value)

    def size(self):
        """
        If the context is a multi rupture context, i.e. it contains an array
        of magnitudes and it refers to a single site, returns the size of
        the array, otherwise returns 1.
        """
        nsites = len(self.sids)
        if nsites == 1 and isinstance(self.mag, numpy.ndarray):
            return len(self.mag)
        return nsites

    # used in acme_2019
    def __len__(self):
        return len(self.sids)

    def roundup(self, minimum_distance):
        """
        If the minimum_distance is nonzero, returns a copy of the
        RuptureContext with updated distances, i.e. the ones below
        minimum_distance are rounded up to the minimum_distance. Otherwise,
        returns the original.
        """
        if not minimum_distance:
            return self
        ctx = copy.copy(self)
        for dist, array in vars(self).items():
            if dist in KNOWN_DISTANCES:
                small_distances = array < minimum_distance
                if small_distances.any():
                    array = numpy.array(array)  # make a copy first
                    array[small_distances] = minimum_distance
                    array.flags.writeable = False
                setattr(ctx, dist, array)
        return ctx


class Effect(object):
    """
    Compute the effect of a rupture of a given magnitude and distance.

    :param effect_by_mag: a dictionary magstring -> intensities
    :param dists: array of distances, one per each intensity
    :param cdist: collapse distance
    """
    def __init__(self, effect_by_mag, dists, collapse_dist=None):
        self.effect_by_mag = effect_by_mag
        self.dists = dists
        self.nbins = len(dists)

    def collapse_value(self, collapse_dist):
        """
        :returns: intensity at collapse distance
        """
        # get the maximum magnitude with a cutoff at 7
        for mag in self.effect_by_mag:
            if mag > '7.00':
                break
        effect = self.effect_by_mag[mag]
        idx = numpy.searchsorted(self.dists, collapse_dist)
        return effect[idx-1 if idx == self.nbins else idx]

    def __call__(self, mag, dist):
        di = numpy.searchsorted(self.dists, dist)
        if di == self.nbins:
            di = self.nbins
        eff = self.effect_by_mag['%.2f' % mag][di]
        return eff

    # this is used to compute the magnitude-dependent pointsource_distance
    def dist_by_mag(self, intensity):
        """
        :returns: a dict magstring -> distance
        """
        dst = {}  # magnitude -> distance
        for mag, intensities in self.effect_by_mag.items():
            if intensity < intensities.min():
                dst[mag] = self.dists[-1]  # largest distance
            elif intensity > intensities.max():
                dst[mag] = self.dists[0]  # smallest distance
            else:
                dst[mag] = interp1d(intensities, self.dists)(intensity)
        return dst


def get_effect_by_mag(mags, sitecol1, gsims_by_trt, maximum_distance, imtls):
    """
    :param mags: an ordered list of magnitude strings with format %.2f
    :param sitecol1: a SiteCollection with a single site
    :param gsims_by_trt: a dictionary trt -> gsims
    :param maximum_distance: an IntegrationDistance object
    :param imtls: a DictArray with intensity measure types and levels
    :returns: a dict magnitude-string -> array(#dists, #trts)
    """
    trts = list(gsims_by_trt)
    ndists = 51
    gmv = numpy.zeros((len(mags), ndists, len(trts)))
    param = dict(maximum_distance=maximum_distance, imtls=imtls)
    for t, trt in enumerate(trts):
        dist_bins = maximum_distance.get_dist_bins(trt, ndists)
        cmaker = ContextMaker(trt, gsims_by_trt[trt], param)
        gmv[:, :, t] = cmaker.max_intensity(sitecol1, F64(mags), dist_bins)
    return dict(zip(mags, gmv))


def read_cmakers(dstore, full_lt=None):
    """
    :param dstore: a DataStore-like object
    :param full_lt: a FullLogicTree instance, if given
    :returns: a list of ContextMaker instance, one per source group
    """
    from openquake.hazardlib.site_amplification import AmplFunction
    cmakers = []
    oq = dstore['oqparam']
    full_lt = full_lt or dstore['full_lt']
    trt_smrs = dstore['trt_smrs'][:]
    toms = decode(dstore['toms'][:])
    rlzs_by_gsim_list = full_lt.get_rlzs_by_gsim_list(trt_smrs)
    trts = list(full_lt.gsim_lt.values)
    num_eff_rlzs = len(full_lt.sm_rlzs)
    if 'source_info' in dstore:
        weight = dstore.read_df('source_info')[
            ['grp_id', 'weight']].groupby('grp_id').sum().weight.to_numpy()
    else:
        weight = [1] * len(rlzs_by_gsim_list)
    start = 0
    aftershock = 'delta_rates' in dstore
    for grp_id, rlzs_by_gsim in enumerate(rlzs_by_gsim_list):
        trti = trt_smrs[grp_id][0] // num_eff_rlzs
        trt = trts[trti]
        if ('amplification' in oq.inputs and
                oq.amplification_method == 'kernel'):
            df = AmplFunction.read_df(oq.inputs['amplification'])
            oq.af = AmplFunction.from_dframe(df)
        else:
            oq.af = None
        oq.mags_by_trt = {k: decode(v[:])
                          for k, v in dstore['source_mags'].items()}
        cmaker = ContextMaker(trt, rlzs_by_gsim, oq)
        if aftershock:
            cmaker.deltagetter = DeltaRatesGetter(dstore)
        cmaker.tom = valid.occurrence_model(toms[grp_id])
        cmaker.trti = trti
        cmaker.start = start
        cmaker.grp_id = grp_id
        cmaker.weight = weight[grp_id]
        start += len(rlzs_by_gsim)
        cmakers.append(cmaker)
    return cmakers


# used in event_based
def read_cmaker(dstore, trt_smr):
    """
    :param dstore: a DataStore-like object
    :returns: a ContextMaker instance
    """
    oq = dstore['oqparam']
    full_lt = dstore['full_lt']
    trts = list(full_lt.gsim_lt.values)
    trt = trts[trt_smr // len(full_lt.sm_rlzs)]
    rlzs_by_gsim = full_lt._rlzs_by_gsim(trt_smr)
    return ContextMaker(trt, rlzs_by_gsim, oq)
