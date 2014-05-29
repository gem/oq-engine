# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`~openquake.hazardlib.calc.gmf` exports
:func:`ground_motion_fields`.
"""

import numpy
import scipy.stats

from openquake.hazardlib.const import StdDev
from openquake.hazardlib.calc import filters


class GmfComputer(object):
    """
    Given an earthquake rupture, the ground motion field computer computes
    ground shaking over a set of sites, by randomly sampling a ground
    shaking intensity model. The usage is::

       gmfcomputer = GmfComputer(rupture, r_sites, imts, gsim,
                                 truncation_level, correlation_model)
       gmf_dict1 = gmfcomputer.compute(seed1)
       gmf_dict2 = gmfcomputer.compute(seed2)

    :param :class:`openquake.hazardlib.source.rupture.Rupture` rupture:
        Rupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` sites:
        Sites of interest to calculate GMFs.

    :param imts:
        List of intensity measure type objects (see
        :mod:`openquake.hazardlib.imt`).

    :param gsims:
        Ground-shaking intensity models, instances of subclass of either
        :class:`~openquake.hazardlib.gsim.base.GMPE` or
        :class:`~openquake.hazardlib.gsim.base.IPE`.

    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution, or ``None``.

    :param correlation_model:
        Instance of correlation model object. See
        :mod:`openquake.hazardlib.correlation`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.
    """
    def __init__(self, rupture, sites, imts, gsims, truncation_level,
                 correlation_model=None):
        assert sites and imts and gsims, (sites, imts, gsims)
        self.rupture = rupture
        self.sites = sites
        self.imts = imts
        self.gsims = gsims
        self.truncation_level = truncation_level
        self.correlation_model = correlation_model
        self.ctx = dict((gsim, gsim.make_contexts(sites, rupture))
                        for gsim in gsims)

    def _compute(self, seed, gsim, realizations):
        # the method doing the real stuff; use compute instead
        if seed is not None:
            numpy.random.seed(seed)
        result = {}
        sctx, rctx, dctx = self.ctx[gsim]

        if self.truncation_level == 0:
            assert self.correlation_model is None
            for imt in self.imts:
                mean, _stddevs = gsim.get_mean_and_stddevs(
                    sctx, rctx, dctx, imt, stddev_types=[])
                mean = gsim.to_imt_unit_values(mean)
                mean.shape += (1, )
                mean = mean.repeat(realizations, axis=1)
                result[imt] = mean
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
                assert self.correlation_model is None

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

            result[imt] = gmf

        return result

    def compute(self, seed):
        """
        Compute the ground motion field for the given sites.

        :param seed:
            the seed for the numpy random number generator
        :returns:
            A list of dictionaries, one for each GSIM instance. Each
            dictionary maps intensity measure type objects (same as in
            parameter ``imts``) to numpy arrays of floats, representing
            ground shaking intensity for all sites in the collection.
        """
        # consider 1 realization, i.e. return column 0-th of the GMF arrays
        return [dict(
                (imt, gmf[:, 0]) for imt, gmf in self._compute(
                    seed, gsim, realizations=1).iteritems())
                for gsim in self.gsims]


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

    gc = GmfComputer(rupture, sites, imts, [gsim], truncation_level,
                     correlation_model)
    result = gc._compute(seed, gsim, realizations)
    for imt, gmf in result.iteritems():
        # makes sure the lenght of the arrays in output is the same as sites
        if rupture_site_filter is not filters.rupture_site_noop_filter:
            result[imt] = sites.expand(gmf, placeholder=0)

    return result
