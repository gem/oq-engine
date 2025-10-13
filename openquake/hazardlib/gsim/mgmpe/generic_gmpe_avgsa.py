# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
        'baker_jayaram', 'akkar', 'eshm20', 'none'. Default is none.
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

        # Check for existing correlation function
        if corr_func not in CORRELATION_FUNCTION_HANDLES:
            raise ValueError('Not a valid correlation function')
        else:
            self.corr_func = \
                CORRELATION_FUNCTION_HANDLES[corr_func](avg_periods)

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


class GmpeIndirectAvgSA(GMPE):
    """Implements an alternative form of GMPE for indirect Average SA (AvgSA)
    that allows for AvgSA to be defined as a vector quantity described by an
    anchoring period (T0) and a set of n_per spectral accelerations linearly
    spaced between t_low * T0 and t_high * T0. This corresponds to the more
    common definition of AvgSA as the mean between, for example, 0.2 * T0 and
    1.5 * T0, used by (among others) Iacoletti et al. (2023).

    In this form of AvgSA GMPE it is possible to run analysis for multiple
    values of AvgSA with different T0 values, such as one might need if
    considering risk for a heterogeneous portfolio of buildings. To do so
    the set of required periods needed for all of the T0 values are assembled
    and SA determined for each of the values needed. However, if the total
    number of SA periods exceeds a user-configurable limit (max_num_per,
    defaulted to 30) then SA will be calculated for the maximum number of
    periods and interpolated to the desired values for each AvgSA(T0).

    :param string gmpe_name:
        The name of a GMPE class used for the calculation.

    :param string corr_func:
        Handle of the function to compute correlation coefficients between
        different spectral acceleration ordinates. Valid options are:
        'baker_jayaram', 'akkar', 'eshm20', 'none'. Default is none.

    :param float t_low:
        Lower bound of period range for calculation (as t_low * T0)

    :param float t_high:
        Upper bound of period range for calculation (as t_high * T0)

    :param int n_per:
        Number of linearly spacee periods beteen t_low * T0 and t_high * T0
        from which AvgSA(T0) is determined

    :param int max_num_per:
        Maximum number of periods permissible for direct calculation of
        AvgSA before switching to an interpolation approach
    """

    # Parameters
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {AvgSA, }
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''

    def __init__(self, gmpe_name, corr_func, t_low: float = 0.2,
                 t_high: float = 1.5, n_per: int = 10, **kwargs):
        super().__init__(gmpe_name=gmpe_name, corr_func=corr_func,
                         t_low=t_low, t_high=t_high, n_per=n_per, **kwargs)
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
        assert t_high > t_low,\
            "Upper bound scaling factor for AvgSA must exceed lower bound"
        self.t_low = t_low
        self.t_high = t_high
        self.t_num = n_per
        self.max_num_per = kwargs.get("max_num_per", 30)

        # Check for existing correlation function
        if corr_func not in CORRELATION_FUNCTION_HANDLES:
            raise ValueError('Not a valid correlation function')
        else:
            self.corr_func = CORRELATION_FUNCTION_HANDLES[corr_func]

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        """
        # Gather together all of the needed periods for the set of imts
        t0s = np.array([imt.period for imt in imts])
        periods = []
        idxs = []
        for i, period in enumerate(t0s):
            periods.extend(np.linspace(self.t_low * period,
                                       self.t_high * period,
                                       self.t_num))
            idxs.extend(i * np.ones(self.t_num, dtype=int))
        periods = np.array(periods)
        idxs = np.array(idxs)
        if len(periods) > self.max_num_per:
            # Maximum number of periods exceeded, so now define a set of
            # max_num_per periods linearly spaced between the lower and
            # upper bound of the total period range considered
            periods = np.linspace(periods[0], periods[-1], self.max_num_per)
            apply_interpolation = True
        else:
            apply_interpolation = False
        # Get mean and stddevs for all required periods
        new_imts = [SA(per) for per in periods]
        mean_sa = np.zeros([len(new_imts), len(ctx)])
        sigma_sa = np.zeros_like(mean_sa)
        tau_sa = np.zeros_like(mean_sa)
        phi_sa = np.zeros_like(mean_sa)
        self.gmpe.compute(ctx, new_imts, mean_sa, sigma_sa, tau_sa, phi_sa)
        for m, imt in enumerate(imts):
            if apply_interpolation:
                # Interpolate mean and sigma to the t_num selected periods
                target_periods = np.linspace(self.t_low * imt.period,
                                             self.t_high * imt.period,
                                             self.t_num)

                ipl_mean = interp1d(
                    periods, mean_sa.T, bounds_error=False,
                    fill_value=(mean_sa[0, :], mean_sa[-1, :]),
                    assume_sorted=True)
                mean[m] += ((1.0 / self.t_num) * np.sum(
                    ipl_mean(target_periods).T, axis=0))

                ipl_sig = interp1d(
                    periods, sigma_sa.T, bounds_error=False,
                    fill_value=(sigma_sa[0, :], sigma_sa[-1, :]),
                    assume_sorted=True)
                sig_target = ipl_sig(target_periods).T
            else:
                # For the given IM simply select the mean and sigma for the
                # corresponding periods
                idx = idxs == m
                target_periods = periods[idx]
                mean[m] += ((1.0 / self.t_num) * np.sum(mean_sa[idx, :],
                                                        axis=0))
                sig_target = sigma_sa[idx, :]

            # For the total standard deviation sum the standard deviations
            # accounting for the cross-correlation
            for j, t_1 in enumerate(target_periods):
                for k, t_2 in enumerate(target_periods):
                    rho = 1.0 if j == k else self.corr_func.get_correlation(
                        t_1, t_2)
                    sig[m] += (rho * sig_target[j, :] * sig_target[k, :])
            sig[m] = np.sqrt((1.0 / (self.t_num ** 2.)) * sig[m])


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

    @staticmethod
    def get_correlation(t1, t2):
        """
        Computes the correlation coefficient for the specified periods.

        :param float t1:
            First period of interest.:w


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

    @staticmethod
    def get_correlation(t1, t2):
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


