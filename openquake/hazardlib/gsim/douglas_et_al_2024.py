# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025 GEM Foundation
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
Module exports  :class:`Douglas_Et_Al_2024Rjb`,
                :class:`Douglas_Et_Al_2024Rjb_3branch`,
                :class:`Douglas_Et_Al_2024Rjb_5branch`,
                :class:`Douglas_Et_Al_2024Rrup`,
                :class:`Douglas_Et_Al_2024Rrup_3branch`,
                :class:`Douglas_Et_Al_2024Rrup_5branch`,
"""
import numpy as np
import pandas as pd
import os

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

# Get the directory of the current script
script_dir = os.path.dirname(__file__)


def _compute_mean(C, mag, dist):
    """
    Compute mean value according to equation in Douglas et al. (2024) Errata.
    """
    mean = (
            C['b1'] +
            _compute_term1(C, mag) +
            _compute_term2(C, mag, dist) +
            _compute_term3(C, dist)
            ) - np.log(9.80665)
    return mean 


def _compute_term1(C, mag):
    """
    This computes the term f1 in Douglas et al. (2024) Errata
    """
    return (C['b2'] * mag) + C['b3'] * (8.5 - mag) ** 2


def _compute_term2(C, mag, dist):
    """
    This computes the term f2 in Douglas et al. (2024) Errata
    """
    c78_factor = (C['b7'] * np.exp(C['b8'] * mag)) ** 2
    R = np.sqrt(dist ** 2 + c78_factor)

    return C['b4'] * np.log(R) + (C['b5'] + C['b6'] * mag) * dist


def _compute_term3(C, dist):
    """
    This computes the term f3 in Douglas et al. (2024) Errata.
    """
    r1 = 50
    r2 = 100

    f3 = np.zeros_like(dist)

    idx_between_50_100 = (dist > r1) & (dist <= r2)
    idx_greater_100 = dist > r2

    f3[idx_between_50_100] = (
            C['b9'] * (np.log(dist[idx_between_50_100]) - np.log(r1))
            )

    f3[idx_greater_100] = (
            C['b9'] * (np.log(dist[idx_greater_100]) - np.log(r1)) +
            C['b10'] * (np.log(dist[idx_greater_100]) - np.log(r2))
            )

    return f3


def _select_coeff_rjb(model, branch, weightopt):
    if model == 162:
        coeffs_path = os.path.join(
            script_dir,
            "Douglas_et_al_2024_COEFFS/Coeffs_162_branch_rjb.csv"
            )
        coeffs_df = pd.read_csv(coeffs_path)
        coeffs_df.columns = coeffs_df.columns.str.strip()
        coeffs_df_branch = coeffs_df[coeffs_df["Branch"] == branch]
    elif model == 5:
        coeffs_path = os.path.join(
            script_dir,
            "Douglas_et_al_2024_COEFFS/Coeffs_5_branch_rjb.csv"
            )
        coeffs_df = pd.read_csv(coeffs_path)
        coeffs_df.columns = coeffs_df.columns.str.strip()
        coeffs_df_branch = coeffs_df[
            (coeffs_df['Weighting Option'] == weightopt) &
            (coeffs_df["Branch"] == branch)
            ]
    elif model == 3:
        coeffs_path = os.path.join(
            script_dir,
            "Douglas_et_al_2024_COEFFS/Coeffs_3_branch_rjb.csv"
            )
        coeffs_df = pd.read_csv(coeffs_path)
        coeffs_df.columns = coeffs_df.columns.str.strip()
        coeffs_df_branch = coeffs_df[
            (coeffs_df['Weighting Option'] == weightopt) &
            (coeffs_df["Branch"] == branch)
            ]

    # Convert the column to object type first
    coeffs_df_branch = coeffs_df_branch.copy()
    coeffs_df_branch['Period'] = coeffs_df_branch['Period'].astype(object)
    # Replace T == 0.01 with 'pga'
    coeffs_df_branch.loc[coeffs_df_branch['Period'] == 0.01, 'Period'] = 'pga'
    # Select only the columns with the period and coefficients
    selected_coeffs = coeffs_df_branch[['Period', 'b1', 'b2', 'b3', 'b4', 'b5',
                                        'b6', 'b7', 'b8', 'b9', 'b10']]

    # Rename 'Period' to 'IMT'
    selected_coeffs = selected_coeffs.rename(columns={'Period': 'IMT'})

    # Convert to a tab-separated string with line breaks
    coeffs_table = selected_coeffs.to_csv(sep='\t', index=False)

    return CoeffsTable(sa_damping=5, table=coeffs_table)

def _select_coeff_rrup(model, branch, weightopt):
    if model == 162:
        coeffs_path = os.path.join(
            script_dir,
            "Douglas_et_al_2024_COEFFS/Coeffs_162_branch_rrup.csv"
            )
        coeffs_df = pd.read_csv(coeffs_path)
        coeffs_df.columns = coeffs_df.columns.str.strip()
        coeffs_df_branch = coeffs_df[coeffs_df["Branch"] == branch]
    elif model == 5:
        coeffs_path = os.path.join(
            script_dir,
            "Douglas_et_al_2024_COEFFS/Coeffs_5_branch_rrup.csv"
            )
        coeffs_df = pd.read_csv(coeffs_path)
        coeffs_df.columns = coeffs_df.columns.str.strip()
        coeffs_df_branch = coeffs_df[
            (coeffs_df['Weighting Option'] == weightopt) &
            (coeffs_df["Branch"] == branch)
            ]
    elif model == 3:
        coeffs_path = os.path.join(
            script_dir,
            "Douglas_et_al_2024_COEFFS/Coeffs_3_branch_rrup.csv"
            )
        coeffs_df = pd.read_csv(coeffs_path)
        coeffs_df.columns = coeffs_df.columns.str.strip()
        coeffs_df_branch = coeffs_df[
            (coeffs_df['Weighting Option'] == weightopt) &
            (coeffs_df["Branch"] == branch)
            ]

    # Convert the column to object type first
    coeffs_df_branch = coeffs_df_branch.copy()
    coeffs_df_branch['Period'] = coeffs_df_branch['Period'].astype(object)
    # Replace T == 0.01 with 'pga'
    coeffs_df_branch.loc[coeffs_df_branch['Period'] == 0.01, 'Period'] = 'pga'
    # Select only the columns with the period and coefficients
    selected_coeffs = coeffs_df_branch[['Period', 'b1', 'b2', 'b3', 'b4', 'b5',
                                        'b6', 'b7', 'b8', 'b9', 'b10']]

    # Rename 'Period' to 'IMT'
    selected_coeffs = selected_coeffs.rename(columns={'Period': 'IMT'})

    # Convert to a tab-separated string with line breaks
    coeffs_table = selected_coeffs.to_csv(sep='\t', index=False)

    return CoeffsTable(sa_damping=5, table=coeffs_table)


def _compute_std(mag, imt):
    # Coefficients for periods not considered by Al Atik (2015) were 
    # interpolated
    sig_coeff_table = """\
        IMT    s1      s2      s3       s4
        pga    0.8435  0.8304  0.7676  0.6744
        0.025  0.8451  0.832  0.7699  0.678
        0.05   0.8772  0.8646  0.8059  0.72
        0.075  0.9094  0.8972  0.8417  0.7611
        0.1    0.9159  0.9039  0.8495  0.771
        0.15   0.8985  0.8862  0.833  0.7562
        0.2    0.8733  0.8606  0.8095  0.7361
        0.3    0.8328  0.8194  0.773  0.7076
        0.4    0.8056  0.7918  0.7503  0.6942
        0.5    0.7863  0.7721  0.7341  0.6851
        0.75   0.7544  0.7396  0.7075  0.671
        1      0.7338  0.7186  0.6892  0.6594
        1.5    0.707  0.6912  0.6645  0.642
        2      0.6903  0.674  0.6485  0.6295
        3      0.6712  0.6544  0.6281  0.6085
        4      0.6617  0.6447  0.6179  0.598
        5      0.6567  0.6395  0.6126  0.5924
        7.5    0.6517  0.6344  0.6073  0.587
        10     0.6502  0.6329  0.6057  0.5853
        """

    Sig_COEFFS = CoeffsTable(sa_damping=5, table=sig_coeff_table)

    # Select coefficient for the given period
    C_sig = Sig_COEFFS[imt]

    stdv = np.zeros(len(mag))

    for mi, m in enumerate(mag):
        if m <= 4.5:
            stdv[mi] = C_sig['s1']
        elif m <= 5.0:
            stdv[mi] = (
                C_sig['s1'] + (C_sig['s2'] - C_sig['s1']) * (m - 4.5) / 0.5
                )
        elif m <= 5.5:
            stdv[mi] = (
                C_sig['s2'] + (C_sig['s3'] - C_sig['s2']) * (m - 5.0) / 0.5
                )
        elif m <= 6.5:
            stdv[mi] = (
                C_sig['s3'] + (C_sig['s4'] - C_sig['s3']) * (m - 5.5) / 0.5
                )
        else:
            stdv[mi] = C_sig['s4']

    return stdv


class Douglas_Et_Al_2024Rjb(GMPE):
    """
    Implements the GMM in Douglas, J., Aldama-Bustos, G., Tallett-Williams, S,.
    Daví, M. and Tromans, I. (2024). 
    "Ground-motion models for earthquakes occurring in the United Kingdom."
    Bull Earthquake Eng 22, 4265–4302. 
    https://doi.org/10.1007/s10518-024-01943-8
    
    This implementation includes corrections in the errata (2024), 
    available at: https://github.com/aldabus/DouglasEtAl_UK_HEM_GMM
    
    Note: Douglas et al. (2024) does not provide a standard deviation. 
    To facilitate its use in PSHA calculations, the central branch of the
    global ergodic model by Al Atkik (2015) is included in this code.
    However, any other aleatory variability model could be combined with the
    Douglas et al. (2024) median model.
    
    :param branch:
        Branch number for the selected model:
        1 to 162 for the 162-branch model
        1 to 5 for the 5-branch model
        1 to 3, for the 3-branch model.
    :param weightopt:
        A string specifying the set of coefficients to use. Admitted values:
        'original': coefficients derived using the a priori branch weights
        'updated': coefficients derived using updated branch weights
        following a Bayesian update using instrumental data.
        Default is 'original'. This parameter is only relevant for the
        5-branch and 3-branch models.
    """

    #: Supported tectonic type is stable continental region as it was developed
    #: for the United Kingdom.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration (PGA is assumed to be equal to SA at 0.01 s)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Douglas et al. (2024) developed only median GMMs. For this script the
    #: central branch of the global ergodic sigma model by Al Atik (2015)
    #: see equation 5.20 and table 5.22 in Al Atik (2015)
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameters are needed
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude, see equation 30 page
    #: 1021.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, see equation
    #: 30 page 1021.
    REQUIRES_DISTANCES = {'rjb'}

    def __init__(self, branch, weightopt="original"):
        self.model = 162
        self.branch = branch
        self.weightopt = weightopt
        self.COEFFS = _select_coeff_rjb(
            self.model, self.branch, self.weightopt
            )

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, ctx.mag, ctx.rjb)
            sig[m] = _compute_std(ctx.mag, imt)

class Douglas_Et_Al_2024Rjb_5branch(Douglas_Et_Al_2024Rjb):

    def __init__(self, branch, weightopt="original"):
        self.model = 5
        self.branch = branch
        self.weightopt = weightopt
        self.COEFFS = _select_coeff_rjb(
            self.model, self.branch, self.weightopt
            )

class Douglas_Et_Al_2024Rjb_3branch(Douglas_Et_Al_2024Rjb):

    def __init__(self, branch, weightopt="original"):
        self.model = 3
        self.branch = branch
        self.weightopt = weightopt
        self.COEFFS = _select_coeff_rjb(
            self.model, self.branch, self.weightopt
            )


class Douglas_Et_Al_2024Rrup(GMPE):
    """
    Implements the GMM in Douglas, J., Aldama-Bustos, G., Tallett-Williams, S,.
    Daví, M. and Tromans, I. (2024). 
    "Ground-motion models for earthquakes occurring in the United Kingdom."
    Bull Earthquake Eng 22, 4265–4302. 
    https://doi.org/10.1007/s10518-024-01943-8
    
    This implementation includes corrections in the errata (2024), 
    available at: https://github.com/aldabus/DouglasEtAl_UK_HEM_GMM
    
    Note: Douglas et al. (2024) does not provide a standard deviation. 
    To facilitate its use in PSHA calculations, the central branch of the
    global ergodic sigma model by Al Atkik (2015) is included in this code.
    However, any other aleatory variability model could be combined with the
    Douglas et al. (2024) median model.
    
    :param branch:
        Branch number for the selected model:
        1 to 162 for the 162-branch model
        1 to 5 for the 5-branch model
        1 to 3, for the 3-branch model.
    :param weightopt:
        A string specifying the set of coefficients to use. Admitted values:
        'original': coefficients derived using the a priori branch weights
        'updated': coefficients derived using updated branch weights
        following a Bayesian update using instrumental data.
        Default is 'original'. This parameter is only relevant for the
        5-branch and 3-branch models.
    """

    #: Supported tectonic type is stable continental region as it was developed
    #: for the United Kingdom.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration (PGA is assumed to be equal to SA at 0.01 s)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Douglas et al. (2024) developed only median GMMs. For this script the
    #: central branch of the global ergodic sigma model by Al Atik (2015)
    #: see equation 5.20 and table 5.22 in Al Atik (2015)
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameters are needed
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude, see equation 30 page
    #: 1021.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, see equation
    #: 30 page 1021.
    REQUIRES_DISTANCES = {'rrup'}

    def __init__(self, branch=1, weightopt="original"):
        self.model = 162
        self.branch = branch
        self.weightopt = weightopt
        self.COEFFS = _select_coeff_rrup(
            self.model, self.branch, self.weightopt
            )

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, ctx.mag, ctx.rrup)
            sig[m] = _compute_std(ctx.mag, imt)

class Douglas_Et_Al_2024Rrup_5branch(Douglas_Et_Al_2024Rrup):

    def __init__(self, branch, weightopt="original"):
        self.model = 5
        self.branch = branch
        self.weightopt = weightopt
        self.COEFFS = _select_coeff_rrup(
            self.model, self.branch, self.weightopt
            )

class Douglas_Et_Al_2024Rrup_3branch(Douglas_Et_Al_2024Rrup):

    def __init__(self, branch, weightopt="original"):
        self.model = 3
        self.branch = branch
        self.weightopt = weightopt
        self.COEFFS = _select_coeff_rrup(
            self.model, self.branch, self.weightopt
            )