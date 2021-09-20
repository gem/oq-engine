# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
import time
import numpy
import scipy.stats

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import decode
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.imt import from_string

U32 = numpy.uint32
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


def rvs(distribution, *size):
    array = distribution.rvs(size)
    return array


def to_imt_unit_values(vals, imt):
    """
    Exponentiate the values unless the IMT is MMI
    """
    if str(imt) == 'MMI':
        return vals
    return numpy.exp(vals)


class GmfComputer(object):
    """
    Given an earthquake rupture, the ground motion field computer computes
    ground shaking over a set of sites, by randomly sampling a ground
    shaking intensity model.

    :param rupture:
        Rupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` sitecol:
        a complete SiteCollection

    :param imts:
        a sorted list of Intensity Measure Type strings

    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance

    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution, or ``None``.

    :param correlation_model:
        Instance of correlation model object. See
        :mod:`openquake.hazardlib.correlation`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.

    :param amplifier:
        None or an instance of Amplifier
    """
    # The GmfComputer is called from the OpenQuake Engine. In that case
    # the rupture is an higher level containing a
    # :class:`openquake.hazardlib.source.rupture.Rupture` instance as an
    # attribute. Then the `.compute(gsim, num_events, ms)` method is called and
    # a matrix of size (I, N, E) is returned, where I is the number of
    # IMTs, N the number of affected sites and E the number of events. The
    # seed is extracted from the underlying rupture.
    def __init__(self, rupture, sitecol, cmaker, correlation_model=None,
                 amplifier=None, sec_perils=()):
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
            rupture = rupture.rupture  # the underlying rupture
        else:  # in the hazardlib tests
            self.source_id = '?'
        self.seed = rupture.rup_id
        self.ctx, sites, dctx = cmaker.make_contexts(sitecol, rupture)
        vars(self.ctx).update(vars(dctx))
        for par in sites.array.dtype.names:
            setattr(self.ctx, par, sites[par])
        self.sids = sites.sids
        if correlation_model:  # store the filtered sitecol
            self.sites = sitecol.complete.filtered(self.sids)
        if cmaker.trunclevel is None:
            self.distribution = scipy.stats.norm()
        elif cmaker.trunclevel == 0:
            self.distribution = None
        else:
            assert cmaker.trunclevel > 0, cmaker.trunclevel
            self.distribution = scipy.stats.truncnorm(
                - cmaker.trunclevel, cmaker.trunclevel)

    def compute_all(self, sig_eps=None):
        """
        :returns: (dict with fields eid, sid, gmv_X, ...), dt
        """
        min_iml = self.cmaker.min_iml
        rlzs_by_gsim = self.cmaker.gsims
        t0 = time.time()
        sids = self.sids
        eids_by_rlz = self.ebrupture.get_eids_by_rlz(rlzs_by_gsim)
        mag = self.ebrupture.rupture.mag
        data = AccumDict(accum=[])
        mean_stds = self.cmaker.get_mean_stds([self.ctx], StdDev.EVENT)
        # G arrays of shape (O, N, M)
        for g, (gs, rlzs) in enumerate(rlzs_by_gsim.items()):
            num_events = sum(len(eids_by_rlz[rlz]) for rlz in rlzs)
            if num_events == 0:  # it may happen
                continue
            # NB: the trick for performance is to keep the call to
            # .compute outside of the loop over the realizations;
            # it is better to have few calls producing big arrays
            array, sig, eps = self.compute(gs, num_events, mean_stds[g])
            M, N, E = array.shape
            for n in range(N):
                for e in range(E):
                    if (array[:, n, e] < min_iml).all():
                        array[:, n, e] = 0
            array = array.transpose(1, 0, 2)  # from M, N, E to N, M, E
            n = 0
            for rlz in rlzs:
                eids = eids_by_rlz[rlz]
                for ei, eid in enumerate(eids):
                    gmfa = array[:, :, n + ei]  # shape (N, M)
                    if sig_eps is not None:
                        tup = tuple([eid, rlz] + list(sig[:, n + ei]) +
                                    list(eps[:, n + ei]))
                        sig_eps.append(tup)
                    items = []
                    for sp in self.sec_perils:
                        o = sp.compute(mag, zip(self.imts, gmfa.T), self.ctx)
                        for outkey, outarr in zip(sp.outputs, o):
                            items.append((outkey, outarr))
                    for i, gmv in enumerate(gmfa):
                        if gmv.sum() == 0:
                            continue
                        data['sid'].append(sids[i])
                        data['eid'].append(eid)
                        data['rlz'].append(rlz)  # used in compute_gmfs_curves
                        for m in range(M):
                            data[f'gmv_{m}'].append(gmv[m])
                        for outkey, outarr in items:
                            data[outkey].append(outarr[i])
                        # gmv can be zero due to the minimum_intensity, coming
                        # from the job.ini or from the vulnerability functions
                n += len(eids)
        return data, time.time() - t0

    def compute(self, gsim, num_events, mean_stds):
        """
        :param gsim: GSIM used to compute mean_stds
        :param num_events: the number of seismic events
        :param mean_stds: array of shape O, M, N
        :returns:
            a 32 bit array of shape (num_imts, num_sites, num_events) and
            two arrays with shape (num_imts, num_events): sig for stddev_inter
            and eps for the random part
        """
        result = numpy.zeros((len(self.imts), len(self.sids), num_events), F32)
        sig = numpy.zeros((len(self.imts), num_events), F32)
        eps = numpy.zeros((len(self.imts), num_events), F32)
        numpy.random.seed(self.seed)
        for imti, imt in enumerate(self.imts):
            try:
                result[imti], sig[imti], eps[imti] = self._compute(
                     mean_stds[:, imti], num_events, imt, gsim)
            except Exception as exc:
                raise RuntimeError(
                    '(%s, %s, source_id=%r) %s: %s' %
                    (gsim, imt, decode(self.source_id),
                     exc.__class__.__name__, exc)
                ).with_traceback(exc.__traceback__)
        if self.amplifier:
            self.amplifier.amplify_gmfs(
                self.ctx.ampcode, result, self.imts, self.seed)
        return result, sig, eps

    def _compute(self, mean_stds, num_events, imt, gsim):
        """
        :param mean_stds: array of shape (O, N)
        :param num_events: the number of seismic events
        :param imt: an IMT instance
        :param gsim: a GSIM instance
        :returns: (gmf(num_sites, num_events), stddev_inter(num_events),
                   epsilons(num_events))
        """
        num_sids = len(self.sids)
        num_stds = len(mean_stds)
        if num_stds == 1:
            # for truncation_level = 0 there is only mean, no stds
            if self.correlation_model:
                raise ValueError('truncation_level=0 requires '
                                 'no correlation model')
            mean = mean_stds[0]
            gmf = to_imt_unit_values(mean, imt)
            gmf.shape += (1, )
            gmf = gmf.repeat(num_events, axis=1)
            return (gmf,
                    numpy.zeros(num_events, F32),
                    numpy.zeros(num_events, F32))
        elif num_stds == 2:
            # If the GSIM provides only total standard deviation, we need
            # to compute mean and total standard deviation at the sites
            # of interest.
            # In this case, we also assume no correlation model is used.
            if self.correlation_model:
                raise CorrelationButNoInterIntraStdDevs(
                    self.correlation_model, gsim)

            mean, stddev_total = mean_stds
            stddev_total = stddev_total.reshape(stddev_total.shape + (1, ))
            mean = mean.reshape(mean.shape + (1, ))

            total_residual = stddev_total * rvs(
                self.distribution, num_sids, num_events)
            gmf = to_imt_unit_values(mean + total_residual, imt)
            stdi = numpy.nan
            epsilons = numpy.empty(num_events, F32)
            epsilons.fill(numpy.nan)
        elif num_stds == 3:
            mean, stddev_inter, stddev_intra = mean_stds
            stddev_intra = stddev_intra.reshape(stddev_intra.shape + (1, ))
            stddev_inter = stddev_inter.reshape(stddev_inter.shape + (1, ))
            mean = mean.reshape(mean.shape + (1, ))
            intra_residual = stddev_intra * rvs(
                self.distribution, num_sids, num_events)

            if self.correlation_model is not None:
                intra_residual = self.correlation_model.apply_correlation(
                    self.sites, imt, intra_residual, stddev_intra)
                sh = intra_residual.shape
                if len(sh) == 1:  # a vector
                    intra_residual = intra_residual.reshape(sh + (1,))

            epsilons = rvs(self.distribution, num_events)
            inter_residual = stddev_inter * epsilons

            gmf = to_imt_unit_values(
                mean + intra_residual + inter_residual, imt)
            stdi = stddev_inter.max(axis=0)
        else:
            # this cannot happen, unless you pass a wrong mean_stds array
            raise ValueError('There are %d>3 stddevs!?' % num_stds)
        return gmf, stdi, epsilons


# this is not used in the engine; it is still useful for usage in IPython
# when demonstrating hazardlib capabilities
def ground_motion_fields(rupture, sites, imts, gsim, truncation_level,
                         realizations, correlation_model=None, seed=None):
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
        distribution, or ``None``.
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
    cmaker = ContextMaker(rupture.tectonic_region_type, [gsim],
                          dict(truncation_level=truncation_level,
                               imtls={str(imt): [1] for imt in imts}))
    rupture.rup_id = seed
    gc = GmfComputer(rupture, sites, cmaker, correlation_model)
    [mean_stds] = cmaker.get_mean_stds([gc.ctx], StdDev.EVENT)
    res, _sig, _eps = gc.compute(gsim, realizations, mean_stds)
    return {imt: res[imti] for imti, imt in enumerate(gc.imts)}
