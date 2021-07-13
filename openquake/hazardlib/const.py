# The Hazard Library
# Copyright (C) 2012-2021 GEM Foundation
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
Module :mod:`openquake.hazardlib.const` defines various constants.
"""
from enum import Enum


class TRT(Enum):
    """
    Container for constants that define some of the common Tectonic Region
    Types.
    """
    # Constant values correspond to the NRML schema definition.
    ACTIVE_SHALLOW_CRUST = 'Active Shallow Crust'
    STABLE_CONTINENTAL = 'Stable Shallow Crust'
    SUBDUCTION_INTERFACE = 'Subduction Interface'
    SUBDUCTION_INTRASLAB = 'Subduction IntraSlab'
    UPPER_MANTLE = "Upper Mantle"
    VOLCANIC = 'Volcanic'
    GEOTHERMAL = 'Geothermal'
    INDUCED = 'Induced'


class IMC(Enum):
    """
    The intensity measure component is the component of interest
    of ground shaking for an
    :mod:`intensity measure <openquake.hazardlib.imt>`.
    """
    #: The horizontal component.
    HORIZONTAL = 'Horizontal'
    #: The median horizontal component.
    MEDIAN_HORIZONTAL = 'Median horizontal'
    #: Usually defined as the geometric average of the maximum
    #: of the two horizontal components (which may not occur
    #: at the same time).
    AVERAGE_HORIZONTAL = 'Average horizontal'
    #: An orientation-independent alternative to :attr:`AVERAGE_HORIZONTAL`.
    #: Defined at Boore et al. (2006, Bull. Seism. Soc. Am. 96, 1502-1511)
    #: and is used for all the NGA GMPEs.
    GMRotI50 = 'Average Horizontal (GMRotI50)'
    #: The geometric mean of the records rotated into the most adverse
    #: direction for the structure.
    GMRotD100 = "Average Horizontal (GMRotD100)"
    #: An orientation-independent alternative to :attr:`AVERAGE_HORIZONTAL`.
    #: Defined at Boore et al. (2006, Bull. Seism. Soc. Am. 96, 1502-1511)
    #: and is used for all the NGA GMPEs.
    RotD50 = 'Average Horizontal (RotD50)'
    #:
    RotD100 = 'Horizontal Maximum Direction (RotD100)'
    #: A randomly chosen horizontal component.
    RANDOM_HORIZONTAL = 'Random horizontal'
    #: The largest value obtained from two perpendicular horizontal
    #: components.
    GREATER_OF_TWO_HORIZONTAL = 'Greater of two horizontal'
    #: The vertical component.
    VERTICAL = 'Vertical'
    #: "Vectorial addition: a_V = sqrt(max|a_1(t)|^2 + max|a_2(t)|^2)).
    #: This means that the maximum ground amplitudes occur simultaneously on
    #: the two horizontal components; this is a conservative assumption."
    #: p. 53 of Douglas (2003, Earth-Sci. Rev. 61, 43-104)
    VECTORIAL = 'Square root of sum of squares of peak horizontals'
    #: "the peak square root of the sum of squares of two orthogonal
    #: horizontal components in the time domain"
    #: p. 880 of Kanno et al. (2006, Bull. Seism. Soc. Am. 96, 879-897)
    PEAK_SRSS_HORIZONTAL = 'Peak square root of sum of squares of horizontals'
    #: A vertical-to-horizontal spectral ratio
    VERTICAL_TO_HORIZONTAL_RATIO = 'Vertical-to-Horizontal Ratio'


# NB: cannot be an enum because it would break the Strong Motion Toolkit :-(
class StdDev(object):
    """
    GSIM standard deviation represents ground shaking variability at a site.
    """
    TOTAL = 'Total'
    #: Standard deviation representing ground shaking variability
    #: within different events.
    INTER_EVENT = 'Inter event'
    #: Standard deviation representing ground shaking variability
    #: within a single event.
    INTRA_EVENT = 'Intra event'
    #: Total standard deviation, defined as the square root of the sum
    #: of inter- and intra-event squared standard deviations, represents
    #: the total ground shaking variability, and is the only one that
    #: is used for calculating a probability of intensity exceedance
    #: (see :func:`openquake.hazardlib.gsim.base.get_poes`).
    EVENT = 'Event'
    #: Used in event based calculations, correspond to TOTAL if the gsim
    #: is defined for TOTAL, otherwise to the pair (INTER_EVENT, INTRA_EVENT)
