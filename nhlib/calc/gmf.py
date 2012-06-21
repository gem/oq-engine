# nhlib: A New Hazard Library
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
:mod:`~nhlib.calc.gmf` exports :func:`ground_motion_fields`.
"""
import numpy
import scipy.stats

from nhlib.const import StdDev
from nhlib.calc import filters


def ground_motion_fields(rupture, sites, imts, gsim, truncation_level,
                         rupture_site_filter=filters.rupture_site_noop_filter):
    """
    TODO: write me

    :param nhlib.source.rupture.Rupture rupture:
        Rupture to calculate ground motion fields radiated from.
    :param nhlib.site.SiteCollection sites:
        Sites of interest to calculate GMFs.
    :param imts:
        List of intensity measure type objects (see :mod:`nhlib.imt`).
    :param gsim:
        Ground-shaking intensity model, instance of subclass of either
        :class:`~nhlib.gsim.base.GMPE` or :class:`~nhlib.gsim.base.IPE`.
    :param trunctation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution, or ``None``.
    :param rupture_site_filter:
        Optional rupture-site filter function. See :mod:`nhlib.calc.filters`.

    :returns:
        Dictionary mapping intensity measure type objects (same
        as in parameter ``imts``) to 1d numpy arrays of float,
        representing ground shaking intensity for all sites
        in the collection.
    """
    ruptures_sites = list(rupture_site_filter([(rupture, sites)]))
    if not ruptures_sites:
        return dict((imt, numpy.zeros(len(sites))) for imt in imts)

    total_sites = len(sites)
    [(rupture, sites)] = ruptures_sites

    sctx, rctx, dctx = gsim.make_contexts(sites, rupture)
    result = {}

    if truncation_level == 0:
        for imt in imts:
            mean, _stddevs = gsim.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                       stddev_types=[])
            result[imt] = sites.expand(mean, total_sites, placeholder=0)
        return result

    if truncation_level is None:
        distribution = scipy.stats.norm()
    else:
        assert truncation_level > 0
        distribution = scipy.stats.truncnorm(- truncation_level,
                                             truncation_level)

    for imt in imts:
        mean, [stddev_inter, stddev_intra] = gsim.get_mean_and_stddevs(
            sctx, rctx, dctx, imt, [StdDev.INTER_EVENT, StdDev.INTRA_EVENT]
        )
        gmf = mean + stddev_inter * distribution.rvs(size=len(sites)) \
                   + stddev_intra * distribution.rvs(size=1)
        result[imt] = sites.expand(gmf, total_sites, placeholder=0)

    return result
