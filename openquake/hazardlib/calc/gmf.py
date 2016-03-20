# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2016 GEM Foundation
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
import collections

import numpy
import scipy.stats

from openquake.hazardlib.const import StdDev
from openquake.hazardlib.calc import filters
from openquake.hazardlib.gsim.base import gsim_imt_dt, ContextMaker
from openquake.hazardlib.imt import from_string


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


class GmfComputer(object):
    """
    Given an earthquake rupture, the ground motion field computer computes
    ground shaking over a set of sites, by randomly sampling a ground
    shaking intensity model. The usage is::

       gmfcomputer = GmfComputer(rupture, r_sites, imts, gsims,
                                 truncation_level, correlation_model)
       gmf1 = gmfcomputer.compute(seed1)
       gmf2 = gmfcomputer.compute(seed2)

    :param :class:`openquake.hazardlib.source.rupture.Rupture` rupture:
        Rupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` sites:
        Sites of interest to calculate GMFs.

    :param imts:
        Sorted list of intensity measure type strings

    :param gsims:
        Ground-shaking intensity models, instances of subclass of either
        :class:`~openquake.hazardlib.gsim.base.GMPE` or
        :class:`~openquake.hazardlib.gsim.base.IPE`, sorted lexicographically.

    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution, or ``None``.

    :param correlation_model:
        Instance of correlation model object. See
        :mod:`openquake.hazardlib.correlation`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.
    """
    def __init__(self, rupture, sites, imts, gsims,
                 truncation_level=None, correlation_model=None):
        assert sites and imts, (sites, imts)
        self.rupture = rupture
        self.sites = sites
        self.imts = list(map(from_string, imts))
        self.gsims = gsims
        self.truncation_level = truncation_level
        self.correlation_model = correlation_model
        self.ctx = ContextMaker(gsims).make_contexts(sites, rupture)
        self.gmf_dt = gsim_imt_dt(gsims, imts)

    def _compute(self, seed, gsim, realizations):
        # the method doing the real stuff; use compute instead
        if seed is not None:
            numpy.random.seed(seed)
        result = collections.OrderedDict()
        sctx, rctx, dctx = self.ctx

        if self.truncation_level == 0:
            assert self.correlation_model is None
            for imt in self.imts:
                mean, _stddevs = gsim.get_mean_and_stddevs(
                    sctx, rctx, dctx, imt, stddev_types=[])
                mean = gsim.to_imt_unit_values(mean)
                mean.shape += (1, )
                mean = mean.repeat(realizations, axis=1)
                result[str(imt)] = mean
            return result
        elif self.truncation_level is None:
            distribution = scipy.stats.norm()
        else:
            assert self.truncation_level > 0
            distribution = scipy.stats.truncnorm(
                - self.truncation_level, self.truncation_level)

        for imt in self.imts:
            if gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == \
               set([StdDev.TOTAL]):
                # If the GSIM provides only total standard deviation, we need
                # to compute mean and total standard deviation at the sites
                # of interest.
                # In this case, we also assume no correlation model is used.
                if self.correlation_model:
                    raise CorrelationButNoInterIntraStdDevs(
                        self.correlation_model, gsim)

                mean, [stddev_total] = gsim.get_mean_and_stddevs(
                    sctx, rctx, dctx, imt, [StdDev.TOTAL]
                )
                stddev_total = stddev_total.reshape(stddev_total.shape + (1, ))
                mean = mean.reshape(mean.shape + (1, ))

                total_residual = stddev_total * distribution.rvs(
                    size=(len(self.sites), realizations)
                )
                gmf = gsim.to_imt_unit_values(mean + total_residual)
            else:
                mean, [stddev_inter, stddev_intra] = gsim.get_mean_and_stddevs(
                    sctx, rctx, dctx, imt,
                    [StdDev.INTER_EVENT, StdDev.INTRA_EVENT]
                )
                stddev_intra = stddev_intra.reshape(stddev_intra.shape + (1, ))
                stddev_inter = stddev_inter.reshape(stddev_inter.shape + (1, ))
                mean = mean.reshape(mean.shape + (1, ))

                intra_residual = stddev_intra * distribution.rvs(
                    size=(len(self.sites), realizations)
                )

                if self.correlation_model is not None:
                    intra_residual = self.correlation_model.apply_correlation(
                        self.sites, imt, intra_residual
                    )

                inter_residual = stddev_inter * distribution.rvs(
                    size=realizations)

                gmf = gsim.to_imt_unit_values(
                    mean + intra_residual + inter_residual)

            result[str(imt)] = gmf

        return result

    def compute(self, seeds):
        """
        Compute the ground motion field for the given sites and seeds.

        :param seeds:
            S seeds for the numpy random number generator
        :returns:
            a numpy array of dtype gmf_dt and shape (num_seeds, num_sites)
        """
        gmfa = numpy.zeros((len(seeds), len(self.sites)), self.gmf_dt)
        for i, seed in enumerate(seeds):
            for gsim in self.gsims:
                gs = str(gsim)
                for imt, value in self._compute(
                        seed, gsim, realizations=1).items():
                    # 1 realization, get the 0-th colum of the v-array
                    array = list(map(float, value[:, 0]))
                    # NB: with correlation, the value is a numpy.matrix
                    # not an array, flatten does not work and the only
                    # way to extract the numbers is the map before!
                    # something is wrong and must be fixed in the future
                    for j, gmv in enumerate(array):
                        gmfa[i, j][gs][imt] = gmv
        return gmfa

    def calcgmfs(self, multiplicity, seed):
        """
        Compute the ground motion field for the given sites and seeds.

        :param multiplicity:
            the number of GMFs to return
        :param seed:
            seed for the numpy random number generator
        :returns:
            a numpy array of dtype gmf_dt and shape (multiplicity, num_sites)
        """
        gmfa = numpy.zeros((multiplicity, len(self.sites)), self.gmf_dt)
        for gsim in self.gsims:
            for imt, gmv in self._compute(seed, gsim, multiplicity).items():
                gmfa[str(gsim)][imt] = gmv.T  # from N x M -> M x N
        return gmfa


