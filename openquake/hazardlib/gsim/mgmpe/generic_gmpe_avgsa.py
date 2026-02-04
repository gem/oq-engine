# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
import os
import abc
import h5py
import numpy as np
from pathlib import Path
from scipy.interpolate import interp1d, RegularGridInterpolator

from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import const, contexts
from openquake.hazardlib.imt import AvgSA, SA
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import compute_imts_subset

CORR_COEFFS_FOLDER = Path(__file__).parent / "corr_coeffs"


class GenericGmpeAvgSA(GMPE):
    """
    Implements a modified GMPE class that can be used to compute indirect
    average ground motion over several spectral ordinates from an arbitrary
    GMPE. The mean and standard deviation are computed according to:
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
        self.gmpe = registry[gmpe_name](**kwargs)
        # Combine the parameters of the GMPE provided at the construction
        # level with the ones assigned to the average GMPE.
        for key in dir(self):
            if key.startswith('REQUIRES_'):
                setattr(self, key, getattr(self.gmpe, key))
            if key.startswith('DEFINED_'):
                if not key.endswith('FOR_INTENSITY_MEASURE_TYPES'):
                    setattr(self, key, getattr(self.gmpe, key))

        # Ensure that it is always recognised that the AvgSA GMPE is defined
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

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Compute the indirect AvgSA using the correlation model and the
        specified GMPE for a prespecified list of averaging periods.
        
        Also, compute the other IMTs using the underlying GMPE (as
        expected, an error will be raised if the underlying GMPE does
        not support the IMT). NOTE: Specifying additional IMTs does not
        affect the AvgSA values because means and std devs are first
        computed within `get_mean_stds` only for the averaging periods
        (i.e., we just update the indices of the non-AvgSA arrays in
        the mean and std dev arrays post AvgSA calculation - checked
        in classical/case34).
        """
        # Get mean and std devs for averaging periods
        averaging_periods = [SA(period) for period in self.avg_periods]
        out = contexts.get_mean_stds(self.gmpe, ctx, averaging_periods)

        # Compute average SA
        stddvs_avgsa = 0.
        for i1 in range(self.tnum):
            mean[:] += out[0, i1]
            for i2 in range(self.tnum):
                rho = self.corr_func(i1, i2)
                stddvs_avgsa += rho * out[1, i1] * out[1, i2]

        mean[:] /= self.tnum
        sig[:] = np.sqrt(stddvs_avgsa) / self.tnum

        # Now update the indices in the mean and std devs that are not AvgSA
        non_avgSA = {imt for imt in imts if imt.name != "AvgSA"}
        if non_avgSA:
            compute_imts_subset(
                self.gmpe, imts, non_avgSA, ctx, mean, sig, tau, phi)


def _get_periods(t_low, t_high, t_num, max_num_per, imts):
    """
    Used in GmpeIndirectAvgSA class to compute target periods per AvgSA
    IMT and determine if interpolation is required.
    """
    # For each IMT get target period range 
    periods_per_avgsa_imt = {
        imt.string: np.linspace(
            t_low * imt.period, t_high * imt.period, t_num)
            for imt in imts if imt.name == "AvgSA"}

    # Get the unique periods over all the AvgSA imts
    if periods_per_avgsa_imt != {}:
        unique_periods = np.unique(
            np.concatenate(list(periods_per_avgsa_imt.values())))
    else:
        # No AvgSA IMTs - edge case where the user is specifying indirect
        # AvgSA model BUT only has non-AvgSA IMTs in job file (return empty
        # list of averaging periods to permit still using underlying GMPE to
        # compute "regular" IMTs - "AvgSA" part of compute method is skipped)
        return list(), False, periods_per_avgsa_imt

    if len(unique_periods) > max_num_per:
        # Maximum number of periods exceeded, so now define a set of
        # max_num_per periods linearly spaced between the lower and
        # upper bound of the total period range considered
        periods_all = np.linspace(
            unique_periods[0], unique_periods[-1], max_num_per)
        apply_interpolation = True
    else:
        periods_all = unique_periods
        apply_interpolation = False
    
    return periods_all, apply_interpolation, periods_per_avgsa_imt


