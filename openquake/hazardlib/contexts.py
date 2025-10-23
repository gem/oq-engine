# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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

import os
import abc
import copy
import time
import logging
import warnings
import itertools
import operator
import collections
import numpy
import shapely
from scipy.interpolate import interp1d

from openquake.baselib import config
from openquake.baselib.general import getsizeof
from openquake.baselib.general import (
    AccumDict, DictArray, RecordBuilder, split_in_slices, block_splitter,
    sqrscale)
from openquake.baselib.performance import Monitor, split_array, kround0, compile
from openquake.baselib.python3compat import decode
from openquake.hazardlib import valid, imt as imt_module
from openquake.hazardlib.const import StdDev, OK_COMPONENTS
from openquake.hazardlib.tom import NegativeBinomialTOM, PoissonTOM
from openquake.hazardlib.stats import ndtr, truncnorm_sf
from openquake.hazardlib.site import SiteCollection, site_param_dt
from openquake.hazardlib.calc.filters import (
    SourceFilter, IntegrationDistance, magdepdist,
    get_dparam, get_distances, getdefault, MINMAG, MAXMAG)
from openquake.hazardlib.map_array import MapArray
from openquake.hazardlib.geo import multiline
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.planar import (
    project, project_back, get_distances_planar)

U8 = numpy.uint8
I32 = numpy.int32
U32 = numpy.uint32
F16 = numpy.float16
F32 = numpy.float32
F64 = numpy.float64
TWO20 = 2**20
TWO16 = 2**16
TWO24 = 2**24
TWO32 = 2**32
STD_TYPES = (StdDev.TOTAL, StdDev.INTER_EVENT, StdDev.INTRA_EVENT)
KNOWN_DISTANCES = frozenset('''rrup rx_ry0 rx ry0 rjb rhypo repi rcdpp azimuth
azimuthcp rvolc clon_clat clon clat'''.split())
NUM_BINS = 256
DIST_BINS = sqrscale(80, 1000, NUM_BINS)
MEA = 0
STD = 1
EPS = float(os.environ.get('OQ_SAMPLE_SITES', 1))
bymag = operator.attrgetter('mag')
# These coordinates were provided by M Gerstenberger (personal
# communication, 10 August 2018)
cshm_polygon = shapely.geometry.Polygon([(171.6, -43.3), (173.2, -43.3),
                                         (173.2, -43.9), (171.6, -43.9)])


def _get(surfaces, param, dparam, mask=slice(None)):
    arr = numpy.array([dparam[sec.idx, param][mask] for sec in surfaces])
    return arr  # shape (S, N, ...)


def _get_tu(rup, dparam, mask):
    tor = rup.surface.tor
    arr = _get(rup.surface.surfaces, 'tuw', dparam, mask)
    S, N = arr.shape[:2]
    # keep the flipped values and then reorder the surface indices
    # arr has shape (S, N, 2, 3) where 2 refer to the flipping
    tuw = numpy.zeros((S, N, 3), F32)
    for s in range(S):
        idx = tor.soidx[s]
        flip = int(tor.flipped[idx])
        tuw[s] = arr[idx, :, flip, :]  # shape (N, 3)
    return multiline.get_tu(tor.shift, tuw)


def set_distances(ctx, rup, r_sites, param, dparam, mask, tu):
    """
    Set the distance attributes on the context; also manages paired
    attributes like clon_lat and rx_ry0.
    """
    if dparam is None:
        # no multifault
        dists = get_distances(rup, r_sites, param)
        if '_' in param:
            p0, p1 = param.split('_')  # clon_clat
            setattr(ctx, p0, dists[:, 0])
            setattr(ctx, p1, dists[:, 1])
        else:
            setattr(ctx, param, dists)
    else:
        # use the MultiLine object
        u_max = rup.surface.msparam['u_max']
        if param in ('rx', 'ry0'):
            tut, uut = tu
            '''
            # sanity check with the right parameters t, u
            t, u = rup.surface.tor.get_tu(r_sites)
            numpy.testing.assert_allclose(tut, t)
            numpy.testing.assert_allclose(uut, u)
            '''
            if param == 'rx':
                ctx.rx = tut
            elif param == 'ry0':
                neg = uut < 0
                ctx.ry0[neg] = numpy.abs(uut[neg])
                big = uut > u_max
                ctx.ry0[big] = uut[big] - u_max
        elif param == 'rjb':
            rjbs = _get(rup.surface.surfaces, 'rjb', dparam, mask)
            ctx['rjb'] = numpy.min(rjbs, axis=0)
            '''
            # sanity check with the right rjb
            rjb = rup.surface.get_joyner_boore_distance(r_sites)
            numpy.testing.assert_allclose(ctx.rjb, rjb)
            '''
        elif param == 'clon_clat':
            coos = _get(rup.surface.surfaces, 'clon_clat', dparam, mask)
            # shape (numsections, numsites, 3)
            m = Mesh(coos[:, :, 0], coos[:, :, 1]).get_closest_points(r_sites)
            # shape (numsites, 3)
            ctx['clon'] = m.lons
            ctx['clat'] = m.lats


def round_dist(dst):
    idx = numpy.searchsorted(DIST_BINS, dst)
    idx[idx == NUM_BINS] -= 1
    return DIST_BINS[idx]


def is_modifiable(gsim):
    """
    :returns: True if it is a ModifiableGMPE
    """
    return hasattr(gsim, 'gmpe') and hasattr(gsim, 'params')


def concat(ctxs):
    """
    Concatenate context arrays.
    :returns: [] or [poisson_ctx] or [nonpoisson_ctx, ...]
    """
    if not ctxs:
        return []
    ctx = ctxs[0]
    out = []
    # if ctx has probs_occur, it is assumed to be non-poissonian
    if hasattr(ctx, 'probs_occur') and ctx.probs_occur.shape[1] >= 1:
        # case 27, 29, 62, 65, 75, 78, 80
        for shp in set(ctx.probs_occur.shape[1] for ctx in ctxs):
            p_array = [p for p in ctxs if p.probs_occur.shape[1] == shp]
            out.append(numpy.concatenate(p_array).view(numpy.recarray))
    else:
        out.append(numpy.concatenate(ctxs).view(numpy.recarray))
    return out


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


class Oq(object):
    """
    A mock for OqParam
    """
    af = None
    impact = False
    cross_correl = None
    mea_tau_phi = False
    split_sources = True
    use_rates = False
    with_betw_ratio = None
    infer_occur_rates = False
    inputs = ()

    def __init__(self, **hparams):
        vars(self).update(hparams)

    @property
    def min_iml(self):
        try:
            imtls = self.imtls
        except AttributeError:
            imtls = self.hazard_imtls
        return numpy.array([1E-10 for imt in imtls])

    def get_reqv(self):
        if 'reqv' not in self.inputs:
            return
        return {key: valid.RjbEquivalent(value)
                for key, value in self.inputs['reqv'].items()}


# same speed as performance.kround, round more
def kround1(ctx, kfields):
    kdist = 2. * ctx.mag**2  # heuristic collapse distance from 32 to 200 km
    close = ctx.rrup < kdist
    far = ~close
    out = numpy.zeros(len(ctx), [(k, ctx.dtype[k]) for k in kfields])
    for kfield in kfields:
        kval = ctx[kfield]
        if kfield == 'vs30':
            out[kfield][close] = numpy.round(kval[close])  # round less
            out[kfield][far] = numpy.round(kval[far], 1)  # round more
        elif kval.dtype == F64 and kfield != 'mag':
            out[kfield][close] = F16(kval[close])  # round less
            out[kfield][far] = numpy.round(kval[far])  # round more
        else:
            out[kfield] = ctx[kfield]
    return out


