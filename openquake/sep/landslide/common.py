from typing import Union

import numpy as np
# import xarray as xr


def static_factor_of_safety(
    slope: Union[float, np.ndarray],
    cohesion: Union[float, np.ndarray],
    friction_angle: Union[float, np.ndarray],
    saturation_coeff: Union[float, np.ndarray] = 0.1,
    slab_thickness: Union[float, np.ndarray] = 2.5,
    soil_dry_density: Union[float, np.ndarray] = 1500.0,
    water_density=1000.0,
) -> Union[float, np.ndarray]:
    """
    The static factor of safety (FS) for slopes relates the forces holding the
    slope in place compared to the static forces attempting to cause the slope
    to slide. If the FS is below 1.0, failure should be expected. Values above
    1.0 are increasingly stable.  See Jibson (2000) Engineering Geology for more
    information.

    This calculation can be done for a scalar or for some mix of scalars and
    arrays of a constant size. For example, if a regional model is made with a
    slope array derived from a DEM, other spatially-variable paramters (such as
    cohesion) should be made into rasters with the same size and resolution.


    :param slope: This is either a scalar or array representing the slope of
        topography at the point of interest, in degrees.

    :param cohesion: This parameter is the unstressed tensile strength of the
        material. It should be given in Pa. Typical values are around 20e3 Pa
        (20 kPa) for soils up to 10e6 (20 MPa) for unfaulted rock, i.e. granite.

    :param friction_angle: The internal friction angle measures the orientation
        of shear fractures within a substance relative to the principal
        compressive stress. It should be given in degrees. Typical values are
        30-40 degrees.

    :param saturation_coeff: The fraction of the earth materials that are
        saturated. Typical values are zero for drained conditions up to xx.

    :param slab_thickness: Thickness of the potential slope failure in meters.
        Defaults to 2.5, which is typical for coseismic landslides in the
        Northridge earthquake (Jibson et al., 2000).

    :param soil_dry_density: Density of the drained soil or rock that would make
        up the slide, in kg/m^3. Many soils are ~1500 kg/m^3, while rock is
        2500-3200 kg/m^3.

    :param water_density: Density of water, 1000 kg/m^3.

    :returns: Scalar or array of the factor of safety.
    """

    soil_weight = 9.81 * soil_dry_density
    water_weight = 9.81 * water_density

    if np.isscalar(slope):
        if slope == 0.0:
            slope = 1e-5
    else:
        slope[slope == 0.0] = 1e-5

    r_slope = np.radians(slope)
    r_fric_ang = np.radians(friction_angle)

    term_1 = cohesion / (soil_weight * slab_thickness * np.sin(r_slope))
    term_2 = np.tan(r_fric_ang) / np.tan(r_slope)
    term_3 = (saturation_coeff * water_weight * np.tan(r_fric_ang)) / (
        soil_weight * np.tan(r_slope)
    )

    return term_1 + term_2 - term_3


def rock_slope_static_factor_of_safety(
    slope: Union[float, np.ndarray],
    cohesion: Union[float, np.ndarray],
    friction_angle: Union[float, np.ndarray],
    relief: Union[float, np.ndarray],
    rock_dry_density: Union[float, np.ndarray] = 2600.0,
    root_cohesion: Union[float, np.ndarray] = 0.0,
) -> Union[float, np.ndarray]:
    """
    Static factor of safety for rock-slope failures, from Grant et al. 2016,
    Engineering Geology.

    This calculation can be done for a scalar or for some mix of scalars and
    arrays of a constant size. For example, if a regional model is made with a
    slope array derived from a DEM, other spatially-variable paramters (such as
    cohesion) should be made into rasters with the same size and resolution.

    :param slope: This is either a scalar or array representing the slope of
        topography at the point of interest, in degrees.

    :param cohesion: This parameter is the unstressed tensile strength of the
        material. It should be given in Pa. Typical values are around 20e3 Pa
        (20 kPa) for soils up to 10e6 (20 MPa) for unfaulted rock, i.e. granite.

    :param friction_angle: The internal friction angle measures the orientation
        of shear fractures within a substance relative to the principal
        compressive stress. It should be given in degrees. Typical values are
        30-40 degrees.

    :param relief: Local relief calculated based on the moving window analysis,
        whose size is selected to best capture the major hillslope features within
        the study area. Units are in meters.

    :param rock_dry_density: Density of the drained soil or rock that would make
        up the slide, in kg/m^3. Many soils are ~1500 kg/m^3, while rock is
        2500-3200 kg/m^3.

    :param root_cohesion: Provided by the root systems of vegetated hillslopes.
        Here, we adopted the default value of 0 root cohesion.


    """
    r_slope = np.radians(slope)
    r_friction_angle = np.radians(friction_angle)

    beta = (r_slope + r_friction_angle) / 2.0
    h = 0.25 * relief
    y = rock_dry_density * 9.81

    term_1 = (2 * (cohesion + root_cohesion) * np.sin(r_slope)) / (
        y * h * np.sin(r_slope - beta) * np.sin(beta)
    )

    return term_1 + (np.tan(r_friction_angle) / np.tan(beta))
