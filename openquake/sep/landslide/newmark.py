from typing import Union

import numpy as np

g: float = 9.81


def newmark_critical_accel(
    factor_of_safety: Union[float, np.ndarray], slope: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """
    Calculates the critical acceleration, i.e. the acceleration at which the
    slope fails.

    :param factor_of_safety:
        Static Factor of Safety for the site in question.

    :param slope:
        Slope of site in degrees.

    :returns:
        Critical acceleration in terms of g (9.81 m s^-2)
    """

    crit_accel = (factor_of_safety - 1) * np.sin(np.radians(slope)) * g
    if np.isscalar(crit_accel):
        return max([0.0, crit_accel])
    else:
        return np.array([max([0.0, ca]) for ca in crit_accel])


def newmark_displ_from_pga_M(
    pga: Union[float, np.ndarray],
    critical_accel: Union[float, np.ndarray],
    M: float,
    c1: float = -2.71,
    c2: float = 2.335,
    c3: float = -1.478,
    c4: float = 0.424,
    crit_accel_threshold: float = 0.05,
) -> Union[float, np.ndarray]:
    """
    Landslide displacement calculated from PGA, M, and critical acceleration,
    from Jibson (2007), equation 7.

    :param pga:
        Peak Ground Acceleration, measured in g.

    :param critical_accel:
        Critical Acceleration, measured in g; this is the acceleration at which
        the slope fails.

    :param M:
        Magnitude (Mw) of the earthquake.

    :param c1:
        Empirical constant

    :param c2:
        Empirical constant

    :param c3:
        Empirical constant

    :param c4:
        Empirical constant

    :param crit_accel_threshold:
        Lower bound for critical acceleration. Values close to or below zero
        may reflect an incorrect factor of safety calculation or site
        characterization, and produce unreasonably high displacements.
        Defaults to 0.05

    :returns:
        Predicted earthquake displacement in meters.
    """

    # Corrections of invalid values
    if np.isscalar(pga):
        if pga == 0.0:
            pga = 1e-5
    else:
        pga[pga == 0.0] = 1e-5

    accel_ratio = critical_accel / pga

    # Corrects too high or too low accel ratios (it breaks powers below)
    if np.isscalar(accel_ratio):
        if accel_ratio > 1.0:
            accel_ratio = 1.0
        elif accel_ratio <= crit_accel_threshold:
            accel_ratio == crit_accel_threshold
    else:
        accel_ratio[accel_ratio > 1.0] = 1.0
        accel_ratio[accel_ratio <= crit_accel_threshold] = crit_accel_threshold

    pow_1 = (1 - accel_ratio) ** c2
    pow_2 = accel_ratio**c3

    pow_prod = pow_1 * pow_2

    # Fix zero products of powers (which breaks log below)
    if np.isscalar(pow_prod):
        if pow_prod == 0.0:
            pow_prod = 1e-100
    else:
        pow_prod[pow_prod == 0.0] = 1e-100

    log_d = c1 + np.log10(pow_prod) + c4 * M

    d_cm = 10.0 ** (log_d)

    # Zero product of powers fix re-fixed to zero displacement
    if np.isscalar(d_cm):
        if d_cm < 1e-99:
            d_cm = 0.0
    else:
        d_cm[d_cm < 1e-99] = 0.0

    # Convert output to m
    d_m = d_cm / 100.0

    return d_m


def prob_failure_given_displacement(
    displacement: Union[float, np.ndarray],
    c1: float = 0.335,
    c2: float = -0.048,
    c3: float = 1.565,
) -> Union[float, np.ndarray]:
    """
    Computes the probability of ground failure using a Weibull
    model based on the predicted Newmark displacements.

    Constants from Jibson et al., 2000 for the Northridge earthquake.

    :param displacement:
        Predicted Newmark displacement at a site, in meters (will be converted
        to cm in the function).  Can be scalar or array.

    :returns:
        Scalar or array of ground failure probability.
    """

    Dn = displacement * 100.0

    return c1 * (1 - np.exp(c2 * Dn**c3))
