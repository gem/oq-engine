# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.hazardlib.mgmp.generic_gmpe_avgsa` implements
:class:`~openquake.hazardlib.mgmpe.GenericGmpeAvgSA`
"""

import abc
import numpy as np
from scipy.interpolate import interp1d
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import const, contexts
from openquake.hazardlib.imt import AvgSA, SA
from openquake.hazardlib.gsim.mgmpe import akkar_coeff_table as act


class GenericGmpeAvgSA(GMPE):
    """
    Implements a modified GMPE class that can be used to compute average
    ground motion over several spectral ordinates from an arbitrary GMPE.
    The mean and standard deviation are computed according to:
    Kohrangi M., Reddy Kotha S. and Bazzurro P., 2018, Ground-motion models
    for average spectral acceleration in a period range: direct and indirect
    methods, Bull. Earthquake. Eng., 16, pp. 45–65.
    Note that only the Total Standard Deviation is supported.

    :param string gmpe_name:
        The name of a GMPE class used for the calculation.

    :param list avg_periods:
        List of averaging periods (must be a subset of the periods allowed
        in the selected GMPE)

    :param string corr_func:
        Handle of the function to compute correlation coefficients between
        different spectral acceleration ordinates. Valid options are:
        'baker_jayaram', 'akkar', 'none'. Default is none.
    """

    # Parameters
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {AvgSA}
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''

    def __init__(self, gmpe_name, avg_periods, corr_func='none', **kwargs):

        super().__init__(gmpe_name=gmpe_name, avg_periods=avg_periods,
                         corr_func=corr_func, **kwargs)
        self.gmpe = registry[gmpe_name](**kwargs)
        # Combine the parameters of the GMPE provided at the construction
        # level with the ones assigned to the average GMPE.
        for key in dir(self):
            if key.startswith('REQUIRES_'):
                setattr(self, key, getattr(self.gmpe, key))
            if key.startswith('DEFINED_'):
                if not key.endswith('FOR_INTENSITY_MEASURE_TYPES'):
                    setattr(self, key, getattr(self.gmpe, key))

        # Ensure that it is always recogised that the AvgSA GMPE is defined
        # only for total standard deviation even if the called GMPE is
        # defined for inter- and intra-event standard deviations too
        self.DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
        self.avg_periods = avg_periods
        self.tnum = len(self.avg_periods)

        correlation_function_handles = {
            'baker_jayaram': BakerJayaramCorrelationModel,
            'akkar': AkkarCorrelationModel,
            'none': DummyCorrelationModel}

        # Check for existing correlation function
        if corr_func not in correlation_function_handles:
            raise ValueError('Not a valid correlation function')
        else:
            self.corr_func = \
                correlation_function_handles[corr_func](avg_periods)

        # Check if this GMPE has the necessary requirements
        # TO-DO

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        :param imts: must be a single IMT of kind AvgSA
        """
        sas = [SA(period) for period in self.avg_periods]
        out = contexts.get_mean_stds(self.gmpe, ctx, sas)

        stddvs_avgsa = 0.
        for i1 in range(self.tnum):
            mean[:] += out[0, i1]
            for i2 in range(self.tnum):
                rho = self.corr_func(i1, i2)
                stddvs_avgsa += rho * out[1, i1] * out[1, i2]

        mean[:] /= self.tnum
        sig[:] = np.sqrt(stddvs_avgsa) / self.tnum


class BaseAvgSACorrelationModel(metaclass=abc.ABCMeta):
    """
    Base class for correlation models used in spectral period averaging.
    """
    def __init__(self, avg_periods):
        self.avg_periods = avg_periods
        self.build_correlation_matrix()

    def build_correlation_matrix(self):
        pass

    def __call__(self, i, j):
        return self.rho[i, j]


