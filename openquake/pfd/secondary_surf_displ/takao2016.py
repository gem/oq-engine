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
Module :mod:`openquake.pfd.secondary_surf_displ.takao2016` implements the
model of Takao et al. (2016) in :class:`Takao2016SecondaryFD`.

Supported Fault Styles: Reverse and Strike-slip

References
----------
Takao, M., Tani, T., Oshima, T., Annaka, T., & Kurita, T. (2016). Maximum
likelihood estimation of the parameters regarding displacement evaluation of
distributed fault in PFDHA. Journal of Japan Association for Earthquake
Engineering, 16(2), 96-101. https://doi.org/10.5610/jaee.16.2_96
"""

import numpy as np
from scipy.stats import gamma
from openquake.pfd.secondary_surf_displ.takao2013 import Takao2013SecondaryFD


class Takao2016SecondaryFD(Takao2013SecondaryFD):
    """Distributed fault-displacement model of Takao et al. (2016).

    Takao et al. (2016) keep the hazard formulation of Takao et al. (2013,
    2014) and re-estimate, by maximum likelihood, the two parameters of the
    gamma distribution of the distributed displacement normalized by the
    average principal displacement, x = DD/PAD (paper Eq. 1):

        f(x) = x^(a-1) exp(-x/b) / (Gamma(a) b^a),   b = eps exp(-k r)

    with r the closest distance [km] from the principal fault (Eq. 5). The
    paper's Table 1 gives two parameter sets, selected here with ``case``:

        case 1: a = 1.282, eps = 0.644, k = 0.17
                (decay of Takao et al. 2013, the paper's Eq. 3; field data
                of Fig. 9 of Takao et al. 2013)
        case 2: a = 1.321, eps = 0.726, k = 0.20
                (decay of Takao et al. 2014, the paper's Eq. 4; field data
                plus the model tests and numerical analyses of Fig. 10 of
                Takao et al. 2014)

    Eq. 5 is printed only for the case 1 decay, "for reasons of space"; the
    case 2 decay k = 0.20 is the one listed for it in Table 1 (the Eq. 4
    form). Case 2 is the default: it is the set drawn in the paper's Fig. 1
    and compared with Takao et al. (2014) in its Section 3.

    Only a and b differ from :class:`Takao2013SecondaryFD` (Section 3 of the
    paper); the magnitude scaling of PAD and its integration are inherited:

        log10(PAD) = -4.80 + 0.69 Mw  (sigma 0.36)

    integrated over ``mean ± n_sigma·sigma`` (log10 space). The paper gives
    the model for PAD only, so the PMD normalization is not available.

    Model contract: DISPLACEMENT_DEFINITION = "distributed",
    DISPLACEMENT_COMPONENT = "net" (as Takao et al. 2013). The declared
    applicability, r up to 20 km, is inherited from
    :class:`Takao2013SecondaryFD`; the 2016 paper states no range and notes
    that the data are sparse beyond about 5 km.
    """

    # (shape a, scale coefficient eps, decay k [1/km]) from Table 1
    _CASES = {
        1: (1.282, 0.644, 0.17),
        2: (1.321, 0.726, 0.20),
    }

    # PAD scaling inherited from Takao et al. (2013); no PMD model in 2016
    _COEFFS = {"AD": Takao2013SecondaryFD._COEFFS["AD"]}

    def __init__(self, n_sigma=3.0, case=2, norm_disp_type=None):
        """
        :param n_sigma: truncation half-width of the PAD distribution.
        :param case: parameter set of the paper's Table 1 (1 or 2).
        :param norm_disp_type: optional; only 'AD' is accepted.
        """
        super().__init__(n_sigma=n_sigma, norm_disp_type=norm_disp_type)
        if self.norm_disp_type not in (None, "AD"):
            raise ValueError(
                f"{type(self).__name__}: invalid norm_disp_type="
                f"{norm_disp_type!r}; accepted values: ['AD']")
        try:
            case_ok = float(case) == int(case) and int(case) in self._CASES
        except (TypeError, ValueError):
            case_ok = False
        if not case_ok:
            raise ValueError(
                f"{type(self).__name__}: invalid case={case!r}; "
                f"accepted values: {sorted(self._CASES)}")
        self.case = int(case)
        self._shape, self._eps, self._k = self._CASES[self.case]

    def get_prob_norm_displ(self, DD_norm, r, norm_disp_type="AD"):
        """
        Conditional exceedance probability of the normalized distributed
        displacement DD/PAD at distance r (paper Eqs. 1-2 and 5, Table 1).

        :param DD_norm: Normalized displacement (array of shape (n_displacements,))
        :param r: Closest distance from the principal fault trace in km
            (scalar or array of shape (n_sites,))
        :param norm_disp_type: Normalization displacement type; only "AD".
        :returns: Exceedance probability (shape (n_sites, n_displacements))
        """
        if norm_disp_type not in self._COEFFS:
            raise ValueError(
                f"Invalid norm_disp_type '{norm_disp_type}'. "
                f"Accepted values are: {', '.join(self._COEFFS)}"
            )
        DD_norm = np.atleast_1d(np.asarray(DD_norm, dtype=float))
        r = np.atleast_1d(np.asarray(r, dtype=float))

        b = self._eps * np.exp(-self._k * r)  # Shape (n_sites,)

        return gamma.sf(DD_norm[np.newaxis, :], self._shape,
                        loc=0, scale=b[:, np.newaxis])