class GmpeIndirectAvgSA(GMPE):
    """
    Implements an alternative form of GMPE for indirect Average SA (AvgSA)
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
            self.corr_func = CORRELATION_FUNCTION_HANDLES[corr_func]()

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Compute the indirect AvgSA using the correlation model and the
        specified GMPE for linspaced t_num periods between t_low and
        t_high, and switch to interpolation if exceeding max_num_per.
        
        Also, compute the other IMTs using the underlying GMPE (as
        expected, an error will be raised if the underlying GMPE does
        not support the IMT).
        """
        # Check if any non-AvgSA IMTs
        non_avgSA = {imt for imt in imts if imt.name != "AvgSA"}
        if non_avgSA:
            compute_imts_subset(
                self.gmpe, imts, non_avgSA, ctx, mean, sig, tau, phi)

        # Get periods
        periods_all, apply_interpolation, periods_per_avgsa_imt = _get_periods(
            self.t_low, self.t_high, self.t_num, self.max_num_per, imts)

        # Get mean and stddevs for all required periods
        new_imts = [SA(per) for per in periods_all]
        sh = (len(new_imts), len(ctx))
        mean_sa, sigma_sa, tau_sa, phi_sa =\
              np.empty(sh), np.empty(sh), np.empty(sh), np.empty(sh)
        self.gmpe.compute(ctx, new_imts, mean_sa, sigma_sa, tau_sa, phi_sa)
        for m, imt in enumerate(imts):
            if imt.name == "AvgSA": # Only proceed for AvgSA imts
                
                # Target periods for given IMT
                target_periods = periods_per_avgsa_imt[imt.string]

                if apply_interpolation:
                    # Interpolate mean and sigma
                    ipl_mean = interp1d(periods_all, mean_sa.T,
                                        bounds_error=False,
                                        fill_value=(
                                            mean_sa[0, :], mean_sa[-1, :]),
                                            assume_sorted=True)
                    m_target = ipl_mean(target_periods).T
                    
                    ipl_sig = interp1d(periods_all, sigma_sa.T,
                                       bounds_error=False,
                                       fill_value=(
                                           sigma_sa[0, :], sigma_sa[-1, :]),
                                           assume_sorted=True)
                    sig_target = ipl_sig(target_periods).T

                else:
                    # For the given IM simply select the mean and
                    # sigma for the corresponding periods
                    idx = np.searchsorted(periods_all, target_periods)
                    m_target = mean_sa[idx, :]
                    sig_target = sigma_sa[idx, :]

                # Calculate Mean for index m
                mean[m] = (1.0 / self.t_num) * np.sum(m_target, axis=0)

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
    def __init__(self, avg_periods=None):

        self.avg_periods = avg_periods

        if avg_periods is not None:
            self.build_correlation_matrix()
        else:
            self.rho = None

    def build_correlation_matrix(self):
        pass

    def __call__(self, i, j):
        if (self.rho is not None) and (self.avg_periods is not None):
            return self.rho[i, j]
        raise RuntimeError("Correlation Matrix not built. "
                           "Provide 'avg_periods' at init.")


