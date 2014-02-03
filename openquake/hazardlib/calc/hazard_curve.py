# coding: utf-8
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
:mod:`openquake.hazardlib.calc.hazard_curve` implements
:func:`hazard_curves`.
"""
import numpy

from openquake.hazardlib.calc import filters


def hazard_curves(
        sources, sites, imts, gsims, truncation_level,
        source_site_filter=filters.source_site_noop_filter,
        rupture_site_filter=filters.rupture_site_noop_filter):
    """
    Compute hazard curves on a list of sites, given a set of seismic sources
    and a set of ground shaking intensity models (one per tectonic region type
    considered in the seismic sources).


    Probability of ground motion exceedance is computed using the following
    formula ::

        P(X≥x|T) = 1 - ∏ ∏ Prup_ij(X<x|T)

    where ``P(X≥x|T)`` is the probability that the ground motion parameter
    ``X`` is exceeding level ``x`` one or more times in a time span ``T``, and
    ``Prup_ij(X<x|T)`` is the probability that the j-th rupture of the i-th
    source is not producing any ground motion exceedance in time span ``T``.
    The first product ``∏`` is done over sources, while the second one is done
    over ruptures in a source.

    The above formula computes the probability of having at least one ground
    motion exceedance in a time span as 1 minus the probability that none of
    the ruptures in none of the sources is causing a ground motion exceedance
    in the same time span. The basic assumption is that seismic sources are
    independent, and ruptures in a seismic source are also independent.

    :param sources:
        An iterator of seismic sources objects (instances of subclasses
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param sites:
        Instance of :class:`~openquake.hazardlib.site.SiteCollection` object,
        representing sites of interest.
    :param imts:
        Dictionary mapping intensity measure type objects (see
        :mod:`openquake.hazardlib.imt`) to lists of intensity measure levels.
    :param gsims:
        Dictionary mapping tectonic region types (members
        of :class:`openquake.hazardlib.const.TRT`) to
        :class:`~openquake.hazardlib.gsim.base.GMPE` or
        :class:`~openquake.hazardlib.gsim.base.IPE` objects.
    :param trunctation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.
    :param source_site_filter:
        Optional source-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.
    :param rupture_site_filter:
        Optional rupture-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.

    :returns:
        Dictionary mapping intensity measure type objects (same keys
        as in parameter ``imts``) to 2d numpy arrays of float, where
        first dimension differentiates sites (the order and length
        are the same as in ``sites`` parameter) and the second one
        differentiates IMLs (the order and length are the same as
        corresponding value in ``imts`` dict).
    """
    curves = dict((imt, numpy.ones([len(sites), len(imts[imt])]))
                  for imt in imts)

    total_sites = len(sites)
    sources_sites = ((source, sites) for source in sources)
    for source, s_sites in source_site_filter(sources_sites):
        try:
            ruptures_sites = ((rupture, s_sites)
                              for rupture in source.iter_ruptures())
            for rupture, r_sites in rupture_site_filter(ruptures_sites):
                gsim = gsims[rupture.tectonic_region_type]
                sctx, rctx, dctx = gsim.make_contexts(r_sites, rupture)
                for imt in imts:
                    poes = gsim.get_poes(sctx, rctx, dctx, imt, imts[imt],
                                         truncation_level)
                    pno = rupture.get_probability_no_exceedance(poes)
                    curves[imt] *= r_sites.expand(
                        pno, total_sites, placeholder=1
                    )
        except Exception, err:
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, err.message)
            raise RuntimeError(msg)

    for imt in imts:
        curves[imt] = 1 - curves[imt]
    return curves