class BakerJayaramCorrelationModel(BaseAvgSACorrelationModel):
    """
    Produce inter-period correlation for any two spectral periods.
    Subroutine taken from: https://usgs.github.io/shakemap/shakelib
    Based upon:
    Baker, J.W. and Jayaram, N., 2007, Correlation of spectral acceleration
    values from NGA ground motion models, Earthquake Spectra.
    """
    def build_correlation_matrix(self):
        """
        Constucts the correlation matrix period-by-period from the
        correlation functions
        """
        self.rho = np.eye(len(self.avg_periods))
        for i, t1 in enumerate(self.avg_periods):
            for j, t2 in enumerate(self.avg_periods[i:]):
                self.rho[i, i + j] = self.get_correlation(t1, t2)
        self.rho += (self.rho.T - np.eye(len(self.avg_periods)))

    def get_correlation(self, t1, t2):
        """
        Computes the correlation coefficient for the specified periods.

        :param float t1:
            First period of interest.

        :param float t2:
            Second period of interest.

        :return float rho:
            The predicted correlation coefficient.
        """

        t_min = min(t1, t2)
        t_max = max(t1, t2)

        c1 = 1.0
        c1 -= np.cos(np.pi / 2.0 - np.log(t_max / max(t_min, 0.109)) * 0.366)

        if t_max < 0.2:
            c2 = 0.105 * (1.0 - 1.0 / (1.0 + np.exp(100.0 * t_max - 5.0)))
            c2 = 1.0 - c2 * (t_max - t_min) / (t_max - 0.0099)
        else:
            c2 = 0

        if t_max < 0.109:
            c3 = c2
        else:
            c3 = c1

        c4 = c1
        c4 += 0.5 * (np.sqrt(c3) - c3) * (1.0 + np.cos(np.pi * t_min / 0.109))

        if t_max <= 0.109:
            rho = c2
        elif t_min > 0.109:
            rho = c1
        elif t_max < 0.2:
            rho = min(c2, c4)
        else:
            rho = c4

        return rho


class AkkarCorrelationModel(BaseAvgSACorrelationModel):
    """
    Read the period-dependent correlation coefficient matrix as in:
    Akkar S., Sandikkaya MA., Ay BO., 2014, Compatible ground-motion
    prediction equations for damping scaling factors and vertical to
    horizontal spectral amplitude ratios for the broader Europe region,
    Bull Earthquake Eng, 12, pp. 517-547.
    """
    def build_correlation_matrix(self):
        """
        Constructs the correlation matrix by two-step linear interpolation
        from the correlation table
        """
        irho = np.array(act.coeff_table)
        iper = np.array(act.periods)
        if np.any(self.avg_periods < iper[0]) or\
                np.any(self.avg_periods > iper[-1]):
            raise ValueError("'avg_periods' contains values outside of the "
                             "range supported by the Akkar et al. (2014) "
                             "correlation model")
        ipl1 = interp1d(iper, irho, axis=1)
        ipl2 = interp1d(iper, ipl1(self.avg_periods), axis=0)
        self.rho = ipl2(self.avg_periods)

    def get_correlation(self, t1, t2):
        """
        Computes the correlation coefficient for the specified periods.

        :param float t1:
            First period of interest.

        :param float t2:
            Second period of interest.

        :return float:
            The predicted correlation coefficient.
        """
        periods = np.array(act.periods)
        rho = np.array(act.coeff_table)
        if t1 < periods[0] or t1 > periods[-1]:
            raise ValueError("t1 %.3f is out of valid period range (%.3f to "
                             "%.3f" % (t1, periods[0], periods[-1]))

        if t2 < periods[0] or t2 > periods[-1]:
            raise ValueError("t1 %.3f is out of valid period range (%.3f to "
                             "%.3f" % (t2, periods[0], periods[-1]))
        iloc1 = np.searchsorted(periods, t1)
        iloc2 = np.searchsorted(periods, t2)
        if iloc1:
            rho1 = rho[iloc1 - 1, :] + (t1 - periods[iloc1 - 1]) *\
                ((periods[iloc1] - periods[iloc1 - 1]) /
                 (rho[iloc1, :] - rho[iloc1 - 1, :]))
        else:
            rho1 = rho[0, :]
        if iloc2:
            rho2 = rho1[iloc2 - 1] + (t2 - periods[iloc2 - 1]) *\
                ((periods[iloc2] - periods[iloc2 - 1]) /
                 (rho1[iloc2] - rho1[iloc2 - 1]))
        else:
            rho2 = rho1[0]
        return rho2


class DummyCorrelationModel(BaseAvgSACorrelationModel):
    """
    Dummy function returning just 1 (used as default function handle)
    """
    def build_correlation_matrix(self):
        self.rho = np.ones([len(self.avg_periods), len(self.avg_periods)])

    def get_correlation(self, t1, t2):
        """
        Computes the correlation coefficient for the specified periods.

        :param float t1:
            First period of interest.

        :param float t2:
            Second period of interest.

        :return float:
            The predicted correlation coefficient.
        """

        return 1.