class EmpiricalAvgSACorrelationModel(BaseAvgSACorrelationModel):
    """
    Intermediate class to handle the interpolation of empirical correlation 
    data and the construction of the correlation matrices.
    """
    def __init__(self, avg_periods, rho_arrays, rho_periods):
        """       
        :param np.ndarray avg_periods : 
            The periods used for calculating the spectral acceleration
        
        :param dict[str, np.ndarray] rho_arrays: 
            The correlation data. The keys rho_arrays are strings that represent
            the type of residual that the associated array corresponds to. 
        
        :param np.ndarray rho_periods: 
            A 1D array of the spectral periods that correspond to the rows and 
            columns of the correlation data

        Notes:
        1)  It is assumed that the same periods apply to all correlation 
            matrices in the same correlation model.
        
        2)  The keys for rho_arrays follow the notation of Al Atik et al (2010).
            Each key maps to a method that returns the appropriate
            correlation coefficient. Currently the this is:
            "total"  -> get_correlation()
            "dB_e"   -> get_between_event_correlation()
            "dS2S_s" -> get_between_site_correlation()
            "dWS_es" -> get_within_event_correlation()
            The class can be instantiated using a dict that doesn't contain all
            the keys, however if the mapped function is called then a ValueError
            will be raised. The provided dict must have as a minimum the key
            "total".
        """
        # rho_arrays is dictionary of the arrays of corr coeffs that are part
        # of the correlation model. The keys of this dictionary indicate what
        # correlation functions can be called without raising an error. 

        if not isinstance(rho_arrays, dict):
            raise TypeError("rho_arrays must be of type dict")
        if "total" not in rho_arrays.keys():
            raise ValueError("rho_arrays must contain the key 'total'")
        
        # store the raw correlation data
        self.raw_rhos = rho_arrays
        self.raw_Ts = rho_periods
        self.valid_residual_types = list(rho_arrays.keys()) 

        # create the interpolation functions for each residual type / array
        self._create_interpers()

        if avg_periods is not None:
            if any(avg_periods < min(rho_periods)):
                raise ValueError(f"Period ({min(avg_periods):.3f}) is less "
                                f"than the minimum allowable period for the "
                                f"correlation model ({min(rho_periods):.3f}).")
            
            if any(avg_periods > max(rho_periods)):
                raise ValueError(f"Period ({max(avg_periods):.3f}) is greater "
                                f"than the maximum allowable period for the "
                                f"correlation model ({max(rho_periods):.3f}).")

        super().__init__(avg_periods)
        
    def build_correlation_matrix(self):
        """
        Interpolate the raw correlation data for required periods (avg_periods)
        """
        self.rho_mats = self._build_correlation_matrices() # dict of rho_mats
        self.rho = self.rho_mats["total"]

    def _build_correlation_matrices(self):
        """
        Interpolate the raw correlation data for required periods (avg_periods).
        Returns a dict with keys indicating the type of residual and the values 
        being 2D numpy arrays of interpolated corr coeffs.
        """
        # interpolates the raw coeff data for all the provided matrices and 
        # returns a dictionary with the keys indicating the type of residual
        # and the values being 2D numpy arrays of interpolated corr coeffs.

        corr_mats = {}
        for residual_type, interper in self.interpers.items():
            corr_mats[residual_type] = self._interpolate_matrix(
                interper, self.avg_periods)
        return corr_mats

    def _create_interpers(self):
        """
        Creates an interpolation function for each correlation matrix in the 
        model and stores them in a dictionary for later use. The keys of the
        dict are the type of residual, e.g. dB_e, dS2S_s etc...
        """
        interpers = {}
        for residual_type, rho_mat in self.raw_rhos.items():
            interper = RegularGridInterpolator(
                points=(self.raw_Ts, self.raw_Ts),
                values=rho_mat,
                method="linear"
                )
            interpers[residual_type] = interper
        self.interpers = interpers  

    def _interpolate_matrix(self, interper, new_Ts):
        """
        2D interpolation of the correlation matrix.
        Returns a symmetric nxn matrix with 1s on the diagonal
        
        :param RegularGridInterpolator interper: 
            interpolation function to be used
        
        :param np.ndarray new_Ts:
            array of periods at which the matrix should be interpolated
        """
        # create an array of interp points with shape (N*N, 2)
        t1, t2 = np.meshgrid(new_Ts, new_Ts, indexing="ij") # t1 and t2 have shape (N, N)
        interp_pts = np.column_stack([t1.ravel(), t2.ravel()])
        interped_rhos = interper(interp_pts).reshape(len(new_Ts), -1)

        # make sure the diagonal terms are equal to 1.0
        np.fill_diagonal(interped_rhos, 1.0)

        return interped_rhos
    
    def _check_valid_residual_type(self, residual_type):
        if not residual_type in self.valid_residual_types:
            raise ValueError(f"Invalid type of residual ({residual_type}) for "
                             f"correlation model.")
    
    def _get_correlation(self, interper, t1, t2):
        """
        Computes the correlation coefficient for the specified periods for the
        correlation matrix defined in the interpolation function.
        
        :param RegularGridInterpolator interper: 
            interpolation function for the correlation matrix
        
        :param float t1:
            First period of interest.

        :param float t2:
            Second period of interest.

        :return float rho:
            The estimated correlation coefficient.
        """

        if all(min(t1, t2) < self.raw_Ts):
             raise ValueError(f"Period {min(t1, t2):.2f} is outside the "
                             "allowable range.")
        
        elif all(max(t1, t2) > self.raw_Ts):
            raise ValueError(f"Period {max(t1, t2):.2f} is outside the "
                             "allowable range.")
        
        if t1 == t2:
            return 1.0  # the same period must have a correlation of 1.0
        
        rho = interper(np.array([[t1, t2]]))
        return float(rho[0])
    
    def get_correlation(self, t1, t2):
        """
        Computes the correlation coefficient for the specified periods for the
        total standard deviation
               
        :param float t1:
            First period of interest.

        :param float t2:
            Second period of interest.

        :return float rho:
            The estimated correlation coefficient.
        """
        self._check_valid_residual_type("total")
        interper = self.interpers["total"]
        return self._get_correlation(interper, t1, t2)
        
    def get_between_event_correlation(self, t1, t2):
        """
        As per the get_correlation function but for the between-event
        residuals only. dB_e - using the Al Atik et al. (2010) notation
        """ 
        self._check_valid_residual_type("dB_e")      
        interper = self.interpers["dB_e"]
        return self._get_correlation(interper, t1, t2)

    def get_between_site_correlation(self, t1, t2):
        """
        As per the get_correlation function but for the between-site
        residuals only. dS2S_s - using the Al Atik et al. (2010) notation
        """
        self._check_valid_residual_type("dS2S_s")
        interper = self.interpers["dS2S_s"]
        return self._get_correlation(interper, t1, t2)

    def get_within_event_correlation(self, t1, t2):
        """
        As per the get_correlation function but for the within-event
        residuals only. dWS_es - using the Al Atik et al. (2010) notation
        """
        self._check_valid_residual_type("dWS_es")
        interper = self.interpers["dWS_es"]
        return self._get_correlation(interper, t1, t2)


