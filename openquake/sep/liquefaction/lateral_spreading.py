from typing import Union, List

import numpy as np

from openquake.sep.liquefaction import (
    HAZUS_LIQUEFACTION_PGA_THRESHOLD_TABLE,
    FT_PER_M,
)

INCH_PER_M = FT_PER_M * 12.0


def _hazus_displacement_correction_factor(
    mag,
    m3_coeff: float = 0.0086,
    m2_coeff: float = -0.0914,
    m1_coeff: float = 0.4698,
    intercept=-0.9835,
):
    """
    Improves estimates of lateral spreading during liquefaction based on the
    magnitude of an earthquake.

    Parameters other than `mag` are numerical coefficients for the polynomial
    fit, which can be modified if one has a region-specific or otherwise
    updated calibration.

    :param mag:
        Moment magnitude of causative earthquake.

    :returns:
        Correction factor to be applied to lateral spreading displacements.
    """
    return (
        m3_coeff * (mag**3) + m2_coeff * (mag**2) + m1_coeff * mag + intercept
    )


def hazus_lateral_spreading_displacement(
    mag: Union[float, np.ndarray],
    pga: Union[float, np.ndarray],
    liq_susc_cat: Union[str, List[str]],
    pga_threshold_table: dict = HAZUS_LIQUEFACTION_PGA_THRESHOLD_TABLE,
    return_unit: str = "m",
) -> Union[float, np.ndarray]:
    """
    Distance of lateral spreading from Hazus
    (https://www.hsdl.org/?view&did=12760)

    :param mag:
        Magnitude of earthquake.

    :param pga:
        Peak Ground Acceleration at site (in units of g).

    :param liq_susc_cat:
        Liquefaction susceptibility category (LSC). This is a category denoting
        the susceptibility of a site to liquefaction, independent of the
        ground motions or earthquake magnitude. Acceptaale values are:
            `vh`: Very high
            `h` : High
            `m` : Medium
            `l` : Low
            `vl`: Very low
            `n` : No susceptibility.

    :returns:
        Displacements from lateral spreading in meters or inches.
    """
    if isinstance(liq_susc_cat, str):
        pga_threshold = pga_threshold_table[liq_susc_cat]
    else:
        pga_threshold = np.array(
            [pga_threshold_table[susc_cat] for susc_cat in liq_susc_cat]
        )
    disp_inch = hazus_lateral_spreading_displacement_fn(
        mag, pga, pga_threshold
    )
    if return_unit == "m":
        disp_m = disp_inch / (INCH_PER_M)
        return disp_m
    elif return_unit == "cm":
        disp_cm = 100.0 * disp_inch / (INCH_PER_M)
        return disp_cm
    elif return_unit == "in":
        return disp_inch
    else:
        raise ValueError(
            "Please choose 'm' or 'cm' or 'in' for return_unit, got %s"
            % return_unit
        )


def hazus_lateral_spreading_displacement_fn(
    mag: Union[float, np.ndarray],
    pga: Union[float, np.ndarray],
    pga_threshold: Union[float, np.ndarray],
):
    """
    Functional form of the Hazus lateral spreading displacement equation.

    :param mag:
        Magnitude of earthquake.

    :param pga:
        Peak Ground Acceleration at site (in units of g).

    :param pga_threshold:
        Threshold for PGA above which liquefaction can occur.

    :returns:
        Displacements from lateral spreading in inches.
    """

    pga_ratio = pga / pga_threshold

    if np.isscalar(pga_ratio):
        if pga_ratio < 1.0:
            a = 0.0
        elif 1.0 < pga_ratio <= 2.0:
            a = 12.0 * pga_ratio - 12.0
        elif 2.0 < pga_ratio <= 3.0:
            a = 18.0 * pga_ratio - 24.0
        else:
            a = 70.0 * pga_ratio - 180.0

    else:
        a = np.zeros(pga_ratio.shape)
        a[(1.0 < pga_ratio) & (pga_ratio <= 2.0)] = (
            12.0 * pga_ratio[(1.0 < pga_ratio) & (pga_ratio <= 2.0)] - 12.0
        )
        a[(2.0 < pga_ratio) & (pga_ratio <= 3.0)] = (
            18.0 * pga_ratio[(2.0 < pga_ratio) & (pga_ratio <= 3.0)] - 24.0
        )
        a[3.0 < pga_ratio] = 70.0 * pga_ratio[3.0 < pga_ratio] - 180.0

    disp_corr_factor = _hazus_displacement_correction_factor(mag)
    disp_inch = disp_corr_factor * a

    return disp_inch