def kround2(ctx, kfields):
    kdist = 5. * ctx.mag**2  # from 80 to 500 km
    close = ctx.rrup < kdist
    far = ~close
    out = numpy.zeros(len(ctx), [(k, ctx.dtype[k]) for k in kfields])
    for kfield in kfields:
        kval = ctx[kfield]
        if kfield == 'rx':   # can be negative
            out[kfield] = numpy.round(kval)
        elif kfield in KNOWN_DISTANCES:
            out[kfield][close] = numpy.ceil(kval[close])  # round to 1 km
            out[kfield][far] = round_dist(kval[far])  # round more
        elif kfield == 'vs30':
            out[kfield][close] = numpy.round(kval[close])  # round less
            out[kfield][far] = numpy.round(kval[far], 1)  # round more
        elif kval.dtype == F64 and kfield != 'mag':
            out[kfield][close] = F16(kval[close])  # round less
            out[kfield][far] = numpy.round(kval[far])  # round more
        else:
            out[kfield] = ctx[kfield]
    return out


kround = {0: kround0, 1: kround1, 2: kround2}


class FarAwayRupture(Exception):
    """Raised if the rupture is outside the maximum distance for all sites"""


def get_num_distances(gsims):
    """
    :returns: the number of distances required for the given GSIMs
    """
    dists = set()
    for gsim in gsims:
        dists.update(gsim.REQUIRES_DISTANCES)
    return len(dists)


# NB: minimum_magnitude is ignored
def _interp(param, name, trt):
    try:
        mdd = param[name]
    except KeyError:
        return magdepdist([(MINMAG, 1000), (MAXMAG, 1000)])
    if isinstance(mdd, IntegrationDistance):
        return mdd(trt)
    elif isinstance(mdd, dict):
        if mdd:
            magdist = getdefault(mdd, trt)
        else:
            magdist = [(MINMAG, 1000), (MAXMAG, 1000)]
        return magdepdist(magdist)
    return mdd


def simple_cmaker(gsims, imts, **params):
    """
    :returns: a simplified ContextMaker for use in the tests
    """
    dic = dict(imtls={imt: [0] for imt in imts})
    dic.update(**params)
    return ContextMaker('*', gsims, dic)


# ############################ genctxs ################################## #

# generator of quintets (rup_index, mag, planar_array, sites)
def _quintets(cmaker, src, sitecol):
    with cmaker.ir_mon:
        # building planar geometries
        planardict = src.get_planar(cmaker.shift_hypo)

    magdist = {mag: cmaker.maximum_distance(mag) for mag in planardict}
    # cmaker.maximum_distance(mag) can be 0 if outside the mag range
    maxmag = max(mag for mag, dist in magdist.items() if dist > 0)
    maxdist = magdist[maxmag]
    cdist = sitecol.get_cdist(src.location)
    # NB: having a decent max_radius is essential for performance!
    mask = cdist <= maxdist + src.max_radius(maxdist)
    sitecol = sitecol.filter(mask)
    if sitecol is None:
        return

    minmag = cmaker.maximum_distance.x[0]
    maxmag = cmaker.maximum_distance.x[-1]
    # splitting by magnitude
    if src.count_nphc() == 1:
        # one rupture per magnitude
        for m, (mag, pla) in enumerate(planardict.items()):
            if minmag <= mag <= maxmag:
                yield m, mag, magdist[mag], pla, sitecol
    else:
        for m, rup in enumerate(src.iruptures()):
            mag = rup.mag
            if mag > maxmag or mag < minmag:
                continue
            mdist = magdist[mag]
            arr = [rup.surface.array.reshape(-1, 3)]  # planar
            pla = planardict[mag]
            # NB: having a good psdist is essential for performance!
            psdist = src.get_psdist(m, mag, cmaker.pointsource_distance,
                                    magdist)
            close = sitecol.filter(cdist[mask] <= psdist)
            far = sitecol.filter(cdist[mask] > psdist)
            if cmaker.fewsites:
                if close is None:  # all is far, common for small mag
                    yield m, mag, mdist, arr, sitecol
                else:  # something is close
                    yield m, mag, mdist, pla, sitecol
            else:  # many sites
                if close is None:  # all is far
                    yield m, mag, mdist, arr, far
                elif far is None:  # all is close
                    yield m, mag, mdist, pla, close
                else:  # some sites are far, some are close
                    yield m, mag, mdist, arr, far
                    yield m, mag, mdist, pla, close


# helper used to populate contexts for planar ruptures
def _get_ctx_planar(cmaker, builder, mag, mrate, magi, planar, sites,
                    src_id, src_offset, tom):
    zeroctx = builder.zeros((len(planar), len(sites)))  # shape (N, U)
    if cmaker.fewsites:
        offset = src_offset + magi * len(planar)
        rup_ids = zeroctx['rup_id'].T  # numpy trick, shape (U, N)
        rup_ids[:] = numpy.arange(offset, offset+len(planar))

    # computing distances
    rrup, xx, yy = project(planar, sites.xyz)  # (3, U, N)
    # get the closest points on the surface
    if cmaker.fewsites or 'clon' in cmaker.REQUIRES_DISTANCES:
        closest = project_back(planar, xx, yy)  # (3, U, N)
    # set distances
    zeroctx['rrup'] = rrup
    for par in cmaker.REQUIRES_DISTANCES - {'rrup'}:
        zeroctx[par] = get_distances_planar(planar, sites, par)
    for par in cmaker.REQUIRES_DISTANCES:
        dst = zeroctx[par]
        if cmaker.minimum_distance:
            dst[dst < cmaker.minimum_distance] = cmaker.minimum_distance

    # ctx has shape (U, N), ctxt (N, U)
    ctxt = zeroctx.T  # smart trick taking advantage of numpy magic
    ctxt['src_id'] = src_id

    # setting rupture parameters
    for par in cmaker.ruptparams:
        if par == 'mag':
            ctxt[par] = mag
        elif par == 'occurrence_rate':
            ctxt[par] = mrate * planar.wlr[:, 2]  # shape U-> (N, U)
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

    if cmaker.fewsites:
        zeroctx['clon'] = closest[0]
        zeroctx['clat'] = closest[1]

    # setting site parameters
    for par in cmaker.siteparams:
        zeroctx[par] = sites.array[par]  # shape N-> (U, N)
    if hasattr(tom, 'get_pmf'):  # NegativeBinomialTOM
        # read Probability Mass Function from model and reshape it
        # into predetermined shape of probs_occur
        pmf = tom.get_pmf(planar.wlr[:, 2] * mrate,
                          n_max=zeroctx['probs_occur'].shape[2])
        zeroctx['probs_occur'] = pmf[:, numpy.newaxis, :]

    return zeroctx.flatten()  # shape N*U


def genctxs_Pp(src, sitecol, cmaker):
    """
    Context generator for point sources and collapsed point sources
    """
    dd = cmaker.defaultdict.copy()
    tom = getattr(src, 'temporal_occurrence_model', None)

    if tom and isinstance(tom, NegativeBinomialTOM):
        if hasattr(src, 'pointsources'):  # CollapsedPointSource
            maxrate = max(max(ps.mfd.occurrence_rates)
                          for ps in src.pointsources)
        else:  # regular source
            maxrate = max(src.mfd.occurrence_rates)
        p_size = tom.get_pmf(maxrate).shape[1]
        dd['probs_occur'] = numpy.zeros(p_size)
    else:
        dd['probs_occur'] = numpy.zeros(0)

    builder = RecordBuilder(**dd)
    cmaker.siteparams = [par for par in sitecol.array.dtype.names
                         if par in dd]
    cmaker.ruptparams = cmaker.REQUIRES_RUPTURE_PARAMETERS | {'occurrence_rate'}

    mrate = dict(src.get_annual_occurrence_rates())
    for magi, mag,  magdist, planars, sites in _quintets(cmaker, src, sitecol):
        if not planars:
            continue
        elif len(planars) > 1:  # when using ps_grid_spacing
            pla = numpy.concatenate(planars).view(numpy.recarray)
            pla.wlr[:, 2] /= len(planars)  # average rate
        else:
            pla = planars[0]
        # building contexts
        ctx = _get_ctx_planar(cmaker, builder, mag, mrate[mag], magi,
                              pla, sites, src.id, src.offset, tom)
        ctxt = ctx[ctx.rrup < magdist]
        if len(ctxt):
            yield ctxt


