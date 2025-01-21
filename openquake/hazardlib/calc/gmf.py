# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
from openquake.hazardlib.source.rupture import EBRupture, get_eid_rlz
from openquake.hazardlib.cross_correlation import NoCrossCorrelation
from openquake.hazardlib.contexts import ContextMaker, FarAwayRupture
from openquake.hazardlib.imt import from_string

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
I64 = numpy.int64
F32 = numpy.float32


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
    eid_sid_rlz = numpy.zeros((3, len(sids) * len(eids)), U32)
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
    rlzs = numpy.arange(3, dtype=numpy.uint32)
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
    [ctx] = cmaker.get_ctx_iter([ebrupture.rupture], sitecol)
    mean, _sig, tau, phi = cmaker.get_mean_stds([ctx])  # shapes (G, M, N)
    rlzs = numpy.concatenate(list(cmaker.gsims.values()))
    _eid, rlz = get_eid_rlz(vars(ebrupture), rlzs, False)
    rng = numpy.random.default_rng(ebrupture.seed)
    cross_correl = NoCrossCorrelation(cmaker.truncation_level)
    ccdist = cross_correl.distribution
    gmfs = []
    for g, (gs, rlzs) in enumerate(cmaker.gsims.items()):
        idxs, = numpy.where(numpy.isin(rlz, rlzs))
        E = len(idxs)
        # build arrays of random numbers of shape (M, N, E) and (M, E)
        intra_eps = [ccdist.rvs((N, E), rng) for _ in range(M)]
        eps = numpy.zeros((E, M), F32)
        eps[idxs] = cross_correl.get_inter_eps(cmaker.imtls, E, rng).T
        gmf = numpy.zeros((M, N, E))
        for m, imt in enumerate(cmaker.imtls):
            intra_res = phi[g, m, :, None] * intra_eps  # shape (N, E)
            inter_res = tau[g, m, :, None] * eps[idxs, m]  # shape (N, E)
            gmf[m] = numpy.exp(mean[g, m, :, None] + intra_res + inter_res)
        gmfs.append(gmf)
    return numpy.concatenate(gmfs)  # shape (M, N, E)


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
    mtp_dt = numpy.dtype([('rup_id', I64), ('site_id', U32), ('gsim_id', U16),
                          ('imt_id', U8), ('mea', F32), ('tau', F32), ('phi', F32)])

    # The GmfComputer is called from the OpenQuake Engine. In that case
    # the rupture is an EBRupture instance containing a
    # :class:`openquake.hazardlib.source.rupture.Rupture` instance as an
    # attribute. Then the `.compute(gsim, num_events, ms)` method is called and
    # a matrix of size (M, N, E) is returned, where M is the number of
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
        self.ebrupture = rupture
        self.rup_id = rupture.id
        self.seed = rupture.seed
        rupture = rupture.rupture  # the underlying rupture
        ctxs = list(cmaker.get_ctx_iter([rupture], sitecol))
        if not ctxs:
            raise FarAwayRupture
        [self.ctx] = ctxs
        self.N = len(self.ctx)
        if correlation_model:  # store the filtered sitecol
            self.sites = sitecol.complete.filtered(self.ctx.sids)
        self.cross_correl = cross_correl or NoCrossCorrelation(
            cmaker.truncation_level)
        self.mea_tau_phi = []
        self.gmv_fields = [f'gmv_{m}' for m in range(len(cmaker.imts))]
        self.mmi_index = -1
        for m, imt in enumerate(cmaker.imtls):
            if imt == 'MMI':
                self.mmi_index = m

    def init_eid_rlz_sig_eps(self):
        """
        Initialize the attributes eid, rlz, sig, eps with shapes E, E, EM, EM
        """
        self.rlzs = numpy.concatenate(list(self.cmaker.gsims.values()))
        self.eid, self.rlz = get_eid_rlz(
            vars(self.ebrupture), self.rlzs, self.cmaker.scenario)
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

    def update(self, data, array, rlzs, mean, max_iml=None):
        """
        Updates the data dictionary with the values coming from the array
        of GMVs. Also indirectly updates the arrays .sig and .eps.
        """
        min_iml = self.cmaker.min_iml
        mag = self.ebrupture.rupture.mag
        if len(mean.shape) == 3:  # shape (M, N, 1) for conditioned gmfs
            mean = mean[:, :, 0]
        if max_iml is None:
            max_iml = numpy.full(self.M, numpy.inf, float)

        set_max_min(array, mean, max_iml, min_iml, self.mmi_index)
        data['gmv'].append(array)

        if self.sec_perils:
            n = 0
            for rlz in rlzs:
                eids = self.eid[self.rlz == rlz]
                E = len(eids)
                for e, eid in enumerate(eids):
                    gmfa = array[:, :, n + e].T  # shape (M, N)
                    for sp in self.sec_perils:
                        o = sp.compute(mag, zip(self.imts, gmfa), self.ctx)
                        for outkey, outarr in zip(sp.outputs, o):
                            data[outkey].append(outarr)
                n += E

    def strip_zeros(self, data):
        """
        :returns: a DataFrame with the nonzero GMVs
        """
        # building an array of shape (3, NE)
        eid_sid_rlz = build_eid_sid_rlz(
            self.rlzs, self.ctx.sids, self.eid, self.rlz)

        for key, val in sorted(data.items()):
            data[key] = numpy.concatenate(data[key], axis=-1, dtype=F32)
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
        return df[ok]

    def compute_all(self, mean_stds=None, max_iml=None,
                    mmon=Monitor(), cmon=Monitor(), umon=Monitor()):
        """
        :returns: DataFrame with fields eid, rlz, sid, gmv_X, ...
        """
        conditioned = mean_stds is not None
        self.init_eid_rlz_sig_eps()
        rng = numpy.random.default_rng(self.seed)
        data = AccumDict(accum=[])
        for g, (gs, rlzs) in enumerate(self.cmaker.gsims.items()):
            gs.gid = self.cmaker.gid[g]
            idxs, = numpy.where(numpy.isin(self.rlz, rlzs))
            E = len(idxs)
            if E == 0:  # crucial for performance
                continue
            if mean_stds is None:
                with mmon:
                    ms = self.cmaker.get_4MN([self.ctx], gs)
            else:  # conditioned
                ms = (mean_stds[0][g], mean_stds[1][g], mean_stds[2][g])
            with cmon:
                E = len(idxs)
                result = numpy.zeros(
                    (len(self.imts), len(self.ctx.sids), E), F32)
                ccdist = self.cross_correl.distribution
                if conditioned:
                    intra_eps = [None] * self.M
                else:
                    # arrays of random numbers of shape (M, N, E) and (M, E)
                    intra_eps = [ccdist.rvs((self.N, E), rng)
                                 for _ in range(self.M)]
                    self.eps[idxs] = self.cross_correl.get_inter_eps(
                        self.imts, E, rng).T
                for m, imt in enumerate(self.imts):
                    try:
                        result[m] = self._compute(
                            [arr[m] for arr in ms], m, imt, gs, intra_eps[m],
                            idxs, rng)
                    except Exception as exc:
                        raise RuntimeError(
                            '(%s, %s, %s): %s' %
                            (gs, imt, exc.__class__.__name__, exc)
                        ).with_traceback(exc.__traceback__)
                if self.amplifier:
                    self.amplifier.amplify_gmfs(
                        self.ctx.ampcode, result, self.imts, self.seed)
            with umon:
                result = result.transpose(1, 0, 2)  # shape (N, M, E)
                self.update(data, result, rlzs, ms[0], max_iml)
        with umon:
            return self.strip_zeros(data)

    def _compute(self, mean_stds, m, imt, gsim, intra_eps, idxs, rng=None):
        if len(mean_stds) == 3:  # conditioned GMFs
            # mea, tau, phi with shapes (N,1), (N,N), (N,N)
            mu_Y, cov_WY_WY, cov_BY_BY = mean_stds
            E = len(idxs)
            eps = self.cmaker.oq.correlation_cutoff
            if self.cmaker.truncation_level <= 1E-9:
                gmf = exp(mu_Y, imt.string != "MMI")
                gmf = gmf.repeat(E, axis=1)
            else:
                # add a cutoff to remove negative eigenvalues
                cov_Y_Y = cov_WY_WY + cov_BY_BY + numpy.eye(len(cov_WY_WY)) * eps
                arr = rng.multivariate_normal(
                    mu_Y.flatten(), cov_Y_Y, size=E,
                    check_valid="raise", tol=1e-5, method="cholesky")
                gmf = exp(arr, imt != "MMI").T
            return gmf  # shapes (N, E)

        # regular case, sets self.sig, returns gmf
        im = imt.string
        mean, sig, tau, phi = mean_stds  # shapes N
        if self.cmaker.oq.mea_tau_phi:
            min_iml = self.cmaker.min_iml[m]
            gmv = numpy.exp(mean)
            for s, sid in enumerate(self.ctx.sids):
                if gmv[s] > min_iml:
                    self.mea_tau_phi.append(
                        (self.rup_id, sid, gsim.gid, m, mean[s], tau[s], phi[s]))

        if self.cmaker.truncation_level <= 1E-9:
            # for truncation_level = 0 there is only mean, no stds
            if self.correlation_model:
                raise ValueError('truncation_level=0 requires '
                                 'no correlation model')
            gmf = exp(mean, im != 'MMI')[:, None].repeat(len(idxs), axis=1)
        elif gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == {StdDev.TOTAL}:
            # If the GSIM provides only total standard deviation, we need
            # to compute mean and total standard deviation at the sites
            # of interest.
            # In this case, we also assume no correlation model is used.
            if self.correlation_model:
                raise CorrelationButNoInterIntraStdDevs(
                    self.correlation_model, gsim)
            gmf = exp(mean[:, None] + sig[:, None] * intra_eps, im != 'MMI')
            self.sig[idxs, m] = numpy.nan
        else:
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

            inter_res = tau[:, None] * self.eps[idxs, m]
            # shape (N, 1) * E => (N, E)
            gmf = exp(mean[:, None] + intra_res + inter_res, im != 'MMI')
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
                               imtls={str(imt): numpy.array([0.])
                                      for imt in imts}))
    cmaker.scenario = True
    ebr = EBRupture(
        rupture, source_id=0, trt_smr=0, n_occ=realizations, id=0, e0=0)
    ebr.seed = seed
    N, E = len(sites), realizations
    gc = GmfComputer(ebr, sites, cmaker, correlation_model)
    df = gc.compute_all()
    res = {}
    for m, imt in enumerate(gc.imts):
        res[imt] = arr = numpy.zeros((N, E), F32)
        for sid, eid, gmv in zip(df.sid, df.eid, df[f'gmv_{m}']):
            arr[sid, eid] = gmv
    return res
