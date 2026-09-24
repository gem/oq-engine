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
Module :mod:`openquake.pfd.primary_surf_rup.moss2013`
"""

import numpy as np
from openquake.pfd.params import check_style
from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup


class Moss2013PrimarySR(BasePrimarySurfRup):
    """Principal surface-rupture probability model of Moss et al. (2013).

    Logistic model of the probability of principal surface rupture as a
    function of magnitude, faulting style, and site Vs30.

    Moss, R. E. S., Stanton, K. V., & Buelna, M. I. (2013). The impact of
    material stiffness on the likelihood of fault rupture propagating to the
    ground surface. Seismological Research Letters, 84(3), 485-488.
    https://doi.org/10.1785/0220110109
    """

    _ACCEPTED_STYLES = frozenset(["reverse", "strike-slip"])

    def __init__(self, style=None, vs30=None):
        """
        :param style: optional faulting style pinned by the logic-tree
            branch ('reverse' or 'strike-slip'); ``None`` defers to the
            ``get_prob`` call (normally resolved from the rupture rake).
        :param vs30: optional site Vs30 (m/s) pinned by the logic-tree
            branch; ``None`` defers to the ``get_prob`` call (normally the
            site collection's value). A pinned value overrides the
            site-specific one, matching the historical parameter-merge
            behaviour of the calculators.
        """
        self.style = check_style(type(self).__name__, style,
                                 self._ACCEPTED_STYLES)
        self.vs30 = None if vs30 is None else float(vs30)

    def get_prob(self, mag: float, style=None, vs30: float = None) -> float:
        """
        Model of Moss et al. (2013) for the probability of surface rupture
        based on the rupture mechanism (faulting style) and site conditions
        (shear-wave velocity).

        This model estimates the likelihood of surface rupture for two styles
        of faulting: "reverse" and "strike-slip." The probability is calculated
        as a function of event magnitude (mag) and the time-averaged shear-wave
        velocity to a depth of 30 meters (Vs30), which characterizes the site as
        soft or stiff soil.

        :param mag:
            The magnitude of the seismic event (float). Higher magnitudes generally
            result in greater probabilities of surface rupture.

        :param style:
            The faulting style (string, required). Accepted values are:
            - "reverse": Reverse faulting mechanism.
            - "strike-slip": Strike-slip faulting mechanism.

            If an unsupported style is provided, a ValueError will be raised.

        :param vs30:
            The time-averaged shear-wave velocity (float) to a depth of 30 meters
            (Vs30). This parameter distinguishes between stiff soil or rock (Vs30 > 600 m/s)
            and soft soil (Vs30 ≤ 600 m/s). The rupture probability varies based on
            this classification.

        :raises ValueError:
            If an invalid style is provided, the function raises an error indicating
            the acceptable faulting styles.

        :return:
            The probability of surface rupture as a float value between 0 and 1.

        :example:
            # Example usage
            model = Moss2013PrimarySR()
            probability = model.get_prob(mag=7.5, style="reverse", vs30=500)
            print(f"Probability of surface rupture: {probability}")
        """

        # Fall back to constructor-pinned values (call-time argument wins)
        if style is None:
            style = self.style
        if vs30 is None:
            vs30 = self.vs30

        # Define the accepted style of faultings
        accepted_styles = ["reverse", "strike-slip"]

        # Validate the style
        if style not in accepted_styles:
            raise ValueError(
                f"Invalid style '{style}'. Accepted values are: {', '.join(accepted_styles)}"
            )
        if vs30 is None:
            raise ValueError(
                "Moss2013PrimarySR requires vs30, either from the site "
                "collection or pinned in the logic-tree branch")

        m = np.asarray(mag, dtype=float)
        if style == 'reverse':
            if vs30 > 600:
                a, b = 13.9745, 2.1395
                prob = 1.0 / (1.0 + np.exp(a - b * m))
            else:
                a, b = 6.2548, 0.8308
                prob = 1.0 / (1.0 + np.exp(a - b * m))
        else:  # strike-slip
            if vs30 > 600:
                a, b = 11.4071, 1.8465
                prob = 1.0 / (1.0 + np.exp(a - b * m))
            else:
                a, b = 12.2908, 1.9520
                prob = 1.0 / (1.0 + np.exp(a - b * m))
        return prob.item() if prob.shape == () else prob