# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from typing import Union
import numpy as np


# Table mapping the qualitative susceptibility of soils to liquefaction
# to the minimum PGA level necessary to induce liquefaction
LIQUEFACTION_PGA_THRESHOLD_TABLE = {
    b"vh": 0.09,
    b"h": 0.12,
    b"m": 0.15,
    b"l": 0.21,
    b"vl": 0.26,
    b"n": 5.0,
    "vh": 0.09,
    "h": 0.12,
    "m": 0.15,
    "l": 0.21,
    "vl": 0.26,
    "n": 5.0,
}

# Table mapping the qualitative susceptibility of soils to liquefaction
# to coefficients for the range of PGA that can cause liquefaction.
# See `hazus_conditional_liquefaction_probability` for more explanation
# of how these values are used.
LIQUEFACTION_COND_PROB_PGA_TABLE = {
    b"vh": [9.09, 0.82],
    b"h": [7.67, 0.92],
    b"m": [6.67, 1.0],
    b"l": [5.57, 1.18],
    b"vl": [4.16, 1.08],
    b"n": [0.0, 0.0],
    "vh": [9.09, 0.82],
    "h": [7.67, 0.92],
    "m": [6.67, 1.0],
    "l": [5.57, 1.18],
    "vl": [4.16, 1.08],
    "n": [0.0, 0.0],
}


LIQUEFACTION_MAP_AREA_PROPORTION_TABLE = {
    b"vh": 0.25,
    b"h": 0.2,
    b"m": 0.1,
    b"l": 0.05,
    b"vl": 0.02,
    b"n": 0.0,
    "vh": 0.25,
    "h": 0.2,
    "m": 0.1,
    "l": 0.05,
    "vl": 0.02,
    "n": 0.0,
}


FT_PER_M = 3.28084


def zhu_magnitude_correction_factor(mag: float):
    """
    Corrects the liquefaction probabilty equations based on the magnitude
    of the causative earthquake.
    """
    return mag ** 2.56 / 10 ** 2.24


def zhu_liquefaction_probability_general(
    pga: Union[float, np.ndarray],
    mag: Union[float, np.ndarray],
    cti: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    intercept: float = 24.1,
    cti_coeff: float = 0.355,
    vs30_coeff: float = -4.784,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of Zhu et al., 2015. This particular equation is
    the 'general model' with global applicability.

    Reference: Zhu et al., 2015, 'A Geospatial Liquefaction Model for Rapid
    Response and Loss Estimation', Earthquake Spectra, 31(3), 1813-1837.

    :param pga:
        Peak Ground Acceleration, measured in g
    :param mag:
        Magnitude of causative earthquake (moment or work scale)
    :param cti:
        Compound Topographic Index, a proxy for soil wetness.
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site.

    :returns:
        Probability of liquefaction at the site.
    """
    pga_scale = pga * zhu_magnitude_correction_factor(mag)
    Xg = (np.log(pga_scale)
          + cti_coeff * cti
          + vs30_coeff * np.log(vs30)
          + intercept)
    prob_liq = 1.0 / (1.0 + np.exp(-Xg))
    return prob_liq


def hazus_magnitude_correction_factor(
    mag,
    m3_coeff: float = 0.0027,
    m2_coeff: float = -0.0267,
    m1_coeff: float = -0.2055,
    intercept=2.9188,
):
    """
    Corrects the liquefaction probabilty equations based on the magnitude
    of the causative earthquake.
    """
    return (m3_coeff * (mag ** 3)
            + m2_coeff * (mag ** 2)
            + m1_coeff * mag
            + intercept)


def hazus_groundwater_correction_factor(
    groundwater_depth,
    gd_coeff: float = 0.022,
    intercept: float = 0.93,
    unit: str = "feet",
):
    """
    Correction for groundwater depth in FEET
    """

    if unit in ["meters", "m"]:
        groundwater_depth = groundwater_depth * FT_PER_M

    return gd_coeff * groundwater_depth + intercept


def hazus_conditional_liquefaction_probability(
    pga, susceptibility_category, coeff_table=LIQUEFACTION_COND_PROB_PGA_TABLE
):
    """
    Calculates the probility of liquefaction of a soil susceptibility category
    conditional on the value of PGA observed.
    """

    if isinstance(susceptibility_category, str):
        coeffs = coeff_table[susceptibility_category]
        liq_prob = coeffs[0] * pga - coeffs[1]
    else:
        coeffs = [coeff_table[susc_cat]
                  for susc_cat in susceptibility_category]
        coeff_0 = np.array([c[0] for c in coeffs])
        coeff_1 = np.array([c[1] for c in coeffs])
        liq_prob = coeff_0 * pga - coeff_1

    if np.isscalar(liq_prob):
        if liq_prob <= 0:
            liq_prob = 0.0
        elif liq_prob >= 1:
            liq_prob = 1.0
        else:
            liq_prob = liq_prob
    else:
        liq_prob = liq_prob
        liq_prob[liq_prob < 0.0] = 0.0
        liq_prob[liq_prob > 1.0] = 1.0

    return liq_prob


def hazus_liquefaction_probability(
    pga: Union[float, np.ndarray],
    mag: Union[float, np.ndarray],
    liq_susc_cat: str,
    groundwater_depth: float = 1.524,
    do_map_proportion_correction: bool = True,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of liquefaction at a site based on the
    HAZUS methodology, which involves both earthquake and ground motion
    characteristics as well as a site characterization.

    For more information, see the HAZUS-MH MR5 Earthquake Model Technical
    Manual (https://www.hsdl.org/?view&did=12760), section 4-21.

    :param pga:
        Peak Ground Acceleration, measured in g
    :param mag:
        Magnitude of causative earthquake (moment or work scale)
    :param liq_susc_cat:
        Liquefaction susceptibility category (LSC). This is a category denoting
        the susceptibility of a site to liquefaction, independent of the
        ground motions or earthquake magnitude. Acceptable values are:
            `vh`: Very high
            `h` : High
            `m` : Medium
            `l` : Low
            `vl`: Very low
            `n` : No suceptibility.
    :param groundwater_depth:
        Depth to the groundwater from the earth surface in meters (note
        that the HAZUS methods call for this depth in feet; a conversion
        is automatically applied).
    :param do_map_proportion_correction:
        Flag to apply an additional LSC-based probability or coefficent to
        the conditional probability. This is part of the HAZUS methodology
        but it is unclear whether this is applicable for point-based site
        analysis, or how to compare this to other liquefaction models.
        Defaults to `True` following the HAZUS methods.
    """
    groundwater_corr = hazus_groundwater_correction_factor(
        groundwater_depth, unit="m")
    mag_corr = hazus_magnitude_correction_factor(mag)

    if isinstance(liq_susc_cat, str):
        liq_susc_prob = hazus_conditional_liquefaction_probability(
            pga, liq_susc_cat)
        if do_map_proportion_correction:
            map_unit_proportion = LIQUEFACTION_MAP_AREA_PROPORTION_TABLE[
                liq_susc_cat]
        else:
            map_unit_proportion = 1.0
    else:
        liq_susc_prob = hazus_conditional_liquefaction_probability(
            pga, liq_susc_cat)

        if do_map_proportion_correction:
            map_unit_proportion = np.array(
                [LIQUEFACTION_MAP_AREA_PROPORTION_TABLE[lsc]
                 for lsc in liq_susc_cat])
        else:
            map_unit_proportion = 1.0

    return liq_susc_prob * map_unit_proportion / (groundwater_corr * mag_corr)
