from typing import Union
import numpy as np


def infinite_slope_fs(
    slope: Union[float, np.ndarray],
    cohesion: Union[float, np.ndarray],
    friction_angle: Union[float, np.ndarray],
    saturation_coeff: Union[float, np.ndarray],
    slab_thickness: Union[float, np.ndarray],
    soil_dry_density: Union[float, np.ndarray],
    water_density=1000.0,
) -> Union[float, np.ndarray]:
    """
    Computes the static factor of safety (FS) for slopes according to the
    infinite slope method. It relates the forces holding the
    slope in place compared to the static forces attempting to cause the slope
    to slide. If the FS is below 1.0, failure should be expected. Values above
    1.0 are increasingly stable.  See Jibson (2000) Engineering Geology for more
    information. 

    This calculation can be done for a scalar or for some mix of scalars and
    arrays of a constant size. For example, if a regional model is made with a
    slope array derived from a DEM, other spatially-variable paramters (such as
    cohesion) should be made into rasters with the same size and resolution.
    
    Reference: Jibson, R. W., Harp, E. L., & Michael, J. A. (2000). A method for 
    producing digital probabilistic seismic landslide hazard maps. 
    Engineering geology, 58(3-4), 271-289.
    https://www.sciencedirect.com/science/article/pii/S0013795200000399.

    :param slope: This is either a scalar or array representing the slope of
        topography at the point of interest, in m/m.

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
        

    :param soil_dry_density: Density of the drained soil or rock that would make
        up the slide, in kg/m^3. Many soils are ~1500 kg/m^3, while rock is
        2500-3200 kg/m^3.

    :param water_density: Density of water, 1000 kg/m^3.

    :returns: 
        Scalar or array of the factor of safety.
    """

    soil_weight = 9.81 * soil_dry_density
    water_weight = 9.81 * water_density

    if np.isscalar(slope):
        if slope == 0.0:
            slope = 1e-5
    else:
        slope[slope == 0.0] = 1e-5

    r_fric_ang = np.radians(friction_angle)

    term_1 = cohesion / (soil_weight * slab_thickness * (slope / np.sqrt(1 + slope**2)))
    term_2 = np.tan(r_fric_ang) / slope
    term_3 = (saturation_coeff * water_weight * np.tan(r_fric_ang)) / (soil_weight * slope)

    return term_1 + term_2 - term_3



