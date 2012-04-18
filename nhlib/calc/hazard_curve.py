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
Module :mod:`nhlib.calc.hazard_curve` implements :func:`hazard_curves`.
"""
import numpy

from nhlib.tom import PoissonTOM


def hazard_curves(sources, sites, imts, time_span,
                  gsims, component_type, truncation_level):
    """
    Compute hazard curves on a list of sites, given a set of seismic sources
    and a set of ground shaking intensity models (one per tectonic region type
    considered in the seismic sources).

    The calculator assumes Poissonian temporal occurrence model.

    :param sources:
        An iterator of seismic sources objects (instances of subclasses
        of :class:`~nhlib.source.base.SeismicSource`).
    :param sites:
        List of :class:`~nhlib.site.Site` objects, representing sites
        of interest.
    :param imts:
        Dictionary mapping intensity measure type objects (see
        :mod:`nhlib.imt`) to lists of intensity measure levels.
    :param time_span:
        An investigation period for Poissonian temporal occurrence model,
        floating point number in years.
    :param gsims:
        Dictionary mapping tectonic region types (members
        of :class:`nhlib.const.TRT`) to :class:`~nhlib.gsim.base.GMPE`
        or :class:`~nhlib.gsim.base.IPE` objects.
    :param component_type:
        Component of ground shaking intensity to consider. Must be one
        of constants in :class:`nhlib.const.IMC`. That component must
        be supported by all the GSIMs in ``gsims`` dict.
    :param trunctation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.

    :returns:
        Dictionary mapping intensity measure type objects (same keys
        as in parameter ``imts``) to 2d numpy arrays of float, where
        first dimension differentiates sites (the order and length
        are the same as in ``sites`` parameter) and the second one
        differentiates IMLs (the order and length are the same as
        corresponding value in ``imts`` dict).
    """
    # TODO: unittest
    curves = dict((imt, numpy.ones([len(sites), len(imts[imt])]))
                  for imt in imts)
    tom = PoissonTOM(time_span)

    for source in sources:
        for rupture in source.iter_ruptures(tom):
            prob = rupture.get_probability()
            gsim = gsims[rupture.tectonic_region_type]

            # TODO: precompute distances to all the sites at once
            for i, site in enumerate(sites):
                ctx = gsim.make_context(site, rupture)
                poes = gsim.get_poes(ctx, imts, component_type,
                                     truncation_level)
                for imt in imts:
                    curves[imt][i] *= (1 - prob) ** poes[imt]

    for imt in imts:
        curves[imt] = 1 - curves[imt]
    return curves
