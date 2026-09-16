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
Module :mod:`openquake.pfd.primary_surf_displ.lavrentiadis2023` implements
the model of Lavrentiadis and Abrahamson (2023) in two classes, one per
displacement definition (the class choice IS the definition -- unlike a mere
shape/parameter selection, which is passed as a model parameter):

- :class:`Lavrentiadis2023PrimaryFD_aggregate` - the AGGREGATE-definition variants
  (``output_type`` ``disp_agg_prime`` (default) or ``disp_agg_seg``);
- :class:`Lavrentiadis2023PrimaryFD_principal` - the sum-of-principal
  variant (``disp_prnc_prime``, hard-pinned by the class).
"""

import numpy as np
from scipy import stats as scipystats
from openquake.pfd.params import check_bool, check_style
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl

class Lavrentiadis2023PrimaryFD_aggregate(BasePrimarySurfDispl):
    """Aggregate fault-displacement model of Lavrentiadis and Abrahamson (2023).

    Model of aggregate fault displacement as a function of magnitude,
    normalized along-strike position, and faulting style, run in the
    principal (primary_surf_displ) slot.

    References
    ----------
    Lavrentiadis, G., and Abrahamson, N.A. (2023). Fault-displacement models
    for aggregate and principal displacements. Earthquake Spectra, 41(4),
    2806-2837. https://doi.org/10.1177/87552930231201531

    Model contract: DISPLACEMENT_DEFINITION = "aggregate",
    DISPLACEMENT_COMPONENT = "net" -- STATIC, the class choice IS the
    definition. Lavrentiadis & Abrahamson (2023) develop their model on the
    FDHI aggregate displacement (net slip summed across principal and
    distributed ruptures in the measurement aperture); Sarmiento et al.
    (2025, Earthquake Spectra) Table 1 lists LA23 under the aggregate
    definition. This class serves ONLY the aggregate-definition variants:
    ``output_type = "disp_agg_prime"`` (default, full rupture) or
    ``"disp_agg_seg"`` (single segment). The paper's third variant,
    ``disp_prnc_prime`` (principal-strand slip summed within the aperture,
    WITHOUT distributed ruptures -- a sum-of-principal definition), is a
    different physical quantity and lives in its own class,
    :class:`Lavrentiadis2023PrimaryFD_principal`; requesting it here raises
    ValueError (and is rejected at logic-tree validation time, FDLT-015).
    As an aggregate model, this class runs single-bucket and forbids
    secondary-slot models (FDLT-013).
    """

    DISPLACEMENT_DEFINITION = "aggregate"
    DISPLACEMENT_COMPONENT = "net"

    def __init__(self, style=None, output_type=None, include_zero_slip=None):
        """
        :param style: optional faulting style pinned by the logic-tree
            branch; ``None`` defers to the ``get_prob`` call (legacy
            default: 'normal').
        :param output_type: optional output-type selector pinned by the
            logic-tree branch ('disp_agg_prime' or 'disp_agg_seg');
            ``None`` defers to the call (legacy default:
            'disp_agg_prime'). The sum-of-principal 'disp_prnc_prime'
            metric is served by
            :class:`Lavrentiadis2023PrimaryFD_principal` and rejected
            here.
        :param include_zero_slip: optional flag pinned by the logic-tree
            branch; ``None`` defers to the call (legacy default: False).
        """
        self.style = check_style(type(self).__name__, style)
        if output_type is not None:
            output_type = str(output_type)
            self._check_aggregate_output_type(output_type)
        self.output_type = output_type
        self.include_zero_slip = check_bool(
            type(self).__name__, "include_zero_slip", include_zero_slip)

    @staticmethod
    def _check_aggregate_output_type(output_type):
        """Reject the sum-of-principal metric on the aggregate class, both
        at construction (logic-tree pin) and at call time."""
        if output_type == "disp_prnc_prime":
            raise ValueError(
                "Lavrentiadis2023PrimaryFD_aggregate is the AGGREGATE-definition "
                "model (disp_agg_prime / disp_agg_seg); the sum-of-"
                "principal metric disp_prnc_prime is a different "
                "displacement definition (Sarmiento et al. 2025, Table 1). "
                "Select the Lavrentiadis2023PrimaryFD_principal model "
                "class instead of passing output_type = disp_prnc_prime."
            )

    def get_prob(self, d, X_L_ratio, mag, style=None, output_type=None, include_zero_slip=None):
        """
        Probability of exceeding displacement thresholds for the
        Lavrentiadis et al. (2023) model (aggregate-definition variants).

        :param d:
            Target displacement in meters.
        :param X_L_ratio:
            Ratio of distance from the closest rupture end to the total rupture
            length.
        :param mag:
            Earthquake magnitude.
        :param style:
            Style of faulting ("normal", "strike-slip" or "reverse").
        :param output_type:
            Displacement metric to evaluate: ``"disp_agg_prime"`` (default) or
            ``"disp_agg_seg"``. The sum-of-principal ``"disp_prnc_prime"``
            metric is served by
            :class:`Lavrentiadis2023PrimaryFD_principal` and is rejected here.
        :param include_zero_slip:
            If ``True`` the probability accounts for zero slip and gap
            probabilities.
        :returns:
            Probability of exceeding ``d`` for the selected ``output_type``.
        :raises ValueError:
            If ``output_type`` is invalid or is ``"disp_prnc_prime"``.
        """
        # Fall back to constructor-pinned values, then legacy defaults
        if style is None:
            style = self.style if self.style is not None else "normal"
        if output_type is None:
            output_type = (self.output_type
                if self.output_type is not None else "disp_agg_prime")
        if include_zero_slip is None:
            include_zero_slip = (self.include_zero_slip
                if self.include_zero_slip is not None else False)
        self._check_aggregate_output_type(output_type)
        return self._evaluate(
            d, X_L_ratio, mag, style=style, output_type=output_type,
            include_zero_slip=include_zero_slip)

    def _evaluate(self, d, X_L_ratio, mag, style, output_type,
            include_zero_slip):
        """Shared implementation for all published output_type variants
        (the public classes pin/restrict output_type; this does not)."""

        (
            disp_agg_prime,
            disp_prnc_prime,
            disp_agg_seg,
            sig_agg,
            sig_prnc,
            phi_agg,
            phi_prnc,
            tau_agg,
            phi_add,
            P_gap,
            P_zero_slip,
        ) = self.LavrentiadisAbrahamson2023SlipProfile(X_L_ratio, mag, 1, style)

        mu_agg_p = disp_agg_prime**0.3
        mu_prnc_p = disp_prnc_prime**0.3
        mu_agg_seg = disp_agg_seg**0.3
        sig_agg_seg = np.sqrt(tau_agg**2 + phi_agg**2)

        # Ensure d is an array and handle broadcasting
        d = np.atleast_1d(d)
        z = d ** 0.3

        # Reshape for proper broadcasting: (n_displacements, n_locations)
        z = z[:, np.newaxis]  # Shape: (n_displacements, 1)

        # mu and sig arrays have shape (n_locations,)
        # Broadcasting will create arrays of shape (n_displacements, n_locations)
        ccdf_agg = scipystats.norm.sf(x=z, loc=mu_agg_p, scale=sig_agg)
        ccdf_prnc = scipystats.norm.sf(x=z, loc=mu_prnc_p, scale=sig_prnc)
        ccdf_seg = scipystats.norm.sf(x=z, loc=mu_agg_seg, scale=sig_agg_seg)

        ccdf_agg_with_zero = ccdf_agg * (1 - P_gap)
        ccdf_prnc_with_zero = ccdf_prnc * (1 - P_zero_slip) * (1 - P_gap)
        ccdf_seg_with_zero = ccdf_seg * (1 - P_zero_slip)

        if output_type == "disp_prnc_prime":
            prob = ccdf_prnc_with_zero if include_zero_slip else ccdf_prnc
        elif output_type == "disp_agg_prime":
            prob = ccdf_agg_with_zero if include_zero_slip else ccdf_agg
        elif output_type == "disp_agg_seg":
            prob = ccdf_seg_with_zero if include_zero_slip else ccdf_seg
        else:
            raise ValueError(f"Invalid output_type '{output_type}'")

        # Normalize output shape:
        # - single site -> (n_displacements,)
        # - single displacement -> (n_locations,)
        # - otherwise -> (n_displacements, n_locations)
        if getattr(prob, "ndim", 0) == 2:
            if prob.shape[1] == 1:
                return prob[:, 0]
            if prob.shape[0] == 1:
                return prob[0, :]
        return prob


    def LavrentiadisAbrahamson2023SlipProfile(self, x_array, mag, srl, sof="Strike-Slip"):
        """
        Lavrentiadis and Abrahamson 2023 fault displacement model for
        aggregate and principal displacement.

        Parameters
        ----------
        x_array : np.array()
            Along strike location - unnormalized (m).
        mag : real
            Moment Magnitude.
        srl : real
            Surface Rupture Length (m).
        sof : string, optional
            Style of faulting. The valid options are: Normal, Strike-Slip, and Reverse
            The default is 'Strike-Slip'.

        Returns
        -------
        disp_agg_prime : np.array()
            Aggregate displacements for entire event rupture (m).
        disp_prnc_prime : np.array()
            Principal displacements for the entire event rupture (m).
        disp_agg_seg : np.array()
            Aggregate displacements for single segment (m).
        sig_agg : np.array()
            Total aggregate aleatory variability. # includes tau_agg, phi_agg, phi_add
        sig_prnc : np.array()
            Total principal aleatory variability. # includes tau_agg, phi_prnc, phi_add
         phi_agg : np.array()
             Within-event aggregate aleatory variability.
         phi_prnc : np.array()
             Within-event principal aleatory variability.
         tau_agg : np.array()
             Between-event aleatory variability.
        sig_add : np.array()
            Additional aleatory variability due to segmentation. # actually called phi_add
        P_gap : np.array()
            Segment gap probability.
        P_zero_slip : np.array()
            Zero slip probability.
        """

        # model coefficient
        # ---   ---   ---   ---   ---
        # general agg slip
        c_0 = 0.272
        c_1 = 0.913
        c_2 = -2.128
        c_3 = 1.15
        # tapering
        c_5 = np.array([0.7, 0.7, -0.2])
        c_6 = np.array([-0.262, -0.314, 0.0])
        c_7 = 0.033
        # magnitude scaling
        M_1 = np.array([6.25, 6.50, 5.00])
        # effect segmentation (median and shape)
        c_10 = np.array([-0.406, -0.394, -0.849])
        c_11 = np.array([-8.205, -2.950, 8.026])
        c_12 = np.array([-165.0, -64.3, 237.2])
        c_13 = np.array([-1372, -833, 927])
        c_14 = np.array([-3013, -2145, 831])
        c_14a = np.array([-0.904, -1.010, -3.555])
        c_15 = np.array([-0.440, -0.155, -0.087])
        c_16 = np.array([0.0767, 0.0263, 0.0148])
        c_17 = np.array([0.0275, 0.0177, 0.0087])
        c_17a = np.array([0.00276, 0.00534, 0.00234])
        # effect segmentation (aleatory variability)
        c_18 = np.array([-0.215, -0.201, -0.165])
        c_19 = np.array([0.0430, 0.0364, 0.0304])
        c_20 = np.array([0.00574, 0.0102, 0.00773])
        # gap probability
        c_21 = np.array([-0.082, -0.135, -0.151])
        c_22 = np.array([0.027, 0.027, 0.033])
        c_23 = np.array([-0.0088, 0.0063, 0.0032])
        c_24a = np.array([0.020, 0.040, 0.04])
        c_24b = np.array([0.00, 0.0050, 0.00])
        c_24c = np.array([0.0247, 0.00273, 0.00843])
        c_25 = np.array([0.60, 0.41, 0.43])
        c_26a = np.array([0.162, 0.153, 0.156])
        c_26b = np.array([0.084, 0.017, 0.031])
        c_26c = np.array([0.0080, 0.00312, 0.00575])
        # principal displacement
        b_0 = np.array([-3.240, 0.867, 1.65])
        b_1 = np.array([9.105, 3.767, 1.349])
        b_2 = np.array([-0.097, -0.048, -0.062])
        # principal aleatory variability
        phi_b2 = 0.11
        tau_b2 = 0.05  # noqa: F841
        rho_b2 = -0.15
        # style fault faulting
        sof_array = np.array(["normal", "strike-slip", "reverse"])

        # normalized
        xl_array = x_array / srl
        # Fold x/L to [0, 0.5] using modulus reflection, robust to 1±eps
        r = xl_array - np.floor(xl_array)  # map to [0,1)
        xl_array = 0.5 - np.abs(r - 0.5)  # symmetric fold to [0,0.5]
        assert xl_array.min() >= 0 and xl_array.max() <= 0.5, "Error. Invalid normalization."

        # convert sof to lower case
        sof = sof.lower()
        # general agg slip
        # ---   ---   ---   ---   ---
        d_agg = c_0 + c_1 * (xl_array - 0.3) + c_2 * (xl_array - 0.3) ** 2 + c_3 * (mag - 7.0)  # eqn 8
        d_agg = np.exp(d_agg)

        # tapering
        # ---   ---   ---   ---   ---
        # slip tapering
        c_5 = c_5[sof_array == sof]
        xl1 = 0.15 - 0.10 * np.minimum(np.maximum(mag - 7.0, 0.0), 1)
        T_xl = np.minimum(xl_array - xl1, 0) / xl1
        # magnitude tapering
        c_6 = c_6[sof_array == sof]
        M_1 = M_1[sof_array == sof]
        T_M = np.maximum(np.minimum((7.0 - mag) / (7.0 - M_1), 1.0), 0.0)

        # median slip (pwr=0.3)
        # ---   ---   ---   ---   ---
        mu_agg_seg = (
            (d_agg * np.exp(c_5 * T_xl)) ** 0.3 + c_6 * T_M + c_7
        )  # eqn 14, which is for indiv segments

        # effect of segmentation
        # ---   ---   ---   ---   ---
        c_10 = c_10[sof_array == sof]
        c_11 = c_11[sof_array == sof]
        c_12 = c_12[sof_array == sof]
        c_13 = c_13[sof_array == sof]
        c_14 = c_14[sof_array == sof]
        c_14a = c_14a[sof_array == sof]
        c_15 = c_15[sof_array == sof]
        c_16 = c_16[sof_array == sof]
        c_17 = c_17[sof_array == sof]
        c_17a = c_17a[sof_array == sof]
        # normalize shape effect
        xl_offset1 = np.minimum(xl_array - 0.3, 0)
        xl_offset2 = np.maximum(xl_array - 0.4, 0)
        f_NDmu = (
            c_11 * xl_offset1
            + c_12 * xl_offset1**2
            + c_13 * xl_offset1**3
            + c_14 * xl_offset1**4
            + c_14a * xl_offset2
        )
        f_NDmu = c_10 + f_NDmu
        # amplitude effect
        Dmu_max = c_15 + c_16 * mag + c_17 * (mag - 6.7) ** 2 + c_17a * (mag - 6.7) ** 3
        # cobined effect
        mu_agg_prime = mu_agg_seg + Dmu_max * f_NDmu  # eqn 22, which is for the full rupture

        # gap probability
        # ---   ---   ---   ---   ---
        c_21 = c_21[sof_array == sof]
        c_22 = c_22[sof_array == sof]
        c_23 = c_23[sof_array == sof]
        c_24a = c_24a[sof_array == sof]
        c_24b = c_24b[sof_array == sof]
        c_24c = c_24c[sof_array == sof]
        c_25 = c_25[sof_array == sof]
        c_26a = c_26a[sof_array == sof]
        c_26b = c_26b[sof_array == sof]
        c_26c = c_26c[sof_array == sof]

        # mag dependent coeffs
        c_24 = c_24a + c_24b * (mag - 5) + c_24c * (mag - 5) ** 3
        c_26 = c_26a + c_26b * (mag - 5) + c_26c * (mag - 5) ** 3

        # max gap probability
        P_gap_max = c_21 + c_22 * mag + c_23 * (mag - 6.5) ** 2

        # shape normalization
        f_NPGap = (
            20.0 * c_24 * np.minimum(np.maximum(xl_array - 0.10, 0.0), 0.05)
        )  # first and second leg
        f_NPGap += (
            0.13**-1 * (1.0 - c_24) * np.minimum(np.maximum(xl_array - 0.15, 0.0), 0.13)
        )  # third leg and fourth
        f_NPGap -= (
            10.0 * (1.0 - c_25) * np.minimum(np.maximum(xl_array - 0.30, 0.0), 0.10)
        )  # fifth leg
        f_NPGap -= (
            10.0 * (c_25 - c_26) * np.minimum(np.maximum(xl_array - 0.40, 0.0), 0.10)
        )  # sixth leg

        # probability of gap
        P_gap = P_gap_max * f_NPGap

        # zero slip probability
        # ---   ---   ---   ---   ---
        b_0 = b_0[sof_array == sof]
        b_1 = b_1[sof_array == sof]

        P_zero_slip = 1 / (1 + np.exp(b_0 + b_1 * mu_agg_prime))

        # principal displacements
        # ---   ---   ---   ---   ---
        # compute b2
        b_2 = b_2[sof_array == sof]

        mu_prnc_prime = mu_agg_prime + b_2
        mu_prnc_prime = np.maximum(mu_prnc_prime, 0.0)

        # aleatory variablity
        # ---   ---   ---   ---   ---
        phi_agg = np.maximum(np.minimum(0.120 + 0.150 * (mag - 6.0), 0.270), 0.120)
        tau_agg = np.maximum(np.minimum(0.115 + 0.060 * (mag - 6.0), 0.205), 0.115)
        phi_prnc = np.sqrt(phi_agg**2 + phi_b2**2 + 2 * rho_b2 * phi_agg * phi_b2)

        # additional variability due to segmentation
        c_18 = c_18[sof_array == sof]
        c_19 = c_19[sof_array == sof]
        c_20 = c_20[sof_array == sof]
        # additional sigma
        phi_add = c_18 + c_19 * mag + c_20 * (mag - 6.7) ** 2
        # total sigma
        sig_agg = np.sqrt(tau_agg**2 + phi_agg**2 + phi_add**2)
        sig_prnc = np.sqrt(tau_agg**2 + phi_prnc**2 + phi_add**2)

        # variable transformation
        # ---   ---   ---   ---   ---
        disp_agg_prime = mu_agg_prime ** (1 / 0.3)
        disp_prnc_prime = mu_prnc_prime ** (1 / 0.3)
        disp_agg_seg = mu_agg_seg ** (1 / 0.3)

        return (
            disp_agg_prime,
            disp_prnc_prime,
            disp_agg_seg,
            sig_agg,
            sig_prnc,
            phi_agg,
            phi_prnc,
            tau_agg,
            phi_add,
            P_gap,
            P_zero_slip,
        )


    def LavrentiadisAbrahamson2023SlipProfilePrc(self, x_array, mag, srl, sof="Strike-Slip", prc=0.5):
        """
        Lavrentiadis and Abrahamson 2023 aggregate and principal displacement
        profiles for selected percentiles.

        Parameters
        ----------
        x_array : np.array()
            Along strike location - unnormalized (m).
        mag : real
            Moment Magnitude.
        srl : real
            Surface Rupture Length (m).
        sof : string, optional
            Style of faulting. The valid options are: Normal, Strike-Slip, and Reverse
            The default is 'Strike-Slip'.
        prc : real, optional
            Percentile for displacement profile. The default is 0.5.

        Returns
        -------
        disp_agg_p_prc : np.array()
            DESCRIPTION.
        disp_prnc_p_prc : np.array()
            DESCRIPTION.
        disp_agg_seg_prc : np.array()
            DESCRIPTION.
        """

        # evaluate LA23 model
        # disp_agg_p, disp_prnc_p, _, sig_agg, sig_prnc, _, _, _, _, _, _  = LavrentiadisAbrahamson2023SlipProfile(x_array, mag, srl, sof)
        # modified by alex to capture segment results
        (
            disp_agg_p,
            disp_prnc_p,
            disp_agg_seg,
            sig_agg,
            sig_prnc,
            phi_agg,
            _,
            tau_agg,
            _,
            _,
            _,
        ) = self.LavrentiadisAbrahamson2023SlipProfile(x_array, mag, srl, sof)
        disp_agg_p = disp_agg_p ** (0.3)
        disp_prnc_p = disp_prnc_p ** (0.3)

        # compute percentile of aggregate profile
        disp_agg_p_prc = scipystats.norm.ppf(prc, loc=disp_agg_p, scale=sig_agg)
        disp_agg_p_prc[disp_agg_p_prc < 0] = 0.0
        disp_agg_p_prc = disp_agg_p_prc ** (1 / 0.3)

        # compute percentile of principal profile
        disp_prnc_p_prc = scipystats.norm.ppf(prc, loc=disp_prnc_p, scale=sig_prnc)
        disp_prnc_p_prc[disp_prnc_p_prc < 0] = 0.0
        disp_prnc_p_prc = disp_prnc_p_prc ** (1 / 0.3)

        # added by alex; compute percentile of segment profile
        sig_agg_seg = np.sqrt(tau_agg**2 + phi_agg**2)
        disp_agg_seg_prc = scipystats.norm.ppf(prc, loc=disp_agg_seg, scale=sig_agg_seg)
        disp_agg_seg_prc[disp_agg_seg_prc < 0] = 0.0
        disp_agg_seg_prc = disp_agg_seg_prc ** (1 / 0.3)

        return disp_agg_p_prc, disp_prnc_p_prc, disp_agg_seg_prc


    def LavrentiadisAbrahamson2023AvgDisp(self, mag, srl, sof="Strike-Slip"):
        """
        Lavrentiadis and Abrahamson 2023 model for average displacement (median value).

        Parameters
        ----------
        mag : real
            Moment Magnitude.
        srl : real
            Surface Rupture Length (m).
        sof : string, optional
            Style of faulting. The valid options are: Normal, Strike-Slip, and Reverse
            The default is 'Strike-Slip'.

        Returns
        -------
        disp_avg : real
            Average slip (m).
        ratio_ad : real
            Ratio for average slip to principal slip at x/L=0.25.
        """

        # model coefficient
        # ---   ---   ---   ---   ---
        b_3 = np.array([0.286, 0.191, 0.28])
        b_4 = np.array([1.195, 1.058, 0.0])
        b_5 = np.array([-1.526, -1.418, 0.0])
        # style fault faulting
        sof_array = np.array(["normal", "strike-slip", "reverse"])

        # average displacement
        # ---   ---   ---   ---   ---
        sof = sof.lower()
        b_3 = b_3[sof_array == sof]
        b_4 = b_4[sof_array == sof]
        b_5 = b_5[sof_array == sof]

        # slip at x/L=0.25
        disp_prnc_prime = self.LavrentiadisAbrahamson2023SlipProfile(0.25 * srl, mag, srl, sof)[1]

        # average displacement ratio
        ratio_ad = np.exp(b_3 + b_4 * np.exp(b_5 * (mag - 5.0)))

        # average displacement
        disp_avg = ratio_ad * disp_prnc_prime

        return disp_avg, ratio_ad


    def LavrentiadisAbrahamson2023MaxDisp(self, mag, srl, sof="Strike-Slip"):
        """
        Lavrentiadis and Abrahamson 2023 model for maximum displacement (median value).


        Parameters
        ----------
        mag : real
            Moment Magnitude.
        srl : real
            Surface Rupture Length (m).
        sof : string, optional
            Style of faulting. The valid options are: Normal, Strike-Slip, and Reverse
            The default is 'Strike-Slip'.

        Returns
        -------
        disp_max : real
            Maximum slip - median value (m).
        sig_dm : real
            Aleatory standard deviation of max displacement

        """

        # model coefficient
        # ---   ---   ---   ---   ---
        e_1 = 0.326
        e_2 = 0.41
        e_3 = np.array([-0.0166, -0.0144, -0.0172])
        e_4 = np.array([0.0244, -0.0109, 0.0094])
        # style fault faulting
        sof_array = np.array(["normal", "strike-slip", "reverse"])

        # maximum displacement
        # ---   ---   ---   ---   ---
        sof = sof.lower()
        e_3 = e_3[sof_array == sof]
        e_4 = e_4[sof_array == sof]

        # slip at x/L=0.25
        disp_agg_prime = self.LavrentiadisAbrahamson2023SlipProfile(0.25 * srl, mag, srl, sof)[0]

        # maximum displacement offset
        dm_pwr = e_1
        dm_pwr += e_2 * np.minimum(np.maximum(mag - 6.0, 0.0), 1.0)
        dm_pwr += e_3 * np.maximum(mag - 7.0, 0.0) + e_4 * np.maximum(mag - 7.0, 0.0) ** 2

        # aleatory variability
        sig_dm = 0.13 + 0.095 * np.minimum(np.maximum(mag - 6.0, 0.0), 1.0)
        sig_dm += 0.050 * np.minimum(np.maximum(mag - 7.0, 0.0), 0.5)

        # max displacement
        disp_max = (disp_agg_prime**0.3 + dm_pwr) ** (1 / 0.3)

        return disp_max, sig_dm


    # added by alex from greg
    def _calc_mean(mean_pn, sd_pn):
        """
        Helper function to calculate the back-transformed predicted mean displacement in meters
        using the model parameters. A closed-form solution is not available, so sampling is used.

        Parameters
        ----------
        mean_pn : float
            mean displacement in power-normal (m^0.3) units

        sd_pn : float
            standard deviation in power-normal (m^0.3) units

        Returns
        -------
        float
            Predicted mean displacement in meters.
        """

        # Ensure inputs are arrays
        mean_pn, sd_pn = np.atleast_1d(mean_pn), np.atleast_1d(sd_pn)

        # Sample
        np.random.seed(1)
        s = np.random.normal(
            loc=mean_pn[:, np.newaxis], scale=sd_pn[:, np.newaxis], size=(len(mean_pn), 1_000_000)
        )

        # Replace negative values with NaN and compute mean
        return np.nanmean(np.where(s >= 0, s, np.nan) ** (10 / 3), axis=1)


class Lavrentiadis2023PrimaryFD_principal(Lavrentiadis2023PrimaryFD_aggregate):
    """Sum-of-principal variant of Lavrentiadis and Abrahamson (2023).

    Identical regression machinery as :class:`Lavrentiadis2023PrimaryFD_aggregate`,
    hard-pinned to the paper's ``disp_prnc_prime`` metric: the principal-
    strand slip summed within the measurement aperture, WITHOUT distributed
    ruptures. Following the Petersen2011PrimaryFD_* variant idiom, the class
    choice IS the definition -- ``output_type`` is fixed by this class and
    passing any explicit value raises ValueError (also rejected at
    logic-tree validation time, FDLT-015).

    Model contract: DISPLACEMENT_DEFINITION = "sum-of-principal",
    DISPLACEMENT_COMPONENT = "net" -- Lavrentiadis & Abrahamson (2023)
    derive the principal-prime profile from the aggregate one (their b_2
    offset and zero-slip probability); like Chiou et al. (2025)'s D_SP it
    excludes distributed ruptures, so secondary-slot models remain
    legitimate alongside this class (it is NOT aggregate; FDLT-013 does not
    apply).
    """

    DISPLACEMENT_DEFINITION = "sum-of-principal"
    DISPLACEMENT_COMPONENT = "net"

    def __init__(self, style=None, output_type=None, include_zero_slip=None):
        """
        Parameters as in :class:`Lavrentiadis2023PrimaryFD_aggregate`, except
        ``output_type``, which must be left unset -- the metric is fixed
        by the class choice (a logic-tree pin would otherwise be silently
        ignored).
        """
        self._check_no_output_type(output_type)
        super().__init__(style=style, include_zero_slip=include_zero_slip)

    @staticmethod
    def _check_no_output_type(output_type):
        if output_type is not None:
            raise ValueError(
                "Lavrentiadis2023PrimaryFD_principal evaluates the "
                "disp_prnc_prime (sum-of-principal) metric; output_type "
                f"is fixed by the class choice (got '{output_type}'). "
                "Remove the output_type parameter, or select "
                "Lavrentiadis2023PrimaryFD_aggregate for the aggregate variants."
            )

    def get_prob(self, d, X_L_ratio, mag, style=None,
            include_zero_slip=None, output_type=None):
        """
        Probability of exceeding sum-of-principal (``disp_prnc_prime``)
        displacement thresholds; parameters as in
        :meth:`Lavrentiadis2023PrimaryFD_aggregate.get_prob`.

        :param output_type:
            Must be left unset -- the metric is fixed by the class choice.
        :raises ValueError:
            If an explicit ``output_type`` is passed.
        """
        self._check_no_output_type(output_type)
        if style is None:
            style = self.style if self.style is not None else "normal"
        if include_zero_slip is None:
            include_zero_slip = (self.include_zero_slip
                if self.include_zero_slip is not None else False)
        return self._evaluate(
            d, X_L_ratio, mag, style=style, output_type="disp_prnc_prime",
            include_zero_slip=include_zero_slip)