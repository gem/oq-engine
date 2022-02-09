# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2022 GEM Foundation
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
Module :mod:`openquake.hazardlib.gsim.gmpe_table` defines the
:class:`openquake.hazardlib.gsim.gmpe_table.GMPETable` for defining GMPEs
in the form of binary tables, and
:class:`openquake.hazardlib.gsim.gmpe_table.AmplificationTable` for defining
the corresponding amplification of the IMLs
"""
from copy import deepcopy

import h5py
from scipy.interpolate import interp1d
import numpy

from openquake.baselib.general import CallableDict
from openquake.baselib.python3compat import decode
from openquake.hazardlib.const import TRT, StdDev
from openquake.hazardlib import site
from openquake.hazardlib import imt as imt_module
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.gsim.base import GMPE
from openquake.baselib.python3compat import round


_get_mean = CallableDict()


@_get_mean.add("base", "nga_east")
def _get_mean_(kind, data, dists, table_dists):
    """
    :param kind:
        The string "base" or "nga_east"
    :param data:
        The intensity measure level table for the given magnitude and IMT
    :param dists:
        The distances for the given magnitude and IMT
    :param table_dists:
        The distance table for the given magnitude and IMT
    :return:
        The mean intensity measure level from the tables.
    """
    # For values outside of the interpolation range use -999. to ensure
    # value is identifiable and outside of potential real values
    interpolator_mean = interp1d(
        table_dists, data, bounds_error=False, fill_value=-999.)
    mean = interpolator_mean(dists)
    # For those distances less than or equal to the shortest distance
    # extrapolate the shortest distance value
    mean[dists < (table_dists[0] + 1.0E-3)] = data[0]
    # For those distances significantly greater than the furthest distance
    # set to 1E-20.
    mean[dists > (table_dists[-1] + 1.0E-3)] = 1E-20
    # If any distance is between the final distance and a margin of 0.001
    # km then assign to smallest distance
    mean[mean < -1.] = data[-1]
    return mean


def todict(hdfgroup):
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
        Parameter to which the amplification applies. There is a check
        on the parameter name.
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
        self.parameter = decode(amplification_group.attrs["apply_to"])
        self.values = numpy.array([float(key) for key in amplification_group])
        self.argrp_id = numpy.argsort(self.values)
        self.values = self.values[self.argrp_id]
        if self.parameter in RuptureContext._slots_:
            self.element = "Rupture"
        elif self.parameter in site.site_param_dt:
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
        self.sigma = deepcopy(self.mean)
        for iloc, (level, amp_model) in enumerate(amplification_group.items()):
            if "SA" in amp_model["IMLs"]:
                if iloc == 0:
                    self.periods = amp_model["IMLs/T"][:]
                else:
                    assert numpy.allclose(self.periods, amp_model["IMLs/T"][:])
            for imt in ["SA", "PGA", "PGV"]:
                if imt in amp_model["IMLs"]:
                    self.mean[imt][:, :, :, self.argrp_id[iloc]] = \
                        amp_model["IMLs/" + imt][:]
                    self.sigma[imt][:, :, :, self.argrp_id[iloc]] = \
                        amp_model["Total/" + imt][:]
        self.shape = (n_d, n_p, n_m, n_levels)

    def get_set(self):
        """
        Return the parameter as an instance a Python set
        """
        return {self.parameter}

    def get_amplification_factors(self, imt, ctx, dists):
        """
        Returns the amplification factors for the given rupture and site
        conditions.

        :param imt:
            Intensity measure type as an instance of the :class:
            `openquake.hazardlib.imt`
        :param ctx:
            RuptureContext
        :param dists:
            Source to site distances (km)
        :returns:
            * mean_amp - Amplification factors applied to the median ground
                         motion
            * sigma_amp - Amplification factors applied to the
                          total standard deviation of ground motion
        """
        dist_level_table = self.get_mean_table(imt, ctx)
        sigma_table = self.get_sigma_table(imt, ctx)
        mean_interpolator = interp1d(
            self.values, numpy.log10(dist_level_table), axis=1)
        sigma_interpolator = interp1d(self.values, sigma_table, axis=1)
        if self.element == "Rupture":
            mean_amp = 10.0 ** mean_interpolator(
                getattr(ctx, self.parameter))[0] * numpy.ones_like(dists)
            sigma_amp = sigma_interpolator(
                getattr(ctx, self.parameter))[0] * numpy.ones_like(dists)
        else:
            mean_amp = 10.0 ** mean_interpolator(
                getattr(ctx, self.parameter))[0, :]
            sigma_amp = sigma_interpolator(
                getattr(ctx, self.parameter))[0, :] * numpy.ones_like(dists)
        return mean_amp, sigma_amp

    def get_mean_table(self, imt, rctx):
        """
        Returns amplification factors for the mean, given the rupture and
        intensity measure type.

        :returns:
            amplification table as an array of [Number Distances,
            Number Levels]
        """
        # Levels by Distances
        if imt.string in 'PGA PGV':
            interpolator = interp1d(self.magnitudes,
                                    numpy.log10(self.mean[imt.string]), axis=2)
            output_table = 10.0 ** (
                interpolator(rctx.mag).reshape(self.shape[0], self.shape[3]))
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

    def get_sigma_table(self, imt, rctx):
        """
        Returns modification factors for the total standard deviations,
        given the rupture and intensity measure type.

        :returns:
            as an array of shape (#Distances, #Levels)
        """
        # For PGA and PGV only needs to apply magnitude interpolation
        if imt.string in 'PGA PGV':
            interpolator = interp1d(
                self.magnitudes, self.sigma[imt.string], axis=2)
            sig = interpolator(rctx.mag).reshape(self.shape[0], self.shape[3])
        else:
            # For spectral accelerations - need two step process
            # Interpolate period
            interpolator = interp1d(numpy.log10(self.periods),
                                    self.sigma["SA"], axis=1)
            period_table = interpolator(numpy.log10(imt.period))
            mag_interpolator = interp1d(
                self.magnitudes, period_table, axis=1)
            sig = mag_interpolator(rctx.mag)
        return sig


def _setup_amplification(self, fle):
    """
    If amplification data is specified then reads into memory and updates
    the required rupture and site parameters
    """
    self.amplification = AmplificationTable(
        fle["Amplification"], self.m_w, self.distances)
    if self.amplification.element == "Sites":
        self.REQUIRES_SITES_PARAMETERS = {self.amplification.parameter}
    elif self.amplification.element == "Rupture":
        # set the site and rupture parameters on the instance
        self.REQUIRES_SITES_PARAMETERS = set()
        self.REQUIRES_RUPTURE_PARAMETERS = (
            self.REQUIRES_RUPTURE_PARAMETERS |
            {self.amplification.parameter})


def _return_tables(self, mag, imt, which):
    """
    Returns the vector of ground motions or standard deviations
    corresponding to the specific magnitude and intensity measure type.

    :param which:
       the string "IMLs" or "Total"
    """
    assert which in "IMLs Total", which
    if imt.string in 'PGA PGV':
        # Get scalar imt
        if which == "IMLs":
            iml_table = self.imls[imt.string][:]
        else:
            iml_table = self.stddev[imt.string][:]

        n_d, n_s, n_m = iml_table.shape
        iml_table = iml_table.reshape([n_d, n_m])
    else:
        if which == "IMLs":
            periods = self.imls["T"][:]
            iml_table = self.imls["SA"][:]
        else:
            periods = self.stddev["T"][:]
            iml_table = self.stddev["SA"][:]

        low_period = round(periods[0], 7)
        high_period = round(periods[-1], 7)
        if (round(imt.period, 7) < low_period) or (
                round(imt.period, 7) > high_period):
            raise ValueError("Spectral period %.3f outside of valid range "
                             "(%.3f to %.3f)" % (imt.period, periods[0],
                                                 periods[-1]))
        # Apply log-log interpolation for spectral period
        interpolator = interp1d(
            numpy.log10(periods), numpy.log10(iml_table), axis=1)
        iml_table = 10. ** interpolator(numpy.log10(imt.period))
    return apply_magnitude_interpolation(self, mag, iml_table)


def apply_magnitude_interpolation(self, mag, iml_table):
    """
    Interpolates the tables to the required magnitude level

    :param float mag:
        Magnitude
    :param iml_table:
        Intensity measure level table
    """
    # do not allow "mag" to exceed maximum table magnitude
    mag = numpy.clip(mag, None, self.m_w[-1])

    # Get magnitude values
    if (mag < self.m_w[0]).any() or (mag > self.m_w[-1]).any():
        raise ValueError("Magnitude %s outside of supported range "
                         "(%.2f to %.2f)" % (mag, self.m_w[0], self.m_w[-1]))
    # It is assumed that log10 of the spectral acceleration scales
    # linearly (or approximately linearly) with magnitude
    m_interpolator = interp1d(self.m_w, numpy.log10(iml_table), axis=1)
    return 10.0 ** m_interpolator(mag)


def _get_stddev(sigma, dists, table_dists, imt):
    """
    Returns the total standard deviation of the intensity measure level
    from the tables.
    """
    stddev = numpy.interp(dists, table_dists, sigma)
    stddev[dists < table_dists[0]] = sigma[0]
    stddev[dists > table_dists[-1]] = sigma[-1]
    return stddev


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
    DEFINED_FOR_TECTONIC_REGION_TYPE = TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {StdDev.TOTAL}

    REQUIRES_SITES_PARAMETERS = set()

    REQUIRES_DISTANCES = set()

    REQUIRES_RUPTURE_PARAMETERS = {"mag"}

    gmpe_table = None  # see subclasses like NBCC2015_AA13_activecrustFRjb_low

    amplification = None

    kind = "base"

    def __init__(self, **kwargs):
        """
        Executes the preprocessing steps at the instantiation stage to read in
        the tables from hdf5 and hold them in memory.
        """
        super().__init__(**kwargs)
        self.table = {}  # dictionary mag_str, imt_str, which -> array
        # populated by the ContextManager once imts and magnitudes are known
        fname = self.kwargs.get('gmpe_table', self.gmpe_table)
        with h5py.File(fname, "r") as fle:
            self.distance_type = decode(fle["Distances"].attrs["metric"])
            self.REQUIRES_DISTANCES = {self.distance_type}
            # Load in magnitude
            self.m_w = fle["Mw"][:]
            # Load in distances
            self.distances = fle["Distances"][:]
            # Load intensity measure types and levels
            self.imls = todict(fle["IMLs"])
            # Update the list of supported IMTs from the tables
            self.DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
                getattr(imt_module, key)
                for key in self.imls if key in imt_module.__dict__}
            if "SA" in self.imls and "T" not in self.imls:
                raise ValueError("Spectral Acceleration must be accompanied by"
                                 " periods")

            # Load in standard deviations
            if self.kind in "nga_east usgs":
                # there are no stddevs in the hdf5 file
                self.stddev = None
                return
            self.stddev = todict(fle["Total"])
            if "Amplification" in fle:
                _setup_amplification(self, fle)

    def compute(self, ctx, imts, mean, sig, tau, phi):
        # Get distance vector for the given magnitude
        idx = numpy.searchsorted(self.m_w, ctx.mag)
        table_dists = self.distances[:, 0, idx - 1]
        dists = getattr(ctx, self.distance_type)
        for m, imt in enumerate(imts):
            # compute Distance and Sigma Tables
            magstr = '%.2f' % ctx.mag
            imls = self.table[magstr, imt.string, "IMLs"]
            sigma = self.table[magstr, imt.string, "Total"]
            # Get mean and standard deviations
            mean_ = _get_mean(self.kind, imls, dists, table_dists)
            stddev = _get_stddev(sigma, dists, table_dists, imt)
            if self.amplification:
                mean_amp, sigma_amp = \
                    self.amplification.get_amplification_factors(
                        imt, ctx, dists)
                mean[m] = numpy.log(mean_ * mean_amp)
                sig[m] = stddev * sigma_amp
            else:
                mean[m] = numpy.log(mean_)
                sig[m] = stddev
