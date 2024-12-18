# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020-2023, GEM Foundation
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

try:
    import xarray as xr
except ImportError:
    pass
from .landslide.common import static_factor_of_safety
from .landslide.newmark import newmark_critical_accel, newmark_displ_from_pga_M


def calc_newmark_soil_slide_single_event(
    pga: Union[float, np.ndarray],
    M: float,
    slope: Union[float, np.ndarray],
    cohesion: Union[float, np.ndarray],
    friction_angle: Union[float, np.ndarray],
    saturation_coeff: Union[float, np.ndarray] = 0.1,
    slab_thickness: Union[float, np.ndarray] = 2.5,
    soil_dry_density: Union[float, np.ndarray] = 1500.0,
    water_density: float = 1000.0,
    out_name=None,
) -> Union[float, np.ndarray]:
    fs = static_factor_of_safety(
        slope,
        cohesion,
        friction_angle,
        saturation_coeff,
        slab_thickness,
        soil_dry_density,
        water_density,
    )

    ca = newmark_critical_accel(fs, slope)

    Dn = newmark_displ_from_pga_M(pga, ca, M)

    if isinstance(Dn, xr.DataArray):
        Dn.name = out_name

    return Dn


def calc_newmark_soil_slide_event_set(
    pga: Union[float, np.ndarray],
    M: Union[float, np.ndarray],
    slope: Union[float, np.ndarray],
    cohesion: Union[float, np.ndarray],
    friction_angle: Union[float, np.ndarray],
    saturation_coeff: Union[float, np.ndarray] = 0.1,
    slab_thickness: Union[float, np.ndarray] = 2.5,
    soil_dry_density: Union[float, np.ndarray] = 1500.0,
    water_density=1000.0,
) -> Union[float, np.ndarray]:
    fs = static_factor_of_safety(
        slope,
        cohesion,
        friction_angle,
        saturation_coeff,
        slab_thickness,
        soil_dry_density,
        water_density,
    )

    ca = newmark_critical_accel(fs, slope)

    if isinstance(pga, xr.Dataset):
        Dn = xr.Dataset(
            {
                k: newmark_displ_from_pga_M(da, ca, da.attrs["mag"])
                for k, da in pga.data_vars.items()
            }
        )
    return Dn


def calc_rock_slope_failures():
    pass


def calc_rotational_failures():
    pass


def calculate_lateral_spreading():
    pass
