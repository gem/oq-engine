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
Module :mod:`openquake.hazardlib.source.rupture` defines classes
:class:`Rupture` and its subclass :class:`ProbabilisticRupture`.
"""
from openquake.hazardlib.geo.nodalplane import NodalPlane


class Rupture(object):
    """
    Rupture object represents a single earthquake rupture.

    :param mag:
        Magnitude of the rupture.
    :param rake:
        Rake value of the rupture.
        See :class:`~openquake.hazardlib.geo.nodalplane.NodalPlane`.
    :param tectonic_region_type:
        Rupture's tectonic regime. One of constants
        in :class:`openquake.hazardlib.const.TRT`.
    :param hypocenter:
        A :class:`~openquake.hazardlib.geo.point.Point`, rupture's hypocenter.
    :param surface:
        An instance of subclass of
        :class:`~openquake.hazardlib.geo.surface.base.BaseSurface`.
        Object representing the rupture surface geometry.
    :param source_typology:
        Subclass of :class:`~openquake.hazardlib.source.base.SeismicSource`
        (class object, not an instance) referencing the typology
        of the source that produced this rupture.

    :raises ValueError:
        If magnitude value is not positive, hypocenter is above the earth
        surface or tectonic region type is unknown.
    """
    def __init__(self, mag, rake, tectonic_region_type, hypocenter,
                 surface, source_typology):
        if not mag > 0:
            raise ValueError('magnitude must be positive')
        if not hypocenter.depth > 0:
            raise ValueError('rupture hypocenter must have positive depth')
        NodalPlane.check_rake(rake)
        self.tectonic_region_type = tectonic_region_type
        self.rake = rake
        self.mag = mag
        self.hypocenter = hypocenter
        self.surface = surface
        self.source_typology = source_typology


class ProbabilisticRupture(Rupture):
    """
    :class:`Rupture` associated with an occurrence rate and a temporal
    occurrence model.

    :param occurrence_rate:
        Number of times rupture happens per year.
    :param temporal_occurrence_model:
        Temporal occurrence model assigned for this rupture. Should
        be an instance of :class:`openquake.hazardlib.tom.PoissonTOM`.

    :raises ValueError:
        If occurrence rate is not positive.
    """
    def __init__(self, mag, rake, tectonic_region_type, hypocenter, surface,
                 source_typology,
                 occurrence_rate, temporal_occurrence_model):
        if not occurrence_rate > 0:
            raise ValueError('occurrence rate must be positive')
        super(ProbabilisticRupture, self).__init__(
            mag, rake, tectonic_region_type, hypocenter, surface,
            source_typology
        )
        self.temporal_occurrence_model = temporal_occurrence_model
        self.occurrence_rate = occurrence_rate

    def get_probability_one_or_more_occurrences(self):
        """
        Return the probability of this rupture to occur one or more times.

        Uses
        :meth:`~openquake.hazardlib.tom.PoissonTOM.get_probability_one_or_more_occurrences`
        of an assigned temporal occurrence model.
        """
        tom = self.temporal_occurrence_model
        rate = self.occurrence_rate
        return tom.get_probability_one_or_more_occurrences(rate)

    def get_probability_one_occurrence(self):
        """
        Return the probability of this rupture to occur exactly one time.

        Uses :meth:
        `~openquake.hazardlib.tom.PoissonTOM.get_probability_one_occurrence`
        of an assigned temporal occurrence model.
        """
        tom = self.temporal_occurrence_model
        rate = self.occurrence_rate
        return tom.get_probability_one_occurrence(rate)

    def sample_number_of_occurrences(self):
        """
        Draw a random sample from the distribution and return a number
        of events to occur.

        Uses :meth:
        `~openquake.hazardlib.tom.PoissonTOM.sample_number_of_occurrences`
        of an assigned temporal occurrence model.
        """
        return self.temporal_occurrence_model.sample_number_of_occurrences(
            self.occurrence_rate
        )