def load_corr_coeff_data_from_hdf5(fp, group_name):
    """
    Loads an HDF5 group into a dictionary of numpy arrays.
    """
    with h5py.File(fp, "r") as f:
        if group_name not in f:
            raise KeyError(f"Group '{group_name}' not found.")
        
        group = f[group_name]
        
        # Dictionary comprehension: 
        # item[()] loads the dataset into a numpy array
        rho_dict = {
            key: item[()] 
            for key, item in group.items() 
            if isinstance(item, h5py.Dataset)
        }

    periods = rho_dict.pop("periods")
        
    return rho_dict, periods


class ClemettCorrelationModelAsc(EmpiricalAvgSACorrelationModel):
    """
    Correlation model for the active shallow crust regions in Europe
    Clemett and Gündel (2026) - Paper in preparation
    """
    def __init__(self, avg_periods):
        fp = CORR_COEFFS_FOLDER / "clemett_corr_coeffs.hdf5"
        rho_arrays, rho_periods = load_corr_coeff_data_from_hdf5(fp, "asc")
        super().__init__(avg_periods, rho_arrays, rho_periods) 


class ClemettCorrelationModelSInter(EmpiricalAvgSACorrelationModel):
    """
    Correlation model for subduction interface regions in Europe
    Clemett and Gündel (2026) - Paper in preparation
    """
    def __init__(self, avg_periods):
        fp = CORR_COEFFS_FOLDER / "clemett_corr_coeffs.hdf5"
        rho_arrays, rho_periods = load_corr_coeff_data_from_hdf5(fp, "sinter")
        super().__init__(avg_periods, rho_arrays, rho_periods) 


