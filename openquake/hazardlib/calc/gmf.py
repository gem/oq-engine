# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
import numpy
import pandas

from openquake.baselib.general import AccumDict
from openquake.baselib.performance import Monitor, compile
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.source.rupture import get_eid_rlz
from openquake.hazardlib.cross_correlation import NoCrossCorrelation
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib.imt import from_string

U32 = numpy.uint32
F32 = numpy.float32


def strip_zeros(data):
    for key, val in sorted(data.items()):
        if key in 'eid sid rlz':
            data[key] = numpy.concatenate(data[key], dtype=U32)
        else:
            data[key] = numpy.concatenate(data[key], dtype=F32)
    gmf_df = pandas.DataFrame(data)
    # remove the rows with all zero values
    cols = [col for col in gmf_df.columns if col not in {'eid', 'sid', 'rlz'}]
    df = gmf_df[cols]
    assert str(df.gmv_0.dtype) == 'float32', df.gmv_0.dtype
    ok = df.to_numpy().sum(axis=1) > 0
    return gmf_df[ok]


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


@compile(["float64[:,:](float64[:,:], boolean)",
          "float64[:](float64[:], boolean)",
          "float64(float64, boolean)"])
def exp(vals, notMMI):
    """
    Exponentiate the values unless the IMT is MMI
    """
    if notMMI:
        return numpy.exp(vals)
    return vals


@compile("(float32[:,:,:],float64[:,:],float64[:],float64[:],int64)")
def set_max_min(array, mean, max_iml, min_iml, mmi_index):
    N, M, E = array.shape

    # manage max_iml
    for m in range(M):
        iml = max_iml[m]
        for n in range(N):
            maxval = exp(mean[m, n], m!=mmi_index)
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


