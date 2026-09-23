# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Probabilistic Fault Displacement (PFD) calculator (``displacement`` mode).

Unlike the classical calculator there are no GSIMs: the ground-shaking
machinery is used only to build the rupture/site contexts (through the
no-op :class:`openquake.pfd.gsim.PFDGMPE`), while the annual exceedance
rates come from the FDHA kernel
:func:`openquake.hazardlib.calc.displacement.calc_rates`.  The PFD logic
tree is the ``extra_lt`` of the full logic tree, so the realizations are
``R = sm_rlzs * gsim_paths * pfd_paths``.

As in the classical calculator the rates are stored sparsely in the
``_rates`` table (``sid, lid, gid, rate``) and the hazard curves are
recomputed from them with
:class:`openquake.calculators.getters.MapGetter`; here the ``gid`` is the
full realization ordinal (``trt_rlzs = [[r] for r in range(R)]``), since
the varying dimension is the extra (PFD) realization, not a GSIM one.
``hcurves-rlzs`` is stored only when ``R == 1`` or ``individual_rlzs``.
"""
import logging
import operator
import time
import numpy
import pandas

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import humansize, block_splitter
from openquake.hazardlib import valid, source_reader
from openquake.hazardlib.calc.displacement import (
    calc_rates, DEFAULT_RED_CFG)
from openquake.hazardlib.map_array import (
    MapArray, compute_hazard_maps, rates_dt)
from openquake.hazardlib.pfd_lt import (
    CALC_R_SIGMA_SLOT, R_SIGMA_KM_KEY, PFD_SLOTS_BY_UTYPE)
from openquake.pfd.adapter import PFDModelAdapter, style_from_rake
from openquake.pfd.registry import get_available
from openquake.pfd.visini import VisiniSecondaryCalculator
from openquake.calculators import base
from openquake.calculators.classical import _store
from openquake.calculators.getters import MapGetter, build_stat_curve, slice_dt

F32 = numpy.float32
F64 = numpy.float64
U32 = numpy.uint32
GZIP = 'gzip'
get_weight = operator.attrgetter('weight')


def get_adapters(selections, r_sigma, near_far_threshold_km=0.2):
    """
    Build the PFD model adapters for one realization.

    The adapters are needed because the ~60 ported FDHA models do not
    share a calling convention: ``get_prob`` takes different arguments
    depending on the model (``d``/``mag``/``r``/``rx``/``X_L_ratio``/
    ``pixel_size``/``version``/``percentile``/``vs30``/...), sometimes
    returns Monte-Carlo samples or a different array orientation, and
    some declare a near-field floor or a multi-fault reference line.
    :class:`~openquake.pfd.adapter.PFDModelAdapter` hides all of this
    behind the fixed ``compute_primary_sr``/``compute_primary_fd``/
    ``compute_secondary_sr``/``compute_secondary_fd`` interface used by
    the rate kernel, so the models can stay paper-faithful.  It is
    scheduled for removal once the models expose a common vectorized
    ``compute(ctx)`` interface (EngineIntegration.md sections 4.2 and 8).

    :param selections: slot -> PfdModelChoice for one realization
    :param r_sigma: the scalar ``r_sigma_km`` (used when not overridden)
    :param near_far_threshold_km: the Visini near/far regime threshold
    :returns: ``(adapters_by_model_type, r_sigma_km)``
    """
    adapters = {}
    for slot, choice in selections.items():
        if slot == CALC_R_SIGMA_SLOT:
            r_sigma = choice.params[R_SIGMA_KM_KEY]
            continue
        cls = get_available(slot)[choice.class_name]
        adapter = PFDModelAdapter(cls(**choice.params), choice.params)
        adapters[adapter.model_type] = adapter
    # the Visini models need the combined secondary pipeline instead of the
    # generic P(SR) x P(FD) product (they sum the A/B/C combinations)
    sr = adapters.get('secondary_sr')
    fd = adapters.get('secondary_fd')
    pipeline = 'generic'
    for adapter in (sr, fd):
        if adapter is not None:
            pipeline = getattr(adapter.model, 'SECONDARY_PIPELINE', 'generic')
            if pipeline != 'generic':
                break
    if sr is not None and fd is not None and pipeline == 'visini':
        case = (fd.model_params.get('case')
                or sr.model_params.get('case') or 'case1')
        adapters['secondary_combined'] = VisiniSecondaryCalculator(
            sr.model, fd.model, case_label=case,
            pixel_size=sr.model_params.get('pixel_size', 100),
            near_far_threshold_km=near_far_threshold_km)
    return adapters, r_sigma


def pfd_methods(pfd_lt):
    """
    :param pfd_lt: a :class:`~openquake.hazardlib.pfd_lt.PFDLogicTree`
    :returns: the union of ``MULTIFAULT_REFERENCE_LINE`` methods declared by
        the PFD models in the logic tree (the FDHA analogue of collecting
        the union of the GMPEs' ``REQUIRES_DISTANCES``)
    """
    # Raw sections are always available and are the safe default.  Only an
    # explicit model declaration requests an expensive smoothed line; the
    # base-class default must not turn every multi-fault rupture into an LCP
    # raster calculation.
    methods = {'segments'}
    for branchset in pfd_lt.branchsets:
        slot = PFD_SLOTS_BY_UTYPE.get(branchset.uncertainty_type)
        if slot is None:
            continue
        available = get_available(slot)
        for branch in branchset.branches:
            if not isinstance(branch.value, tuple):
                continue  # dummy/pseudo branch
            cls = available.get(branch.value[0])
            if cls is not None:
                method = cls.__dict__.get('MULTIFAULT_REFERENCE_LINE')
                if method is not None:
                    methods.add(method)
    return methods


def set_pfd_methods(cmakers, methods):
    """
    Attach the multi-fault reference-line union to the cmakers and add the
    matching context fields (one ``(r, x_L, L)`` set per non-'segments'
    method; 'segments' reuses the canonical ``rtor``/``x_l``/``length``).
    """
    extra = set()
    for method in methods:
        if method != 'segments':
            extra.update((f'rtor_{method}', f'x_l_{method}',
                          f'length_{method}'))
    for cmaker in cmakers:
        cmaker.pfd_methods = methods
        for name in extra:
            cmaker.defaultdict[name] = F64(0.)


def displacement(srcs, cmaker, sitecol, pfd_lt, rlzs, monitor):
    """
    Compute the displacement rates of a block of sources for the active
    realizations of the source group.

    :param rlzs: the :class:`~openquake.hazardlib.logictree.LtRealization`
        objects active for the group
    :returns: ``(rmap, src_rates)`` where ``rmap`` is a rates
        :class:`~openquake.hazardlib.map_array.MapArray` with ``gids`` set
        to the realization ordinals, and ``src_rates`` maps source
        basename to the mean over the realizations, shape ``(N, M, L1)``
    """
    cmaker.init_monitoring(monitor)
    oq = cmaker.oq
    N = len(sitecol)
    imts = list(cmaker.imtls)
    imls = [cmaker.imtls[imt] for imt in imts]
    M, L1 = len(imts), cmaker.imtls.size // len(imts)
    L = M * L1
    gids = U32([rlz.ordinal for rlz in rlzs])
    rmap = MapArray(sitecol.sids, L, len(gids), rates=True).fill(0.)
    rmap.gids = gids
    src_rates = {}
    source_data = {k: [] for k in (
        'src_id', 'grp_id', 'nctxs', 'nrupts', 'weight', 'ctimes', 'taskno')}
    task_no = getattr(monitor, 'task_no', 0)
    tolerance = oq.surface_rupture_depth_tolerance_km
    for src in srcs:
        t0 = time.time()
        basename = valid.basename(src)
        style = style_from_rake(getattr(src, 'rake', 0.0))
        # a rupture contributes only if its top edge reaches the surface
        # (surface_rupture_depth_tolerance_km), like oq-pfdha
        ctxs = [ctx for ctx in cmaker.get_ctxs(src, sitecol)
                if float(numpy.asarray(ctx.ztor).flat[0]) <= tolerance]
        if ctxs:
            src_rate = src_rates.setdefault(
                basename, numpy.zeros((N, M, L1), F64))
            for k, rlz in enumerate(rlzs):
                selections = pfd_lt.selections_for(
                    rlz.extra_rlz.lt_path, basename, style)
                adapters, r_sigma = get_adapters(
                    selections, oq.r_sigma_km, oq.near_far_threshold_km)
                for m, levels in enumerate(imls):
                    rate, _principal, _distributed = calc_rates(
                        ctxs, N, adapters, levels, oq.r_threshold_km,
                        r_sigma, DEFAULT_RED_CFG)
                    rmap.array[:, m*L1:(m+1)*L1, k] += rate
                    src_rate[:, m, :] += rlz.weight[-1] * rate
        source_data['src_id'].append(basename)
        source_data['grp_id'].append(src.grp_id)
        source_data['nctxs'].append(sum(len(ctx) for ctx in ctxs))
        source_data['nrupts'].append(src.num_ruptures)
        source_data['weight'].append(src.weight)
        source_data['ctimes'].append(time.time() - t0)
        source_data['taskno'].append(task_no)
    return rmap, src_rates, source_data


@base.calculators.add('displacement')
class DisplacementCalculator(base.HazardCalculator):
    """
    Calculator for the ``displacement`` calculation mode.
    """
    def agg(self, acc, result):
        if result is None:
            raise MemoryError('You ran out of memory!')
        rmap, src_rates, source_data = result
        rates = rmap.to_array(rmap.gids)
        if len(rates):
            _store(rates, 1, self.datastore.hdf5)
        for key, value in src_rates.items():
            if key in acc['src_rates']:
                acc['src_rates'][key] += value
            else:
                acc['src_rates'][key] = value
        for key, values in source_data.items():
            acc['source_data'].setdefault(key, []).extend(values)
        return acc

    def execute(self):
        oq = self.oqparam
        N = len(self.sitecol)
        self.store_rlz_info({})
        # create source_info before the tasks, so store_source_info will
        # update the actual number of contexts (not the estimated one)
        source_reader.create_source_info(self.csm, self.datastore.hdf5)
        # multiFaultSource sections need their .msparams before iter_ruptures
        self.csm.set_msparams()
        rlzs = self.full_lt.get_realizations()
        pfd_lt = self.full_lt.extra_lt
        cmakers = self.csm.get_cmakers()
        # only the reference-line methods the PFD models actually declare
        set_pfd_methods(cmakers, pfd_methods(pfd_lt))
        # the sparse table from which the curves are recomputed
        self.datastore.create_df(
            '_rates', [(n, rates_dt[n]) for n in rates_dt.names], GZIP)
        self.datastore.create_dset('_rates/slice_by_idx', slice_dt)
        allargs = []
        for grp_id, src_group in enumerate(self.csm.src_groups):
            cmaker = cmakers[grp_id]
            active = next(iter(cmaker.gsims.values()))
            grp_rlzs = [rlzs[r] for r in active]
            sources = list(src_group)
            maxw = sum(s.weight for s in sources) / (
                oq.concurrent_tasks or 1)
            for block in block_splitter(
                    sources, maxw, get_weight, sort=True):
                allargs.append((
                    block, cmaker, self.sitecol, pfd_lt, grp_rlzs))
        logging.info('Sending {:_d} tasks'.format(len(allargs)))
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            displacement, allargs, h5=self.datastore.hdf5)
        acc = smap.reduce(self.agg, {'src_rates': {}, 'source_data': {}})
        self.store_source_info(acc['source_data'])
        df = pandas.DataFrame(acc['source_data'])
        df['impact'] = df.nctxs / N
        self.datastore.create_df('source_data', df)
        return acc['src_rates']

    def _store_mean_rates_by_src(self):
        M = len(self.oqparam.imtls)
        L1 = self.oqparam.imtls.size // M
        dic = dict(shape_descr=['site_id', 'imt', 'lvl', 'src_id'],
                   site_id=len(self.sitecol), imt=list(self.oqparam.imtls),
                   lvl=L1, src_id=numpy.array(self.basenames))
        arr = numpy.zeros((len(self.sitecol), M, L1, len(self.basenames)), F32)
        for b, s in enumerate(self.basenames):
            arr[:, :, :, b] = self.src_rates.get(
                s, numpy.zeros((len(self.sitecol), M, L1), F64))
        self.datastore['mean_rates_by_src'] = hdf5.ArrayWrapper(arr, dic)

    def post_execute(self, src_rates):
        oq = self.oqparam
        self.src_rates = src_rates
        self.basenames = self.csm.get_basenames()
        N = len(self.sitecol)
        R = self.full_lt.get_num_paths()
        imts = list(oq.imtls)
        # create the hcurves-*/hmaps-* datasets (shared with classical)
        S, M, P, L1 = base.create_hcurves_maps(
            self.datastore, oq, N, R)
        store_rlzs = R == 1 or oq.individual_rlzs
        sids = self.sitecol.sids
        # the varying dimension is the extra (PFD) realization, so gid=rlz
        trt_rlzs = [U32([r]) for r in range(R)]
        # Unlike the classical calculator, which splits the sites in
        # chunks via get_num_chunks/MapGetter tiles, here we read the whole
        # _rates table with a single MapGetter (chunk 0).  This is simpler
        # and fine for the current use cases; for very large N x R it would
        # materialize the full (N, L, R) array in memory.
        getter = MapGetter([self.datastore.filename], 0, trt_rlzs, sids, R, oq)
        wget = self.full_lt.gsim_lt.wget
        wget.weights = self.datastore['weights'][:].reshape(-1, 1)
        hstats = oq.hazard_stats()
        if store_rlzs:
            hcurves_rlzs = numpy.zeros((N, R, M, L1), F32)
            if P:
                hmaps_rlzs = numpy.zeros((N, R, M, P), F32)
        if S:
            hcurves_stats = numpy.zeros((N, S, M, L1), F32)
            if P:
                hmaps_stats = numpy.zeros((N, S, M, P), F32)
        for idx, sid in enumerate(sids):
            hcurve = getter.get_hcurve(sid)  # shape (L, R), probabilities
            if store_rlzs:
                for r in range(R):
                    hcurves_rlzs[idx, r] = hcurve[:, r].reshape(M, L1)
                    if P:
                        for m, imt in enumerate(imts):
                            slc = oq.imtls(imt)
                            hmaps_rlzs[idx, r, m] = compute_hazard_maps(
                                hcurve[slc, r].reshape(1, L1),
                                oq.imtls[imt], oq.poes)
            for s, stat in enumerate(hstats.values()):
                arr = build_stat_curve(
                    hcurve, oq.imtls, stat, wget, use_rates=True)
                hcurves_stats[idx, s] = arr.reshape(M, L1)
                if P:
                    for m, imt in enumerate(imts):
                        slc = oq.imtls(imt)
                        hmaps_stats[idx, s, m] = compute_hazard_maps(
                            arr[slc].reshape(1, L1), oq.imtls[imt], oq.poes)
        if store_rlzs:
            self.datastore['hcurves-rlzs'][:] = hcurves_rlzs
            if P:
                self.datastore['hmaps-rlzs'][:] = hmaps_rlzs
        if S:
            self.datastore['hcurves-stats'][:] = hcurves_stats
            if P:
                self.datastore['hmaps-stats'][:] = hmaps_stats
        self._store_mean_rates_by_src()
        logging.info('Stored %s of hazard curves',
                     humansize(self.datastore['hcurves-stats'].nbytes))