class ClemettCorrelationModelSSlab(EmpiricalAvgSACorrelationModel):
    """
    Correlation model for subduction slab regions in Europe
    Clemett and Gündel (2026) - Paper in preparation
    """
    def __init__(self, avg_periods):
        fp = CORR_COEFFS_FOLDER / "clemett_corr_coeffs.hdf5"
        rho_arrays, rho_periods = load_corr_coeff_data_from_hdf5(fp, "sslab")
        super().__init__(avg_periods, rho_arrays, rho_periods)  


class ClemettCorrelationModelVrancea(EmpiricalAvgSACorrelationModel):
    """
    Correlation model for the Vrancea deep seismicity region in Europe
    Clemett and Gündel (2026) - Paper in preparation
    """
    def __init__(self, avg_periods):
        fp = CORR_COEFFS_FOLDER / "clemett_corr_coeffs.hdf5"
        rho_arrays, rho_periods = load_corr_coeff_data_from_hdf5(fp, "vrancea")
        super().__init__(avg_periods, rho_arrays, rho_periods)  


class AkkarCorrelationModel(BaseAvgSACorrelationModel):
    """
    Read the period-dependent correlation coefficient matrix as in:
    Akkar S., Sandikkaya MA., Ay BO., 2014, Compatible ground-motion
    prediction equations for damping scaling factors and vertical to
    horizontal spectral amplitude ratios for the broader Europe region,
    Bull Earthquake Eng, 12, pp. 517-547.
    """
    periods = [
        0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.11, 0.12, 0.13, 0.14,
        0.15, 0.16, 0.17, 0.18, 0.19, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3,
        0.32, 0.34, 0.36, 0.38, 0.4, 0.42, 0.44, 0.46, 0.48, 0.5, 0.55, 0.6,
        0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.1, 1.2, 1.3, 1.4, 1.5,
        1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4
        ]

    coeff_table = []
    path = os.path.join(
        os.path.dirname(__file__), "corr_coeffs", "akkar_coeff_table.csv")
    with open(path) as f:
        for row in f:
            coeff_table.append(
                [float(col) for col in row.split(',')])

    def build_correlation_matrix(self):
        """
        Constructs the correlation matrix by two-step linear interpolation
        from the correlation table
        """
        irho = np.array(self.coeff_table)
        iper = np.array(self.periods)
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
        periods = np.array(self.periods)
        rho = np.array(self.coeff_table)
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
        d1, d2, d3, d4, d5 = (0.366, 0.105, 0.0099, 0.109, 0.2)
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)


class ESHM20CorrelationModel(BakerJayaramCorrelationModel):
    """
    Variation of the Baker & Jayaram (2007) cross-correlation model with
    coefficients calibrated on European data, and with separate functions
    for correlation in between-event, between-site and within-event residuals.
    """

    def get_correlation(self, t1, t2):
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

    def get_between_event_correlation(self, t1, t2):
        """
        As per the get_correlation function but for the between-event
        residuals only
        """
        d1, d2, d3, d4, d5 = ESHM20_COEFFICIENTS["between-event"]
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)

    def get_between_site_correlation(self, t1, t2):
        """
        As per the get_correlation function but for the between-site
        residuals only
        """
        d1, d2, d3, d4, d5 = ESHM20_COEFFICIENTS["between-site"]
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)

    def get_within_event_correlation(self, t1, t2):
        """
        As per the get_correlation function but for the between-event
        residuals only
        """
        d1, d2, d3, d4, d5 = ESHM20_COEFFICIENTS["within-event"]
        return baker_jayaram_correlation_model_function(d1, d2, d3, d4, d5,
                                                        t1, t2)


CORRELATION_FUNCTION_HANDLES = {
    'baker_jayaram': BakerJayaramCorrelationModel,
    'akkar': AkkarCorrelationModel,
    "eshm20": ESHM20CorrelationModel,
    "clemett_asc": ClemettCorrelationModelAsc,
    "clemett_sinter": ClemettCorrelationModelSInter,
    "clemett_sslab": ClemettCorrelationModelSSlab,
    "clemett_vrancea": ClemettCorrelationModelVrancea,
    'none': DummyCorrelationModel
}
