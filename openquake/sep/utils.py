from typing import Callable, Union

import os
import tempfile
import logging
import numpy as np
import pandas as pd
import pyproj as pj
from osgeo import gdal
from numpy.lib.stride_tricks import as_strided


# Set PROJ_DATA (proj == 9.0.1) to dir containing proj.db to avoid:
# 'ERROR 1: PROJ: proj_create_from_name: Cannot find proj.db'
if "PROJ_DATA" not in os.environ:
    os.environ["PROJ_DATA"] = pj.datadir.get_data_dir()


def sample_raster_at_points(
    raster_file: str,
    lon_pts: np.ndarray,
    lat_pts: np.ndarray,
    out_of_bounds_val: float = 0.0,
):
    """
    Gets the values of a raster at each (lon,lat) point specified.
    This is done using a nearest-neighbor approach; no interpolation is
    performed.

    :param raster_file:
        A filename (and path) of a raster value to be opened by GDAL.

    :param lon_pts:
        Longitudes of points

    :param lat_pts:
        Latitudes of points

    :param out_of_bounds_val:
        Value to be returned if the points fall outside of the raster's extent.
        Defaults to 0.0

    :returns:
        Numpy array of raster values sampled at points.
    """

    if isinstance(lon_pts, pd.Series):
        lon_pts = lon_pts.values
    if isinstance(lat_pts, pd.Series):
        lat_pts = lat_pts.values

    raster_ds = gdal.Open(raster_file)
    gt = raster_ds.GetGeoTransform()
    raster_proj_wkt = raster_ds.GetProjection()
    raster_data = raster_ds.GetRasterBand(1).ReadAsArray()

    raster_proj = pj.CRS(raster_proj_wkt)
    if raster_proj.to_epsg() != 4326:
        trans = pj.transformer.Transformer.from_crs("epsg:4326", raster_proj)
        lat_pts, lon_pts = trans.transform(lat_pts, lon_pts)

    x_rast = np.int_(np.round((lon_pts - gt[0]) / gt[1]))
    y_rast = np.int_(np.round((lat_pts - gt[3]) / gt[5]))

    N, M = raster_data.shape
    interp_vals = []
    for i, col in enumerate(x_rast):
        row = y_rast[i]
        interp_vals.append(
            raster_data[row, col] if 0 <= row < N and 0 <= col < M
            else out_of_bounds_val)

    return np.array(interp_vals)


def make_2d_array_strides(arr, window_radius, linear=True):
    """
    Creates an array of strides representing indices for windows/sub-arrays
    over a larger array, for rapid calculations of rolling window functions.

    :param arr:
        Array of values to be used in the calculations.

    :param window_radius:
        Radius of the window (not counting the origin) in array count units.

    :param linear:
        Flag specifying the shape of the stride collection.

    :returns:
        Array of strides

    Slightly modified from https://gist.github.com/thengineer/10024511
    """

    if np.isscalar(window_radius):
        window_radius = (window_radius, window_radius)

    ax = np.zeros(
        shape=(
            arr.shape[0] + 2 * window_radius[0],
            arr.shape[1] + 2 * window_radius[1],
        )
    )
    ax[:] = np.nan
    ax[
        window_radius[0] : ax.shape[0] - window_radius[0],
        window_radius[1] : ax.shape[1] - window_radius[1],
    ] = arr

    shape = arr.shape + (1 + 2 * window_radius[0], 1 + 2 * window_radius[1])
    strides = ax.strides + ax.strides
    s = as_strided(ax, shape=shape, strides=strides)

    return s.reshape(arr.shape + (shape[2] * shape[3],)) if linear else s


def rolling_array_operation(
    array: np.ndarray, func: Callable, window_size: int, trim: bool = False
) -> np.ndarray:
    """
    Rolls a function that operates on a square subarray over the array. The
    values in the resulting array will be at the center of each subarray.

    :param array:
        Array of values that the window function will be passed over.

    :param func:
        Function to be applied to each subarray. Should operate on an array and
        return a scalar.

    :param window_size:
        Dimension of the (square) sub-array or window in array counts, not in
        spatial (or other dimensional) units. Should be an odd
        integer, so that the result of the function can be unambiguously applied
        to the center of the window.

    :param trim:
        Boolean flag to trim off the borders of the resulting array, from where
        the window overhangs the array.
    """
    if window_size % 2 != 1:
        raise ValueError(
            "window_size should be an odd integer; {} passed".format(
                window_size
            )
        )

    window_rad = window_size // 2

    strides = make_2d_array_strides(array, window_rad)
    strides = np.ma.masked_array(strides, mask=np.isnan(strides))

    result = func(strides, axis=-1).data

    if trim:
        result = result[window_rad:-window_rad, window_rad:-window_rad]

    return result


