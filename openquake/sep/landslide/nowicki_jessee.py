from typing import Union
import numpy as np


landcover_values={
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
    "180": 1.19,
    "190": 0.30,
    "200": -0.06,
    "220": -0.18,
    "230": -1.08
}


lithology_values={
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


LANDCOVER_TABLE = {**landcover_values, **{bytes(k, 'utf-8'): v for k, v in landcover_values.items()}}
LITHOLOGY_TABLE = {**lithology_values, **{bytes(k, 'utf-8'): v for k, v in lithology_values.items()}}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _landslide_spatial_extent(p: float):
    """Calculates the landslide spatial extent (LSE) as per formulae 9
    from the Reference. LSE after an earthquake can be interpreted as the
    portion of each cell that is expected to have landslide occurrence.

    Reference: Nowicki Jessee, M. A., Hamburger, M. W., Allstadt, K., 
    Wald, D. J., Robeson, S. M., Tanyas, H., et al. (2018). 
    A global empirical model for near-real-time assessment of seismically 
    induced landslides. 
    Journal of Geophysical Research: Earth Surface, 123, 1835–1859. 
    https://doi.org/10.1029/2017JF004494
    """
    a = -7.592
    b = 5.237
    c = -3.042
    d = 4.035
    LSE = 100 *     np.exp(a + b * p + c * p**2 + d * p**3)
    return LSE

    
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

    if isinstance(lithology, str):
        lithology_coeff = coeff_table_lith.get(lithology, -0.66)
    else:
        lithology_coeff = np.array([coeff_table_lith.get(lith, -0.66) for lith in lithology])

    if isinstance(landcover, int):   
        landcover = str(landcover)
        landcover_coeff = coeff_table_cov.get(landcover, -1.08)
    else:
        landcover_coeff = np.array([coeff_table_cov.get(str(lc), -1.08) for lc in landcover])

    cti = np.clip(cti, 0, 19)
    pgv = np.clip(pgv, 1e-5, 211)

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
    LSE = _landslide_spatial_extent(prob_ls)

    # Slope cutoff proposed by Allstadt et al. (2022), minimum pga threshold proposed by Jibson and Harp (2016)
    LSE = np.where((slope < 2) | (pga < 0.02), 0, LSE)

    return prob_ls, LSE