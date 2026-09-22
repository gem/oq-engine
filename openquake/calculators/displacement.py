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
rates come from the PFD kernel
:func:`openquake.hazardlib.calc.displacement.calc_rates`.  The PFD logic
tree is the ``extra_lt`` of the full logic tree, so ``hcurves-rlzs`` has
the full cardinality ``R = sm_rlzs * gsim_paths * pfd_paths``.

The calculation is parallelized with :class:`openquake.baselib.parallel.
Starmap` over blocks of sources: each task returns the ``(N, R, M, L1)``
rates of its block plus the per-source mean rates used by
``mean_rates_by_src``.
"""
import logging
import operator
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import humansize, block_splitter
from openquake.hazardlib import valid
from openquake.hazardlib.calc.displacement import (
    calc_rates, DEFAULT_RED_CFG)
from openquake.hazardlib.calc.mean_rates import to_probs
from openquake.hazardlib.map_array import compute_hazard_maps
from openquake.hazardlib.pfd_lt import CALC_R_SIGMA_SLOT, R_SIGMA_KM_KEY
from openquake.pfd.adapter import PFDModelAdapter, style_from_rake
from openquake.pfd.registry import get_available
from openquake.calculators import base

F32 = numpy.float32
F64 = numpy.float64
get_weight = operator.attrgetter('weight')


def get_adapters(selections, r_sigma):
    """
    Build the PFD model adapters for one realization.

    The adapters are needed because the ~60 ported PFD models do not
    share a calling convention: ``get_prob`` takes different arguments
    depending on the model (``d``/``mag``/``r``/``rx``/``X_L_ratio``/
    ``pixel_size``/``version``/``percentile``/``vs30``/...), sometimes
    returns Monte-Carlo samples or a different array orientation, and
    some declare a near-field floor or a multi-fault reference line.
    :class:`~openquake.pfd.adapter.PFDModelAdapter` hides all of this
    behind the fixed ``compute_primary_sr``/``compute_primary_fd``/
    ``compute_secondary_sr``/``compute_secondary_fd`` interface used by
    the rate kernel, so the models can stay paper-faithful.  It would be
    nice if the models exposed a common vectorized ``compute(ctx)`` interface.

    :param selections: slot -> PfdModelChoice for one realization
    :param r_sigma: the scalar ``r_sigma_km`` (used when not overridden)
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
    return adapters, r_sigma


def displacement(srcs, cmaker, sitecol, pfd_lt, rlzs, N, R, monitor):
    """
    Compute the displacement rates of a block of sources for the active
    realizations of the source group.

    :param rlzs: the :class:`~openquake.hazardlib.logictree.LtRealization`
        objects active for the group
    :returns: ``(rates, src_rates)`` where ``rates`` has shape
        ``(N, R, M, L1)`` and ``src_rates`` maps source basename to the
        mean over the realizations, shape ``(N, M, L1)``
    """
    cmaker.init_monitoring(monitor)
    oq = cmaker.oq
    imts = list(cmaker.imtls)
    imls = [cmaker.imtls[imt] for imt in imts]
    M, L1 = len(imts), cmaker.imtls.size // len(imts)
    rates = numpy.zeros((N, R, M, L1), F32)
    src_rates = {}
    for src in srcs:
        basename = valid.basename(src)
        style = style_from_rake(getattr(src, 'rake', 0.0))
        ctxs = list(cmaker.get_ctxs(src, sitecol))
        if not ctxs:
            continue
        src_rate = src_rates.setdefault(
            basename, numpy.zeros((N, M, L1), F64))
        for rlz in rlzs:
            rlz_id = rlz.ordinal
            selections = pfd_lt.selections_for(
                rlz.extra_rlz.lt_path, basename, style)
            adapters, r_sigma = get_adapters(selections, oq.r_sigma_km)
            for imt_idx, levels in enumerate(imls):
                rate, _principal, _distributed = calc_rates(
                    ctxs, N, adapters, levels, oq.r_threshold_km, r_sigma,
                    DEFAULT_RED_CFG)
                rates[:, rlz_id, imt_idx, :] += rate
                src_rate[:, imt_idx, :] += rlz.weight[-1] * rate
    return rates, src_rates


