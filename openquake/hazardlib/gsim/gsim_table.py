# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.hazardlib.gsim.gsim_table` defines the
:class:`openquake.hazardlib.gsim.gsim_table.GMPETable` for defining GMPEs
in the form of binary tables, and
:class:`openquake.hazardlib.gsim.gsim_table.AmplificationTable` for defining
the corresponding amplification of the IMLs
"""

from __future__ import division
import os
from copy import deepcopy

import h5py

from scipy.interpolate import interp1d
import numpy

from openquake.hazardlib import const
from openquake.hazardlib import imt as imt_module
from openquake.hazardlib.gsim.base import GMPE, RuptureContext, SitesContext
from openquake.baselib.python3compat import round


def hdf_arrays_to_dict(hdfgroup):
    """
    Convert an hdf5 group contains only data sets to a dictionary of
    data sets

    :param hdfgroup:
        Instance of :class:`h5py.Group`
    :returns:
        Dictionary containing each of the datasets within the group arranged
        by name
    """
    return {key: hdfgroup[key][:] for key in hdfgroup}


class AmplificationTable(object):
    """
    Class to apply amplification from the GMPE tables.

    :attr shape:
        Shape of the amplification arrays as a tuple of (Number Distances,
        Number IMTs, Number Magnitudes, Number Amplification Levels)
    :attr periods:
        Spectral periods defined in table
    :attr mean:
        Amplification factors for the mean ground motion
    :attr sigma:
        List of modification factors for the standard deviation of ground
        motion
    :attr magnitudes:
        Magnitude values for the tables
    :attr distances:
        Distance values for the tables
    :attr parameter:
        Parameter to which the amplification applies. Must be an element
        inside the _slots_ defines in the :class:`openquake.hazardlib.
        gsim.base.RuptureContext` or the :class:`openquake.hazardlib.gsim.base.
        SitesContext`
    :attr values:
        Array of values to which each amplification table corresponds
    :attr element:
        Indicates if the amplification corresponds to a rupture attribute or
        a site attribute
    """
    def __init__(self, amplification_group, magnitudes, distances):
        """
        Setup the amplification factors.

        :param amplification_group:
            Amplification model as instance of :class:`h5py.Group`
        :param magnitudes:
            Array of magnitudes
        :param distances:
            Array of distances
        """
        self.shape = None
        self.periods = None
        self.mean = None
        self.sigma = None
        self.magnitudes = magnitudes
        self.distances = distances
        self.parameter = amplification_group.attrs["apply_to"].decode('utf8')
        self.values = numpy.array([float(key) for key in amplification_group])
        self.argidx = numpy.argsort(self.values)
        self.values = self.values[self.argidx]
        if self.parameter in RuptureContext._slots_:
            self.element = "Rupture"
        elif self.parameter in SitesContext._slots_:
            self.element = "Sites"
        else:
            raise ValueError("Amplification parameter %s not recognised!"
                             % self.parameter)
        self._build_data(amplification_group)

    def _build_data(self, amplification_group):
        """
        Creates the numpy array tables from the hdf5 tables
        """
        # Determine shape of the tables
        n_levels = len(amplification_group)
        # Checks the first group in the amplification group and returns the
        # shape of the SA array - implicitly assumes the SA array in all
        # amplification groups is the same shape
        level = next(iter(amplification_group))
        n_d, n_p, n_m = amplification_group[level]["IMLs/SA"].shape
        assert n_d == len(self.distances), (n_d, len(self.distances))
        assert n_m == len(self.magnitudes), (n_m, len(self.magnitudes))
        # Instantiate the arrays with ones
        self.mean = {"SA": numpy.ones([n_d, n_p, n_m, n_levels]),
                     "PGA": numpy.ones([n_d, 1, n_m, n_levels]),
                     "PGV": numpy.ones([n_d, 1, n_m, n_levels])}
        self.sigma = {}
        for stddev_type in [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
                            const.StdDev.INTRA_EVENT]:
            level = next(iter(amplification_group))
            if stddev_type in amplification_group[level]:
                self.sigma[stddev_type] = deepcopy(self.mean)

        for iloc, (level, amp_model) in enumerate(amplification_group.items()):
            if "SA" in amp_model["IMLs"]:
                if iloc == 0:
                    self.periods = amp_model["IMLs/T"][:]
                else:
                    assert numpy.allclose(self.periods, amp_model["IMLs/T"][:])
            for imt in ["SA", "PGA", "PGV"]:
                if imt in amp_model["IMLs"]:
                    self.mean[imt][:, :, :, self.argidx[iloc]] = \
                        amp_model["IMLs/" + imt][:]
                    for stddev_type in self.sigma:
                        self.sigma[stddev_type][imt][
                            :, :, :, self.argidx[iloc]] = \
                            amp_model["/".join([stddev_type, imt])][:]
        self.shape = (n_d, n_p, n_m, n_levels)

    def get_set(self):
        """
        Return the parameter as an instance a Python set
        """
        return {self.parameter}

    def get_amplification_factors(self, imt, sctx, rctx, dists, stddev_types):
        """
        Returns the amplification factors for the given rupture and site
        conditions.

        :param imt:
            Intensity measure type as an instance of the :class:
            `openquake.hazardlib.imt`
        :param sctx:
            Site parameters as instance of the :class:
            `openquake.hazardlib.gsim.base.SitesContext`
        :param rctx:
            Rupture parameters as instance of the :class:
            `openquake.hazardlib.gsim.base.RuptureContext`
        :param dists:
            Source to site distances (km)
        :param stddev_types:
            List of required standard deviation types
        :returns:
            * mean_amp - Amplification factors applied to the median ground
                         motion
            * sigma_amps - List of modification factors applied to the
                         standard deviations of ground motion
        """
        dist_level_table = self.get_mean_table(imt, rctx)
        sigma_tables = self.get_sigma_tables(imt, rctx, stddev_types)
        mean_interpolator = interp1d(self.values,
                                     numpy.log10(dist_level_table),
                                     axis=1)
        sigma_interpolators = [interp1d(self.values, sigma_table, axis=1)
                               for sigma_table in sigma_tables]
        if self.element == "Rupture":
            mean_amp = 10.0 ** mean_interpolator(
                getattr(rctx, self.parameter))[0] * numpy.ones_like(dists)
            sigma_amps = []
            for sig_interpolator in sigma_interpolators:
                sigma_amps.append(sig_interpolator(
                    getattr(rctx, self.parameter))[0] * numpy.ones_like(dists))
        else:
            mean_amp = 10.0 ** mean_interpolator(
                getattr(sctx, self.parameter))[0, :]
            sigma_amps = []
            for sig_interpolator in sigma_interpolators:
                sigma_amps.append(sig_interpolator(
                    getattr(sctx, self.parameter))[0, :] *
                    numpy.ones_like(dists))
        return mean_amp, sigma_amps

    def get_mean_table(self, imt, rctx):
        """
        Returns amplification factors for the mean, given the rupture and
        intensity measure type.

        :returns:
            amplification table as an array of [Number Distances,
            Number Levels]
        """
        # Levels by Distances
        if isinstance(imt, (imt_module.PGA, imt_module.PGV)):
            interpolator = interp1d(self.magnitudes,
                                    numpy.log10(self.mean[str(imt)]), axis=2)
            output_table = 10.0 ** (
                interpolator(rctx.mag).reshape(self.shape[0], self.shape[3])
                )
        else:
            # For spectral accelerations - need two step process
            # Interpolate period - log-log space
            interpolator = interp1d(numpy.log10(self.periods),
                                    numpy.log10(self.mean["SA"]),
                                    axis=1)
            period_table = interpolator(numpy.log10(imt.period))
            # Interpolate magnitude - linear-log space
            mag_interpolator = interp1d(self.magnitudes, period_table, axis=1)
            output_table = 10.0 ** mag_interpolator(rctx.mag)
        return output_table

    def get_sigma_tables(self, imt, rctx, stddev_types):
        """
        Returns modification factors for the standard deviations, given the
        rupture and intensity measure type.

        :returns:
            List of standard deviation modification tables, each as an array
            of [Number Distances, Number Levels]

        """
        output_tables = []
        for stddev_type in stddev_types:
            # For PGA and PGV only needs to apply magnitude interpolation
            if isinstance(imt, (imt_module.PGA, imt_module.PGV)):
                interpolator = interp1d(self.magnitudes,
                                        self.sigma[stddev_type][str(imt)],
                                        axis=2)
                output_tables.append(
                    interpolator(rctx.mag).reshape(self.shape[0],
                                                   self.shape[3]))

            else:
                # For spectral accelerations - need two step process
                # Interpolate period
                interpolator = interp1d(numpy.log10(self.periods),
                                        self.sigma[stddev_type]["SA"],
                                        axis=1)
                period_table = interpolator(numpy.log10(imt.period))
                mag_interpolator = interp1d(self.magnitudes,
                                            period_table,
                                            axis=1)
                output_tables.append(mag_interpolator(rctx.mag))
        return output_tables


class GMPETable(GMPE):
    """
    Implements ground motion prediction equations in the form of a table from
    which the expected ground motion intensity levels and standard deviations
    are interpolated.

    In a GMPE tables the expected ground motions for each of the IMTs over the
    range of magnitudes and distances are stored in an hdf5 file on the path
    specified by the user.

    In this version of the GMPE the expected values are interpolated to the
    required IMT, magnitude and distance in three stages.

    i) Initially the correct IMT values are identified, interpolating in
       log-T|log-IML space between neighbouring spectral periods.

    ii) The IML values are then interpolated to the correct magnitude using
        linear-M|log-IML space

    iii) The IML values are then interpolated to the correct distance via
         linear-D|linear-IML interpolation
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,))

    REQUIRES_SITES_PARAMETERS = set()

    REQUIRES_DISTANCES = set()

    REQUIRES_RUPTURE_PARAMETERS = {"mag"}

    GMPE_TABLE = None
    GMPE_DIR = '.'

    def __init__(self, gmpe_table=None):
        """
        If the path to the GMPE table is not assigned as an attribute of the
        class then instantiate with a path to the GMPE table. If the
        gmpe_table is input this will replace the path to the hdf5 file if it
        has already been assigned. Otherwise, if the path to the hdf5 file
        is not assigned as a property or the class nor is it input at
        instantiation, an error will be raised

        :param str gmpe_table:
            Path to the hdf5 file containing the GMPE table
        """
        if not self.GMPE_TABLE:
            if gmpe_table:
                if os.path.isabs(gmpe_table):
                    self.GMPE_TABLE = gmpe_table
                else:
                    self.GMPE_TABLE = os.path.abspath(
                        os.path.join(self.GMPE_DIR, gmpe_table))
                if not os.path.exists(self.GMPE_TABLE):
                    raise IOError('Missing file %r' % self.GMPE_TABLE)
            else:
                raise IOError("GMPE Table Not Defined!")
        super(GMPETable, self).__init__()
        self.imls = None
        self.stddevs = {}
        self.m_w = None
        self.distances = None
        self.distance_type = None
        self.amplification = None
        self._run_setup()

    def _run_setup(self):
        """
        Executes the preprocessing steps at the instantiation stage to read in
        the tables from hdf5 and hold them in memory.
        """
        fle = h5py.File(self.GMPE_TABLE, "r")
        self.distance_type = fle["Distances"].attrs["metric"].decode('utf8')
        self.REQUIRES_DISTANCES = set([self.distance_type])
        # Load in magnitude
        self.m_w = fle["Mw"][:]
        # Load in distances
        self.distances = fle["Distances"][:]
        # Load intensity measure types and levels
        self.imls = hdf_arrays_to_dict(fle["IMLs"])
        self.DEFINED_FOR_INTENSITY_MEASURE_TYPES = set(self._supported_imts())
        if "SA" in self.imls.keys() and "T" not in self.imls:
            raise ValueError("Spectral Acceleration must be accompanied by "
                             "periods")
        # Get the standard deviations
        self._setup_standard_deviations(fle)
        if "Amplification" in fle:
            self._setup_amplification(fle)
        fle.close()

    def _setup_standard_deviations(self, fle):
        """
        Reads the standard deviation tables from hdf5 and stores them in
        memory
        :param fle:
            HDF5 Tables as instance of :class:`h5py.File`
        """
        # Load in total standard deviation
        self.stddevs[const.StdDev.TOTAL] = hdf_arrays_to_dict(fle["Total"])
        # If other standard deviations
        for stddev_type in [const.StdDev.INTER_EVENT,
                            const.StdDev.INTRA_EVENT]:
            if stddev_type in fle:
                self.stddevs[stddev_type] = hdf_arrays_to_dict(
                    fle[stddev_type])
                self.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(stddev_type)

    def _setup_amplification(self, fle):
        """
        If amplification data is specified then reads into memory and updates
        the required rupture and site parameters
        """
        self.amplification = AmplificationTable(fle["Amplification"],
                                                self.m_w,
                                                self.distances)
        if self.amplification.element == "Sites":
            self.REQUIRES_SITES_PARAMETERS = set(
                [self.amplification.parameter])
        elif self.amplification.element == "Rupture":
            # Re-set the site parameters
            self.REQUIRES_SITES_PARAMETERS = set()
            self.REQUIRES_RUPTURE_PARAMETERS.add(
                self.amplification.parameter)

    def _supported_imts(self):
        """
        Updates the list of supported IMTs from the tables
        """
        imt_list = []
        for key in self.imls:
            if "SA" in key:
                imt_list.append(imt_module.SA)
            elif key == "T":
                continue
            else:
                try:
                    imt_val = imt_module.from_string(key)
                except:
                    continue
                imt_list.append(imt_val.__class__)
        return imt_list

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        # Return Distance Tables
        imls = self._return_tables(rctx.mag, imt, "IMLs")
        # Get distance vector for the given magnitude
        idx = numpy.searchsorted(self.m_w, rctx.mag)
        dists = self.distances[:, 0, idx - 1]
        # Get mean and standard deviations
        mean = self._get_mean(imls, dctx, dists)
        stddevs = self._get_stddevs(dists, rctx.mag, dctx, imt, stddev_types)
        if self.amplification:
            # Apply amplification
            mean_amp, sigma_amp = self.amplification.get_amplification_factors(
                imt,
                sctx,
                rctx,
                getattr(dctx, self.distance_type),
                stddev_types)
            mean = numpy.log(mean) + numpy.log(mean_amp)
            for iloc in range(len(stddev_types)):
                stddevs[iloc] *= sigma_amp[iloc]
            return mean, stddevs
        else:
            return numpy.log(mean), stddevs

    def _get_mean(self, data, dctx, dists):
        """
        Returns the mean intensity measure level from the tables
        :param data:
            The intensity measure level vector for the given magnitude and IMT
        :param key:
            The distance type
        :param distances:
            The distance vector for the given magnitude and IMT
        """
        # For values outside of the interpolation range use -999. to ensure
        # value is identifiable and outside of potential real values
        interpolator_mean = interp1d(dists, data,
                                     bounds_error=False,
                                     fill_value=-999.)
        mean = interpolator_mean(getattr(dctx, self.distance_type))
        # For those distances less than or equal to the shortest distance
        # extrapolate the shortest distance value
        mean[getattr(dctx, self.distance_type) < (dists[0] + 1.0E-3)] = data[0]
        # For those distances significantly greater than the furthest distance
        # set to 1E-20.
        mean[getattr(dctx, self.distance_type) > (dists[-1] + 1.0E-3)] = 1E-20
        # If any distance is between the final distance and a margin of 0.001
        # km then assign to smallest distance
        mean[mean < -1.] = data[-1]
        return mean

    def _get_stddevs(self, dists, mag, dctx, imt, stddev_types):
        """
        Returns the total standard deviation of the intensity measure level
        from the tables.

        :param fle:
            HDF5 data stream as instance of :class:`h5py.File`
        :param distances:
            The distance vector for the given magnitude and IMT
        :param key:
            The distance type
        :param mag:
            The rupture magnitude
        """
        stddevs = []
        for stddev_type in stddev_types:
            if stddev_type not in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES:
                raise ValueError("Standard Deviation type %s not supported"
                                 % stddev_type)
            sigma = self._return_tables(mag, imt, stddev_type)
            interpolator_std = interp1d(dists, sigma,
                                        bounds_error=False)
            stddev = interpolator_std(getattr(dctx, self.distance_type))
            stddev[getattr(dctx, self.distance_type) < dists[0]] = sigma[0]
            stddev[getattr(dctx, self.distance_type) > dists[-1]] = sigma[-1]
            stddevs.append(stddev)
        return stddevs

    def _return_tables(self, mag, imt, val_type):
        """
        Returns the vector of ground motions or standard deviations
        corresponding to the specific magnitude and intensity measure type.

        :param val_type:
            String indicating the type of data {"IMLs", "Total", "Inter" etc}
        """
        if isinstance(imt, (imt_module.PGA, imt_module.PGV)):
            # Get scalar imt
            if val_type == "IMLs":
                iml_table = self.imls[str(imt)][:]
            else:
                iml_table = self.stddevs[val_type][str(imt)][:]
            n_d, n_s, n_m = iml_table.shape
            iml_table = iml_table.reshape([n_d, n_m])
        else:
            if val_type == "IMLs":
                periods = self.imls["T"][:]
                iml_table = self.imls["SA"][:]
            else:
                periods = self.stddevs[val_type]["T"][:]
                iml_table = self.stddevs[val_type]["SA"][:]

            low_period = round(periods[0], 7)
            high_period = round(periods[-1], 7)

            if imt.period < low_period or imt.period > high_period:
                raise ValueError("Spectral period %.3f outside of valid range "
                                 "(%.3f to %.3f)" % (imt.period, periods[0],
                                                     periods[-1]))
            # Apply log-log interpolation for spectral period
            interpolator = interp1d(numpy.log10(periods),
                                    numpy.log10(iml_table),
                                    axis=1)
            iml_table = 10. ** interpolator(numpy.log10(imt.period))
        return self.apply_magnitude_interpolation(mag, iml_table)

    def apply_magnitude_interpolation(self, mag, iml_table):
        """
        Interpolates the tables to the required magnitude level

        :param float mag:
            Magnitude
        :param iml_table:
            Intensity measure level table
        """
        # do not allow "mag" to exceed maximum table magnitude
        if mag > self.m_w[-1]:
            mag = self.m_w[-1]

        # Get magnitude values
        if mag < self.m_w[0] or mag > self.m_w[-1]:
            raise ValueError("Magnitude %.2f outside of supported range "
                             "(%.2f to %.2f)" % (mag,
                                                 self.m_w[0],
                                                 self.m_w[-1]))
        # It is assumed that log10 of the spectral acceleration scales
        # linearly (or approximately linearly) with magnitude
        m_interpolator = interp1d(self.m_w, numpy.log10(iml_table), axis=1)
        return 10.0 ** m_interpolator(mag)
