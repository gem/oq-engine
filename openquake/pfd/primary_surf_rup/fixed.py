# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.primary_surf_rup.fixed` implements
a fixed probability model for Primary Surface Rupture.
"""

from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup


class FixedPrimarySR(BasePrimarySurfRup):
    """
    Fixed probability model for Primary Surface Rupture.

    Returns a constant P(SR) value regardless of magnitude or style.
    This is useful when the user wants to assume surface rupture is
    certain (P(SR) = 1.0) or set to any other fixed probability.

    Parameters
    ----------
    value : float, optional
        The fixed probability value to return. Must be between 0 and 1.
        Default is 1.0.
    """

    def __init__(self, value=1.0):
        """
        Initialize the FixedPrimarySR model.

        Parameters
        ----------
        value : float, optional
            The fixed probability value to return. Must be between 0 and 1.
            Default is 1.0.
        """
        self.value = float(value)
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Value must be between 0 and 1, got {self.value}")

    def get_prob(self, mag=None, style=None, **kwargs):
        """
        Return the fixed probability value.

        This method accepts any keyword arguments but ignores them all,
        always returning the fixed probability value set at initialization.

        Parameters
        ----------
        mag : float, optional
            Earthquake magnitude (ignored).
        style : str, optional
            Rupture style (ignored).
        **kwargs : dict
            Any other keyword arguments (ignored).

        Returns
        -------
        float
            The fixed probability value.
        """
        return self.value

    def __repr__(self):
        return f"FixedPrimarySR(value={self.value})"