class GmfComputer(object):
    """
    Given an earthquake rupture, the ground motion field computer computes
    ground shaking over a set of sites, by randomly sampling a ground
    shaking intensity model.

    :param rupture:
        Rupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` sitecol:
        a complete SiteCollection

    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance

    :param correlation_model:
        Instance of a spatial correlation model object. See
        :mod:`openquake.hazardlib.correlation`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.

    :param cross_correl:
        Instance of a cross correlation model object. See
        :mod:`openquake.hazardlib.cross_correlation`. Can be ``None``, in which
        case non-cross-correlated ground motion fields are calculated.

    :param amplifier:
        None or an instance of Amplifier

    :param sec_perils:
        Tuple of secondary perils. See
        :mod:`openquake.hazardlib.sep`. Can be ``None``, in which
        case no secondary perils need to be evaluated.
    """
    # The GmfComputer is called from the OpenQuake Engine. In that case
    # the rupture is an higher level containing a
    # :class:`openquake.hazardlib.source.rupture.Rupture` instance as an
    # attribute. Then the `.compute(gsim, num_events, ms)` method is called and
    # a matrix of size (I, N, E) is returned, where I is the number of
    # IMTs, N the number of affected sites and E the number of events. The
    # seed is extracted from the underlying rupture.
    def __init__(self, rupture, sitecol, cmaker, correlation_model=None,
                 cross_correl=None, amplifier=None, sec_perils=()):
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
        self.correlation_model = correlation_model
        self.amplifier = amplifier
        self.sec_perils = sec_perils
        # `rupture` is an EBRupture instance in the engine
        if hasattr(rupture, 'source_id'):
            self.ebrupture = rupture
            self.source_id = rupture.source_id  # the underlying source
            self.seed = rupture.seed
            rupture = rupture.rupture  # the underlying rupture
        else:  # in the hazardlib tests
            self.ebrupture = {'e0': 0, 'n_occ': 1, 'seed': rupture.seed}
            self.source_id = '?'
            self.seed = rupture.seed
        ctxs = list(cmaker.get_ctx_iter([rupture], sitecol))
        if not ctxs:
            raise FarAwayRupture
        [self.ctx] = ctxs
        if correlation_model:  # store the filtered sitecol
            self.sites = sitecol.complete.filtered(self.ctx.sids)
        self.cross_correl = cross_correl or NoCrossCorrelation(
            cmaker.truncation_level)
        self.gmv_fields = [f'gmv_{m}' for m in range(len(cmaker.imts))]
        self.init_eid_rlz_sig_eps()

    def init_eid_rlz_sig_eps(self):
        """
        Initialize the attributes eid, rlz, sig, eps with shapes E, E, EM, EM
        """
        rlzs = numpy.concatenate(list(self.cmaker.gsims.values()))
        if isinstance(self.ebrupture, dict):  # with keys e0, n_occ, seed
            dic = self.ebrupture
        else:
            dic = vars(self.ebrupture)
        self.eid, self.rlz = get_eid_rlz(dic, rlzs, self.cmaker.scenario)
        self.E = E = len(self.eid)
        self.M = M = len(self.gmv_fields)
        self.sig = numpy.zeros((E, M), F32)  # same for all events
        self.eps = numpy.zeros((E, M), F32)  # not the same

    def build_sig_eps(self, se_dt):
        """
        :returns: a structured array of size E with fields
                  (eid, rlz_id, sig_inter_IMT, eps_inter_IMT)
        """
        sig_eps = numpy.zeros(self.E, se_dt)
        sig_eps['eid'] = self.eid
        sig_eps['rlz_id'] = self.rlz
        for m, imt in enumerate(self.cmaker.imtls):
            sig_eps[f'sig_inter_{imt}'] = self.sig[:, m]
            sig_eps[f'eps_inter_{imt}'] = self.eps[:, m]
        return sig_eps

    def update(self, data, array, rlzs, mean_stds, max_iml):
        sids = self.ctx.sids
        min_iml = self.cmaker.min_iml
        mag = self.ebrupture.rupture.mag
        mean = mean_stds[0]
        if len(mean.shape) == 3:  # shape (M, N, 1) for conditioned gmfs
            mean = mean[:, :, 0]
        mmi_index = -1
        for m, imt in enumerate(self.cmaker.imtls):
            if imt == 'MMI':
                mmi_index = m
        set_max_min(array, mean, max_iml, min_iml, mmi_index)
        for m, gmv_field in enumerate(self.gmv_fields):
            data[gmv_field].append(array[:, m].T.reshape(-1))

        N = len(array)
        n = 0
        for rlz in rlzs:
            eids = self.eid[self.rlz == rlz]
            E = len(eids)
            data['eid'].append(numpy.repeat(eids, N))
            data['sid'].append(numpy.tile(sids, E))
            data['rlz'].append(numpy.full(N * E, rlz, U32))
            if self.sec_perils:
                for e, eid in enumerate(eids):
                    gmfa = array[:, :, n + e].T  # shape (M, N)
                    for sp in self.sec_perils:
                        o = sp.compute(mag, zip(self.imts, gmfa), self.ctx)
                        for outkey, outarr in zip(sp.outputs, o):
                            data[outkey].append(outarr)
            n += E

    def compute_all(self, max_iml=None,
                    mmon=Monitor(), cmon=Monitor(), umon=Monitor()):
        """
        :returns: DataFrame with fields eid, rlz, sid, gmv_X, ...
        """
        with mmon:
            mean_stds = self.cmaker.get_mean_stds([self.ctx])  # (4, G, M, N)
            rng = numpy.random.default_rng(self.seed)
            if max_iml is None:
                M = len(self.cmaker.imts)
                max_iml = numpy.full(M, numpy.inf, float)

        data = AccumDict(accum=[])
        ne = 0
        for g, (gs, rlzs) in enumerate(self.cmaker.gsims.items()):
            num_events = numpy.isin(self.rlz, rlzs).sum()
            if num_events == 0:  # it may happen
                continue
            with cmon:
                arrayNME = self.compute(
                    gs, num_events, mean_stds[:, g], rng,
                    slice(ne, ne + num_events))
            with umon:
                self.update(data, arrayNME, rlzs,
                            mean_stds[:, g], max_iml)
            ne += num_events
        with umon:
            return strip_zeros(data)

    def compute(self, gsim, num_events, mean_stds, rng, slc=slice(None)):
        """
        :param gsim: GSIM used to compute mean_stds
        :param num_events: the number of seismic events
        :param mean_stds: array of shape (4, M, N)
        :param rng: random number generator for the rupture
        :returns: a 32 bit array of shape (N, M, E)
        """
        M = len(self.imts)
        result = numpy.zeros(
            (len(self.imts), len(self.ctx.sids), num_events), F32)
        num_sids = len(self.ctx.sids)
        ccdist = self.cross_correl.distribution
        # build arrays of random numbers of shape (M, N, E) and (M, E)
        intra_eps = [
            ccdist.rvs((num_sids, num_events), rng) for _ in range(M)]
        self.eps[slc] = self.cross_correl.get_inter_eps(
            self.imts, num_events, rng).T
        for m, imt in enumerate(self.imts):
            try:
                result[m] = self._compute(
                    mean_stds[:, m], m, imt, gsim, intra_eps[m], slc)
            except Exception as exc:
                raise RuntimeError(
                    '(%s, %s, source_id=%r) %s: %s' %
                    (gsim, imt, self.source_id,
                     exc.__class__.__name__, exc)
                ).with_traceback(exc.__traceback__)
        if self.amplifier:
            self.amplifier.amplify_gmfs(
                self.ctx.ampcode, result, self.imts, self.seed)
        return result.transpose(1, 0, 2)

    def _compute(self, mean_stds, m, imt, gsim, intra_eps, slc):
        im = imt.string
        if self.cmaker.truncation_level <= 1E-9:
            # for truncation_level = 0 there is only mean, no stds
            if self.correlation_model:
                raise ValueError('truncation_level=0 requires '
                                 'no correlation model')
            mean, _, _, _ = mean_stds
            gmf = exp(mean, im!='MMI')[:, None]
            gmf = gmf.repeat(len(intra_eps[0]), axis=1)
        elif gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == {StdDev.TOTAL}:
            # If the GSIM provides only total standard deviation, we need
            # to compute mean and total standard deviation at the sites
            # of interest.
            # In this case, we also assume no correlation model is used.
            if self.correlation_model:
                raise CorrelationButNoInterIntraStdDevs(
                    self.correlation_model, gsim)

            mean, sig, _, _ = mean_stds
            gmf = exp(mean[:, None] + sig[:, None] * intra_eps, im!='MMI')
            self.sig[slc, m] = numpy.nan
        else:
            mean, sig, tau, phi = mean_stds
            # the [:, None] is used to implement multiplication by row;
            # for instance if  a = [1 2], b = [[1 2] [3 4]] then
            # a[:, None] * b = [[1 2] [6 8]] which is the expected result;
            # otherwise one would get multiplication by column [[1 4] [3 8]]
            intra_res = phi[:, None] * intra_eps  # shape (N, E)

            if self.correlation_model is not None:
                intra_res = self.correlation_model.apply_correlation(
                    self.sites, imt, intra_res, phi)
                if len(intra_res.shape) == 1:  # a vector
                    intra_res = intra_res[:, None]

            inter_res = tau[:, None] * self.eps[slc, m]
            # shape (N, 1) * E => (N, E)
            gmf = exp(mean[:, None] + intra_res + inter_res, im!='MMI')
            self.sig[slc, m] = tau.max()  # from shape (N, 1) => scalar
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
     same results numpy random numbers generator needs to be seeded, see
     http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.seed.html

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
        Integer number of GMF realizations to compute.
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
        representing different realizations of ground shaking intensity
        for all sites in the collection. First dimension represents
        sites and second one is for realizations.
    """
    cmaker = ContextMaker(rupture.tectonic_region_type, {gsim: [0]},
                          dict(truncation_level=truncation_level,
                               imtls={str(imt): [1] for imt in imts}))
    cmaker.scenario = True
    rupture.seed = seed
    gc = GmfComputer(rupture, sites, cmaker, correlation_model)
    mean_stds = cmaker.get_mean_stds([gc.ctx])[:, 0]
    res = gc.compute(gsim, realizations, mean_stds,
                     numpy.random.default_rng(seed))
    return {imt: res[:, m] for m, imt in enumerate(gc.imts)}
