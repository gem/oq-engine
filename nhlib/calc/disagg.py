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
:mod:`nhlib.calc.disagg` contains :func:`disaggregation`.
"""
import numpy

from nhlib.site import SiteCollection


def disaggregation():
    """
    """



def _collect_bins_data(sources, site, iml, imt, gsims, tom,
                       truncation_level, n_epsilons):
    # TODO: filters
    mags = []
    dists = []
    lons = []
    lats = []
    tect_reg_types = set()
    joint_probs = []
    sitecol = SiteCollection([site])
    sitemesh = sitecol.mesh

    for source in sources:
        tect_reg = source.tectonic_region_type
        gsim = gsims[tect_reg]
        for rupture in source.iter_ruptures(tom):
            # extract rupture parameters of interest
            mags.append(rupture.mag)
            [jb_dist] = rupture.surface.get_joyner_boore_distance(sitemesh)
            dists.append(jb_dist)
            [closest_point] = rupture.surface.get_closest_points(sitemesh)
            lons.append(closest_point.longitude)
            lats.append(closest_point.latitude)
            tect_reg_types.add(tect_reg)

            # compute conditional probability of exceeding iml given
            # the current rupture, and different epsilon level, that is
            # ``P(IMT >= iml | rup, epsilon_bin)`` for each of epsilon bins
            sctx, rctx, dctx = gsim.make_contexts(sitecol, rupture)
            [poes_given_rup_eps] = gsim.disaggregate_poe(
                sctx, rctx, dctx, imt, iml, truncation_level, n_epsilons
            )
            # compute the probability of the rupture occurring once,
            # that is ``P(rup)``
            p_rup = rupture.get_probability_one_occurrence()

            # compute joint probability of rupture occurrence and
            # iml exceedance for the different epsilon levels
            joint_probs.append(poes_given_rup_eps * p_rup)

    mags = numpy.array(mags, float)
    dists = numpy.array(dists, float)
    lons = numpy.array(lons, float)
    lats = numpy.array(lats, float)
    joint_probs = numpy.array(joint_probs, float)

    return mags, dists, lons, lats, joint_probs, tect_reg_types