def _build_dparam(src, sitecol, cmaker):
    dparams = {'rjb', 'tuw'}
    if cmaker.fewsites:
        dparams |= {'clon_clat'}
    sections = src.get_sections(src.get_unique_idxs())
    out = {}
    for sec in sections:
        out[sec.idx, 'rrup'] = get_dparam(sec, sitecol, 'rrup')
        for param in dparams:
            out[sec.idx, param] = get_dparam(sec, sitecol, param)
    cmaker.dparam_mb = max(cmaker.dparam_mb, getsizeof(out) / TWO20)
    cmaker.source_mb += getsizeof(src) / TWO20
    return out


# this is the critical function for the performance of the classical calculator
# the performance is dominated by the CPU cache, i.e. large arrays are slow
# the only way to speedup is to reduce the maximum_distance, then the array
# will become shorter in the N dimension (number of affected sites), or to
# collapse the ruptures, then truncnorm_sf will be called less times
@compile("(float64[:,:,:], float64[:,:], float64, float32[:,:])")
def _set_poes(mean_std, loglevels, phi_b, out):
    L1 = loglevels.size // len(loglevels)
    for m, levels in enumerate(loglevels):
        mL1 = m * L1
        mea, std = mean_std[:, m]  # shape N
        for lvl, iml in enumerate(levels):
            out[mL1 + lvl] = truncnorm_sf(phi_b, (iml - mea) / std)

# ############################ ContextMaker ############################### #


