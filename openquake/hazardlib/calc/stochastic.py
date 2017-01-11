# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
:mod:`openquake.hazardlib.calc.stochastic` contains
:func:`stochastic_event_set`.
"""
import sys
from openquake.baselib.python3compat import range
from openquake.baselib.python3compat import raise_
from openquake.hazardlib.calc import filters


def stochastic_event_set(
        sources,
        sites=None,
        source_site_filter=filters.source_site_noop_filter):
    """
    Generates a 'Stochastic Event Set' (that is a collection of earthquake
    ruptures) representing a possible *realization* of the seismicity as
    described by a source model.

    The calculator loops over sources. For each source, it loops over ruptures.
    For each rupture, the number of occurrence is randomly sampled by
    calling
    :meth:`openquake.hazardlib.source.rupture.BaseProbabilisticRupture.sample_number_of_occurrences`

    .. note::
        This calculator is using random numbers. In order to reproduce the
        same results numpy random numbers generator needs to be seeded, see
        http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.seed.html

    :param sources:
        An iterator of seismic sources objects (instances of subclasses
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param sites:
        A list of sites to consider (or None)
    :param source_site_filter:
        The source filter to use (only meaningful is sites is not None)
    :param source_site_filter:
        The rupture filter to use (only meaningful is sites is not None)
    :returns:
        Generator of :class:`~openquake.hazardlib.source.rupture.Rupture`
        objects that are contained in an event set. Some ruptures can be
        missing from it, others can appear one or more times in a row.
    """
    if sites is None:  # no filtering
        for source in sources:
            try:
                for rupture in source.iter_ruptures():
                    for i in range(rupture.sample_number_of_occurrences()):
                        yield rupture
            except Exception as err:
                etype, err, tb = sys.exc_info()
                msg = 'An error occurred with source id=%s. Error: %s'
                msg %= (source.source_id, str(err))
                raise_(etype, msg, tb)
        return
    # else apply filtering
    for source, s_sites in source_site_filter(sources, sites):
        try:
            for rupture in source.iter_ruptures():
                for i in range(rupture.sample_number_of_occurrences()):
                    yield rupture
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, str(err))
            raise_(etype, msg, tb)
