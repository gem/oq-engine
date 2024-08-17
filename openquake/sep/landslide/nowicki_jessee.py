from typing import Union
import numpy as np


LANDCOVER_TABLE={
    b"14": 0.91,
    b"20": 0.88,
    b"30": 0.78,
    b"40": 0.68,
    b"50": 0.30,
    b"60": 1.77,
    b"70": 1.71,
    b"90": -1.26,
    b"100": 1.50,
    b"110": 0.68,
    b"120": 1.13,
    b"130": 0.79,
    b"140": 1.03,
    b"150": 0.54,
    b"160": 2.34,
    b"170": 1.19,
    b"180": 1.19,
    b"190": 0.30,
    b"200": -0.06,
    b"220": -0.18,
    b"230": -1.08,
    "14": 0.91,
    "20": 0.88,
    "30": 0.78,
    "40": 0.68,
    "50": 0.30,
    "60": 1.77,
    "70": 1.71,
    "90": -1.26,
    "100": 1.50,
    "110": 0.68,
    "120": 1.13,
    "130": 0.79,
    "140": 1.03,
    "150": 0.54,
    "160": 2.34,
    "170": 1.19,
    "180": 1.19,
    "190": 0.30,
    "200": -0.06,
    "220": -0.18,
    "230": -1.08
}


LITHOLOGY_TABLE={
    b"mt": -1.87,
    b"nd": -0.66,
    b"pa": -0.78,
    b"pb": -1.88,
    b"vi": -1.61,
    b"py": -1.05,
    b"sc": -0.95,
    b"sm": -1.36,
    b"ss": -1.92,
    b"su": -1.36,
    b"va": -1.54,
    b"vb": -1.50,
    b"pi": -0.81,
    "mt": -1.87,
    "nd": -0.66,
    "pa": -0.78,
    "pb": -1.88,
    "vi": -1.61,
    "py": -1.05,
    "sc": -0.95,
    "sm": -1.36,
    "ss": -1.92,
    "su": -1.36,
    "va": -1.54,
    "vb": -1.50,
    "pi": -0.81
}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def areal_coverage(a: float, b: float, c: float, d: float, p: float):
    LP = np.exp(a + b * p + c * p**2 + d * p**3)

    return LP

    
def nowicki_jessee_2018(
    pga: Union[float, np.ndarray],
    pgv: Union[float, np.ndarray],
    slope: Union[float, np.ndarray],
    lithology: str,
    landcover: Union[int, np.ndarray],
    cti: Union[float, np.ndarray],
    intercept: float = -6.30,
    pgv_coeff: float = 1.65,
    slope_coeff: float = 0.06,
    coeff_table_lith=LITHOLOGY_TABLE,
    coeff_table_cov=LANDCOVER_TABLE,
    cti_coeff: float = 0.03,
    interaction_term: float = 0.01
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of landsliding using the logistic
    regression of Nowicki Jessee et al. (2018). As per USGS recommendation,
    the values of pgv and cti are capped to 211 cm/s and 19, respectively.
    Furthermore, the model computes the areal coverage, which unbiases the
    calculated probabilities.

    Reference: Nowicki Jessee, M. A., Hamburger, M. W., Allstadt, K., 
    Wald, D. J., Robeson, S. M., Tanyas, H., et al. (2018). 
    A global empirical model for near-real-time assessment of seismically 
    induced landslides. 
    Journal of Geophysical Research: Earth Surface, 123, 1835–1859. 
    https://doi.org/10.1029/2017JF004494

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param slope:
        Topographic slope expressed in degrees
    :param lithology:
        Rock lithology, a "measure" of rock strength
    :param landcover:
        Land cover, procxy for vegetation cover
    :param cti:
        Compound Topographic Index, a proxy for soil wetness.

    :returns:
        prob_ls: Probability of landslide.
        coverage: Landslide areal coverage.
    """

    if isinstance(lithology, (str)):
        lithology_coeff = coeff_table_lith.get(lithology, -0.66)
    else:
        lithology_coeff = np.array([coeff_table_lith.get(lith, -0.66) for lith in lithology])

    if isinstance(landcover, (int)):   
        landcover = str(landcover)
        landcover_coeff = coeff_table_cov.get(landcover, -1.08)
    else:
        landcover_coeff = np.array([coeff_table_cov.get(str(lc), -1.08) for lc in landcover])

    cti = np.clip(np.where(cti > 19, 19, cti), 0, None)
    pgv = np.clip(np.where(pgv > 211, 211, pgv), 1e-5, None)

    Xg = (
        pgv_coeff * np.log(pgv) +
        slope_coeff * slope +
        lithology_coeff +
        landcover_coeff +
        cti_coeff * cti +
        interaction_term * np.log(pgv) * slope +
        intercept
    )

    prob_ls = sigmoid(Xg)
    coverage = areal_coverage(-7.592, 5.237, -3.042, 4.035, prob_ls)
    coverage = np.where((slope < 2) | (pga < 0.02), 0, coverage)

    return prob_ls, coverage