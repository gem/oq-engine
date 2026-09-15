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
Module :mod:`openquake.pfd.primary_surf_rup.pizza2023`
"""

import numpy as np
from openquake.pfd.params import check_style
from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup


class Pizza2023PrimarySR(BasePrimarySurfRup):
    """Principal surface-rupture probability model of Pizza et al. (2023).

    Logistic model of the probability of principal surface rupture as a
    function of magnitude, with coefficients for the ``all``, ``normal``,
    ``reverse``, and ``strike-slip`` faulting styles.

    References
    ----------
    Pizza, M., Ferrario, M.F., Thomas, F., Tringali, G., & Livio, F. (2023).
    Likelihood of primary surface faulting: updating of empirical regressions.
    Bulletin of the Seismological Society of America, 113(5), 2106-2118.
    https://doi.org/10.1785/0120230019
    """

    def __init__(self, style=None):
        """
        :param style: optional faulting style pinned by the logic-tree
            branch ('all', 'normal', 'reverse' or 'strike-slip'); ``None``
            defers the choice to the ``get_prob`` call (legacy default:
            'all').
        """
        super().__init__()
        self.style = check_style(type(self).__name__, style)

    def get_prob(self, mag, style=None):
        """
        Model of Pizza et al., 2023 for the probability of surface rupture
        based on rupture mechanism and earthquake magnitude.

        This model estimates the likelihood of surface rupture for four faulting
        styles: "all", "normal", "reverse", and "strike-slip." The probability is
        calculated using a logistic regression formula, with coefficients varying
        based on the selected faulting style.

        :param mag:
            The magnitude of the seismic event (float). Larger magnitudes generally
            lead to higher probabilities of surface rupture.

        :param style:
            The faulting style (string). Accepted values are:
            - "all": Represents a combination of all faulting styles.
            - "normal": Represents normal faulting mechanisms.
            - "reverse": Represents reverse faulting mechanisms.
            - "strike-slip": Represents strike-slip faulting mechanisms.

            Default is "all." If an unsupported style is provided, a ValueError will
            be raised.

        :raises ValueError:
            If an invalid style is provided, the function raises an error indicating
            the acceptable faulting styles.

        :return:
            The probability of surface rupture as a float value between 0 and 1,
            calculated using a logistic regression model.
        """

        # Fall back to the constructor-pinned style, then legacy default
        if style is None:
            style = self.style if self.style is not None else "all"

        # Define the accepted style of faultings
        accepted_styles = ["all", "normal", "reverse", "strike-slip"]

        # Validate the style
        if style not in accepted_styles:
            raise ValueError(
                f"Invalid style '{style}'. Accepted values are: {', '.join(accepted_styles)}"
            )

        m = np.asarray(mag, dtype=float)

        if style == "all":
            a = -14.47
            b = 2.177
        elif style == "normal":
            a = -13.5
            b = 2.159
        elif style == "reverse":
            a = -10.75
            b = 1.427
        elif style == "strike-slip":
            a = -28.56
            b = 4.436
        else:
            raise ValueError(f"Invalid style '{style}'.")
        fx = a + b * m
        prob = np.exp(fx) / (1.0 + np.exp(fx))

        return prob.item() if prob.shape == () else prob
