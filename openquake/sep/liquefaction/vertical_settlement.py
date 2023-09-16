from typing import Union, List

import numpy as np
import pandas as pd

from openquake.sep.liquefaction.liquefaction import hazus_liquefaction_probability
from openquake.sep.liquefaction import FT_PER_M


INCH_PER_M = FT_PER_M * 12.

# Vertical settlement in inches from HAZUS, which
# only considers the liquefaction susceptibility
# category (earthquake characteristics are not factors).
HAZUS_VERT_SETTLEMENT_TABLE = {
    b'vh': 12.,
    b'h' : 6.,
    b'm' : 2.,
    b'l' : 1.,
    b'vl': 0.,
    b'n' : 0.,
    'vh': 12.,
    'h' : 6.,
    'm' : 2.,
    'l' : 1.,
    'vl': 0.,
    'n' : 0.
}


def hazus_vertical_settlement(
    liq_susc_cat: Union[str, List[str]],
    pga: Union[float, np.ndarray],
    mag: Union[float, np.ndarray],
    settlement_table: dict = HAZUS_VERT_SETTLEMENT_TABLE,
    return_unit: str = 'm',
    groundwater_depth: float = 1.524,
    do_map_proportion_correction: bool = True
) -> Union[float, np.ndarray]:
    """
    Distance of vertical settlement from Hazus.

    :param liq_susc_cat:
        Liquefaction susceptibility category
    :param pga:
        Peak Ground Acceleration, measured in g
    :param mag:
        Magnitude of causative earthquake
    :param settlement_table:
        Dictionary of settlement values
    :param return_unit:
        Specifies the distance unit for the vertical settlement. Options
        are `in` and `m` (default).
    :param groundwater_depth:
        Depth to the groundwater from the earth surface in meters
    :param do_map_proportion_correction:
        Flag to apply an additional LSC-based probability or coefficent to
        the conditional probability

    :returns:
        Displacements from vertical settlement in meters or inches.
    """
    if isinstance(liq_susc_cat, pd.Series):
        liq_susc_cat = liq_susc_cat.tolist()

    if isinstance(liq_susc_cat, list):
        vert_settlement = np.array([settlement_table[susc_cat] for susc_cat in liq_susc_cat])
    else:
        vert_settlement = settlement_table[liq_susc_cat]

    liquefaction_prob = hazus_liquefaction_probability(pga, mag, liq_susc_cat, 
                                                       groundwater_depth, do_map_proportion_correction)

    vert_settlement *= liquefaction_prob

    if return_unit == 'in':
        vert_settlement *= 39.37  # Conversion factor from meters to inches
    elif return_unit != 'm':
        raise ValueError("Please choose 'm' or 'in' for return_unit.")

    return vert_settlement