from typing import Union, List

import numpy as np

from openquake.sep.liquefaction import FT_PER_M

INCH_PER_M = FT_PER_M * 12.0

# Vertical settlement in inches from HAZUS, which
# only considers the liquefaction susceptibility
# category (earthquake characteristics are not factors).
HAZUS_VERT_SETTLEMENT_TABLE = {
    b"vh": 12.0,
    b"h": 6.0,
    b"m": 2.0,
    b"l": 1.0,
    b"vl": 0.0,
    b"n": 0.0,
    "vh": 12.0,
    "h": 6.0,
    "m": 2.0,
    "l": 1.0,
    "vl": 0.0,
    "n": 0.0,
}


def hazus_vertical_settlement(
    liq_susc_cat: Union[str, List[str]],
    settlement_table: dict = HAZUS_VERT_SETTLEMENT_TABLE,
    return_unit: str = "m",
) -> Union[float, np.ndarray]:
    """
    Distance of vertical settlement from Hazus
    (https://www.hsdl.org/?view&did=12760)

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

    :param return_unit:
        Specifies the distance unit for the vertical settlement. Options
        are `in` and `m` (default).

    :returns:
        Displacements from vertical settlement in meters or inches.
    """
    if isinstance(liq_susc_cat, str):
        vert_settlement = settlement_table[liq_susc_cat]
    else:
        vert_settlement = np.array(
            [settlement_table[susc_cat] for susc_cat in liq_susc_cat]
        )

    if return_unit == "in":
        pass
    elif return_unit == "m":
        vert_settlement /= INCH_PER_M
    else:
        raise ValueError("Please choose 'm' or 'in' for return_unit.")

    return vert_settlement
