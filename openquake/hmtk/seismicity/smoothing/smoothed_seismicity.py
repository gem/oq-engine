# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module :mod: openquake.hmtk.seismicity.smoothing.smoothed_seismicity implements the
:class: openquake.hmtk.seismicity.smoothing.smoothed_seismicity.SmoothedSeismicity,
a general class for implementing seismicity smoothing algorithms
"""
import csv

from math import fabs, log
import numpy as np
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hmtk.seismicity.smoothing import utils
from openquake.hmtk.seismicity.smoothing.kernels.isotropic_gaussian import (
    IsotropicGaussian,
)
from openquake.hmtk.registry import CatalogueFunctionRegistry


class Grid(dict):
    @classmethod
    def make_from_list(cls, grid_limits):
        new = cls()
        new.update(
            {
                "xmin": grid_limits[0],
                "xmax": grid_limits[1],
                "xspc": grid_limits[2],
                "ymin": grid_limits[3],
                "ymax": grid_limits[4],
                "yspc": grid_limits[5],
                "zmin": grid_limits[6],
                "zmax": grid_limits[7],
                "zspc": grid_limits[8],
            }
        )
        return new

    @classmethod
    def make_from_catalogue(cls, catalogue, spacing, dilate):
        """
        Defines the grid on the basis of the catalogue
        """
        new = cls()
        cat_bbox = get_catalogue_bounding_polygon(catalogue)

        if dilate > 0:
            cat_bbox = cat_bbox.dilate(dilate)

        # Define Grid spacing
        new.update(
            {
                "xmin": np.min(cat_bbox.lons),
                "xmax": np.max(cat_bbox.lons),
                "xspc": spacing,
                "ymin": np.min(cat_bbox.lats),
                "ymax": np.max(cat_bbox.lats),
                "yspc": spacing,
                "zmin": 0.0,
                "zmax": np.max(catalogue.data["depth"]),
                "zspc": np.max(catalogue.data["depth"]),
            }
        )

        if new["zmin"] == new["zmax"] == new["zspc"] == 0:
            new["zmax"] = new["zspc"] = 1

        return new

    def as_list(self):
        return [
            self["xmin"],
            self["xmax"],
            self["xspc"],
            self["ymin"],
            self["ymax"],
            self["yspc"],
            self["zmin"],
            self["zmax"],
            self["zspc"],
        ]

    def as_polygon(self):
        return Polygon(
            [
                Point(self["xmin"], self["ymax"]),
                Point(self["xmax"], self["ymax"]),
                Point(self["xmax"], self["ymin"]),
                Point(self["xmin"], self["ymin"]),
            ]
        )

    def dilate(self, width):
        polygon = self.as_polygon().dilate(width)

        self.update(
            {
                "xmin": np.min(polygon.lons),
                "xmax": np.max(polygon.lons),
                "ymin": np.min(polygon.lats),
                "ymax": np.max(polygon.lats),
            }
        )
        return self


def _get_adjustment(mag, year, mmin, completeness_year, t_f, mag_inc=0.1):
    """
    If the magnitude is greater than the minimum in the completeness table
    and the year is greater than the corresponding completeness year then
    return the Weichert factor

    :param float mag:
        Magnitude of an earthquake

    :param float year:
        Year of earthquake

    :param np.ndarray completeness_table:
        Completeness table

    :param float mag_inc:
        Magnitude increment

    :param float t_f:
        Weichert adjustment factor

    :returns:
        Weichert adjustment factor is event is in complete part of catalogue
        (0.0 otherwise)
    """
    if len(completeness_year) == 1:
        if (mag >= mmin) and (year >= completeness_year[0]):
            # No adjustment needed - event weight == 1
            return 1.0
        else:
            # Event should not be counted
            return False

    kval = int(((mag - mmin) / mag_inc)) + 1

    if (kval >= 1) and (year >= completeness_year[kval - 1]):
        return t_f
    else:
        return False


def get_catalogue_bounding_polygon(catalogue):
    """
    Returns a polygon containing the bounding box of the catalogue
    """
    upper_lon = np.max(catalogue.data["longitude"])
    upper_lat = np.max(catalogue.data["latitude"])
    lower_lon = np.min(catalogue.data["longitude"])
    lower_lat = np.min(catalogue.data["latitude"])

    return Polygon(
        [
            Point(lower_lon, upper_lat),
            Point(upper_lon, upper_lat),
            Point(upper_lon, lower_lat),
            Point(lower_lon, lower_lat),
        ]
    )


class SmoothedSeismicity(object):
    """
    Class to implement an analysis of Smoothed Seismicity, including the
    grid counting of data and the smoothing.

    :param np.ndarray grid:
        Observed count in each cell [Long., Lat., Depth., Count]

    :param catalogue:
        Valid instance of the :class: openquake.hmtk.seismicity.catalogue.Catalogue

    :param bool use_3d:
        Decide if analysis is 2-D (False) or 3-D (True). If 3-D then distances
        will use hypocentral distance, otherwise epicentral distance

    :param float bval:
        b-value

    :param float beta:
        Beta value for exponential form (beta = bval * log(10.))

    :param np.ndarray data:
        Smoothed seismicity output

    :param dict grid_limits:
        Limits ot the grid used for defining the cells
    """

    def __init__(self, grid_limits, use_3d=False, bvalue=None):
        """
        Instatiate class with a set of grid limits

        :param grid_limits:
            It could be a float (in that case the grid is computed from the
            catalogue with the given spacing).

            Or an array of the form:
            [xmin, xmax, spcx, ymin, ymax, spcy, zmin, spcz]

        :param bool use_3d:
            Choose whether to use hypocentral distances for smoothing or only
            epicentral

        :param float bval:
            b-value for analysis
        """
        self.grid = None
        self.catalogue = None
        self.use_3d = use_3d
        self.bval = bvalue
        if self.bval:
            self.beta = self.bval * log(10.0)
        else:
            self.beta = None
        self.data = None

        self.grid_limits = grid_limits
        self.kernel = None

    def run_analysis(
        self, catalogue, config, completeness_table=None, smoothing_kernel=None
    ):
        """
        Runs an analysis of smoothed seismicity in the manner
        originally implemented by Frankel (1995)

        :param catalogue:
            Instance of the openquake.hmtk.seismicity.catalogue.Catalogue class
            catalogue.data dictionary containing the following -
            'year' - numpy.ndarray vector of years
            'longitude' - numpy.ndarray vector of longitudes
            'latitude' - numpy.ndarray vector of latitudes
            'depth' - numpy.ndarray vector of depths

        :param dict config:
            Configuration settings of the algorithm:
            * 'Length_Limit' - Maximum number of bandwidths for use in
            smoothing (Float)
            * 'BandWidth' - Bandwidth (km) of the Smoothing Kernel (Float)
            * 'increment' - Output incremental (True) or cumulative a-value
            (False)

        :param np.ndarray completeness_table:
            Completeness of the catalogue assuming evenly spaced magnitudes
            from most recent bin to oldest bin [year, magnitude]

        :param smoothing_kernel:
            Smoothing kernel as instance of :class:
            `openquake.hmtk.seismicity.smoothing.kernels.base.BaseSmoothingKernel`

        :returns:
            Full smoothed seismicity data as np.ndarray, of the form
            [Longitude, Latitude, Depth, Observed, Smoothed]
        """

        self.catalogue = catalogue
        if smoothing_kernel:
            self.kernel = smoothing_kernel
        else:
            self.kernel = IsotropicGaussian()

        # If no grid limits are specified then take from catalogue
        if isinstance(self.grid_limits, list):
            self.grid_limits = Grid.make_from_list(self.grid_limits)
            assert self.grid_limits["xmax"] >= self.grid_limits["xmin"]
            assert self.grid_limits["xspc"] > 0.0
            assert self.grid_limits["ymax"] >= self.grid_limits["ymin"]
            assert self.grid_limits["yspc"] > 0.0
        elif isinstance(self.grid_limits, float):
            self.grid_limits = Grid.make_from_catalogue(
                self.catalogue,
                self.grid_limits,
                config["Length_Limit"] * config["BandWidth"],
            )

        completeness_table, mag_inc = utils.get_even_magnitude_completeness(
            completeness_table, self.catalogue
        )

        end_year = self.catalogue.end_year

        # Get Weichert factor
        t_f, _ = utils.get_weichert_factor(
            self.beta,
            completeness_table[:, 1],
            completeness_table[:, 0],
            end_year,
        )
        # Get the grid
        self.create_3D_grid(self.catalogue, completeness_table, t_f, mag_inc)
        if config["increment"]:
            # Get Hermann adjustment factors
            fval, fival = utils.hermann_adjustment_factors(
                self.bval, completeness_table[0, 1], config["increment"]
            )
            self.data[:, -1] = fval * fival * self.data[:, -1]

        # Apply smoothing
        smoothed_data, sum_data, sum_smooth = self.kernel.smooth_data(
            self.data, config, self.use_3d
        )
        print(
            "Smoothing Total Rate Comparison - "
            "Observed: %.6g, Smoothed: %.6g" % (sum_data, sum_smooth)
        )
        self.data = np.column_stack([self.data, smoothed_data])
        return self.data

    def create_2D_grid_simple(
        self,
        longitude,
        latitude,
        year,
        magnitude,
        completeness_table,
        t_f=1.0,
        mag_inc=0.1,
    ):
        """
        Generates the grid from the limits using an approach closer to that of
        Frankel (1995)

        :param numpy.ndarray longitude:
            Vector of earthquake longitudes

        :param numpy.ndarray latitude:
            Vector of earthquake latitudes

        :param numpy.ndarray year:
            Vector of earthquake years

        :param numpy.ndarray magnitude:
            Vector of earthquake magnitudes

        :param numpy.ndarray completeness_table:
            Completeness table

        :param float t_f:
            Weichert adjustment factor

        :returns:
           Two-dimensional spatial grid of observed rates

        """
        assert mag_inc > 0.0

        xlim = np.ceil(
            (self.grid_limits["xmax"] - self.grid_limits["xmin"])
            / self.grid_limits["xspc"]
        )
        ylim = np.ceil(
            (self.grid_limits["ymax"] - self.grid_limits["ymin"])
            / self.grid_limits["yspc"]
        )
        ncolx = int(xlim)
        ncoly = int(ylim)
        grid_count = np.zeros(ncolx * ncoly, dtype=float)
        for iloc in range(0, len(longitude)):
            dlon = (
                longitude[iloc] - self.grid_limits["xmin"]
            ) / self.grid_limits["xspc"]
            if (dlon < 0.0) or (dlon > xlim):
                # Earthquake outside longitude limits
                continue
            xcol = int(dlon)
            if xcol == ncolx:
                # If longitude is directly on upper grid line then retain
                xcol = ncolx - 1
            dlat = (
                fabs(self.grid_limits["ymax"] - latitude[iloc])
                / self.grid_limits["yspc"]
            )
            if (dlat < 0.0) or (dlat > ylim):
                # Earthquake outside latitude limits
                continue
            ycol = int(dlat)  # Correct for floating precision
            if ycol == ncoly:
                # If latitude is directly on upper grid line then retain
                ycol = ncoly - 1
            kmarker = (ycol * int(xlim)) + xcol
            adjust = _get_adjustment(
                magnitude[iloc],
                year[iloc],
                completeness_table[0, 1],
                completeness_table[:, 0],
                t_f,
                mag_inc,
            )
            if adjust:
                grid_count[kmarker] = grid_count[kmarker] + adjust
        return grid_count

    def _xyz(self):
        x_bins = np.arange(
            self.grid_limits["xmin"],
            self.grid_limits["xmax"],
            self.grid_limits["xspc"],
        )
        if x_bins[-1] < self.grid_limits["xmax"]:
            x_bins = np.hstack([x_bins, x_bins[-1] + self.grid_limits["xspc"]])

        y_bins = np.arange(
            self.grid_limits["ymin"],
            self.grid_limits["ymax"],
            self.grid_limits["yspc"],
        )
        if y_bins[-1] < self.grid_limits["ymax"]:
            y_bins = np.hstack([y_bins, y_bins[-1] + self.grid_limits["yspc"]])

        z_bins = np.arange(
            self.grid_limits["zmin"],
            self.grid_limits["zmax"] + self.grid_limits["zspc"],
            self.grid_limits["zspc"],
        )

        if z_bins[-1] < self.grid_limits["zmax"]:
            z_bins = np.hstack([z_bins, z_bins[-1] + self.grid_limits["zspc"]])

        # Define centre points of grid cells
        grid_x, grid_y = np.meshgrid(
            (x_bins[1:] + x_bins[:-1]) / 2.0, (y_bins[1:] + y_bins[:-1]) / 2.0
        )
        return grid_x, grid_y, z_bins

    def create_3D_grid(self, catalogue, completeness_table,
                       t_f=1.0, mag_inc=0.1):
        """
        Counts the earthquakes observed in a three dimensional grid


        :param catalogue:
            Instance of the openquake.hmtk.seismicity.catalogue.Catalogue class
            catalogue.data dictionary containing the following -
            'year' - numpy.ndarray vector of years
            'longitude' - numpy.ndarray vector of longitudes
            'latitude' - numpy.ndarray vector of latitudes
            'depth' - numpy.ndarray vector of depths

        :param np.ndarray completeness_table:
            Completeness of the catalogue assuming evenly spaced magnitudes
            from most recent bin to oldest bin [year, magnitude]

        :param float t_f:
            Weichert adjustment factor

        :param float mag_inc:
            Increment of the completeness magnitude (rendered 0.1)

        :returns:
           Three-dimensional spatial grid of observed rates (or two dimensional
           if only one depth layer is considered)

        """
        gridx, gridy, z_bins = self._xyz()
        n_x, n_y = np.shape(gridx)
        gridx = np.reshape(gridx, [n_x * n_y, 1])
        gridy = np.reshape(np.flipud(gridy), [n_x * n_y, 1])

        # Only one depth range
        idx = np.logical_and(
            catalogue.data["depth"] >= z_bins[0],
            catalogue.data["depth"] < z_bins[1],
        )
        mid_depth = (z_bins[0] + z_bins[1]) / 2.0

        data_grid = np.column_stack(
            [
                gridx,
                gridy,
                mid_depth * np.ones(n_x * n_y, dtype=float),
                self.create_2D_grid_simple(
                    catalogue.data["longitude"][idx],
                    catalogue.data["latitude"][idx],
                    catalogue.data["year"][idx],
                    catalogue.data["magnitude"][idx],
                    completeness_table,
                    t_f,
                    mag_inc,
                ),
            ]
        )

        if len(z_bins) < 3:
            # Only one depth range
            self.data = data_grid
            return

        # Multiple depth layers - append to grid
        for iloc in range(1, len(z_bins) - 1):
            idx = np.logical_and(
                catalogue.data["depth"] >= z_bins[iloc],
                catalogue.data["depth"] < z_bins[iloc + 1],
            )
            mid_depth = (z_bins[iloc] + z_bins[iloc + 1]) / 2.0

            temp_grid = np.column_stack(
                [
                    gridx,
                    gridy,
                    mid_depth * np.ones(n_x * n_y, dtype=float),
                    self.create_2D_grid_simple(
                        catalogue.data["longitude"][idx],
                        catalogue.data["latitude"][idx],
                        catalogue.data["year"][idx],
                        catalogue.data["magnitude"][idx],
                        completeness_table,
                        t_f,
                        mag_inc,
                    ),
                ]
            )

            data_grid = np.vstack([data_grid, temp_grid])
        self.data = data_grid

    def write_to_csv(self, filename):
        """
        Exports to simple csv

        :param str filename:
            Path to file for export
        """
        fid = open(filename, "wt")
        # Create header list
        header_info = [
            "Longitude",
            "Latitude",
            "Depth",
            "Observed Count",
            "Smoothed Rate",
            "b-value",
        ]
        writer = csv.DictWriter(fid, fieldnames=header_info)
        headers = dict((name0, name0) for name0 in header_info)
        # Write to file
        writer.writerow(headers)
        for row in self.data:
            # institute crude compression by omitting points with no seismicity
            # and taking advantage of the %g format
            if row[4] == 0:
                continue
            row_dict = {
                "Longitude": "%g" % row[0],
                "Latitude": "%g" % row[1],
                "Depth": "%g" % row[2],
                "Observed Count": "%d" % row[3],
                "Smoothed Rate": "%.6g" % row[4],
                "b-value": "%g" % self.bval,
            }
            writer.writerow(row_dict)
        fid.close()


SMOOTHED_SEISMICITY_METHODS = CatalogueFunctionRegistry()


@SMOOTHED_SEISMICITY_METHODS.add(
    "run",
    completeness=True,
    b_value=float,
    use_3d=bool,
    grid_limits=Grid,
    Length_Limit=float,
    BandWidth=float,
    increment=bool,
)
class IsotropicGaussianMethod(object):
    def run(self, catalogue, config, completeness=None):
        ss = SmoothedSeismicity(
            config["grid_limits"], config["use_3d"], config["b_value"]
        )
        return ss.run_analysis(
            catalogue, config, completeness_table=completeness
        )
