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

from openquake.baselib import parallel, general
from openquake.hazardlib.contexts import read_cmakers
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32


def conditional_spectrum(dstore, slc, cmaker, monitor):
    """
    :param dstore:
        a DataStore instance
    :param slc:
        a slice of ruptures
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param monitor:
        monitor of the currently running job
    :returns:
        dictionary grp_id -> poes of shape (N, L, G)
    """
    with monitor('reading contexts', measuremem=True):
        dstore.open('r')
        allctxs, _close = cmaker.read_ctxs(dstore, slc)
    N, L, G = len(_close), cmaker.imtls.size, len(cmaker.gsims)
    acc = numpy.ones((N, L, G))
    for ctx, poes in cmaker.gen_ctx_poes(allctxs):
        acc *= ctx.get_probability_no_exceedance(poes, cmaker.tom)
    return {cmaker.grp_id: 1 - acc}


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
        trt_smrs = dstore['trt_smrs'][:]
        rlzs_by_gsim = self.full_lt.get_rlzs_by_gsim_list(trt_smrs)
        L = oq.imtls.size
        poes_shape = (sum(len(rbg) for rbg in rlzs_by_gsim), self.N, L)
        self.datastore.create_dset('poes', float, poes_shape)
        G = max(len(rbg) for rbg in rlzs_by_gsim)
        maxw = 2 * 1024**3 / (16 * G * self.M)  # at max 2 GB
        maxweight = min(
            numpy.ceil(totweight / (oq.concurrent_tasks or 1)), maxw)
        U = 0
        Ta = 0
        self.cmakers = read_cmakers(self.datastore)
        self.datastore.swmr_on()
        smap = parallel.Starmap(conditional_spectrum, h5=self.datastore.hdf5)
        # IMPORTANT!! we rely on the fact that the classical part
        # of the calculation stores the ruptures in chunks of constant
        # grp_id, therefore it is possible to build (start, stop) slices
        for block in general.block_splitter(rdata, maxweight,
                                            operator.itemgetter('nsites'),
                                            operator.itemgetter('grp_id')):
            Ta += 1
            grp_id = block[0]['grp_id']
            G = len(rlzs_by_gsim[grp_id])
            cmaker = self.cmakers[grp_id]
            U = max(U, block.weight)
            slc = slice(block[0]['idx'], block[-1]['idx'] + 1)
            smap.submit((dstore, slc, cmaker))
        results = smap.reduce(self.agg_result)
        return results

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results.

        :param acc: dictionary grp_id -> NLG
        :param result: dictionary grp_id -> NLG
        """
        with self.monitor('aggregating results'):
            [(grp_id, poes)] = result.items()
            if grp_id not in acc:
                acc[grp_id] = poes
            else:
                acc[grp_id] = 1 - (1 - acc[grp_id]) * (1 - poes)
        return acc

    def post_execute(self, acc):
        for grp_id, poes in acc.items():
            poes = poes.transpose(2, 0, 1)  # NLG -> GNL
            self.datastore['poes'][self.cmakers[grp_id].slc] = poes
