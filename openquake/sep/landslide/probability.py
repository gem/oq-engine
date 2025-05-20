from typing import Union
import scipy
import numpy as np

g: float = 9.81


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
    "su": -3.22,
    "va": -1.54,
    "vb": -1.50,
    "pi": -0.81
}


LANDCOVER_TABLE = {**landcover_values, **{bytes(k, 'utf-8'): v for k, v in landcover_values.items()}}
LITHOLOGY_TABLE = {**lithology_values, **{bytes(k, 'utf-8'): v for k, v in lithology_values.items()}}


def _landslide_spatial_extent(p: float):
    """
    Calculates the landslide spatial extent (LSE) as per formulae 9
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
    
    p = np.asarray(p, dtype=float)
    
    LSE = 100 * np.exp(a + b * p + c * p**2 + d * p**3)
    return LSE

    
def nowicki_jessee_2018(
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
        Topographic slope expressed in m/m
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

    Xg = (
        pgv_coeff * np.log(pgv) +
        slope_coeff * np.degrees(np.arctan(slope)) +
        lithology_coeff +
        landcover_coeff +
        cti_coeff * cti +
        interaction_term * np.log(pgv) * np.degrees(np.arctan(slope)) +
        intercept
    )

    prob_ls = scipy.special.expit(Xg)
    LSE = _landslide_spatial_extent(prob_ls)

    return prob_ls, LSE
    
    
def allstadt_etal_2022_b(
    pga: Union[float, np.ndarray],
    pgv: Union[float, np.ndarray],
    slope: Union[float, np.ndarray],
    lithology: str,
    landcover: Union[int, np.ndarray],
    cti: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """
    Includes the updates proposed by Allstadt et al. (2022) in the Nowicki Jessee et al. (2018) model. 
    The minimum pga threshold was proposed by Jibson and Harp (2016).
    
    Reference:Allstadt, K. E., Thompson, E. M., Jibson, R. W., Wald, D. J., Hearne, M., Hunter, 
    E. J., Fee, J., Schovanec, H., Slosky, D., & Haynie, K. L. (2022). The US Geological Survey 
    ground failure product: Near-real-time estimates of earthquake-triggered landslides and liquefaction. 
    Earthquake Spectra, 38(1), 5–36. https://doi.org/10.1177/87552930211032685.
    
    :param pga:
        Peak Ground Acceleration, measured in g
    :param slope:
        Topographic slope expressed in m/m
    :param prob_ls:
        Probability of landslide
        
    :returns:
        LSE from Nowicki Jessee et al. (2018) corrected according to Allstadt et al. (2022)
        prob_ls: Probability of landslide according to Nowicki Jessee et al. (2018) corrected according to Allstadt et al. (2022)
    """
    
    cti = np.clip(cti, 0, 19)
    pgv = np.clip(pgv, 1e-5, 211)

    coeff_table_lith = LITHOLOGY_TABLE.copy()
    coeff_table_lith["su"] = -1.36
    
    prob_ls, LSE = nowicki_jessee_2018 (
        pgv = pgv,
        slope = slope,
        lithology = lithology,
        landcover = landcover,
        cti = cti,
        coeff_table_lith=coeff_table_lith,
    )
    
    LSE = np.where((slope < 3.5e-2) | (pga < 0.02), 0, LSE)
    
    return prob_ls, LSE
    
    
def jibson_etal_2000_probability(
    Disp: Union[float, np.ndarray],
    c1: float = 0.335,
    c2: float = -0.048,
    c3: float = 1.565,
) -> Union[float, np.ndarray]:
    """
    Computes the probability of ground failure using a Weibull
    model based on the predicted Newmark displacements (eq. 5 from Jibson et al. (2000)). 
    Exclusively based on data from the Northridge earthquake.

    Reference: Jibson, R.W., Harp, E.L., & Michael, J.A. (2000). A method for 
    producing digital probabilistic seismic landslide hazard maps. Engineering 
    Geology, 58(3-4), 271-289.
    https://doi.org/10.1016/S0013-7952(00)00039-9.

    :param Disp_cm:
        Earthquake-induced displacements in cm predicted according eq. 3 from Jibson et al. (2000)
        
    :returns:
        Scalar or array of ground failure probability.
    """

    Disp_cm = Disp * 100.0  #required conversion in cm, outputs from all displacement models are in m

    return c1 * (1 - np.exp(c2 * Disp_cm**c3))