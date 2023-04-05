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

from openquake.baselib import parallel, hdf5
from openquake.baselib.python3compat import decode
from openquake.hazardlib.probability_map import compute_hazard_maps
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import valid
from openquake.hazardlib.contexts import read_cmakers, read_ctx_by_grp
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


def store_spectra(dstore, name, R, oq, spectra):
    """
    Store the conditional spectra array
    """
    N = len(spectra)
    stats = list(oq.hazard_stats())
    kind = 'rlz' if 'rlzs' in name else 'stat'
    dic = dict(shape_descr=['site_id', 'poe', kind, 'period'])
    dic['site_id'] = numpy.arange(N)
    dic[kind] = numpy.arange(R) if kind == 'rlz' else stats
    dic['poe'] = list(oq.poes)
    dic['period'] = [from_string(imt).period for imt in oq.imtls]
    hdf5.ArrayWrapper(spectra, dic, ['mea', 'std']).save(name, dstore.hdf5)
    # NB: the following would segfault
    # dstore.hdf5[name] = hdf5.ArrayWrapper(spectra, dic, ['mea', 'std'])


@base.calculators.add('conditional_spectrum')
class ConditionalSpectrumCalculator(base.HazardCalculator):
    """
    Conditional spectrum calculator, to be used for few sites only
    """
    precalc = 'classical'
    accept_precalc = ['classical', 'disaggregation']

    def execute(self):
        """
        Compute the conditional spectrum in a sequential way.
        NB: since conditional spectra are meant to be computed only for few
        sites, there is no point in parallelizing: the computation is dominated
        by the time spent reading the contexts, not by the CPU.
        """
        assert self.N <= self.oqparam.max_sites_disagg, (
            self.N, self.oqparam.max_sites_disagg)
        logging.warning('Conditional spectrum calculations are still '
                        'experimental')

        oq = self.oqparam
        self.full_lt = self.datastore['full_lt'].init()
        self.trts = list(self.full_lt.gsim_lt.values)
        self.imts = list(oq.imtls)
        imti = self.imts.index(oq.imt_ref)
        self.M = len(self.imts)
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
        if 'hcurves-stats' in dstore:  # shape (N, S, M, L1)
            curves = dstore.sel('hcurves-stats', stat='mean', imt=oq.imt_ref)
        else:  # there is only 1 realization
            curves = dstore.sel('hcurves-rlzs', rlz_id=0, imt=oq.imt_ref)
        self.imls = compute_hazard_maps(  # shape (N, L) => (N, P)
            curves[:, 0, 0, :], oq.imtls[oq.imt_ref], oq.poes)
        N, self.P = self.imls.shape
        self.cmakers = read_cmakers(self.datastore)

        # IMPORTANT!! we rely on the fact that the classical part
        # of the calculation stores the ruptures in chunks of constant
        # grp_id, therefore it is possible to build (start, stop) slices

        # Computing CS
        toms = decode(dstore['toms'][:])
        ctx_by_grp = read_ctx_by_grp(dstore)
        self.datastore.swmr_on()
        smap = parallel.Starmap(get_cs_out, h5=self.datastore)
        for gid, ctx in ctx_by_grp.items():
            tom = valid.occurrence_model(toms[gid])
            cmaker = self.cmakers[gid]
            smap.submit((cmaker, ctx, imti, self.imls, tom))
        out = smap.reduce()
        
        # Apply weights and get two dictionaries with integer keys
        # (corresponding to the rlz ID) and array values
        # of shape (M, N, 3, P) where:
        # M is the number of IMTs
        # N is the number of sites
        # 3 is the number of statistical momenta
        # P is the the number of IMLs
        outdic, outmean = self._apply_weights(out)

        # sanity check: the mean conditional spectrum must be close to the imls
        ref_idx = list(oq.imtls).index(oq.imt_ref)
        mean_cs = numpy.exp(outmean[0][ref_idx, :, 1, :])  # shape (N, P)
        for n in range(self.N):
            for p in range(self.P):
                diff = abs(1. - self.imls[n, p]/ mean_cs[n, p])
                if diff > .03:
                    logging.warning('Conditional Spectrum vs mean IML\nfor '
                                    'site_id=%d, poe=%s, imt=%s: %.5f vs %.5f',
                                    n, oq.poes[p], oq.imt_ref,
                                    mean_cs[n, p], self.imls[n, p])

        # Computing standard deviation
        smap = parallel.Starmap(get_cs_out, h5=self.datastore.hdf5)
        for gid, ctx in ctx_by_grp.items():
            cmaker = self.cmakers[gid]
            smap.submit((cmaker, ctx, imti, self.imls, tom, outmean[0]))
        for res in smap:
            for g in res:
                out[g][:, :, 2] += res[g][:, :, 2]  # STDDEV
        return out

    def convert_and_save(self, dsetname, outdic):
        """
        Save the conditional spectra
        """
        spe = numpy.array([[to_spectra(outdic, n, p) for p in range(self.P)]
                           for n in range(self.N)])
        store_spectra(self.datastore, dsetname, self.R, self.oqparam, spe)

    def post_execute(self, acc):
        # apply weights
        outdic, outmean = self._apply_weights(acc)
        # convert dictionaries into spectra and save them
        self.convert_and_save('cs-rlzs', outdic)
        self.convert_and_save('cs-stats', outmean)

    def _apply_weights(self, acc):
        # build conditional spectra for each realization
        outdic = outdict(self.M, self.N, self.P, 0, self.R)
        for g, rlzs in self.full_lt.rlzs_by_g.items():
            for r in rlzs:
                outdic[r] += acc[g]

        # build final conditional mean and std
        weights = self.datastore['weights'][:]
        outmean = outdict(self.M, self.N, self.P, 0, 1)  # dict with key 0
        for r, weight in enumerate(weights):
            outmean[0] += outdic[r] * weight

        return outdic, outmean
