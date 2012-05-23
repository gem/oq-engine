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
Module :mod:`nhlib.source.base` defines a base class for seismic sources.
"""
import abc

from nhlib import const


class SeismicSource(object):
    """
    Seismic Source is an object representing geometry and activity rate
    of a structure generating seismicity.

    :param source_id:
        Some (numeric or literal) source identifier. Supposed to be unique
        within the source model.
    :param name:
        String, a human-readable name of the source.
    :param tectonic_region_type:
        Source's tectonic regime. See :class:`const.TRT`.
    :param mfd:
        Magnitude-Frequency distribution for the source. See :mod:`nhlib.mfd`.
    :param rupture_mesh_spacing:
        The desired distance between two adjacent points in source's
        ruptures' mesh, in km. Mainly this parameter allows to balance
        the trade-off between time needed to compute the :meth:`distance
        <nhlib.geo.surface.base.BaseSurface.get_min_distance>` between
        the rupture surface and a site and the precision of that computation.
    :param magnitude_scaling_relationship:
        Instance of subclass of :class:`nhlib.msr.base.BaseMSR` to describe
        how does the area of the rupture depend on magnitude and rake.
    :param rupture_aspect_ratio:
        Float number representing how much source's ruptures are more wide
        than tall. Aspect ratio of 1 means ruptures have square shape,
        value below 1 means ruptures stretch vertically more than horizontally
        and vice versa.

    :raises ValueError:
        If tectonic region type is wrong/unknown, if either rupture aspect
        ratio or rupture mesh spacing is not positive.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, source_id, name, tectonic_region_type,
                 mfd, rupture_mesh_spacing,
                 magnitude_scaling_relationship, rupture_aspect_ratio):

        if not const.TRT.is_valid(tectonic_region_type):
            raise ValueError('unknown tectonic region type %r' %
                              tectonic_region_type)

        if not rupture_mesh_spacing > 0:
            raise ValueError('rupture mesh spacing must be positive')

        if not rupture_aspect_ratio > 0:
            raise ValueError('rupture aspect ratio must be positive')

        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.mfd = mfd
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.magnitude_scaling_relationship = magnitude_scaling_relationship
        self.rupture_aspect_ratio = rupture_aspect_ratio

    @abc.abstractmethod
    def iter_ruptures(self, temporal_occurrence_model):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :param temporal_occurrence_model:
            Temporal occurrence model (supposedly
            :class:`nhlib.tom.PoissonTOM`). It is passed intact
            to the probabilistic rupture constructor.
        :returns:
            Generator of instances
            of :class:`~nhlib.source.rupture.ProbabilisticRupture`.
        """

    def get_annual_occurrence_rates(self, min_rate=0):
        """
        Get a list of pairs "magnitude -- annual occurrence rate".

        The list is taken from assigned MFD object
        (see :meth:`nhlib.mfd.base.BaseMFD.get_annual_occurrence_rate`)
        with simple filtering by rate applied.

        :param min_rate:
            A non-negative value to filter magnitudes by minimum annual
            occurrence rate. Only magnitudes with rates greater than that
            are included in the result list.
        :returns:
            A list of two-item tuples -- magnitudes and occurrence rates.
        """
        return [(mag, occ_rate)
                for (mag, occ_rate) in self.mfd.get_annual_occurrence_rates()
                if min_rate is None or occ_rate > min_rate]
