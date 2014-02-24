# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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


def ground_motion_fields(rupture, sites, imts, gsim, truncation_level,
                         realizations, correlation_model=None,
                         rupture_site_filter=filters.rupture_site_noop_filter):
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
    :param rupture_site_filter:
        Optional rupture-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.

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
    no_filter = rupture_site_filter is filters.rupture_site_noop_filter
    [(rupture, sites)] = ruptures_sites

    sctx, rctx, dctx = gsim.make_contexts(sites, rupture)
    result = {}

    if truncation_level == 0:
        assert correlation_model is None
        for imt in imts:
            mean, _stddevs = gsim.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                       stddev_types=[])
            mean = gsim.to_imt_unit_values(mean)
            mean.shape += (1, )
            mean = mean.repeat(realizations, axis=1)
            result[imt] = mean if no_filter else sites.expand(
                mean, placeholder=0)
        return result

    if truncation_level is None:
        distribution = scipy.stats.norm()
    else:
        assert truncation_level > 0
        distribution = scipy.stats.truncnorm(- truncation_level,
                                             truncation_level)

    for imt in imts:

        if gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == set([StdDev.TOTAL]):
            # If the GSIM provides only total standard deviation, then we need
            # to compute only mean and total standard deviation at the sites
            # of interest.
            # In this case, we also assume that no correlation model is used.
            assert correlation_model is None

            mean, [stddev_total] = gsim.get_mean_and_stddevs(
                sctx, rctx, dctx, imt, [StdDev.TOTAL]
            )
            stddev_total = stddev_total.reshape(stddev_total.shape + (1, ))
            mean = mean.reshape(mean.shape + (1, ))

            total_residual = stddev_total * distribution.rvs(
                size=(len(sites), realizations)
            )
            gmf = gsim.to_imt_unit_values(mean + total_residual)
        else:
            mean, [stddev_inter, stddev_intra] = gsim.get_mean_and_stddevs(
                sctx, rctx, dctx, imt, [StdDev.INTER_EVENT, StdDev.INTRA_EVENT]
            )
            stddev_intra = stddev_intra.reshape(stddev_intra.shape + (1, ))
            stddev_inter = stddev_inter.reshape(stddev_inter.shape + (1, ))
            mean = mean.reshape(mean.shape + (1, ))

            intra_residual = stddev_intra * distribution.rvs(
                size=(len(sites), realizations)
            )

            if correlation_model is not None:
                intra_residual = correlation_model.apply_correlation(
                    sites, imt, intra_residual
                )

            inter_residual = stddev_inter * distribution.rvs(size=realizations)

            gmf = gsim.to_imt_unit_values(
                mean + intra_residual + inter_residual)

        result[imt] = gmf if no_filter else sites.expand(gmf, placeholder=0)

    return result


def ground_motion_field_with_residuals(
        rupture, sites, imt, gsim, truncation_level,
        total_residual_epsilons=None,
        intra_residual_epsilons=None,
        inter_residual_epsilons=None):
    """
    A simplified version of ``ground_motion_fields`` where: the values
    due to uncertainty (total, intra-event or inter-event residual
    epsilons) are given in input; only one intensity measure type is
    considered.

    See :func:``openquake.hazardlib.calc.gmf.ground_motion_fields`` for
    the description of most of the input parameters.

    :param total_residual_epsilons:
        a 2d numpy array of floats with the epsilons needed to compute the
        total residuals in the case the GSIM provides only total standard
        deviation.
    :param intra_residual_epsilons:
        a 2d numpy array of floats with the epsilons needed to compute the
        intra event residuals
    :param inter_residual_epsilons:
        a 2d numpy array of floats with the epsilons needed to compute the
        intra event residuals

    :returns:
        a 1d numpy array of floats, representing ground shaking intensity
        for all sites in the collection.
    """

    sctx, rctx, dctx = gsim.make_contexts(sites, rupture)

    if truncation_level == 0:
        mean, _stddevs = gsim.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                   stddev_types=[])
        return gsim.to_imt_unit_values(mean)

    if gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == set([StdDev.TOTAL]):
        assert total_residual_epsilons is not None

        mean, [stddev_total] = gsim.get_mean_and_stddevs(
            sctx, rctx, dctx, imt, [StdDev.TOTAL]
        )
        stddev_total = stddev_total.reshape(stddev_total.shape + (1, ))
        total_residual = stddev_total * total_residual_epsilons
        gmf = gsim.to_imt_unit_values(mean + total_residual)
    else:
        assert inter_residual_epsilons is not None
        assert intra_residual_epsilons is not None
        mean, [stddev_inter, stddev_intra] = gsim.get_mean_and_stddevs(
            sctx, rctx, dctx, imt, [StdDev.INTER_EVENT, StdDev.INTRA_EVENT]
        )

        intra_residual = stddev_intra * intra_residual_epsilons
        inter_residual = stddev_inter * inter_residual_epsilons

        gmf = gsim.to_imt_unit_values(
            mean + intra_residual + inter_residual)

    return gmf