@base.calculators.add('displacement')
class DisplacementCalculator(base.HazardCalculator):
    """
    Calculator for the ``displacement`` calculation mode.
    """
    def pre_execute(self):
        super().pre_execute()
        self.store_rlz_info({})

    def agg(self, acc, result):
        if result is None:
            raise MemoryError('You ran out of memory!')
        rates, src_rates = result
        acc[0] += rates
        for key, value in src_rates.items():
            if key in acc[1]:
                acc[1][key] += value
            else:
                acc[1][key] = value
        return acc

    def execute(self):
        oq = self.oqparam
        N = len(self.sitecol)
        R = self.full_lt.get_num_paths()
        M = len(oq.imtls)
        L1 = oq.imtls.size // M
        rlzs = self.full_lt.get_realizations()
        pfd_lt = self.full_lt.extra_lt
        cmakers = self.csm.get_cmakers()
        allargs = []
        for grp_id, src_group in enumerate(self.csm.src_groups):
            cmaker = cmakers[grp_id]
            active = next(iter(cmaker.gsims.values()))
            grp_rlzs = [rlzs[r] for r in active]
            sources = list(src_group)
            maxw = sum(s.weight for s in sources) / (
                oq.concurrent_tasks or 1)
            for block in block_splitter(sources, maxw, get_weight, sort=True):
                allargs.append((
                    block, cmaker, self.sitecol, pfd_lt, grp_rlzs, N, R))
        logging.info('Sending {:_d} tasks'.format(len(allargs)))
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            displacement, allargs, h5=self.datastore.hdf5)
        zeros = numpy.zeros((N, R, M, L1), F32)
        rates, src_rates = smap.reduce(self.agg, [zeros, {}])
        self.src_rates = src_rates
        self.basenames = self.csm.get_basenames()
        return rates

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

    def post_execute(self, rates):
        oq = self.oqparam
        N, R, M, L1 = rates.shape
        itime = oq.investigation_time
        imts = list(oq.imtls)
        # individual hazard curves (converted to probabilities)
        self.datastore.create_dset('hcurves-rlzs', F32, (N, R, M, L1))
        self.datastore.set_shape_descr(
            'hcurves-rlzs', site_id=N, rlz_id=R, imt=imts, lvl=L1)
        hcurves = to_probs(rates, itime)
        self.datastore['hcurves-rlzs'][:] = hcurves
        # statistics computed on the rates, like the use_rates=True path
        hstats = oq.hazard_stats()
        S = len(hstats)
        hcurves_stats = numpy.zeros((N, S, M, L1), F32)
        weights = numpy.array(
            [rlz.weight[-1] for rlz in self.full_lt.get_realizations()], F64)
        for s, func in enumerate(hstats.values()):
            for m in range(M):
                stat_rates = func(
                    rates[:, :, m, :].transpose(1, 0, 2), weights)
                hcurves_stats[:, s, m, :] = to_probs(stat_rates, itime)
        self.datastore.create_dset('hcurves-stats', F32, (N, S, M, L1))
        self.datastore.set_shape_descr(
            'hcurves-stats', site_id=N, stat=list(hstats),
            imt=imts, lvl=numpy.arange(L1))
        self.datastore['hcurves-stats'][:] = hcurves_stats
        if oq.poes:
            P = len(oq.poes)
            hmaps_rlzs = numpy.zeros((N, R, M, P), F32)
            for r in range(R):
                for m, imt in enumerate(imts):
                    hmaps_rlzs[:, r, m, :] = compute_hazard_maps(
                        hcurves[:, r, m, :], oq.imtls[imt], oq.poes)
            self.datastore.create_dset('hmaps-rlzs', F32, (N, R, M, P))
            self.datastore.set_shape_descr(
                'hmaps-rlzs', site_id=N, rlz_id=R, imt=imts, poe=oq.poes)
            self.datastore['hmaps-rlzs'][:] = hmaps_rlzs
            hmaps_stats = numpy.zeros((N, S, M, P), F32)
            for s in range(S):
                for m, imt in enumerate(imts):
                    hmaps_stats[:, s, m, :] = compute_hazard_maps(
                        hcurves_stats[:, s, m, :], oq.imtls[imt], oq.poes)
            self.datastore.create_dset('hmaps-stats', F32, (N, S, M, P))
            self.datastore.set_shape_descr(
                'hmaps-stats', site_id=N, stat=list(hstats),
                imt=imts, poe=oq.poes)
            self.datastore['hmaps-stats'][:] = hmaps_stats
        self._store_mean_rates_by_src()
        logging.info('Stored %s of hazard curves',
                     humansize(hcurves_stats.nbytes))
