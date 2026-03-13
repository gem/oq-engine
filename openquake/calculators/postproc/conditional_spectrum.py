# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
"""
Conditional spectrum post-processor
"""
import logging
import numpy
from openquake.baselib import parallel, hdf5, sap
from openquake.baselib.python3compat import decode
from openquake.hazardlib.map_array import compute_hazard_maps
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import valid, InvalidFile
from openquake.hazardlib.contexts import read_cmakers, read_ctx_by_grp
from openquake.hazardlib.calc.cond_spectra import get_cs_out, outdict

U16 = numpy.uint16
U32 = numpy.uint32
TWO24 = 2 ** 24

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


def compute_cs(dstore, oq, N, M, P):
    """
    Compute the conditional spectrum in a sequential way.
    NB: since conditional spectra are meant to be computed only for few
    sites, there is no point in parallelizing: the computation is dominated
    by the time spent reading the contexts, not by the CPU.
    """
    full_lt = dstore['full_lt'].init()
    trt_rlzs = full_lt.get_trt_rlzs(dstore['trt_smrs'][:])
    R = full_lt.get_num_paths()
    imts = list(oq.imtls)
    imti = imts.index(oq.imt_ref)
    totrups = len(dstore['rup/mag'])
    logging.info('Reading {:_d} contexts'.format(totrups))
    rdt = [('grp_id', U32), ('idx', U32)]
    rdata = numpy.zeros(totrups, rdt)
    rdata['idx'] = numpy.arange(totrups)
    rdata['grp_id'] = dstore['rup/grp_id'][:]

    # extract imls from the "mean" hazard map
    if 'hcurves-stats' in dstore:  # shape (N, S, M, L1)
        curves = dstore.sel('hcurves-stats', stat='mean', imt=oq.imt_ref)
    else:  # there is only 1 realization
        curves = dstore.sel('hcurves-rlzs', rlz_id=0, imt=oq.imt_ref)
    imls = compute_hazard_maps(  # shape (N, L) => (N, P)
        curves[:, 0, 0, :], oq.imtls[oq.imt_ref], oq.poes)
    N, P = imls.shape
    cmakers = read_cmakers(dstore).to_array()

    # Computing CS
    toms = decode(dstore['toms'][:])
    ctx_by_grp = read_ctx_by_grp(dstore)
    dstore.swmr_on()
    smap = parallel.Starmap(get_cs_out, h5=dstore)
    for grp_id, ctx in ctx_by_grp.items():
        tom = valid.occurrence_model(toms[grp_id])
        cmaker = cmakers[grp_id]
        smap.submit((cmaker, ctx, imti, imls, tom))
    out = smap.reduce()

    # Apply weights and get two dictionaries with integer keys
    # (corresponding to the rlz ID) and array values
    # of shape (M, N, 3, P) where:
    # M is the number of IMTs
    # N is the number of sites
    # 3 is the number of statistical momenta
    # P is the the number of IMLs
    outdic, outmean = _apply_weights(dstore, out, N, R, M, P, trt_rlzs)

    # sanity check: the mean conditional spectrum must be close to the imls
    ref_idx = list(oq.imtls).index(oq.imt_ref)
    mean_cs = numpy.exp(outmean[0][ref_idx, :, 1, :])  # shape (N, P)
    for n in range(N):
        for p in range(P):
            diff = abs(1. - imls[n, p]/ mean_cs[n, p])
            if diff > .03:
                logging.warning('Conditional Spectrum vs mean IML\nfor '
                                'site_id=%d, poe=%s, imt=%s: %.5f vs %.5f',
                                n, oq.poes[p], oq.imt_ref,
                                mean_cs[n, p], imls[n, p])

    # Computing standard deviation
    dstore.swmr_on()
    smap = parallel.Starmap(get_cs_out, h5=dstore.hdf5)
    for grp_id, ctx in ctx_by_grp.items():
        cmaker = cmakers[grp_id]
        smap.submit((cmaker, ctx, imti, imls, tom, outmean[0]))
    for res in smap:
        for g in res:
            out[g][:, :, 2] += res[g][:, :, 2]  # STDDEV

    # apply weights
    outdic, outmean = _apply_weights(dstore, out, N, R, M, P, trt_rlzs)
    # convert dictionaries into spectra and save them
    convert_and_save(dstore, 'cs-rlzs', outdic, oq, N, R, P)
    convert_and_save(dstore, 'cs-stats', outmean, oq, N, R, P)


def convert_and_save(dstore, dsetname, outdic, oq, N, R, P):
    """
    Save the conditional spectra
    """
    spe = numpy.array([[to_spectra(outdic, n, p) for p in range(P)]
                       for n in range(N)])
    store_spectra(dstore, dsetname, R, oq, spe)


def _apply_weights(dstore, acc, N, R, M, P, trt_rlzs):
    # build conditional spectra for each realization
    outdic = outdict(M, N, P, 0, R)
    for g, trs in enumerate(trt_rlzs):
        if g in acc:  # missing in case_3, with a non-contributing TRT
            for r in trs % TWO24:
                outdic[r] += acc[g]

    # build final conditional mean and std
    weights = dstore['weights'][:]
    outmean = outdict(M, N, P, 0, 1)  # dict with key 0
    for r, weight in enumerate(weights):
        outmean[0] += outdic[r] * weight

    return outdic, outmean


def main(dstore):
    logging.warning('Conditional spectrum calculations are still '
                    'experimental')
    oq = dstore['oqparam']
    if not oq.cross_correl:
        raise InvalidFile("%(job_ini)s: you must specify cross_correlation"
                          % oq.inputs)
    if not oq.imt_ref:
        raise InvalidFile("%(job_ini)s: you must specify imt_ref" % oq.inputs)
    if not oq.poes:
        raise InvalidFile("%(job_ini)s: you must specify the poes" % oq.inputs)
    if list(oq.hazard_stats()) != ['mean']:
        raise InvalidFile('%(job_ini)s: only the mean is supported' % oq.inputs)

    sitecol = dstore['sitecol']
    N  = len(sitecol)
    M = len(oq.imtls)
    P = len(oq.poes)
    assert N <= oq.max_sites_disagg, (N, oq.max_sites_disagg)
    compute_cs(dstore, oq, N, M, P)


if __name__ == '__main__':
    sap.run(main)