def _fix(gsimdict, betw):
    if betw:
        out = {}
        for gsim, uints in gsimdict.items():
            if len(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES) == 1:
                out[valid.modified_gsim(gsim, add_between_within_stds=betw)] \
                    = uints
            else:
                out[gsim] = uints
        return out
    return gsimdict


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
    scenario = False
    deltagetter = None
    fewsites = False
    ilabel = None
    tom = None
    cluster = None  # set in RmapMaker
    dparam_mb = 0  # set in build_dparam
    source_mb = 0  # set in build_dparam

    def __init__(self, trt, gsims, oq, monitor=Monitor(), extraparams=()):
        self.trt = trt
        if isinstance(oq, dict):
            # this happens when instantiating RuptureData in extract.py
            param = oq
            oq = Oq(**param)
            self.mags = param.get('mags', ())  # list of strings %.2f
            self.cross_correl = param.get('cross_correl')  # cond_spectra_test
        else:  # OqParam
            param = vars(oq)
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

        if oq.with_betw_ratio:
            betw_ratio = {'with_betw_ratio': oq.with_betw_ratio}
        elif oq.impact:
            betw_ratio = {'with_betw_ratio': 1.7}  # same as in GEESE
        else:
            betw_ratio = {}
        if isinstance(gsims, dict):
            self.gsims = _fix(gsims, betw_ratio)
        else:
            self.gsims = _fix({gsim: U32([i]) for i, gsim in enumerate(gsims)},
                              betw_ratio)
        # NB: the gid array can be overridden later on
        self.gid = numpy.arange(len(gsims), dtype=numpy.uint16)
        self.oq = oq
        self.monitor = monitor
        self._init1(param)
        self._init2(param, extraparams)
        self.set_imts_conv()
        self.init_monitoring(self.monitor)

    def _init1(self, param):
        if 'poes' in param:
            self.poes = param['poes']
        if 'imtls' in param:
            for imt in param['imtls']:
                if not isinstance(imt, str):
                    raise TypeError('Expected string, got %s' % type(imt))
            self.imtls = param['imtls']
        elif 'hazard_imtls' in param:
            self.imtls = imt_module.dictarray(param['hazard_imtls'])
        elif not hasattr(self, 'imtls'):
            raise KeyError('Missing imtls in ContextMaker!')
        self.cache_distances = param.get('cache_distances', False)
        self.max_sites_disagg = param.get('max_sites_disagg', 10)
        self.time_per_task = param.get('time_per_task', 60)
        self.collapse_level = int(param.get('collapse_level', -1))
        self.disagg_by_src = param.get('disagg_by_src', False)
        self.horiz_comp = param.get('horiz_comp_to_geom_mean', False)
        self.maximum_distance = _interp(param, 'maximum_distance', self.trt)
        if 'pointsource_distance' not in param:
            self.pointsource_distance = float(
                config.performance.pointsource_distance)
        else:
            self.pointsource_distance = getdefault(
                param['pointsource_distance'], self.trt)
        self.minimum_distance = param.get('minimum_distance', 0)
        self.investigation_time = param.get('investigation_time')
        self.ses_seed = param.get('ses_seed', 42)
        self.ses_per_logic_tree_path = param.get('ses_per_logic_tree_path', 1)
        self.truncation_level = param.get('truncation_level', 99.)
        self.phi_b = ndtr(self.truncation_level)
        self.num_epsilon_bins = param.get('num_epsilon_bins', 1)
        self.disagg_bin_edges = param.get('disagg_bin_edges', {})
        self.ps_grid_spacing = param.get('ps_grid_spacing')
        self.split_sources = self.oq.split_sources
        for gsim in self.gsims:
            if hasattr(gsim, 'set_tables'):
                if len(self.mags) == 0 and not is_modifiable(gsim):
                    raise ValueError(
                        'You must supply a list of magnitudes as 2-digit '
                        'strings, like mags=["6.00", "6.10", "6.20"]')
                gsim.set_tables(self.mags, self.imtls)

    def _init2(self, param, extraparams):
        for req in self.REQUIRES:
            reqset = set()
            for gsim in self.gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
                if getattr(self.oq, 'af', None) and req == 'SITES_PARAMETERS':
                    reqset.add('ampcode')
                if is_modifiable(gsim) and req == 'SITES_PARAMETERS':
                    reqset.add('vs30')  # required by the ModifiableGMPE
                    reqset.update(gsim.gmpe.REQUIRES_SITES_PARAMETERS)
                    if 'apply_swiss_amplification' in gsim.params:
                        reqset.add('amplfactor')
                    if ('apply_swiss_amplification_sa' in gsim.params):
                        reqset.add('ch_ampl03')
                        reqset.add('ch_ampl06')
                        reqset.add('ch_phis2s03')
                        reqset.add('ch_phis2s06')
                        reqset.add('ch_phiss03')
                        reqset.add('ch_phiss06')
            setattr(self, 'REQUIRES_' + req, reqset)
        self.min_iml = self.oq.min_iml
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
        dic['src_id'] = I32(0)
        dic['rup_id'] = U32(0)
        dic['sids'] = U32(0)
        dic['rrup'] = F64(0)
        dic['occurrence_rate'] = F64(0)
        self.defaultdict = dic
        self.shift_hypo = param.get('shift_hypo')

    def init_monitoring(self, monitor):
        # instantiating child monitors, may be called in the workers
        self.pla_mon = monitor('planar contexts', measuremem=False)
        self.ctx_mon = monitor('nonplanar contexts', measuremem=False)
        self.gmf_mon = monitor('computing mean_std', measuremem=False)
        self.poe_mon = monitor('get_poes', measuremem=False)
        self.ir_mon = monitor('iter_ruptures', measuremem=False)
        self.sec_mon = monitor('building dparam', measuremem=False)
        self.delta_mon = monitor('getting delta_rates', measuremem=False)
        self.clu_mon = monitor('cluster loop', measuremem=True)
        self.task_no = getattr(monitor, 'task_no', 0)
        self.out_no = getattr(monitor, 'out_no', self.task_no)
        self.cfactor = numpy.zeros(2)

    def copy(self, **kw):
        """
        :returns: a copy of the ContextMaker with modified attributes
        """
        new = copy.copy(self)
        for k, v in kw.items():
            setattr(new, k, v)
        if 'imtls' in kw:
            new.set_imts_conv()
        return new

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
        conversion (if any). Also set the .loglevels.
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
            if not imc:  # for GMPETables
                continue
            elif imc.name == 'GEOMETRIC_MEAN':
                pass  # nothing to do
            elif imc.name in OK_COMPONENTS:
                dic = {imt: imc.apply_conversion(imt) for imt in self.imts}
                self.conv[gsim].update(dic)
            else:
                logging.info(f'Conversion from {imc.name} not applicable to'
                             f' {gsim.__class__.__name__}')

    def split(self, blocksize):
        """
        Split the ContextMaker by blocks of GSIMs
        """
        for gid, wei, gsims in zip(block_splitter(self.gid, blocksize),
                                   block_splitter(self.wei, blocksize),
                                   block_splitter(self.gsims, blocksize)):
            new = copy.copy(self)
            new.gsims = gsims
            new.gid = gid
            new.wei = wei
            yield new

    def horiz_comp_to_geom_mean(self, mean_stds, gsim):
        """
        This function converts ground-motion obtained for a given description
        of horizontal component into ground-motion values for geometric_mean.

        The conversion equations used are from:
            - Beyer and Bommer (2006): for arithmetic mean, GMRot and random
            - Boore and Kishida (2017): for RotD50
        """
        if not self.conv[gsim]:
            return
        for m, imt in enumerate(self.imts):
            me, si, _ta, _ph = mean_stds[:, m]
            conv_median, conv_sigma, rstd = self.conv[gsim][imt]
            me[:] = numpy.log(numpy.exp(me) / conv_median)
            si[:] = ((si**2 - conv_sigma**2) / rstd**2)**0.5

    @property
    def Z(self):
        """
        :returns: the number of realizations associated to self
        """
        return sum(len(rlzs) for rlzs in self.gsims.values())

    def new_ctx(self, size):
        """
        :returns: a recarray of the given size full of zeros
        """
        return RecordBuilder(**self.defaultdict).zeros(size)

    def recarray(self, ctxs):
        """
        :params ctxs: a non-empty list of homogeneous contexts
        :returns: a recarray, possibly collapsed
        """
        assert ctxs
        dd = self.defaultdict.copy()
        if not hasattr(ctxs[0], 'probs_occur'):
            for ctx in ctxs:
                ctx.probs_occur = numpy.zeros(0)
            np = 0
        else:
            shps = [ctx.probs_occur.shape for ctx in ctxs]
            np = max(i[1] if len(i) > 1 else i[0] for i in shps)
        dd['probs_occur'] = numpy.zeros(np)
        C = sum(len(ctx) for ctx in ctxs)
        ra = RecordBuilder(**dd).zeros(C)
        start = 0
        for ctx in ctxs:
            if self.minimum_distance:
                for name in self.REQUIRES_DISTANCES:
                    array = ctx[name]
                    small_distances = array < self.minimum_distance
                    if small_distances.any():
                        array = numpy.array(array)  # make a copy first
                        array[small_distances] = self.minimum_distance
                        ctx[name] = array
            slc = slice(start, start + len(ctx))
            for par in dd:
                if par == 'rup_id':
                    val = getattr(ctx, par)
                else:
                    val = getattr(ctx, par, numpy.nan)
                if par == 'clon_clat':
                    ra['clon'][slc] = ctx.clon
                    ra['clat'][slc] = ctx.clat
                else:
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

    def from_planar(self, rup, hdist, step, point='TC', toward_azimuth=90.,
                    direction='positive'):
        """
        :param rup:
            a BaseRupture instance with a PlanarSurface and site parameters

        :returns: a context array for the sites around the rupture
        """
        sitecol = SiteCollection.from_planar(
            rup, point='TC', toward_azimuth=toward_azimuth,
            direction=direction, hdist=hdist, step=step,
            req_site_params=self.REQUIRES_SITES_PARAMETERS)
        ctxs = list(self.genctxs([rup], sitecol, src_id=0))
        return self.recarray(ctxs)

    def from_srcs(self, srcs, sitecol):
        # used in disagg.disaggregation
        """
        :param srcs: a list of Source objects
        :param sitecol: a SiteCollection instance
        :returns: a list of context arrays
        """
        ctxs = []
        srcfilter = SourceFilter(sitecol, self.maximum_distance)
        for i, src in enumerate(srcs):
            if src.id == -1:  # not set yet
                src.id = i
            sites = srcfilter.get_close_sites(src)
            if sites is not None:
                ctxs.extend(self.get_ctx_iter(src, sites))
        return concat(ctxs)

    def get_rparams(self, rup):
        """
        :returns: a dictionary with the rupture parameters
        """
        dic = {}
        if hasattr(self, 'dparam') and self.dparam:
            msparam = rup.surface.msparam
        else:
            msparam = None
        for param in self.REQUIRES_RUPTURE_PARAMETERS:
            if param == 'mag':
                value = numpy.round(rup.mag, 3)
            elif param == 'strike':
                if msparam:
                    value = msparam['strike']
                else:
                    value = rup.surface.get_strike()
            elif param == 'dip':
                if msparam:
                    value = msparam['dip']
                else:
                    value = rup.surface.get_dip()
            elif param == 'rake':
                value = rup.rake
            elif param == 'ztor':
                if msparam:
                    value = msparam['ztor']
                else:
                    value = rup.surface.get_top_edge_depth()
            elif param == 'hypo_lon':
                value = rup.hypocenter.longitude
            elif param == 'hypo_lat':
                value = rup.hypocenter.latitude
            elif param == 'hypo_depth':
                value = rup.hypocenter.depth
            elif param == 'width':
                if msparam:
                    value = msparam['width']
                else:
                    value = rup.surface.get_width()
            elif param == 'in_cshm':
                # used in McVerry and Bradley GMPEs
                if rup.surface:
                    # this is really expensive
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
                if msparam:
                    value = msparam['zbot']
                elif rup.surface and hasattr(rup, 'surfaces'):
                    value = rup.surface.zbot
                elif rup.surface:
                    value = rup.surface.mesh.depths.max()
                else:
                    value = rup.hypocenter.depth
            else:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (type(self).__name__, param))
            dic[param] = value
        dic['occurrence_rate'] = getattr(rup, 'occurrence_rate', numpy.nan)
        if hasattr(rup, 'temporal_occurrence_model'):
            if isinstance(rup.temporal_occurrence_model, NegativeBinomialTOM):
                dic['probs_occur'] = rup.temporal_occurrence_model.get_pmf(
                    rup.occurrence_rate)
        elif hasattr(rup, 'probs_occur'):
            dic['probs_occur'] = rup.probs_occur

        return dic

    def genctxs(self, same_mag_rups, sites, src_id):
        """
        :params same_mag_rups: a list of ruptures
        :param sites: a (filtered) site collection
        :param src_id: source index
        :yields: a context array for each rupture
        """
        magdist = self.maximum_distance(same_mag_rups[0].mag)
        dparam = getattr(self, 'dparam', None)
        for rup in same_mag_rups:
            if dparam:
                rrups = _get(rup.surface.surfaces, 'rrup', dparam)
                rrup = numpy.min(rrups, axis=0)
            else:
                rrup = get_distances(rup, sites, 'rrup')
            mask = rrup <= magdist
            if not mask.any():
                continue

            r_sites = sites.filter(mask)
            # to debug you can insert here
            # print(rup.surface.tor.get_tuw_df(r_sites))
            # import pdb; pdb.set_trace()

            ''' # sanity check
            true_rrup = rup.surface.get_min_distance(r_sites)
            numpy.testing.assert_allclose(true_rrup, rrup[mask])
            '''
            rparams = self.get_rparams(rup)
            dd = self.defaultdict.copy()
            try:
                po = rparams['probs_occur']
            except KeyError:
                dd['probs_occur'] = numpy.zeros(0)
            else:
                L = len(po) if len(po.shape) == 1 else po.shape[1]
                dd['probs_occur'] = numpy.zeros(L)
            ctx = RecordBuilder(**dd).zeros(len(r_sites))
            for par, val in rparams.items():
                ctx[par] = val

            ctx.rrup = rrup[mask]
            ctx.sids = r_sites.sids
            params = self.REQUIRES_DISTANCES - {'rrup'}
            if self.fewsites or 'clon' in params or 'clat' in params:
                params.add('clon_clat')

            # compute tu only once
            if dparam and ('rx' in params or 'ry0' in params):
                tu = _get_tu(rup, dparam, mask)
            else:
                tu = None
            for param in params - {'clon', 'clat'}:
                set_distances(ctx, rup, r_sites, param, dparam, mask, tu)

            # Equivalent distances
            reqv_obj = (self.reqv.get(self.trt) if self.reqv else None)
            if reqv_obj and not rup.surface:  # PointRuptures have no surface
                reqv = reqv_obj.get(ctx.repi, rup.mag)
                if 'rjb' in self.REQUIRES_DISTANCES:
                    ctx.rjb = reqv
                if 'rrup' in self.REQUIRES_DISTANCES:
                    ctx.rrup = numpy.sqrt(reqv**2 + rup.hypocenter.depth**2)

            for name in r_sites.array.dtype.names:
                setattr(ctx, name, r_sites[name])

            ctx.src_id = src_id
            if src_id >= 0:
                ctx.rup_id = rup.rup_id
            yield ctx

    # this is called for non-point sources (or point sources in preclassical)
    def gen_contexts(self, rups_sites, src_id):
        """
        :yields: the old-style RuptureContexts generated by the source
        """
        for rups, sites in rups_sites:  # ruptures with the same magnitude
            yield from self.genctxs(rups, sites, src_id)

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
        if self.fewsites or 'clon' in self.REQUIRES_DISTANCES:
            self.defaultdict['clon'] = F64(0.)
            self.defaultdict['clat'] = F64(0.)

        if getattr(src, 'location', None) and step == 1:
            return self.pla_mon.iter(genctxs_Pp(src, sitecol, self))
        elif hasattr(src, 'source_id'):  # other source
            if src.code == b'F' and step == 1:
                with self.sec_mon:
                    self.dparam = _build_dparam(src, sitecol, self)
            else:
                self.dparam = None
            minmag = self.maximum_distance.x[0]
            maxmag = self.maximum_distance.x[-1]
            with self.ir_mon:
                allrups = list(src.iter_ruptures(
                    shift_hypo=self.shift_hypo, step=step))
                for i, rup in enumerate(allrups):
                    rup.rup_id = src.offset + i
                allrups = sorted([rup for rup in allrups
                                  if minmag <= rup.mag <= maxmag],
                                 key=bymag)
                self.num_rups = len(allrups) or 1
                if not allrups:
                    return iter([])
                # sorted by mag by construction
                u32mags = U32([rup.mag * 100 for rup in allrups])
                rups_sites = [(rups, sitecol) for rups in split_array(
                    numpy.array(allrups), u32mags)]
            src_id = src.id
        else:  # in event based we get a list with a single rupture
            rups_sites = [(src, sitecol)]
            self.dparam = None
            src_id = -1
        ctxs = self.gen_contexts(rups_sites, src_id)
        blocks = block_splitter(ctxs, 10_000, weight=len)
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

    def get_occ_rates(self, ctxt):
        """
        :param ctxt: context array generated by this ContextMaker
        :returns: occurrence rates, possibly from probs_occur[0]
        """
        # thanks to split_by_tom we can assume ctx to be homogeneous
        if numpy.isfinite(ctxt[0].occurrence_rate):
            return ctxt.occurrence_rate
        else:
            probs = [rec.probs_occur[0] for rec in ctxt]
            return -numpy.log(probs) / self.investigation_time

    # not used by the engine, it is meant for notebooks
    def get_poes(self, srcs, sitecol, tom=None, rup_mutex={},
                 collapse_level=-1):
        """
        :param srcs: a list of sources with the same TRT
        :param sitecol: a SiteCollection instance with N sites
        :returns: an array of PoEs of shape (N, L, G)
        """
        ctxs = self.from_srcs(srcs, sitecol)
        return self.get_pmap(ctxs, tom, rup_mutex).array

    def _gen_poes(self, ctx):
        # NB: by construction ctx.mag contains a single magnitude
        from openquake.hazardlib.site_amplification import get_poes_site
        (M, L1), G = self.loglevels.array.shape, len(self.gsims)

        # split large context arrays to avoid filling the CPU cache
        with self.gmf_mon:
            mean_stdt = self.get_mean_stds([ctx], split_by_mag=False)

        if len(ctx) < 100:
            # do not split in slices to make debugging easier
            slices = [slice(0, len(ctx))]
        else:
            # making plenty of slices so that the array `poes` is small
            slices = split_in_slices(len(ctx), 2*L1)
        for slc in slices:
            with self.poe_mon:
                # this is allocating at most a few MB of RAM
                poes = numpy.zeros((slc.stop-slc.start, M*L1, G), F32)
                # NB: using .empty would break the MixtureModelGMPETestCase
                for g, gsim in enumerate(self.gsims):
                    ms = mean_stdt[:2, g, :, slc]
                    # builds poes of shape (n, L, G)
                    if self.oq.af:  # amplification method
                        poes[:, :, g] = get_poes_site(ms, self, ctx[slc])
                    else:  # regular case
                        set_poes(gsim, ms, self, ctx, poes[:, :, g], slc)
            yield (poes,
                   mean_stdt[0, :, :, slc],
                   mean_stdt[1, :, :, slc],
                   mean_stdt[2, :, :, slc],
                   slc)
        #cs,ms,ps = ctx.nbytes/TWO20, mean_stdt.nbytes/TWO20, poes.nbytes/TWO20
        #print('C=%.1fM, mean_stds=%.1fM, poes=%.1fM, G=%d' % (cs, ms, ps, G))

    def gen_poes(self, ctx):
        """
        :param ctx: a vectorized context (recarray) of size N
        :param rup_indep: rupture flag (false for mutex ruptures)
        :yields: poes, mea_sig, ctxt with poes of shape (N, L, G)
        """
        ctx.mag = numpy.round(ctx.mag, 3)
        for mag in numpy.unique(ctx.mag):
            ctxt = ctx[ctx.mag == mag]
            self.cfactor += [len(ctxt), 1]
            for poes, mea, sig, tau, slc in self._gen_poes(ctxt):
                # NB: using directly 64 bit poes would be slower without reason
                # since with astype(F64) the numbers are identical
                yield poes.astype(F64), mea, sig, tau, ctxt[slc]

    # documented but not used in the engine
    def get_pmap(self, ctxs, tom=None, rup_mutex={}):
        """
        :param ctxs: a list of context arrays (only one for poissonian ctxs)
        :param tom: temporal occurrence model (default PoissonTom)
        :param rup_mutex: dictionary of weights (default empty)
        :returns: a MapArray
        """
        rup_indep = not rup_mutex
        sids = numpy.unique(ctxs[0].sids)
        pmap = MapArray(sids, size(self.imtls), len(self.gsims)).fill(rup_indep)
        self.tom = tom or PoissonTOM(self.investigation_time)
        for ctx in ctxs:
            self.update(pmap, ctx, rup_mutex)
        return ~pmap if rup_indep else pmap

    def get_rmap(self, srcgroup, sitecol):
        """
        Used for debugging simple sources

        :param srcgroup: a group of sources
        :param sitecol: a SiteCollection instance
        :returns: an array of annual rates of shape (N, L, G)
        """
        pmap = self.get_pmap(self.from_srcs(srcgroup, sitecol))
        return (~pmap).to_rates()

    ratesNLG = get_rmap  # for compatibility with the past

    def update(self, pmap, ctx, rup_mutex=None):
        """
        :param pmap: probability map to update
        :param ctx: a context array
        :param rup_mutex: dictionary (src_id, rup_id) -> weight
        """
        for poes, mea, sig, tau, ctxt in self.gen_poes(ctx):
            # ctxt contains an unique magnitude
            if rup_mutex:
                pmap.update_mutex(poes, ctxt, self.tom.time_span, rup_mutex)
            elif self.cluster:
                # in classical/case_35
                for poe, sidx in zip(poes, pmap.sidx[ctxt.sids]):
                    pmap.array[sidx] *= 1. - poe
            else:
                pmap.update_indep(poes, ctxt, self.tom.time_span)

    # called by gen_poes and by the GmfComputer
    def get_mean_stds(self, ctxs, split_by_mag=True):
        """
        :param ctxs: a list of contexts with N=sum(len(ctx) for ctx in ctxs)
        :param split_by_mag: where to split by magnitude
        :returns: an array of shape (4, G, M, N) with mean and stddevs
        """
        N = sum(len(ctx) for ctx in ctxs)
        M = len(self.imts)
        G = len(self.gsims)
        if all(isinstance(ctx, numpy.recarray) for ctx in ctxs):
            # contexts already vectorized
            recarrays = ctxs
        else:  # vectorize the contexts
            recarrays = [self.recarray(ctxs)]
        if split_by_mag:
            recarr = numpy.concatenate(
                recarrays, dtype=recarrays[0].dtype).view(numpy.recarray)
            recarrays = split_array(recarr, U32(numpy.round(recarr.mag*100)))
        out = numpy.empty((4, G, M, N))
        for g, gsim in enumerate(self.gsims):
            out[:, g] = self.get_4MN(recarrays, gsim)
        return out

    def get_4MN(self, ctxs, gsim):
        """
        Called by the GmfComputer
        """
        N = sum(len(ctx) for ctx in ctxs)
        M = len(self.imts)
        out = numpy.zeros((4, M, N))
        gsim.adj = []  # NSHM2014P adjustments
        compute = gsim.__class__.compute
        start = 0
        for ctx in ctxs:
            slc = slice(start, start + len(ctx))
            adj = compute(gsim, ctx, self.imts, *out[:, :, slc])
            if adj is not None:
                gsim.adj.append(adj)
            start = slc.stop
        if self.truncation_level not in (0, 1E-9, 99.) and (out[1] == 0.).any():
            raise ValueError('Total StdDev is zero for %s' % gsim)
        if gsim.adj:
            gsim.adj = numpy.concatenate(gsim.adj)
        if self.conv:  # apply horizontal component conversion
            self.horiz_comp_to_geom_mean(out, gsim)
        return out

    # not used right now
    def get_att_curves(self, site, msr, mag, aratio=1., strike=0.,
                       dip=45., rake=-90):
        """
        :returns:
            4 attenuation curves mea, sig, tau, phi
            (up to 500 km from the site at steps of 5 km)
        """
        from openquake.hazardlib.source import rupture
        rup = rupture.get_planar(
            site, msr, mag, aratio, strike, dip, rake, self.trt)
        ctx = self.from_planar(rup, hdist=500, step=5)
        mea, sig, tau, phi = self.get_mean_stds([ctx])
        return (interp1d(ctx.rrup, mea),
                interp1d(ctx.rrup, sig),
                interp1d(ctx.rrup, tau),
                interp1d(ctx.rrup, phi))

    # tested in test_collapse_small
    def estimate_weight(self, src, srcfilter):
        """
        :param src: a source object
        :param srcfilter: a SourceFilter instance
        :returns: (weight, estimate_sites)
        """
        eps = .01 * EPS if src.code == 'S' else EPS  # needed for EUR
        src.dt = 0
        if src.nsites == 0:  # was discarded by the prefiltering
            return (0, 0) if src.code in b'pP' else (eps, 0)
        # sanity check, preclassical must has set .num_ruptures
        assert src.num_ruptures, src
        sites = srcfilter.get_close_sites(src)
        if sites is None:
            # may happen for CollapsedPointSources
            return eps, 0
        src.nsites = len(sites)
        t0 = time.time()
        ctxs = list(self.get_ctx_iter(src, sites, step=5))  # reduced
        src.dt = time.time() - t0
        if not ctxs:
            return eps, 0
        lenctx = sum(len(ctx) for ctx in ctxs)
        esites = (lenctx * src.num_ruptures /
                  self.num_rups * srcfilter.multiplier)
        # NB: num_rups is set by get_ctx_iter
        weight = src.dt * src.num_ruptures / self.num_rups
        if src.code in b'NX':  # increase weight
            weight *= 5.
        elif src.code == b'S':  # needed for SAM
            weight *= 2
        if len(srcfilter.sitecol) < 100 and src.code in b'NFSC':  # few sites
            weight *= 10  # make fault sources much heavier
        elif len(sites) > 100:  # many sites, raise the weight for many gsims
            # important for USA 2023
            weight *= (1 + len(self.gsims) // 5)
        return max(weight, eps), int(esites)

    def set_weight(self, sources, srcfilter):
        """
        Set the weight attribute on each prefiltered source
        """
        if srcfilter.sitecol is None:
            for src in sources:
                src.weight = EPS
        else:
            for src in sources:
                src.weight, src.esites = self.estimate_weight(src, srcfilter)
                # if src.code == b'S':
                #     print(src, src.dt, src.num_ruptures / self.num_rups)


def by_dists(gsim):
    return tuple(sorted(gsim.REQUIRES_DISTANCES))


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


def _get_poes(mean_std, loglevels, phi_b):
    # returns a matrix of shape (N, L)
    N = mean_std.shape[2]  # shape (2, M, N)
    out = numpy.empty((loglevels.size, N), F32)  # shape (L, N)
    _set_poes(mean_std, loglevels, phi_b, out)
    return out.T


def set_poes(gsim, mean_std, cmaker, ctx, out, slc):
    """
    Calculate and return probabilities of exceedance (PoEs) of one or more
    intensity measure levels (IMLs) of one intensity measure type (IMT)
    for one or more pairs "site -- rupture".

    :param gsim:
        A GMPE instance
    :param mean_std:
        An array of shape (2, M, N) with mean and standard deviations
        for the sites and intensity measure types
    :param cmaker:
        A ContextMaker instance, used only in nhsm_2014
    :param ctx:
        A context array used only in avg_poe_gmpe
    :param out:
        An array of PoEs of shape (N, L) to be filled
    :param slc:
        A slice object used only in avg_poe_gmpe
    :raises ValueError:
        If truncation level is not ``None`` and neither non-negative
        float number, and if ``imts`` dictionary contain wrong or
        unsupported IMTs (see :attr:`DEFINED_FOR_INTENSITY_MEASURE_TYPES`).
    """
    loglevels = cmaker.loglevels.array
    phi_b = cmaker.phi_b
    _M, L1 = loglevels.shape
    if hasattr(gsim, 'weights_signs'):  # for nshmp_2014, case_72
        adj = gsim.adj[slc]
        outs = []
        weights, signs = zip(*gsim.weights_signs)
        for s in signs:
            ms = numpy.array(mean_std)  # make a copy
            for m in range(len(loglevels)):
                ms[0, m] += s * adj
            outs.append(_get_poes(ms, loglevels, phi_b))
        out[:] = numpy.average(outs, weights=weights, axis=0)
    elif hasattr(gsim, 'mixture_model'):
        for f, w in zip(gsim.mixture_model["factors"],
                        gsim.mixture_model["weights"]):
            mean_stdi = mean_std.copy()
            mean_stdi[1] *= f  # multiply stddev by factor
            out[:] += w * _get_poes(mean_stdi, loglevels, phi_b)
    elif hasattr(gsim, 'weights'):  # avg_poe_gmpe
        cm = copy.copy(cmaker)
        cm.poe_mon = Monitor()  # avoid double counts
        cm.gsims = gsim.gsims
        avgs = []
        for poes, _mea, _sig, _tau, _ctx in cm.gen_poes(ctx[slc]):
            # poes has shape N, L, G
            avgs.append(poes @ gsim.weights)
        out[:] = numpy.concatenate(avgs)
    else:  # regular case
        _set_poes(mean_std, loglevels, phi_b, out.T)
    imtweight = getattr(gsim, 'weight', None)  # ImtWeight or None
    for m, imt in enumerate(cmaker.imtls):
        mL1 = m * L1
        if imtweight and imtweight.dic.get(imt) == 0:
            # set by the engine when parsing the gsim logictree
            # when 0 ignore the contribution: see _build_branches
            out[:, mL1:mL1 + L1] = 0


class RmapMaker(object):
    """
    A class to compute the PoEs from a given source
    """
    def __init__(self, cmaker, sitecol, group):
        vars(self).update(vars(cmaker))
        self.cmaker = cmaker
        if hasattr(sitecol, 'sitecol'):
            self.srcfilter = sitecol
        else:
            self.srcfilter = SourceFilter(sitecol, cmaker.maximum_distance)
        self.N = len(self.srcfilter.sitecol.complete)
        try:
            self.sources = group.sources
        except AttributeError:  # already a list of sources
            self.sources = group
        self.src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
        if getattr(group, 'rup_interdep', None) != 'mutex':
            self.rup_mutex = {}
        else:
            self.rup_mutex = {}  # src_id, rup_id -> rup_weight
            for src in group:
                for i, (rup, _) in enumerate(src.data):
                    self.rup_mutex[src.id, i] = rup.weight
        self.fewsites = self.N <= cmaker.max_sites_disagg
        self.grp_probability = getattr(group, 'grp_probability', 1.)
        self.cluster = self.cmaker.cluster = getattr(group, 'cluster', 0)
        if self.cluster:
            tom = group.temporal_occurrence_model
        else:
            tom = getattr(self.sources[0], 'temporal_occurrence_model',
                          PoissonTOM(self.cmaker.investigation_time))
        self.cmaker.tom = self.tom = tom
        M, G = len(self.cmaker.imtls), len(self.cmaker.gsims)
        self.maxsize = 8 * TWO20 // (M*G)  # crucial for a fast get_mean_stds

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
        # to avoid running OOM in multifault sources when building
        # the dparam cache, we split the sites in tiles
        tiles = [sites]
        if src.code == b'F':
            # tested in oq-risk-tests/test/classical/usa_ucerf
            if len(sites) >= 2000:
                tiles = sites.split_in_tiles(len(sites) // 1000)
        for tile in tiles:
            for ctx in self.cmaker.get_ctx_iter(src, tile):
                if self.cmaker.deltagetter:
                    # adjust occurrence rates in case of aftershocks
                    with self.cmaker.delta_mon:
                        delta = self.cmaker.deltagetter(src.id)
                        ctx.occurrence_rate += delta[ctx.rup_id]
                if self.fewsites:  # keep rupdata in memory (before collapse)
                    if self.src_mutex:
                        # needed for Disaggregator.init
                        ctx.src_id = valid.fragmentno(src)
                    self.rupdata.append(ctx)
                yield ctx

    def _make_src_indep(self):
        # sources with the same ID
        cm = self.cmaker
        allctxs = []
        ctxlen = 0
        totlen = 0
        t0 = time.time()
        sids = self.srcfilter.sitecol.sids
        # using most memory here; limited by pmap_max_gb
        pnemap = MapArray(
            sids, self.cmaker.imtls.size, len(self.cmaker.gsims),
            not self.cluster).fill(self.cluster)
        for src in self.sources:
            src.nsites = 0
            for ctx in self.gen_ctxs(src):
                ctxlen += len(ctx)
                src.nsites += len(ctx)
                totlen += len(ctx)
                allctxs.append(ctx)
                if ctxlen > self.maxsize:
                    for ctx in concat(allctxs):
                        cm.update(pnemap, ctx)
                    allctxs.clear()
                    ctxlen = 0
        if allctxs:
            # all sources have the same tom by construction
            for ctx in concat(allctxs):
                cm.update(pnemap, ctx)
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
        return pnemap

    def _make_src_mutex(self):
        # used in Japan (case_27) and in New Madrid (case_80)
        cm = self.cmaker
        t0 = time.time()
        weight = 0.
        nsites = 0
        esites = 0
        nctxs = 0
        G = len(self.cmaker.gsims)
        sids = self.srcfilter.sitecol.sids
        pmap = MapArray(sids, self.cmaker.imtls.size, G).fill(0)
        for src in self.sources:
            t0 = time.time()
            pm = MapArray(
                pmap.sids, cm.imtls.size, len(cm.gsims)
            ).fill(not self.rup_mutex)
            ctxs = list(self.gen_ctxs(src))
            n = sum(len(ctx) for ctx in ctxs)
            if n == 0:
                continue
            nctxs += len(ctxs)
            nsites += n
            esites += src.esites
            for ctx in ctxs:
                cm.update(pm, ctx, self.rup_mutex)
            if self.rup_mutex:
                # in classical/case_80
                pmap.array += (1.- pmap.array) * pm.array
            else:
                # in classical/case_27
                pmap.array += (1. - pm.array) * src.mutex_weight
            weight += src.weight
        pmap.array *= self.grp_probability
        dt = time.time() - t0
        self.source_data['src_id'].append(valid.basename(src))
        self.source_data['grp_id'].append(src.grp_id)
        self.source_data['nsites'].append(nsites)
        self.source_data['esites'].append(esites)
        self.source_data['nrupts'].append(nctxs)
        self.source_data['weight'].append(weight)
        self.source_data['ctimes'].append(dt)
        self.source_data['taskno'].append(cm.task_no)
        return ~pmap

    def make(self):
        dic = {}
        self.rupdata = []
        self.source_data = AccumDict(accum=[])
        if not self.src_mutex and not self.rup_mutex:
            pnemap = self._make_src_indep()
        else:
            pnemap = self._make_src_mutex()
        if self.cluster:
            with self.cmaker.clu_mon:
                probs = F32(self.tom.get_probability_n_occurrences(
                    self.tom.occurrence_rate, numpy.arange(20)))
                array = numpy.full(pnemap.shape, probs[0], dtype=F32)
                for nocc, probn in enumerate(probs[1:], 1):
                    array += pnemap.array ** nocc * probn
                pnemap.array = array

        dic['rmap'] = pnemap.to_rates()
        dic['rmap'].gid = self.cmaker.gid
        dic['cfactor'] = self.cmaker.cfactor
        dic['rup_data'] = concat(self.rupdata)
        dic['source_data'] = self.source_data
        dic['task_no'] = self.task_no
        dic['grp_id'] = self.sources[0].grp_id
        dic['dparam_mb'] = self.cmaker.dparam_mb
        dic['source_mb'] = self.cmaker.source_mb
        if self.disagg_by_src:
            # all the sources in the group must have the same source_id because
            # of the groupby(group, corename) in classical.py
            coreids = set(map(valid.corename, self.sources))
            if len(coreids) > 1:
                raise NameError('Invalid source naming: %s' % coreids)

            # in oq-risk-tests test_phl there are multiple srcids
            # (mps-0!b1;0, mps-0!b1;1, ...); you can simply use the first,
            # since in `store_mean_rates_by_src` we use corename
            dic['basename'] = valid.basename(self.sources[0])
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


# mock of a site collection used in the tests and in the SMT module of the OQ-MBTK
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
    # _slots_ is used in hazardlib check_gsim and in the SMT
    def __init__(self, slots='vs30 vs30measured z1pt0 z2pt5'.split(),
                 sitecol=None):
        self._slots_ = slots
        if sitecol is not None:
            self.sids = sitecol.sids
            for slot in slots:
                setattr(self, slot, getattr(sitecol, slot))

    # used in the SMT
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


# used in boore_atkinson_2008
def get_dists(ctx):
    """
    Extract the distance parameters from a context.

    :returns: a dictionary dist_name -> distances
    """
    return {par: dist for par, dist in vars(ctx).items()
            if par in KNOWN_DISTANCES}


# used to produce a RuptureContext suitable for legacy code, i.e. for calls
# to .get_mean_and_stddevs, like for instance in the SMT module of the OQ-MBTK
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


def get_mean_stds(gsim, ctx, imts, return_dicts=False, **kw):
    """
    :param gsim: a single GSIM or a a list of GSIMs
    :param ctx: a RuptureContext or a recarray of size N with same magnitude
    :param imts: a list of M IMT objects
    :param return_dicts: if True, returns 4 dictionaries keyed by IMT strings
    :param kw: additional keyword arguments
    :returns:
        an array of shape (4, M, N) obtained by applying the
        given GSIM, ctx amd imts, or an array of shape (G, 4, M, N)
    """
    single = hasattr(gsim, 'compute')
    kw['imtls'] = {imt.string: [0] for imt in imts}
    cmaker = ContextMaker('*', [gsim] if single else gsim, kw)
    out = cmaker.get_mean_stds([ctx], split_by_mag=False)  # (4, G, M, N)
    out = out[:, 0] if single else out
    if return_dicts:
        assert single
        return [{imt.string: out[o, m] for m, imt in enumerate(imts)}
                for o in range(4)]
    return out


# mock of a rupture used in the tests and in the module of the OQ-MBTK
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


class ContextMakerSequence(collections.abc.Sequence):
    """
    Wrapper over a sequence of ContextMakers
    """
    def __init__(self, cmakers, inverse):
        self.cmakers = cmakers
        self.inverse = inverse

    @property
    def Gt(self):
        """
        The total number of gsims in the underlying context makers
        """
        return sum(len(cm.gsims) for cm in self.cmakers)

    def __getitem__(self, idx):
        return self.cmakers[idx]

    def __len__(self):
        return len(self.cmakers)

    def enumerate(self):
        for grp_id, inv in enumerate(self.inverse):
            yield grp_id, self[inv]

    def to_array(self, grp_ids=slice(None)):
        return numpy.array([self[inv] for inv in self.inverse[grp_ids]])

    def get_rmap(self, src_groups, sitecol):
        """
        :returns: a RateMap of shape (N, L, Gt)
        """
        cmakers = self.to_array()
        assert cmakers[0].oq.use_rates
        assert len(src_groups) == len(cmakers)
        L = cmakers[0].imtls.size
        rmap = MapArray(sitecol.sids, L, self.Gt).fill(0)
        for group, cmaker in zip(src_groups, cmakers):
            rmap += RmapMaker(cmaker, sitecol, group).make()['rmap']
        return rmap

    def get_rmaps(self, sources, sitecol):
        """
        :param sources: a list of R variations of the same source
        :param sitecol: a SiteCollection instance
        :returns: a list of RateMaps of shape (N, L, G), one per smr
        """
        # FIXME: works only for logic trees not changing the geometries
        # and only for pointlike sources
        R = len(sources)
        cmaker = self.cmakers[0]
        assert cmaker.oq.use_rates
        assert len(self) == R, (len(self), R)
        L = cmaker.imtls.size
        G = len(cmaker.gsims)
        tom = PoissonTOM(cmaker.oq.investigation_time)
        pmaps = [MapArray(sitecol.sids, L, G, True).fill(0) for rlz in range(R)]
        [ctx] = cmaker.from_srcs([sources[0]], sitecol)
        magrates = [{numpy.round(mag, 3): rate
                     for mag, rate in src.get_annual_occurrence_rates()}
                     for src in sources]
        for poes, mea, sig, tau, ctxt in cmaker.gen_poes(ctx):
            mag = ctxt.mag[0]  # ctxt contains a single magnitude
            for smr, magrate in enumerate(magrates):
                orate = ctxt.occurrence_rate / magrates[0][mag] * magrate[mag]
                pmaps[smr].update_indep(poes, ctxt, tom.time_span, orate)
        return [pmap.to_rates() for pmap in pmaps]

    def combine_rates(self, rmap):
        """
        :returns: an array of shape (N, L, R) for the given site ID
        """
        N, L, G = rmap.array.shape
        assert self.Gt == G, (self.Gt, G)
        maxr = 0
        for cm in self.cmakers:
            for rlzs in cm.gsims.values():
                maxr = max(maxr, rlzs[-1])
        r0 = numpy.zeros((N, L, maxr + 1))
        g = 0
        for cm in self.cmakers:
            for i, rlzs in enumerate(cm.gsims.values()):
                rates = rmap.array[:, :, g]
                for rlz in rlzs:
                    r0[:, :, rlz] += rates
                g += 1
        return r0

    def __repr__(self):
        name = self.__class__.__name__
        return f'<{name} Gt={self.Gt}, groups={len(self.inverse)}>'


def get_unique_inverse(all_trt_smrs):
    """
    :returns: unique tuples trt_smrs and an array of indices
    """
    strings = [','.join(map(str, ts)) for ts in all_trt_smrs]
    unique, inverse = numpy.unique(strings, return_inverse=True)
    return [tuple(map(int, u.split(','))) for u in unique], inverse


def get_cmakers(all_trt_smrs, full_lt, oq):
    """
    :params all_trt_smrs: a list of arrays
    :param full_lt: a FullLogicTree instance
    :param oq: object containing the calculation parameters
    :returns: list of ContextMakers associated to the given src_groups
    """
    from openquake.hazardlib.site_amplification import AmplFunction
    all_trt_smrs, inverse = get_unique_inverse(all_trt_smrs)
    if 'amplification' in oq.inputs and oq.amplification_method == 'kernel':
        df = AmplFunction.read_df(oq.inputs['amplification'])
        oq.af = AmplFunction.from_dframe(df)
    else:
        oq.af = None
    trts = list(full_lt.gsim_lt.values)
    gweights = full_lt.g_weights(all_trt_smrs)[:, -1]  # shape Gt
    cmakers = []
    for grp_id, trt_smrs in enumerate(all_trt_smrs):
        rlzs_by_gsim = full_lt.get_rlzs_by_gsim(trt_smrs)
        if not rlzs_by_gsim:  # happens for gsim_lt.reduce() on empty TRTs
            continue
        trti = trt_smrs[0] // TWO24
        cm = ContextMaker(trts[trti], rlzs_by_gsim, oq)
        cm.trti = trti
        cm.trt_smrs = trt_smrs
        cmakers.append(cm)
    gids = full_lt.get_gids(cm.trt_smrs for cm in cmakers)
    for cm, gid in zip(cmakers, gids):
        cm.gid = gid
        cm.wei = gweights[gid]
    return ContextMakerSequence(cmakers, inverse)


def read_cmakers(dstore, full_lt=None):
    """
    :param dstore: a DataStore-like object
    :param all_trt_smrs: a list of arrays
    :returns: an array of ContextMaker instances, one per source group
    """
    oq = dstore['oqparam']
    oq.mags_by_trt = {
        k: decode(v[:]) for k, v in dstore['source_mags'].items()}
    all_trt_smrs = dstore['trt_smrs'][:]
    if not full_lt:
        full_lt = dstore['full_lt'].init()
    cmakers = get_cmakers(all_trt_smrs, full_lt, oq)
    return cmakers


def read_full_lt_by_label(dstore):
    """
    :param dstore: a DataStore-like object
    :returns: a dictionary label -> full_lt
    """
    oq = dstore['oqparam']
    full_lt = dstore['full_lt'].init()
    attrs = vars(full_lt)
    dic = {'Default': full_lt}
    for label in oq.site_labels:
        dic[label] = copy.copy(full_lt)
        dic[label].__dict__.update(attrs)
        dic[label].gsim_lt = dstore['gsim_lt' + label]
    return dic


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


def get_src_mutex(srcs):
    """
    :param srcs: a list of sources with weights and the same grp_id
    :returns: a dictionary grp_id -> {'src_id': [...], 'weight': [...]}
    """
    grp_ids = [src.grp_id for src in srcs]
    [grp_id] = set(grp_ids)
    ok = all(hasattr(src, 'mutex_weight') for src in srcs)
    if not ok:
        return {grp_id: {}}
    dic = dict(src_ids=U32([src.id for src in srcs]),
               weights=F64([src.mutex_weight for src in srcs]))
    return {grp_id: dic}


def read_ctx_by_grp(dstore):
    """
    :param dstore: DataStore instance
    :returns: dictionary grp_id -> ctx
    """
    sitecol = dstore['sitecol'].complete.array
    params = {n: dstore['rup/' + n][:] for n in dstore['rup']}
    dtlist = []
    for par, val in params.items():
        if len(val) == 0:
            return {}
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
    ctx = numpy.zeros(len(params['grp_id']), dtlist).view(numpy.recarray)
    for par, val in params.items():
        ctx[par] = val
    for par in sitecol.dtype.names:
        if par != 'sids':
            ctx[par] = sitecol[par][ctx.sids]
    grp_ids = numpy.unique(ctx.grp_id)
    ctx = ctx[numpy.argsort(ctx.mag)]  # NB: crucial for performance
    return {grp_id: ctx[ctx.grp_id == grp_id] for grp_id in grp_ids}
