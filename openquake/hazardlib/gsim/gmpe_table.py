# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
in the form of binary tables
"""
import h5py
from scipy.interpolate import interp1d
import numpy as np

from openquake.baselib.general import CallableDict
from openquake.baselib.python3compat import decode
from openquake.hazardlib.const import TRT, StdDev
from openquake.hazardlib import imt as imt_module
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
    mean = np.interp(dists, table_dists, data)
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

        n_d, _n_s, n_m = iml_table.shape
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
        period = round(imt.period, 7)
        if period < low_period or period > high_period:
            raise ValueError("Spectral period %.3f outside of valid range "
                             "(%.3f to %.3f)" % (imt.period, periods[0],
                                                 periods[-1]))
        # Apply log-log interpolation for spectral period
        interpolator = interp1d(
            np.log10(periods), np.log10(iml_table), axis=1)
        iml_table = 10. ** interpolator(np.log10(imt.period))

    # do not allow "mag" to exceed maximum table magnitude
    mag = np.clip(mag, None, self.m_w[-1])

    # Get magnitude values
    if (mag < self.m_w[0]).any() or (mag > self.m_w[-1]).any():
        raise ValueError("Magnitude %.2f outside of supported range "
                         "(%.2f to %.2f)" % (mag, self.m_w[0], self.m_w[-1]))
    # It is assumed that log10 of the spectral acceleration scales
    # linearly (or approximately linearly) with magnitude
    m_interpolator = interp1d(self.m_w, np.log10(iml_table), axis=1)
    return 10.0 ** m_interpolator(mag)


def _get_stddev(sigma, dists, table_dists, imt):
    """
    Returns the total standard deviation of the intensity measure level
    from the tables.
    """
    stddev = np.interp(dists, table_dists, sigma)
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

    #: REQUIRES_DISTANCES is set at the instance level
    REQUIRES_DISTANCES = set()

    REQUIRES_RUPTURE_PARAMETERS = {"mag"}

    gmpe_table = None  # see subclasses like NBCC2015_AA13_activecrustFRjb_low

    kind = "base"

    def __init__(self, gmpe_table):
        """
        Executes the preprocessing steps at the instantiation stage to read in
        the tables from hdf5 and hold them in memory.
        """
        self.gmpe_table = self.filename = gmpe_table
        # populated by the ContextManager once imts and magnitudes are known
        with h5py.File(self.filename, "r") as fle:
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

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        [mag] = np.unique(np.round(ctx.mag, 2))  # constructed unique
        idx = np.searchsorted(self.m_w, mag)
        table_dists = self.distances[:, 0, idx - 1]
        dists = getattr(ctx, self.distance_type)
        for m, imt in enumerate(imts):
            key = ('%.2f' % mag, imt.string)
            imls = self.mean_table[key]
            mean[m] = np.log(_get_mean(self.kind, imls, dists, table_dists))
            sig[m] = _get_stddev(self.sig_table[key], dists, table_dists, imt)

    # called by the ContextMaker
    def set_tables(self, mags, imts):
        """
        :param mags: a list of magnitudes as strings
        :param imts: a list of IMTs as strings

        Set the .mean_table and .sig_table attributes
        """
        self.mean_table = {}  # dictionary mag_str, imt_str -> array
        self.sig_table = {}  # dictionary mag_str, imt_str -> array
        if 'PGA' in self.imls and 'PGA' not in imts:
            # add PGA since it will be needed in get_mean_amp
            imts = sorted(set(imts) | {'PGA'})
        if 'SA(0.2)' not in imts:
            # add SA(0.2) since it will be needed in get_mean_amp
            imts = sorted(set(imts) | {'SA(0.2)'})
        for imt in imts:
            imt_obj = imt_module.from_string(imt)
            for mag in mags:
                self.mean_table[mag, imt] = _return_tables(
                    self, float(mag), imt_obj, 'IMLs')
                if self.stddev is not None:
                    self.sig_table[mag, imt] = _return_tables(
                        self, float(mag), imt_obj, 'Total')
