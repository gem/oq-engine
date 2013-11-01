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
Module :mod:`~openquake.hazardlib.calc.filters` contain filter functions for
calculators.

Filters are functions (or other callable objects) that should take generators
and return generators. There are two different kinds of filter functions:

1. Source-site filters. Those functions take a generator of two-item tuples,
   each pair consists of seismic source object (that is, an instance of
   a subclass of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`)
   and a site collection (instance of
   :class:`~openquake.hazardlib.site.SiteCollection`).
2. Rupture-site filters. Those also take a generator of pairs, but in this
   case the first item in the pair is a rupture object (instance of
   :class:`~openquake.hazardlib.source.rupture.Rupture`). The second element in
   generator items is still site collection.

The purpose of both kinds of filters is to limit the amount of calculation
to be done based on some criteria, like the distance between the source
and the site. So common design feature of all the filters is the loop over
pairs of the provided generator, filtering the sites collection, and if
there are no items left in it, skipping the pair and continuing to the next
one. If some sites need to be considered together with that source / rupture,
the pair gets generated out, with a (possibly) :meth:`limited
<openquake.hazardlib.site.SiteCollection.filter>` site collection.

Consistency of filters' input and output stream format allows several filters
(obviously, of the same kind) to be chained together.

Filter functions should not make assumptions about the ordering of items
in the original generator or draw more than one pair at once. Ideally, they
should also perform reasonably fast (filtering stage that takes longer than
the actual calculation on unfiltered collection only decreases performance).

Module :mod:`openquake.hazardlib.calc.filters` exports one distance-based
filter function of each kind (see :func:`source_site_distance_filter` and
:func:`rupture_site_distance_filter`) as well as "no operation" filters
(:func:`source_site_noop_filter` and :func:`rupture_site_noop_filter`).
"""


def source_site_distance_filter(integration_distance):
    """
    Source-site filter based on distance.

    :param integration_distance:
        Threshold distance in km, this value gets passed straight to
        :meth:`openquake.hazardlib.source.base.BaseSeismicSource.filter_sites_by_distance_to_source`
        which is what is actually used for filtering.
    """
    def filter_func(sources_sites):
        for source, sites in sources_sites:
            s_sites = source.filter_sites_by_distance_to_source(
                integration_distance, sites
            )
            if s_sites is None:
                continue
            yield source, s_sites
    return filter_func


def rupture_site_distance_filter(integration_distance):
    """
    Rupture-site filter based on distance.

    :param integration_distance:
        Threshold distance in km, this value gets passed straight to
        :meth:`openquake.hazardlib.source.base.BaseSeismicSource.filter_sites_by_distance_to_rupture`
        which is what is actually used for filtering.
    """
    def filter_func(ruptures_sites):
        for rupture, sites in ruptures_sites:
            source_cls = rupture.source_typology
            r_sites = source_cls.filter_sites_by_distance_to_rupture(
                rupture, integration_distance, sites
            )
            if r_sites is None:
                continue
            yield rupture, r_sites
    return filter_func


#: Transparent source-site "no-op" filter -- behaves like a real filter
#: but never filters anything out and doesn't have any overhead.
source_site_noop_filter = lambda sources_sites: sources_sites

#: Rupture-site "no-op" filter, same as :func:`source_site_noop_filter`.
rupture_site_noop_filter = lambda ruptures_sites: ruptures_sites