ESHM20_COEFFICIENTS = {
     "total": (0.18141134, 0.1555742,  -0.10851875, 0.08, 0.2),
     "between-event": (0.15881576, 0.08439678, -0.13915732, 0.08, 0.2),
     "between-site": (0.15751022, 0.15934185, -0.17513388, 0.08, 0.2),
     "within-event": (0.26023904, 0.27590487, -0.0951078, 0.08, 0.2)
}


def baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5, t1, t2):
    """
    Basic function of the Baker & Jayaram (2007) cross-correlation model
    allowing for flexibility in the coefficients of the model

    :param float d1:
        Coefficient d1 (0.366 in original model)

    :param float d2:
        Coefficient d2 (0.105 in original model)

    :param float d3:
        Coefficient d3 (0.0099 in original model)

    :param float d4:
        Coefficient d4 (0.109 in the original model)

    :param float d5:
        Coefficient d5 (0.2 in the original model)

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
    c1 -= np.cos(np.pi / 2.0 - np.log(t_max / max(t_min, d4)) * d1)

    if t_max < d5:
        c2 = d2 * (1.0 - 1.0 / (1.0 + np.exp(100.0 * t_max - 5.0)))
        c2 = 1.0 - c2 * (t_max - t_min) / (t_max - d3)
    else:
        c2 = 0

    if t_max < d4:
        c3 = c2
    else:
        c3 = c1

    c4 = c1
    c4 += 0.5 * (np.sqrt(c3) - c3) * (1.0 + np.cos(np.pi * t_min / d4))

    if t_max <= d4:
        rho = c2
    elif t_min > d4:
        rho = c1
    elif t_max < d5:
        rho = min(c2, c4)
    else:
        rho = c4

    return rho


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

    @staticmethod
    def get_correlation(t1, t2):
        """
        Computes the correlation coefficient for the specified periods.

        :param float t1:
            First period of interest.

        :param float t2:
            Second period of interest.

        :return float rho:
            The predicted correlation coefficient.
        """
        d1, d2, d3, d4, d5 = (0.366, 0.105, 0.0099, 0.109, 0.2)
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)


class ESHM20CorrelationModel(BakerJayaramCorrelationModel):
    """Variation of the Baker & Jayaram (2007) cross-correlation model with
    coefficients calibrated on European data, and with separate functions
    for correlation in between-event, between-site and within-event residuals
    """

    @staticmethod
    def get_correlation(t1, t2):
        """
        Computes the correlation coefficient for the specified periods for the
        total standard deviation

        :param float t1:
            First period of interest.

        :param float t2:
            Second period of interest.

        :return float rho:
            The predicted correlation coefficient.

        Original
        0.366, 0.105, 0.0099
        New
        0.20698079,  0.0888577,  -0.03330
        """
        d1, d2, d3, d4, d5 = ESHM20_COEFFICIENTS["total"]
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)

    @staticmethod
    def get_between_event_correlation(t1, t2):
        """As per the get_correlation function but for the between-event
        residuals only
        """
        d1, d2, d3, d4, d5 = ESHM20_COEFFICIENTS["between-event"]
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)

    @staticmethod
    def get_between_site_correlation(t1, t2):
        """As per the get_correlation function but for the between-site
        residuals only
        """
        d1, d2, d3, d4, d5 = ESHM20_COEFFICIENTS["between-site"]
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)

    @staticmethod
    def get_within_event_correlation(t1, t2):
        """As per the get_correlation function but for the between-event
        residuals only
        """
        d1, d2, d3, d4, d5 = ESHM20_COEFFICIENTS["within-event"]
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)


CORRELATION_FUNCTION_HANDLES = {
    'baker_jayaram': BakerJayaramCorrelationModel,
    'akkar': AkkarCorrelationModel,
    "eshm20": ESHM20CorrelationModel,
    'none': DummyCorrelationModel
}