def rolling_raster_operation(
    in_raster,
    func: Callable,
    window_size: int,
    outfile=None,
    raster_band: int = 1,
    trim: bool = False,
    write: bool = False,
):
    if trim:
        return NotImplementedError("Trimming not supported at this time.")

    if outfile is None:
        if write:
            raise ValueError("Must specify raster outfile")
        else:
            _outfile_handler, outfile = tempfile.mkstemp(suffix=".tiff")

    ds = gdal.Open(in_raster)

    rast = ds.GetRasterBand(raster_band).ReadAsArray()
    rast = np.asarray(rast)

    new_arr = rolling_array_operation(rast, func, window_size, trim=trim)

    drv = gdal.GetDriverByName("GTiff")

    logging.info(f"Writing {outfile}")
    new_ds = drv.Create(
        outfile,
        xsize=new_arr.shape[1],
        ysize=new_arr.shape[0],
        bands=1,
        eType=gdal.GDT_Float32,
    )

    new_ds.SetGeoTransform(ds.GetGeoTransform())
    new_ds.SetProjection(ds.GetProjection())
    new_ds.GetRasterBand(1).WriteArray(new_arr)

    if write:
        new_ds.FlushCache()
        new_ds = None

    return new_ds


def relief(arr, axis=-1):
    return np.amax(arr, axis=axis) - np.amin(arr, axis=axis)


def make_local_relief_raster(
    input_dem, window_size, outfile=None, write=False, trim=False
):
    relief_arr = rolling_raster_operation(
        input_dem, relief, window_size, outfile, write=write, trim=trim
    )

    return relief_arr


def slope_angle_to_gradient(slope, unit: str = "deg"):
    if unit in ["radians", "radian", "rad"]:
        slope_r = slope
    elif unit in ["degrees", "deg", "degree"]:
        slope_r = np.radians(slope)
    else:
        raise ValueError('Slope units need to be "radians" or "degrees"')

    return np.tan(slope_r)


def vs30_from_slope(
    slope: Union[float, np.array],
    slope_unit: str = "deg",
    tectonic_region_type: str = "active",
    method: str = "wald_allen_2007",
) -> Union[float, np.array]:
    """ """
    if slope_unit in ["grad", "gradient"]:
        grad = slope
    else:
        grad = slope_angle_to_gradient(slope, unit=slope_unit)

    if method == "wald_allen_2007":
        vs30 = vs30_from_slope_wald_allen_2007(
            grad, tectonic_region_type=tectonic_region_type
        )
    else:
        raise NotImplementedError(f"{method} not yet implemented.")
    return vs30


def vs30_from_slope_wald_allen_2007(
    gradient: Union[float, np.array], tectonic_region_type: str = "active"
) -> Union[float, np.array]:
    """
    Calculates Vs30 from the topographic slope (given as a gradient) using
    the methods of Wald and Allen, 2007 BSSA.

    Either 'active' or 'stable' are valid for the `tectonic_region_type`
    argument.
    """
    if np.isscalar(gradient):
        grad = np.array([gradient])
        if tectonic_region_type == "active":
            vs30 = vs30_from_slope_wald_allen_2007_active(grad)
        elif tectonic_region_type == "stable":
            vs30 = vs30_from_slope_wald_allen_2007_stable(grad)
        else:
            raise ValueError(
                f"'{tectonic_region_type}' must be 'active' or 'stable'"
            )
        vs30 = vs30[0]
    else:
        if tectonic_region_type == "active":
            vs30 = vs30_from_slope_wald_allen_2007_active(gradient)
        elif tectonic_region_type == "stable":
            vs30 = vs30_from_slope_wald_allen_2007_stable(gradient)
        else:
            raise ValueError(
                f"'{tectonic_region_type}' must be 'active' or 'stable'"
            )
    return vs30


def vs30_from_slope_wald_allen_2007_active(gradient: np.array) -> np.ndarray:
    vs30 = np.zeros(gradient.shape)
    vs30[(gradient < 1.0e-4)] = np.mean([0.0, 180.0])
    vs30[(1.0e-4 <= gradient) & (gradient < 2.2e-3)] = np.mean([180.0, 240.0])
    vs30[(2.2e-3 <= gradient) & (gradient < 6.3e-3)] = np.mean([240.0, 300.0])
    vs30[(6.3e-3 <= gradient) & (gradient < 0.0180)] = np.mean([300.0, 360.0])
    vs30[(0.0180 <= gradient) & (gradient < 0.0500)] = np.mean([360.0, 490.0])
    vs30[(0.0500 <= gradient) & (gradient < 0.1000)] = np.mean([490.0, 620.0])
    vs30[(0.1000 <= gradient) & (gradient < 0.1380)] = np.mean([620.0, 760.0])
    vs30[(0.1380 <= gradient)] = 760.0

    return vs30


def vs30_from_slope_wald_allen_2007_stable(gradient: np.array) -> np.ndarray:
    vs30 = np.zeros(gradient.shape)
    vs30[(gradient < 2.0e-5)] = np.mean([0.0, 180.0])
    vs30[(2.0e-5 <= gradient) & (gradient < 2.0e-3)] = np.mean([180.0, 240.0])
    vs30[(2.0e-3 <= gradient) & (gradient < 4.0e-3)] = np.mean([240.0, 300.0])
    vs30[(4.0e-3 <= gradient) & (gradient < 7.2e-3)] = np.mean([300.0, 360.0])
    vs30[(7.2e-3 <= gradient) & (gradient < 0.0130)] = np.mean([360.0, 490.0])
    vs30[(0.0130 <= gradient) & (gradient < 0.0180)] = np.mean([490.0, 620.0])
    vs30[(0.0180 <= gradient) & (gradient < 0.0250)] = np.mean([620.0, 760.0])
    vs30[(0.0250 <= gradient)] = 760.0

    return vs30
