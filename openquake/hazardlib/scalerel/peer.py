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
Module :mod:`openquake.hazardlib.scalerel.peer` implements :class:`PeerMSR`.
"""
from openquake.hazardlib.scalerel.base import BaseMSRSigma
from openquake.hazardlib.slots import with_slots


@with_slots
class PeerMSR(BaseMSRSigma):
    """
    Magnitude-Scaling Relationship defined for PEER PSHA test cases.

    See "Verification of Probabilistic Seismic Hazard Analysis Computer
    Programs", Patricia Thomas and Ivan Wong, PEER Report 2010/106, May 2010.
    """
    __slots__ = []

    def get_median_area(self, mag, rake):
        """
        Calculates median area as ``10 ** (mag - 4)``. Rake is ignored.
        """
        return 10 ** (mag - 4.0)

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for PeerMSR. Mag and rake are ignored.

        >>> peer = PeerMSR()
        >>> 0.25 == peer.get_std_dev_area(4.0, 50)
        True
        """
        return 0.25
