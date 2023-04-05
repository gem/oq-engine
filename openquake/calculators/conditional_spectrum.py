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
import numpy

from openquake.baselib import general, performance
from openquake.commonlib.calc import compute_hazard_maps, get_mean_curve
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.contexts import read_cmakers
from openquake.hazardlib.calc.cond_spectra import get_cs_out, outdict
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32


# helper function to be used when saving the spectra as an array
def to_spectra(outdic, n, p):
    """
    :param outdic: dictionary rlz_id -> array MNOP
    :param n: site index in the range 0..N-1
    :param p: IMLs index in the range 0..P-1
    :returns: conditional spectra as an array of shape (R, M, 2)
    """
    R = len(outdic)
    M = len(outdic[0])
    out = numpy.zeros((R, M, 2))
    for r in range(R):
        c = outdic[r]
        out[r, :, 0] = numpy.exp(c[:, n, 1, p])  # NB: seems wrong!
        out[r, :, 1] = numpy.sqrt(c[:, n, 2, p])
    return out


@base.calculators.add('conditional_spectrum')
class ConditionalSpectrumCalculator(base.HazardCalculator):
    """
    Conditional spectrum calculator, to be used for few sites only
    """
    precalc = 'classical'
    accept_precalc = ['classical', 'disaggregation']

    def pre_execute(self):
        raise RuntimeError('Please use a more recent version of the engine '
                           'to run conditional spectrum calculations')

    def execute(self):
        """
        Compute the conditional spectrum in a sequential way.
        NB: since conditional spectra are meant to be computed only for few
        sites, there is no point in parallelizing: the computation is dominated
        by the time spent reading the contexts, not by the CPU.
        """
        assert self.N <= self.oqparam.max_sites_disagg, (
            self.N, self.oqparam.max_sites_disagg)
        oq = self.oqparam
        self.full_lt = self.datastore['full_lt']
        self.trts = list(self.full_lt.gsim_lt.values)
        self.imts = list(oq.imtls)
        imti = self.imts.index(oq.imt_ref)
        self.M = M = len(self.imts)
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        totrups = len(dstore['rup/mag'])
        logging.info('Reading {:_d} ruptures'.format(totrups))
        rdt = [('grp_id', U32), ('idx', U32)]
        rdata = numpy.zeros(totrups, rdt)
        rdata['idx'] = numpy.arange(totrups)
        rdata['grp_id'] = dstore['rup/grp_id'][:]
        self.periods = [from_string(imt).period for imt in self.imts]
        # extract imls from the "mean" hazard map
        curve = get_mean_curve(self.datastore, oq.imt_ref)
        # there is 1 site
        [self.imls] = compute_hazard_maps(curve, oq.imtls[oq.imt_ref], oq.poes)
        self.P = P = len(self.imls)
        self.datastore.create_dset(
            'cs-rlzs', float, (self.R, M, self.N, 2, self.P))
        self.datastore.set_shape_descr(
            'cs-rlzs', rlz_id=self.R, period=self.periods,  sid=self.N,
            cs=2, poe_id=P)
        self.datastore.create_dset('cs-stats', float, (1, M, self.N, 2, P))
        self.datastore.set_shape_descr(
            'cs-stats', stat='mean', period=self.periods, sid=self.N,
            cs=['spec', 'std'], poe_id=P)
        self.cmakers = read_cmakers(self.datastore)
        # self.datastore.swmr_on()
        # IMPORTANT!! we rely on the fact that the classical part
        # of the calculation stores the ruptures in chunks of constant
        # grp_id, therefore it is possible to build (start, stop) slices
        out = general.AccumDict()  # grp_id => dict

        # Computing CS
        for gid, start, stop in performance.idx_start_stop(rdata['grp_id']):
            cmaker = self.cmakers[gid]
            cmaker.poes = oq.poes
            ctxs = cmaker.read_ctxs(dstore, slice(start, stop))
            for ctx in ctxs:
                out += get_cs_out(cmaker, ctx, imti, self.imls)

        # Apply weights and get two dictionaries with integer keys
        # (corresponding to the rlz ID) and array values
        # of shape (M, N, 3, P) where:
        # M is the number of IMTs
        # N is the number of sites
        # 3 is the number of statistical momenta
        # P is the the number of IMLs
        outdic, outmean = self._apply_weights(out)

        # Computing standard deviation
        for gid, start, stop in performance.idx_start_stop(rdata['grp_id']):
            cmaker = self.cmakers[gid]
            cmaker.poes = oq.poes
            ctxs = cmaker.read_ctxs(dstore, slice(start, stop))
            for ctx in ctxs:
                res = get_cs_out(cmaker, ctx, imti, self.imls, outmean[0])
                for g in res:
                    out[g][:, :, 2] += res[g][:, :, 2]  # STDDEV
        return out

    def convert_and_save(self, dsetname, outdic):
        """
        Save the conditional spectra
        """
        for n in range(self.N):
            for p in range(self.P):  # shape (R, M, N, 2, P)
                self.datastore[dsetname][:, :, n, :, p] = to_spectra(
                    outdic, n, p)  # shape (R, M, 2)
        attrs = dict(imls=self.imls, periods=self.periods)
        if self.oqparam.poes:
            attrs['poes'] = self.oqparam.poes
        self.datastore.set_attrs(dsetname, **attrs)

    def post_execute(self, acc):
        # apply weights
        outdic, outmean = self._apply_weights(acc)
        # convert dictionaries into spectra and save them
        self.convert_and_save('cs-rlzs', outdic)
        self.convert_and_save('cs-stats', outmean)

    def _apply_weights(self, acc):
        # build conditional spectra for each realization
        rlzs_by_g = self.datastore['rlzs_by_g'][()]
        outdic = outdict(self.M, self.N, self.P, 0, self.R)
        for _g, rlzs in enumerate(rlzs_by_g):
            for r in rlzs:
                outdic[r] += acc[_g]
        self.convert_and_save('cs-rlzs', outdic)

        # build final conditional mean and std
        weights = self.datastore['weights'][:]
        outmean = outdict(self.M, self.N, self.P, 0, 1)  # dict with key 0
        for r, weight in enumerate(weights):
            outmean[0] += outdic[r] * weight

        return outdic, outmean
