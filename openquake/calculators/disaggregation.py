# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
Disaggregation calculator core functionality
"""
import logging
import operator
import numpy

from openquake.baselib import parallel, hdf5
from openquake.baselib.general import AccumDict, gen_slices, get_indices
from openquake.baselib.python3compat import encode
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.tom import PoissonTOM
from openquake.calculators import getters
from openquake.calculators import base

weight = operator.attrgetter('weight')
DISAGG_RES_FMT = 'rlz-%(rlz)s-%(imt)s-%(sid)s-%(poe)s/'
BIN_NAMES = 'mag', 'dist', 'lon', 'lat', 'eps', 'trt'
POE_TOO_BIG = '''\
Site #%d: you are trying to disaggregate for poe=%s.
However the source model produces at most probabilities
of %.7f for rlz=#%d, IMT=%s.
The disaggregation PoE is too big or your model is wrong,
producing too small PoEs.'''


def _check_curve(sid, rlz, curve, imtls, poes_disagg):
    # there may be sites where the sources are too small to produce
    # an effect at the given poes_disagg
    bad = 0
    for imt in imtls:
        max_poe = curve[imt].max()
        for poe in poes_disagg:
            if poe > max_poe:
                logging.warning(POE_TOO_BIG, sid, poe, max_poe, rlz, imt)
                bad += 1
    return bool(bad)


def _8d_matrix(matrices, num_trts):
    # convert a dict trti -> matrix into a single matrix of shape (T, ...)
    trti = next(iter(matrices))
    mat = numpy.zeros((num_trts,) + matrices[trti].shape)
    for trti in matrices:
        mat[trti] = matrices[trti]
    return mat


def _iml2s(rlzs, iml_disagg, imtls, poes_disagg, curves):
    # a list of N arrays of shape (M, P) with intensities
    M = len(imtls)
    P = len(poes_disagg)
    imts = [from_string(imt) for imt in imtls]
    lst = []
    for s, curve in enumerate(curves):
        iml2 = numpy.empty((M, P))
        iml2.fill(numpy.nan)
        if poes_disagg == (None,):
            for m, imt in enumerate(imtls):
                iml2[m, 0] = imtls[imt]
        elif curve:
            for m, imt in enumerate(imtls):
                poes = curve[imt][::-1]
                imls = imtls[imt][::-1]
                iml2[m] = numpy.interp(poes_disagg, poes, imls)
        aw = hdf5.ArrayWrapper(
            iml2, dict(poes_disagg=poes_disagg, imts=imts, rlzi=rlzs[s]))
        lst.append(aw)
    return lst


def compute_disagg(dstore, slc, cmaker, iml2s, trti, bin_edges, monitor):
    # see https://bugs.launchpad.net/oq-engine/+bug/1279247 for an explanation
    # of the algorithm used
    """
    :param dstore:
        a :class:`openquake.baselib.datastore.DataStore` instance
    :param slc:
        a slice of ruptures
    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance
    :param iml2s:
        a list of N arrays of shape (M, P)
    :param dict trti:
        tectonic region type index
    :param bin_egdes:
        a quintet (mag_edges, dist_edges, lon_edges, lat_edges, eps_edges)
    :param monitor:
        monitor of the currently running job
    :returns:
        a dictionary sid -> 7D-array
    """
    dstore.open('r')
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    rupdata = {k: dstore['rup/' + k][slc] for k in dstore['rup']}
    result = {'trti': trti}
    # all the time is spent in collect_bin_data
    RuptureContext.temporal_occurrence_model = PoissonTOM(
        oq.investigation_time)
    pne_mon = monitor('disaggregate_pne', measuremem=False)
    mat_mon = monitor('build_disagg_matrix', measuremem=False)
    gmf_mon = monitor('computing mean_std', measuremem=False)
    for sid, arr in disagg.build_matrices(
            rupdata, sitecol, cmaker, iml2s,
            oq.num_epsilon_bins, bin_edges, pne_mon, mat_mon, gmf_mon):
        result[sid] = arr
    return result  # sid -> array


def agg_probs(*probs):
    """
    Aggregate probabilities withe the usual formula 1 - (1 - P1) ... (1 - Pn)
    """
    acc = 1. - probs[0]
    for prob in probs[1:]:
        acc *= 1. - prob
    return 1. - acc


@base.calculators.add('disaggregation')
class DisaggregationCalculator(base.HazardCalculator):
    """
    Classical PSHA disaggregation calculator
    """
    precalc = 'classical'
    accept_precalc = ['classical', 'disaggregation']

    def init(self):
        few = self.oqparam.max_sites_disagg
        if self.N > few:
            raise ValueError(
                'The max number of sites for disaggregation set in '
                'openquake.cfg is %d, but you have %s' % (few, self.N))
        super().init()

    def execute(self):
        """Performs the disaggregation"""
        return self.full_disaggregation()

    def get_curve(self, sid, rlz_by_sid):
        """
        Get the hazard curve for the given site ID.
        """
        imtls = self.oqparam.imtls
        ws = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        pgetter = getters.PmapGetter(self.datastore, ws, numpy.array([sid]))
        rlz = rlz_by_sid[sid]
        try:
            pmap = pgetter.get(rlz)
        except ValueError:  # empty pmaps
            logging.info(
                'hazard curve contains all zero probabilities; '
                'skipping site %d, rlz=%d', sid, rlz.ordinal)
            return
        if sid not in pmap:
            return
        poes = pmap[sid].convert(imtls)
        for imt_str in imtls:
            if all(x == 0.0 for x in poes[imt_str]):
                logging.info(
                    'hazard curve contains all zero probabilities; '
                    'skipping site %d, rlz=%d, IMT=%s',
                    sid, rlz.ordinal, imt_str)
                return
        return poes

    def check_poes_disagg(self, curves, rlzs):
        """
        Raise an error if the given poes_disagg are too small compared to
        the hazard curves.
        """
        oq = self.oqparam
        # there may be sites where the sources are too small to produce
        # an effect at the given poes_disagg
        ok_sites = []
        for sid in self.sitecol.sids:
            if curves[sid] is None:
                ok_sites.append(sid)
                continue
            bad = _check_curve(sid, rlzs[sid], curves[sid],
                               oq.imtls, oq.poes_disagg)
            if not bad:
                ok_sites.append(sid)
        if len(ok_sites) == 0:
            raise SystemExit('Cannot do any disaggregation')
        elif len(ok_sites) < self.N:
            logging.warning('Doing the disaggregation on' % self.sitecol)
        return ok_sites

    def full_disaggregation(self):
        """
        Run the disaggregation phase.
        """
        oq = self.oqparam
        tl = oq.truncation_level
        src_filter = SourceFilter(self.sitecol, oq.maximum_distance)
        if hasattr(self, 'csm'):
            for sg in self.csm.src_groups:
                if sg.atomic:
                    raise NotImplementedError(
                        'Atomic groups are not supported yet')
            if not self.csm.get_sources():
                raise RuntimeError('All sources were filtered away!')

        csm_info = self.datastore['csm_info']
        self.poes_disagg = oq.poes_disagg or (None,)
        self.imts = list(oq.imtls)
        if oq.rlz_index is None:
            try:
                rlzs = self.datastore['best_rlz'][()]
            except KeyError:
                rlzs = numpy.zeros(self.N, int)
        else:
            rlzs = [oq.rlz_index] * self.N

        if oq.iml_disagg:
            self.poe_id = {None: 0}
            curves = [None] * len(self.sitecol)  # no hazard curves are needed
            self.ok_sites = set(self.sitecol.sids)
        else:
            self.poe_id = {poe: i for i, poe in enumerate(oq.poes_disagg)}
            curves = [self.get_curve(sid, rlzs) for sid in self.sitecol.sids]
            self.ok_sites = set(self.check_poes_disagg(curves, rlzs))
        self.iml2s = _iml2s(rlzs, oq.iml_disagg, oq.imtls,
                            self.poes_disagg, curves)
        if oq.disagg_by_src:
            self.build_disagg_by_src()

        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

        # build trt_edges
        trts = tuple(csm_info.trts)
        trt_num = {trt: i for i, trt in enumerate(trts)}
        self.trts = trts

        # build mag_edges
        min_mag = csm_info.min_mag
        max_mag = csm_info.max_mag
        mag_edges = oq.mag_bin_width * numpy.arange(
            int(numpy.floor(min_mag / oq.mag_bin_width)),
            int(numpy.ceil(max_mag / oq.mag_bin_width) + 1))

        # build dist_edges
        maxdist = max(oq.maximum_distance(trt, max_mag) for trt in trts)
        dist_edges = oq.distance_bin_width * numpy.arange(
            0, int(numpy.ceil(maxdist / oq.distance_bin_width) + 1))

        # build eps_edges
        eps_edges = numpy.linspace(-tl, tl, oq.num_epsilon_bins + 1)

        # build lon_edges, lat_edges per sid
        bbs = src_filter.get_bounding_boxes(mag=max_mag)
        lon_edges, lat_edges = {}, {}  # by sid
        for sid, bb in zip(self.sitecol.sids, bbs):
            lon_edges[sid], lat_edges[sid] = disagg.lon_lat_bins(
                bb, oq.coordinate_bin_width)
        self.bin_edges = mag_edges, dist_edges, lon_edges, lat_edges, eps_edges
        self.save_bin_edges()

        self.imldict = {}  # sid, rlzi, poe, imt -> iml
        for s in self.sitecol.sids:
            iml2 = self.iml2s[s]
            r = rlzs[s]
            logging.info('Site #%d, disaggregating for rlz=#%d', s, r)
            for p, poe in enumerate(self.poes_disagg):
                for m, imt in enumerate(oq.imtls):
                    self.imldict[s, r, poe, imt] = iml2[m, p]

        # submit disagg tasks
        gid = self.datastore['rup/grp_id'][()]
        indices_by_grp = get_indices(gid)  # grp_id -> [(start, stop),...]
        blocksize = len(gid) // (oq.concurrent_tasks or 1) + 1
        allargs = []
        for grp_id, trt in csm_info.trt_by_grp.items():
            trti = trt_num[trt]
            rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(grp_id)
            cmaker = ContextMaker(
                trt, rlzs_by_gsim,
                {'truncation_level': oq.truncation_level,
                 'maximum_distance': src_filter.integration_distance,
                 'filter_distance': oq.filter_distance, 'imtls': oq.imtls})
            for start, stop in indices_by_grp[grp_id]:
                for slc in gen_slices(start, stop, blocksize):
                    allargs.append((self.datastore, slc, cmaker,
                                    self.iml2s, trti, self.bin_edges))
        self.datastore.swmr_on()
        results = parallel.Starmap(
            compute_disagg, allargs, h5=self.datastore.hdf5
        ).reduce(self.agg_result, AccumDict(accum={}))
        self.datastore.open('r+')
        return results  # sid -> trti-> 7D array

    def agg_result(self, acc, result):
        """
        Collect the results coming from compute_disagg into self.results.

        :param acc: dictionary sid -> trti -> 7D array
        :param result: dictionary with the result coming from a task
        """
        # this is fast
        trti = result.pop('trti')
        for sid, arr in result.items():
            acc[sid][trti] = agg_probs(acc[sid].get(trti, 0), arr)
        return acc

    def save_bin_edges(self):
        """
        Save disagg-bins
        """
        b = self.bin_edges
        for sid in self.sitecol.sids:
            bins = disagg.get_bins(b, sid)
            shape = [len(bin) - 1 for bin in bins] + [len(self.trts)]
            shape_dic = dict(zip(BIN_NAMES, shape))
            if sid == 0:
                logging.info('nbins=%s for site=#%d', shape_dic, sid)
            matrix_size = numpy.prod(shape)
            if matrix_size > 1E7:
                raise ValueError(
                    'The disaggregation matrix for site #%d is too large '
                    '(%d elements): fix the binnning!' % (sid, matrix_size))
        self.datastore['disagg-bins/mags'] = b[0]
        self.datastore['disagg-bins/dists'] = b[1]
        for sid in self.sitecol.sids:
            self.datastore['disagg-bins/lons/sid-%d' % sid] = b[2][sid]
            self.datastore['disagg-bins/lats/sid-%d' % sid] = b[3][sid]
        self.datastore['disagg-bins/eps'] = b[4]

    def post_execute(self, results):
        """
        Save all the results of the disaggregation. NB: the number of results
        to save is #sites * #rlzs * #disagg_poes * #IMTs.

        :param results:
            a dictionary sid -> trti -> disagg matrix
        """
        self.datastore.open('r+')
        T = len(self.trts)
        # build a dictionary sid -> 8D matrix of shape (T, ..., M, P)
        results = {sid: _8d_matrix(dic, T) for sid, dic in results.items()}

        # get the number of outputs
        shp = (len(self.sitecol), len(self.poes_disagg), len(self.imts))
        logging.info('Extracting and saving the PMFs for %d outputs '
                     '(N=%s, P=%d, M=%d)', numpy.prod(shp), *shp)
        self.save_disagg_result(results, trts=encode(self.trts))

    def save_disagg_result(self, results, **attrs):
        """
        Save the computed PMFs in the datastore

        :param results:
            an 8D-matrix of shape (T, .., M, P)
        """
        for sid, matrix8 in results.items():
            rlzi = self.iml2s[sid].rlzi
            for p, poe in enumerate(self.poes_disagg):
                for m, imt in enumerate(self.imts):
                    self._save_result(
                        'disagg', sid, rlzi, poe, imt, matrix8[..., m, p, :])
        self.datastore.set_attrs('disagg', **attrs)

    def _save_result(self, dskey, site_id, rlz_id, poe, imt_str, matrix6):
        disagg_outputs = self.oqparam.disagg_outputs
        lon = self.sitecol.lons[site_id]
        lat = self.sitecol.lats[site_id]
        disp_name = dskey + '/' + DISAGG_RES_FMT % dict(
            rlz=rlz_id, imt=imt_str, sid='sid-%d' % site_id,
            poe='poe-%d' % self.poe_id[poe])
        mag, dist, lonsd, latsd, eps = self.bin_edges
        lons, lats = lonsd[site_id], latsd[site_id]
        with self.monitor('extracting PMFs'):
            poe_agg = []
            aggmatrix = agg_probs(*matrix6)
            for key, fn in disagg.pmf_map.items():
                if not disagg_outputs or key in disagg_outputs:
                    pmf = fn(matrix6 if key.endswith('TRT') else aggmatrix)
                    self.datastore[disp_name + key] = pmf
                    poe_agg.append(1. - numpy.prod(1. - pmf))

        attrs = self.datastore.hdf5[disp_name].attrs
        attrs['site_id'] = site_id
        attrs['rlzi'] = rlz_id
        attrs['imt'] = imt_str
        attrs['iml'] = self.imldict[site_id, rlz_id, poe, imt_str]
        attrs['mag_bin_edges'] = mag
        attrs['dist_bin_edges'] = dist
        attrs['lon_bin_edges'] = lons
        attrs['lat_bin_edges'] = lats
        attrs['eps_bin_edges'] = eps
        attrs['trt_bin_edges'] = self.trts
        attrs['location'] = (lon, lat)
        # sanity check: all poe_agg should be the same
        attrs['poe_agg'] = poe_agg
        if poe and site_id in self.ok_sites:
            attrs['poe'] = poe
            poe_agg = numpy.mean(attrs['poe_agg'])
            if abs(1 - poe_agg / poe) > .1:
                logging.warning(
                    'Site #%d: poe_agg=%s is quite different from the expected'
                    ' poe=%s; perhaps the number of intensity measure'
                    ' levels is too small?', site_id, poe_agg, poe)

    def build_disagg_by_src(self):
        """
        :param dstore: a datastore
        :param iml2s: N arrays of IMLs with shape (M, P)
        """
        logging.warning('Disaggregation by source is experimental')
        oq = self.oqparam
        ws = [rlz.weight for rlz in self.rlzs_assoc.realizations]
        pgetter = getters.PmapGetter(self.datastore, ws, self.sitecol.sids)
        groups = list(self.datastore['rlzs_by_grp'])
        M = len(oq.imtls)
        P = len(self.poes_disagg)
        for sid in self.sitecol.sids:
            poes = numpy.zeros((M, P, len(groups)))
            iml2 = self.iml2s[sid]
            for g, grp_id in enumerate(groups):
                pcurve = pgetter.get_pcurve(sid, iml2.rlzi, int(grp_id[4:]))
                if pcurve is None:
                    continue
                for m, imt in enumerate(oq.imtls):
                    xs = oq.imtls[imt]
                    ys = pcurve.array[oq.imtls(imt), 0]
                    poes[m, :, g] = numpy.interp(iml2[m], xs, ys)
            for m, imt in enumerate(oq.imtls):
                for p, poe in enumerate(self.poes_disagg):
                    pref = ('iml-%s' % oq.iml_disagg[imt] if poe is None
                            else 'poe-%s' % poe)
                    name = 'disagg_by_src/%s-%s-sid-%s' % (pref, imt, sid)
                    if poes[m, p].sum():  # nonzero contribution
                        poe_agg = 1 - numpy.prod(1 - poes[m, p])
                        if poe and abs(1 - poe_agg / poe) > .1:
                            logging.warning(
                                'poe_agg=%s is quite different from '
                                'the expected poe=%s', poe_agg, poe)
                        self.datastore[name] = poes[m, p]
                        self.datastore.set_attrs(name, poe_agg=poe_agg)
