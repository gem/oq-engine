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
Conditional spectrum calculator, inspired by the disaggregation calculator
"""
import logging
import operator
import numpy

from openquake.baselib import parallel, general
from openquake.commonlib.calc import compute_hazard_maps
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.contexts import read_cmakers
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32


# helper function to be used when saving the spectra as an array
def to_spectra(nums, denums):
    """
    :param nums: a sequence of R components of kind "c", each with M values
    :param denums: a sequence of R components of kind "s", each with M values
    :returns: conditional spectra as an array of shape (R, 2, M)
    """
    out = []
    for num, denum in zip(nums, denums):
        mea, var = num / denum
        out.append((numpy.exp(mea), numpy.sqrt(var)))
    return numpy.array(out)  # shape R, 2, M


# the core task to be run in parallel
def conditional_spectrum(dstore, slc, cmaker, imti, imls, monitor):
    """
    :param dstore:
        a DataStore instance
    :param slc:
        a slice of contexts
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param imti:
        IMT index in the range 0..M-1
    :param imls:
        intensity measure levels associated to the IMT index
    :param monitor:
        monitor of the currently running job
    :returns:
        dictionary key -> conditional spectrum contribution
    """
    res = {}
    G = len(cmaker.gsims)
    with monitor('reading contexts', measuremem=True):
        dstore.open('r')
        ctxs = cmaker.read_ctxs(dstore, slc)
        c, s = cmaker.get_cs_contrib(ctxs, imti, imls)
        for g in range(G):
            res['_c', cmaker.start + g] = c[:, g]
            res['_s', cmaker.start + g] = s[:, g]
    return res


@base.calculators.add('conditional_spectrum')
class ConditionalSpectrumCalculator(base.HazardCalculator):
    """
    Conditional spectrum calculator, to be used for few sites only
    """
    precalc = 'classical'
    accept_precalc = ['classical', 'disaggregation']

    def pre_checks(self):
        """
        Check the number of sites and the absence of atomic groups
        """
        assert self.N == 1, self.N
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
        self.imts = list(oq.imtls)
        imti = self.imts.index(oq.imt_ref)
        self.M = len(self.imts)
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        totrups = len(dstore['rup/mag'])
        logging.info('Reading {:_d} ruptures'.format(totrups))
        rdt = [('grp_id', U16), ('nsites', U16), ('idx', U32)]
        rdata = numpy.zeros(totrups, rdt)
        rdata['idx'] = numpy.arange(totrups)
        rdata['grp_id'] = dstore['rup/grp_id'][:]
        rdata['nsites'] = [len(sids) for sids in dstore['rup/sids_']]
        totweight = rdata['nsites'].sum()
        trt_smrs = dstore['trt_smrs'][:]
        rlzs_by_gsim = self.full_lt.get_rlzs_by_gsim_list(trt_smrs)
        G_ = sum(len(rbg) for rbg in rlzs_by_gsim)
        self.periods = [from_string(imt).period for imt in self.imts]
        if oq.imls_ref:
            self.imls = oq.imls_ref
        else:  # extract imls from the "mean" hazard map
            curve = self.datastore.sel(
                'hcurves-stats', stat='mean')[0, 0, imti]
            [self.imls] = compute_hazard_maps(
                curve, oq.imtls[oq.imt_ref], oq.poes)  # there is 1 site
        self.P = P = len(self.imls)
        self.datastore.create_dset('cs-rlzs', float, (P, self.R, 2, self.M))
        self.datastore.set_shape_descr(
                'cs-rlzs', poe_id=P, rlz_id=self.R, cs=2, m=self.M)
        self.datastore.create_dset('cond-spectra', float, (P, 2, self.M))
        self.datastore.set_shape_descr(
            'cond-spectra', poe_id=P, cs=['spec', 'std'], period=self.periods)
        self.datastore.create_dset('_c', float, (G_, P, 2, self.M))
        self.datastore.create_dset('_s', float, (G_, P,))
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
            smap.submit((dstore, slc, cmaker, imti, self.imls))
        return smap.reduce()

    def post_execute(self, acc):
        # store the conditional spectrum contributions in the datasets _c, _s
        for (key, g_), arr in acc.items():
            self.datastore[key][g_] = arr

        # build conditional spectra for each realization
        rlzs_by_g = self.datastore['rlzs_by_g'][()]
        nums = numpy.zeros((self.P, self.R, 2, self.M))
        denums = numpy.zeros((self.P, self.R))
        for g_, rlzs in enumerate(rlzs_by_g):
            c = acc['_c', g_]
            s = acc['_s', g_]
            for r in rlzs:
                nums[:, r] += c
                denums[:, r] += s
        for p in range(self.P):
            self.datastore['cs-rlzs'][p] = to_spectra(nums[p], denums[p])

        # build mean spectrum
        weights = self.datastore['weights'][:]
        num = numpy.average(nums, weights=weights, axis=1)  # (P, 2, M)
        denum = numpy.average(denums, weights=weights, axis=1)  # (P,)
        self.datastore['cond-spectra'][:] = to_spectra(num, denum)
        attrs = dict(imls=self.imls, periods=self.periods)
        if self.oqparam.poes:
            attrs['poes'] = self.oqparam.poes
        self.datastore.set_attrs('cond-spectra', **attrs)
