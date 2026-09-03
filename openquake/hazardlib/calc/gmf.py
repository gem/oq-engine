# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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
Module :mod:`~openquake.hazardlib.calc.gmf` exports
:func:`ground_motion_fields`.
"""
import logging

import numpy as np
import pandas

from openquake.baselib import config
from openquake.baselib.general import AccumDict, humansize
from openquake.baselib.performance import Monitor, compile
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.source.rupture import EBRupture, get_eid_rlz
from openquake.hazardlib.correlation_models.cross_imt.no_cross_correlation \
    import NoCrossCorrelation
from openquake.hazardlib.correlation_models.base import (
    CorrelationContext, ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, RegularGridLayout)
from openquake.hazardlib.contexts import ContextMaker, FarAwayRupture
from openquake.hazardlib.imt import from_string

U8 = np.uint8
U16 = np.uint16
U32 = np.uint32
I64 = np.int64
F32 = np.float32
TRUNCATION_THRESHOLD = 1E-9
CE_MIN_SITES = 1_000


def _correlation_budget():
    """Return the configured per-worker correlation workspace budget."""
    return int(float(config.memory.correlated_gmf_gb) * 1024 ** 3)


def _dense_correlation_bytes(model, sites, num_imts):
    """Estimate peak bytes required by the existing dense factorization."""
    if isinstance(model, SpatialCorrelationModel):
        num_sites = len(sites.complete)
        matrices = num_imts + 2
        return matrices * num_sites ** 2 * 8
    dimension = num_imts * len(sites)
    return 3 * dimension ** 2 * 8


def _site_positions(complete, selected):
    """Return positions of selected site IDs in the complete collection."""
    complete_sids = np.asarray(complete.sids)
    selected_sids = np.asarray(selected.sids)
    order = np.argsort(complete_sids)
    sorted_sids = complete_sids[order]
    positions = np.searchsorted(sorted_sids, selected_sids)
    if (np.any(positions == len(sorted_sids)) or
            np.any(sorted_sids[positions] != selected_sids)):
        raise ValueError('Affected sites are absent from the complete grid')
    return order[positions]


class CorrelationButNoInterIntraStdDevs(Exception):
    def __init__(self, corr, gsim):
        self.corr = corr
        self.gsim = gsim

    def __str__(self):
        return '''\
You cannot use the correlation model %s with the GSIM %s, \
that defines only the total standard deviation. If you want to use a \
correlation model you have to select a GMPE that provides the inter and \
intra event standard deviations.''' % (
            self.corr.__class__.__name__, self.gsim.__class__.__name__)


@compile(["(float32[:,:], boolean)",
          "(float32[:], boolean)",
          "(float64, boolean)"])
def exp(vals, notMMI):
    """
    Exponentiate the values unless the IMT is MMI
    """
    if notMMI:
        return np.exp(vals)
    return vals


@compile("(float32[:,:,:],float32[:,:],float64[:],float64[:],int64)")
def set_max_min(array, mean, max_iml, min_iml, mmi_index):
    N, M, E = array.shape

    # manage max_iml
    for m in range(M):
        iml = max_iml[m]
        for n in range(N):
            # capping the gmv at the median value if val > max_iml[m]
            maxval = exp(mean[m, n], m != mmi_index)
            for e in range(E):
                val = array[n, m, e]
                if val > iml:
                    array[n, m, e] = maxval

    # manage min_iml
    for n in range(N):
        for e in range(E):
            # set to zero only if all IMTs are below the thresholds
            if (array[n, :, e] < min_iml).all():
                array[n, :, e] = 0


@compile("(uint32[:],uint32[:],uint32[:],uint32[:])")
def build_eid_sid_rlz(allrlzs, sids, eids, rlzs):
    eid_sid_rlz = np.zeros((3, len(sids) * len(eids)), U32)
    idx = 0
    for rlz in allrlzs:
        for eid in eids[rlzs == rlz]:
            for sid in sids:
                eid_sid_rlz[0, idx] = eid
                eid_sid_rlz[1, idx] = sid
                eid_sid_rlz[2, idx] = rlz
                idx += 1
    return eid_sid_rlz


def calc_gmf_simplified(ebrupture, sitecol, cmaker):
    """
    A simplified version of the GmfComputer for event based calculations.
    Used only for pedagogical purposes. Here is an example of usage:

    from unittest.mock import Mock
    import numpy
    from openquake.hazardlib import valid, contexts, site, geo
    from openquake.hazardlib.source.rupture import EBRupture, build_planar
    from openquake.hazardlib.calc.gmf import calc_gmf_simplified, GmfComputer

    imts = ['PGA']
    rlzs = np.arange(3, dtype=np.uint32)
    rlzs_by_gsim = {valid.gsim('BooreAtkinson2008'): rlzs}
    lons = [0., 0.]
    lats = [0., 1.]
    siteparams = Mock(reference_vs30_value=760.)
    sitecol = site.SiteCollection.from_points(lons, lats, sitemodel=siteparams)
    hypo = geo.point.Point(0, .5, 20)
    rup = build_planar(hypo, mag=7., rake=0.)
    cmaker = contexts.simple_cmaker(rlzs_by_gsim, imts, truncation_level=3.)
    ebr = EBRupture(rup, 0, 0, n_occ=2, id=1)
    ebr.seed = 42
    print(cmaker)
    print(sitecol.array)
    print(ebr)

    gmfa = calc_gmf_simplified(ebr, sitecol, cmaker)
    print(gmfa) # numbers considering the full site collection
    sites = site.SiteCollection.from_points([0], [1], sitemodel=siteparams)
    gmfa = calc_gmf_simplified(ebr, sites, cmaker)
    print(gmfa)  # different numbers considering half of the site collection
    """
    N = len(sitecol)
    M = len(cmaker.imtls)
    [ctx] = cmaker.get_ctxs([ebrupture.rupture], sitecol)
    mean, _sig, tau, phi = cmaker.get_mean_stds([ctx])  # shapes (G, M, N)
    rlzs = np.concatenate(list(cmaker.gsims.values()))
    _eid, rlz = get_eid_rlz(vars(ebrupture), rlzs, False)
    rng = np.random.default_rng(ebrupture.seed)
    between_correl = NoCrossCorrelation(cmaker.truncation_level_between)
    within_dist = NoCrossCorrelation(
        cmaker.truncation_level_within).distribution
    gmfs = []
    for g, (gs, rlzs) in enumerate(cmaker.gsims.items()):
        idxs, = np.where(np.isin(rlz, rlzs))
        E = len(idxs)
        # build arrays of random numbers of shape (M, N, E) and (M, E)
        within_eps = [within_dist.rvs((N, E), rng).astype(F32)
                      for _ in range(M)]
        eps = np.zeros((E, M), F32)
        eps[idxs] = between_correl.get_inter_eps(cmaker.imtls, E, rng).T
        gmf = np.zeros((M, N, E))
        for m, imt in enumerate(cmaker.imtls):
            within_res = phi[g, m, :, None] * within_eps  # shape (N, E)
            between_res = tau[g, m, :, None] * eps[idxs, m]  # shape (N, E)
            gmf[m] = np.exp(mean[g, m, :, None] + within_res + between_res)
        gmfs.append(gmf)
    return np.concatenate(gmfs)  # shape (M, N, E)


class GmfComputer(object):
    """
    Given an earthquake rupture, the GmfComputer computes
    ground shaking over a set of sites, by randomly sampling a ground
    shaking intensity model.

    :param rupture:
        EBRupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` sitecol:
        a complete SiteCollection

    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance

    :param within_event_model:
        Instance of a within-event correlation model object. See
        :mod:`openquake.hazardlib.correlation_models`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.

    :param between_event_model:
        Instance of a between-event correlation model object. See
        :mod:`openquake.hazardlib.correlation_models`. Can be ``None``, in which
        case non-cross-correlated ground motion fields are calculated.

    :param amplifier:
        None or an instance of Amplifier

    :param sec_perils:
        Tuple of secondary perils. See
        :mod:`openquake.hazardlib.sep`. Can be ``None``, in which
        case no secondary perils need to be evaluated.
    """
    mtp_dt = np.dtype([('rup_id', I64), ('site_id', U32),
                          ('gsim_id', U16), ('imt_id', U8),
                          ('mea', F32), ('tau', F32), ('phi', F32)])

    # The GmfComputer is called from the OpenQuake Engine. In that case
    # the rupture is an EBRupture instance containing a
    # :class:`openquake.hazardlib.source.rupture.Rupture` instance as an
    # attribute. Then the `.compute(gsim, num_events, ms)` method is called and
    # a matrix of size (M, N, E) is returned, where M is the number of
    # IMTs, N the number of affected sites and E the number of events. The
    # seed is extracted from the underlying rupture.
    def __init__(self, rupture, sitecol, cmaker, within_event_model=None,
                 between_event_model=None, amplifier=None, sec_perils=(),
                 **legacy):
        if 'correlation_model' in legacy:
            if within_event_model is not None:
                raise TypeError('Pass only within_event_model')
            within_event_model = legacy.pop('correlation_model')
        if 'cross_correl' in legacy:
            if between_event_model is not None:
                raise TypeError('Pass only between_event_model')
            between_event_model = legacy.pop('cross_correl')
        if legacy:
            raise TypeError('Unknown arguments: %s' % sorted(legacy))
        if len(sitecol) == 0:
            raise ValueError('No sites')
        elif len(cmaker.imtls) == 0:
            raise ValueError('No IMTs')
        elif len(cmaker.gsims) == 0:
            raise ValueError('No GSIMs')
        self.cmaker = cmaker
        self.imts = [from_string(imt) for imt in cmaker.imtls]
        self.cmaker = cmaker
        self.gsims = sorted(cmaker.gsims)
        self.within_event_model = within_event_model
        self.amplifier = amplifier
        self.sec_perils = sec_perils
        self.ebrupture = rupture
        self.rup_id = rupture.id
        self.seed = rupture.seed
        rupture = rupture.rupture  # the underlying rupture
        ctxs = list(cmaker.get_ctxs([rupture], sitecol))
        if not ctxs:
            raise FarAwayRupture
        [self.ctx] = ctxs
        self.N = len(self.ctx)
        if within_event_model:  # store the filtered sitecol
            self.sites = sitecol.complete.filtered(self.ctx.sids)
            within_event_model.validate_imts(self.imts)
        self.between_event_model = between_event_model or NoCrossCorrelation(
            cmaker.truncation_level_between)
        self.between_event_model.validate_imts(self.imts)
        self.correlation_context = CorrelationContext(
            mag=rupture.mag, rake=getattr(rupture, 'rake', None),
            trt=cmaker.trt)
        self._within_event_factor = None
        self._ce_factor = None
        self._ce_checked = False
        self.within_dist = NoCrossCorrelation(
            cmaker.truncation_level_within).distribution
        self.mea_tau_phi = []
        self.gmv_fields = [str(imt) for imt in cmaker.imts]
        self.mmi_index = -1
        for m, imt in enumerate(cmaker.imtls):
            if imt == 'MMI':
                self.mmi_index = m

    @property
    def correlation_model(self):
        """Compatibility alias for :attr:`within_event_model`."""
        return self.within_event_model

    @correlation_model.setter
    def correlation_model(self, model):
        self.within_event_model = model

    @property
    def cross_correl(self):
        """Compatibility alias for :attr:`between_event_model`."""
        return self.between_event_model

    @cross_correl.setter
    def cross_correl(self, model):
        self.between_event_model = model

    def init_eid_rlz_sig_eps(self):
        """
        Initialize the attributes eid, rlz, sig, eps with shapes E, E, EM, EM
        """
        self.rng = np.random.default_rng(self.seed)
        self.rlzs = np.concatenate(list(self.cmaker.gsims.values()))
        self.eid, self.rlz = get_eid_rlz(
            vars(self.ebrupture), self.rlzs, self.cmaker.scenario)
        self.E = E = len(self.eid)
        self.M = M = len(self.gmv_fields)
        self.sig = np.zeros((E, M), F32)  # same for all events
        self.between_eps = np.zeros((E, M), F32)  # not the same

    def build_sig_eps(self, se_dt, event_indices=None):
        """
        :returns: a structured array of size E with fields
                  (eid, rlz_id, sig_inter_IMT, eps_inter_IMT)
        """
        if event_indices is None:
            event_indices = np.arange(self.E)
        sig_eps = np.zeros(len(event_indices), se_dt)
        sig_eps['eid'] = self.eid[event_indices]
        sig_eps['rlz_id'] = self.rlz[event_indices]
        for m, imt in enumerate(self.cmaker.imtls):
            sig_eps[f'sig_inter_{imt}'] = self.sig[event_indices, m]
            sig_eps[f'eps_inter_{imt}'] = \
                self.between_eps[event_indices, m]
        return sig_eps

    def update(self, data, array, rlzs, mean, max_iml=None,
               event_indices=None):
        """
        Updates the data dictionary with the values coming from the array
        of GMVs. Also indirectly updates the arrays .sig and .eps.
        """
        min_iml = self.cmaker.min_iml
        mag = self.ebrupture.rupture.mag
        if max_iml is None:
            max_iml = np.full(self.M, np.inf, float)

        set_max_min(array, mean, max_iml, min_iml, self.mmi_index)
        data['gmv'].append(array)

        if self.sec_perils and event_indices is not None:
            for e in range(len(event_indices)):
                gmfa = array[:, :, e].T  # shape (M, N)
                self._update_secondary(data, gmfa, mag)
        elif self.sec_perils:
            n = 0
            for rlz in rlzs:
                eids = self.eid[self.rlz == rlz]
                E = len(eids)
                for e, _eid in enumerate(eids):
                    gmfa = array[:, :, n + e].T  # shape (M, N)
                    self._update_secondary(data, gmfa, mag)
                n += E

    def _update_secondary(self, data, gmfa, mag):
        """Append secondary-peril outputs for one event."""
        for sp in self.sec_perils:
            outputs = sp.compute(mag, zip(self.imts, gmfa), self.ctx)
            for outkey, outarr in zip(sp.outputs, outputs):
                key = f'{sp.__class__.__name__}_{outkey}'
                if outkey == 'Disp':
                    # Catarina says to ignore small displacements
                    outarr[outarr < 1e-4] = 0
                data[key].append(outarr)

    def strip_zeros(self, data, event_indices=None):
        """
        :returns: a DataFrame with the nonzero GMVs
        """
        # building an array of shape (3, NE)
        if event_indices is None:
            eid_sid_rlz = build_eid_sid_rlz(
                self.rlzs, self.ctx.sids, self.eid, self.rlz)
        else:
            num_sites = len(self.ctx.sids)
            eids = self.eid[event_indices]
            rlzs = self.rlz[event_indices]
            eid_sid_rlz = np.array([
                np.repeat(eids, num_sites),
                np.tile(self.ctx.sids, len(event_indices)),
                np.repeat(rlzs, num_sites)], dtype=U32)

        for key, val in sorted(data.items()):
            data[key] = np.concatenate(data[key], axis=-1, dtype=F32)
        gmv = data.pop('gmv')  # shape (N, M, E)
        ok = gmv.sum(axis=1).T.reshape(-1) > 0
        for m, gmv_field in enumerate(self.gmv_fields):
            data[gmv_field] = gmv[:, m].T.reshape(-1)

        # build dataframe
        df = pandas.DataFrame(data)
        df['eid'] = eid_sid_rlz[0]
        df['sid'] = eid_sid_rlz[1]
        df['rlz'] = eid_sid_rlz[2]

        # remove the rows with all zero values
        df = df[ok]

        # remove the rows with low intensity secondary perils to save
        # storage space (i.e. the computed seismic risk will be wrong)
        minimum = self.cmaker.oq.minimum_intensity
        for sec_imt in self.cmaker.oq.sec_imts:
            _col, imt = sec_imt.split('_')
            if imt in minimum:
                df = df[df[sec_imt] >= minimum[imt]]
        return df
    
    @staticmethod
    def get_symmetric_bounds(cov_matrix, level):
        """
        Calculates the lower and upper bound vectors for symmetric truncation
        based on the marginal standard deviations of the covariance matrix.
        """
        # Extract marginal standard deviations from the diagonal
        sigmas = np.sqrt(np.diag(cov_matrix))
        upper = level * sigmas
        return -upper, upper

    @property
    def tlb(self):
        return self.cmaker.truncation_level_between

    @property
    def tlw(self):
        return self.cmaker.truncation_level_within

    def compute_all(self, MNE=None, cmon=Monitor(), umon=Monitor()):
        """
        :returns: DataFrame with fields eid, rlz, sid, gmv_X, ...
        """
        max_iml = self.cmaker.oq.get_max_iml()
        self.init_eid_rlz_sig_eps()
        data = AccumDict(accum=[])
        conditioned = MNE is not None
        for g, (gs, rlzs) in enumerate(self.cmaker.gsims.items()):
            if not conditioned:
                with self.cmaker.gmf_mon:
                    mean_stds = self.cmaker.get_4MN([self.ctx], gs).astype(F32)
            gs.gid = self.cmaker.gid[g]
            idxs, = np.where(np.isin(self.rlz, rlzs))
            E = len(idxs)
            if E == 0:  # crucial for performance
                continue
            with cmon:
                E = len(idxs)
                result = np.zeros((len(self.imts), len(self.ctx.sids), E), F32)
                # arrays of random numbers of shape (M, N, E) and (M, E)
                within_eps = self._draw_within_eps(
                    E, correlate=not conditioned)
                # between_eps are used in _compute
                if self.tlb <= TRUNCATION_THRESHOLD:
                    self.between_eps[idxs] = 0.
                else:
                    self.between_eps[idxs] = \
                        self.between_event_model.get_inter_eps(
                            self.imts, E, self.rng).T
                mean = []
                for m, imt in enumerate(self.imts):
                    if conditioned:
                        result[m] = exp(MNE[g][m, :, :E], imt != 'MMI')
                        if self.amplifier:
                            self.amplifier.amplify_gmfs(
                                self.ctx.ampcode, result, m, imt, self.rng)
                        mean.append(MNE[g][m, :, E])
                    else:
                        ms = mean_stds[:, m]
                        mean.append(ms[0])
                        self._compute_update(
                            result, m, imt, gs, ms, idxs, within_eps)
            with umon:
                result = result.transpose(1, 0, 2)  # shape (N, M, E)
                self.update(data, result, rlzs, np.array(mean), max_iml)
        with umon:
            return self.strip_zeros(data)

    def compute_all_batches(self, cmon=Monitor(), umon=Monitor()):
        """Yield bounded GMF tables and their global event indices."""
        self.init_eid_rlz_sig_eps()
        if (self.within_event_model is not None and
                self.tlw > TRUNCATION_THRESHOLD):
            factor = self._get_ce_factor()
        else:
            factor = None
        if factor is None:
            indices = np.arange(self.E)
            yield self.compute_all(None, cmon, umon), indices, True
            return
        yield from self._compute_ce_batches(factor, cmon, umon)

    def _compute_ce_batches(self, factor, cmon, umon):
        """Yield unconditioned CE fields without forming the full cube."""
        max_iml = self.cmaker.oq.get_max_iml()
        batch_size = self._ce_batch_size(factor)
        streams = np.random.SeedSequence(self.seed).spawn(3)
        within_rng, between_rng, amplifier_rng = (
            np.random.default_rng(stream) for stream in streams)
        batches = []
        for g, (gs, rlzs) in enumerate(self.cmaker.gsims.items()):
            idxs, = np.where(np.isin(self.rlz, rlzs))
            if self.tlb > TRUNCATION_THRESHOLD:
                self.between_eps[idxs] = \
                    self.between_event_model.get_inter_eps(
                        self.imts, len(idxs), between_rng).T
            for start in range(0, len(idxs), batch_size):
                batches.append((g, gs, rlzs,
                                idxs[start:start + batch_size]))
        logging.info(
            'Streaming %d correlated fields in %d batches of at most %d',
            self.E, len(batches), batch_size)

        recorded_gsims = set()
        mean_stds_by_gsim = {}
        for number, (g, gs, rlzs, idxs) in enumerate(batches, 1):
            if g not in mean_stds_by_gsim:
                with self.cmaker.gmf_mon:
                    mean_stds_by_gsim[g] = self.cmaker.get_4MN(
                        [self.ctx], gs).astype(F32)
            gs.gid = self.cmaker.gid[g]
            record_stats = g not in recorded_gsims
            df = self._compute_ce_batch(
                factor, gs, rlzs, mean_stds_by_gsim[g], idxs, max_iml,
                within_rng, amplifier_rng, record_stats,
                cmon, umon)
            recorded_gsims.add(g)
            yield df, idxs, number == len(batches)

    def _ce_batch_size(self, factor):
        """Bound a batch by both FFT workspace and returned GMF rows."""
        fft_events = factor.batch_size(_correlation_budget())
        max_rows = int(config.memory.max_gmvs_chunk)
        output_events = max(1, max_rows // self.N)
        return min(fft_events, output_events)

    def _compute_ce_batch(self, factor, gs, rlzs, mean_stds, idxs,
                          max_iml, within_rng, amplifier_rng, record_stats,
                          cmon, umon):
        """Compute and tabulate one bounded group of CE realizations."""
        num_events = len(idxs)
        data = AccumDict(accum=[])
        with cmon:
            result = np.zeros((self.M, self.N, num_events), F32)
            within_eps = self._draw_ce_eps(
                factor, num_events, within_rng)
            mean = []
            for m, imt in enumerate(self.imts):
                ms = mean_stds[:, m]
                mean.append(ms[0])
                self._compute_update(
                    result, m, imt, gs, ms, idxs, within_eps,
                    amplifier_rng, record_stats)
        with umon:
            result = result.transpose(1, 0, 2)
            self.update(
                data, result, rlzs, np.array(mean), max_iml, idxs)
            return self.strip_zeros(data, idxs)

    def _get_ce_factor(self):
        """Return a cached CE factor when the large-grid path is eligible."""
        if self._ce_checked:
            return self._ce_factor
        self._ce_checked = True
        model = self.within_event_model
        dense_bytes = _dense_correlation_bytes(model, self.sites, self.M)
        dense_sites = (len(self.sites.complete)
                       if isinstance(model, SpatialCorrelationModel)
                       else len(self.sites))
        compatible = model.SUPPORTS_CIRCULANT_EMBEDDING
        if dense_sites < CE_MIN_SITES or not compatible:
            if dense_bytes > _correlation_budget():
                qualifier = ('too small for automatic circulant embedding'
                             if compatible else
                             'not enabled for circulant embedding')
                raise ValueError(
                    f'{model.__class__.__name__} is {qualifier}; its dense '
                    f'factorization requires about '
                    f'{humansize(dense_bytes)}')
            return None

        try:
            complete = self.sites.complete
            layout = RegularGridLayout.from_sites(complete)
            positions = _site_positions(complete, self.sites)
            site_indices = layout.site_indices[positions]
            self._ce_factor = CirculantEmbeddingFactor.build(
                model, self.imts, layout.grid_shape, layout.spacing,
                ResidualComponent.WITHIN_EVENT,
                self.correlation_context, site_indices)
        except ValueError as exc:
            if dense_bytes > _correlation_budget():
                raise ValueError(
                    f'Cannot sample {model.__class__.__name__} within the '
                    f'correlation memory budget: {exc}') from exc
            logging.warning(
                'Falling back to dense %s correlation: %s',
                model.__class__.__name__, exc)
            return None

        factor = self._ce_factor
        logging.info(
            'Using circulant embedding for %s: grid=%sx%s, '
            'occupancy=%.1f%%, embedding=%sx%s, factor=%s',
            model.__class__.__name__, *layout.grid_shape,
            100 * layout.occupancy, *factor.embedded_shape,
            humansize(factor.spectral_root.nbytes))
        return factor

    def _draw_ce_eps(self, factor, num_events, rng=None):
        """Draw correlated residual fields in bounded FFT batches."""
        if rng is None:
            rng = self.rng
        batch_size = min(
            num_events, factor.batch_size(_correlation_budget()))
        correlated = np.empty(
            (factor.output_size, num_events), dtype=F32)
        for start in range(0, num_events, batch_size):
            stop = min(start + batch_size, num_events)
            samples = self.within_dist.rvs(
                (stop - start, factor.input_size), rng)
            correlated[:, start:stop] = factor.apply(samples.T)
        return correlated.reshape(self.M, self.N, num_events)

    def _draw_within_eps(self, num_events, correlate=True):
        if self.tlw <= TRUNCATION_THRESHOLD:
            return np.zeros((self.M, self.N, num_events), F32)
        model = self.within_event_model
        if correlate and model is not None:
            factor = self._get_ce_factor()
            if factor is not None:
                return self._draw_ce_eps(factor, num_events)
        samples = np.asarray([
            self.within_dist.rvs((self.N, num_events), self.rng).astype(F32)
            for _ in range(self.M)])
        if (not correlate or model is None or
                isinstance(model, SpatialCorrelationModel)):
            return samples
        if self._within_event_factor is None:
            self._within_event_factor = model.factor(
                self.sites, self.imts, ResidualComponent.WITHIN_EVENT,
                self.correlation_context)
        flattened = samples.reshape(-1, num_events)
        correlated = self._within_event_factor.apply(flattened)
        return correlated.reshape(samples.shape).astype(F32)

    def _compute_update(self, result, m, imt, gs, ms, idxs, within_eps,
                        rng=None, record_stats=True):
        try:
            result[m] = self._compute(
                ms, m, imt, gs, within_eps[m], idxs, record_stats)
        except Exception as exc:
            if exc.__class__ is RuntimeError:
                msg = str(exc)
            else:
                msg = f'{exc.__class__.__name__}:{exc}'
            raise RuntimeError(
                '(%s, %s): %s' % (gs, imt, msg)
            ).with_traceback(exc.__traceback__)
        if self.amplifier:
            self.amplifier.amplify_gmfs(
                self.ctx.ampcode, result, m, imt,
                self.rng if rng is None else rng)

    def _compute(self, mean_stds, m, imt, gsim, within_eps, idxs,
                 record_stats=True):
        # regular case, sets self.sig, returns gmf
        im = imt.string
        mean, sig, tau, phi = mean_stds  # shapes N
        if self.cmaker.oq.mea_tau_phi and record_stats:
            min_iml = self.cmaker.min_iml[m]
            gmv = np.exp(mean)
            for s, sid in enumerate(self.ctx.sids):
                if gmv[s] > min_iml:
                    self.mea_tau_phi.append(
                        (self.rup_id, sid, gsim.gid, m,
                         mean[s], tau[s], phi[s]))

        if (self.tlw <= TRUNCATION_THRESHOLD and
                self.tlb <= TRUNCATION_THRESHOLD):
            # for zero between/within truncation there is only mean, no stds
            if self.within_event_model:
                raise ValueError('truncation_level_within=0 requires '
                                 'no correlation model')
            gmf = exp(mean, im != 'MMI')[:, np.newaxis].repeat(
                len(idxs), axis=1)
        elif gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == {StdDev.TOTAL}:
            # If the GSIM provides only total standard deviation, we need
            # to compute mean and total standard deviation at the sites
            # of interest.
            # In this case, we also assume no correlation model is used.
            if self.within_event_model:
                raise CorrelationButNoInterIntraStdDevs(
                    self.within_event_model, gsim)
            gmf = exp(mean[:, np.newaxis] + sig[:, np.newaxis] * within_eps,
                      im != 'MMI')
            self.sig[idxs, m] = np.nan
        else:
            # NB: [:, newaxis] is used to implement multiplication by row;
            # for instance, if  a = [1 2], b = [[1 2] [3 4]], then
            # a[:, newaxis] * b = [[1 2] [6 8]] which is the expected result;
            # otherwise one would get multiplication by column [[1 4] [3 8]]
            within_res = phi[:, np.newaxis] * within_eps  # shape (N, E)
            if (isinstance(
                    self.within_event_model, SpatialCorrelationModel) and
                    self._ce_factor is None):
                within_res = self.within_event_model.apply_correlation(
                    self.sites, imt, within_res, phi).astype(F32)
            between_res = tau[:, np.newaxis] * self.between_eps[idxs, m]
            # shape (N, 1) * E => (N, E)
            gmf = exp(mean[:, np.newaxis] + within_res + between_res,
                      im != 'MMI')
            self.sig[idxs, m] = tau.max()  # from shape (N, 1) => scalar
        return gmf  # shapes (N, E)


# this is not used in the engine; it is still useful for usage in IPython
# when demonstrating hazardlib capabilities
def ground_motion_fields(rupture, sites, imts, gsim, truncation_level,
                         realizations, correlation_model=None, seed=0):
    """
    Given an earthquake rupture, the ground motion field calculator computes
    ground shaking over a set of sites, by randomly sampling a ground shaking
    intensity model. A ground motion field represents a possible 'realization'
    of the ground shaking due to an earthquake rupture.

    .. note::

     This calculator is using random numbers. In order to reproduce the
     same results numpy random numbers generator needs to be seeded.

    :param openquake.hazardlib.source.rupture.Rupture rupture:
        Rupture to calculate ground motion fields radiated from.
    :param openquake.hazardlib.site.SiteCollection sites:
        Sites of interest to calculate GMFs.
    :param imts:
        List of intensity measure type objects (see
        :mod:`openquake.hazardlib.imt`).
    :param gsim:
        Ground-shaking intensity model, instance of subclass of either
        :class:`~openquake.hazardlib.gsim.base.GMPE` or
        :class:`~openquake.hazardlib.gsim.base.IPE`.
    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution
    :param realizations:
        Integer number of GMF simulations to compute.
    :param correlation_model:
        Instance of correlation model object. See
        :mod:`openquake.hazardlib.correlation`. Can be ``None``, in which case
        non-correlated ground motion fields are calculated. Correlation model
        is not used if ``truncation_level`` is zero.
    :param int seed:
        The seed used in the numpy random number generator
    :returns:
        Dictionary mapping intensity measure type objects (same
        as in parameter ``imts``) to 2d numpy arrays of floats,
        representing different simulations of ground shaking intensity
        for all sites in the collection. First dimension represents
        sites and second one is for simulations.
    """
    cmaker = ContextMaker(rupture.tectonic_region_type, {gsim: U32([0])},
                          dict(truncation_level=truncation_level,
                               imtls={str(imt): np.array([0.])
                                      for imt in imts}))
    cmaker.oq.calculation_mode = 'scenario'
    ebr = EBRupture(
        rupture, source_id=0, trt_smr=0, n_occ=realizations, id=0, e0=0)
    ebr.seed = seed
    N, E = len(sites), realizations
    gc = GmfComputer(ebr, sites, cmaker, correlation_model)
    df = gc.compute_all()
    res = {}
    for m, imt in enumerate(gc.imts):
        res[imt] = arr = np.zeros((N, E), F32)
        for sid, eid, gmv in zip(df.sid, df.eid, df[str(imt)]):
            arr[sid, eid] = gmv
    return res