# this is not used in the engine; it is still useful for usage in IPython
# when demonstrating hazardlib capabilities
def ground_motion_fields(rupture, sites, imts, gsim, truncation_level,
                         realizations, correlation_model=None,
                         rupture_site_filter=filters.rupture_site_noop_filter,
                         seed=None):
    """
    Given an earthquake rupture, the ground motion field calculator computes
    ground shaking over a set of sites, by randomly sampling a ground shaking
    intensity model. A ground motion field represents a possible 'realization'
    of the ground shaking due to an earthquake rupture. If a non-trivial
    filtering function is passed, the final result is expanded and filled
    with zeros in the places corresponding to the filtered out sites.

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
    :param rupture_site_filter:
        Optional rupture-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.
    :param int seed:
        The seed used in the numpy random number generator
    :returns:
        Dictionary mapping intensity measure type objects (same
        as in parameter ``imts``) to 2d numpy arrays of floats,
        representing different realizations of ground shaking intensity
        for all sites in the collection. First dimension represents
        sites and second one is for realizations.
    """
    ruptures_sites = list(rupture_site_filter([(rupture, sites)]))
    if not ruptures_sites:
        return dict((imt, numpy.zeros((len(sites), realizations)))
                    for imt in imts)
    [(rupture, sites)] = ruptures_sites

    gc = GmfComputer(rupture, sites, list(map(str, imts)), [gsim],
                     truncation_level, correlation_model)
    result = gc._compute(seed, gsim, realizations)
    for imt, gmf in result.items():
        # makes sure the lenght of the arrays in output is the same as sites
        if rupture_site_filter is not filters.rupture_site_noop_filter:
            result[imt] = sites.expand(gmf, placeholder=0)

    return {from_string(imt): result[imt] for imt in result}
