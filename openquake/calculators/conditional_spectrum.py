# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Conditional spectrum calculator
"""
import logging
import operator
import numpy

from openquake.baselib import parallel
from openquake.baselib.general import block_splitter
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.contexts import read_ctxs, RuptureContext
from openquake.hazardlib.tom import PoissonTOM
from openquake.calculators import base, getters

U16 = numpy.uint16
U32 = numpy.uint32


def conditional_spectrum(dstore, slc, cmaker, grp_id, monitor):
    """
    :param dstore:
        a DataStore instance
    :param slc:
        a slice of ruptures
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param grp_id:
        the group of ruptures currently considered
    :param monitor:
        monitor of the currently running job
    :returns:
        dictionary grp_id -> poes of shape (N, L, G)
    """
    RuptureContext.temporal_occurrence_model = PoissonTOM(
        cmaker.investigation_time)
    with monitor('reading contexts', measuremem=True):
        dstore.open('r')
        allctxs, _close = read_ctxs(
            dstore, slc, req_site_params=cmaker.REQUIRES_SITES_PARAMETERS)

    # ------------------------------------------------------------------------
    # TODO This should be taken from input!
    from openquake.hazardlib.cross_correlation import BakerJayaram2008, \
        get_correlation_mtx
    com = BakerJayaram2008()
    from openquake.hazardlib.imt import SA, from_string
    imts = [from_string(key) for key in cmaker.imtls]
    cvec = numpy.squeeze(get_correlation_mtx(com, SA(0.2), imts, 1))
    eps = 1.55
    # ------------------------------------------------------------------------

    # Get site list
    sids = set()
    for c in allctxs:
        sids = sids | set(c.sids)

    # Collector for CS
    spectra = {i: [] for i in list(sids)}

    # Compute CS
    for ctx, mean_std in cmaker.gen_ctx_cs_mean_and_stds(allctxs, cvec, eps):
        for i, idx in enumerate(ctx.sids):
            spectra[idx].append(mean_std[:, i, :, :])
    return {grp_id: spectra}


@base.calculators.add('conditional_spectrum')
class ConditionalSpectrumCalculator(base.HazardCalculator):
    """
    Conditional spectrum calculator
    """
    precalc = 'classical'
    accept_precalc = ['classical', 'disaggregation']

    def pre_checks(self):
        """
        Check the number of sites and the absence of atomic groups
        """
        if self.N >= 32768:
            raise ValueError('You can disaggregate at max 32,768 sites')
        few = self.oqparam.max_sites_disagg
        if self.N > few:
            raise ValueError(
                'The number of sites is to disaggregate is %d, but you have '
                'max_sites_disagg=%d' % (self.N, few))
        if hasattr(self, 'csm'):
            for sg in self.csm.src_groups:
                if sg.atomic:
                    raise NotImplementedError(
                        'Atomic groups are not supported yet')
        elif self.datastore['source_info'].attrs['atomic']:
            raise NotImplementedError(
                'Atomic groups are not supported yet')

    def execute(self):
        """
        Compute the conditional spectrum
        """
        oq = self.oqparam
        self.full_lt = self.datastore['full_lt']
        self.trts = list(self.full_lt.gsim_lt.values)
        [self.poe] = oq.poes_disagg
        self.imts = list(oq.imtls)
        self.M = len(self.imts)
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        totrups = len(dstore['rup/mag'])
        logging.info('Reading {:_d} ruptures'.format(totrups))
        rdt = [('grp_id', U16), ('nsites', U16), ('idx', U32)]
        rdata = numpy.zeros(totrups, rdt)
        rdata['idx'] = numpy.arange(totrups)
        rdata['grp_id'] = dstore['rup/grp_id'][:]
        rdata['nsites'] = dstore['rup/nsites'][:]
        totweight = rdata['nsites'].sum()
        et_ids = dstore['et_ids'][:]
        rlzs_by_gsim = self.full_lt.get_rlzs_by_gsim_list(et_ids)
        self.slice_by_g = getters.get_slice_by_g(rlzs_by_gsim)
        L = oq.imtls.size
        poes_shape = (sum(len(rbg) for rbg in rlzs_by_gsim), self.N, L)
        self.datastore.create_dset('poes', float, poes_shape)
        G = max(len(rbg) for rbg in rlzs_by_gsim)
        maxw = 2 * 1024**3 / (16 * G * self.M)  # at max 2 GB
        maxweight = min(
            numpy.ceil(totweight / (oq.concurrent_tasks or 1)), maxw)
        num_eff_rlzs = len(self.full_lt.sm_rlzs)
        U = 0
        Ta = 0
        self.datastore.swmr_on()
        smap = parallel.Starmap(conditional_spectrum, h5=self.datastore.hdf5)
        # IMPORTANT!! we rely on the fact that the classical part
        # of the calculation stores the ruptures in chunks of constant
        # grp_id, therefore it is possible to build (start, stop) slices
        for block in block_splitter(rdata, maxweight,
                                    operator.itemgetter('nsites'),
                                    operator.itemgetter('grp_id')):
            Ta += 1
            grp_id = block[0]['grp_id']
            trti = et_ids[grp_id][0] // num_eff_rlzs
            trt = self.trts[trti]
            G = len(rlzs_by_gsim[grp_id])
            cmaker = ContextMaker(
                trt, rlzs_by_gsim[grp_id],
                {'truncation_level': oq.truncation_level,
                 'maximum_distance': oq.maximum_distance,
                 'investigation_time': oq.investigation_time,
                 'imtls': oq.imtls})
            U = max(U, block.weight)
            slc = slice(block[0]['idx'], block[-1]['idx'] + 1)
            smap.submit((dstore, slc, cmaker, grp_id))
        results = smap.reduce(self.agg_result)
        return results

    def agg_result(self, css, result):
        """
        Collect the results coming from conditional_spectrum into self.results.

        :param acc: dictionary grp_id -> list
        :param result: dictionary grp_id -> list

        """
        with self.monitor('aggregating results'):
            [(grp_id, cs_mea_std)] = result.items()
            for sid in cs_mea_std:
                if grp_id in css:
                    if sid in css[grp_id].keys():
                        css[grp_id][sid].extend = cs_mea_std[sid]
                    else:
                        css[grp_id] = {sid: cs_mea_std[sid]}
                else:
                    css[grp_id] = {sid: cs_mea_std[sid]}
        return css

    def post_execute(self, results):
        for grp_id, css in results.items():
            # TODO poes is wrong and should be changed
            self.datastore['poes'][self.slice_by_g[grp_id]] = css
