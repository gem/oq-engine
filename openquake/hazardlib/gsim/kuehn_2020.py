# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
Module exports :class:`KuehnEtAl2020SInter`,
               :class:`KuehnEtAl2020SInterAlaska`,
               :class:`KuehnEtAl2020SInterCascadia`,
               :class:`KuehnEtAl2020SInterCentralAmericaMexico`,
               :class:`KuehnEtAl2020SInterJapan`,
               :class:`KuehnEtAl2020SInterNewZealand`,
               :class:`KuehnEtAl2020SInterSouthAmerica`,
               :class:`KuehnEtAl2020SInterTaiwan`,
               :class:`KuehnEtAl2020SSlab`,
               :class:`KuehnEtAl2020SSlabAlaska`,
               :class:`KuehnEtAl2020SSlabCascadia`
               :class:`KuehnEtAl2020SSlabCentralAmericaMexico`,
               :class:`KuehnEtAl2020SSlabJapan`,
               :class:`KuehnEtAl2020SSlabNewZealand`,
               :class:`KuehnEtAl2020SSlabSouthAmerica`,
               :class:`KuehnEtAl2020SSlabTaiwan`
"""
import numpy as np
import os
import h5py
from scipy.interpolate import interp1d

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


# Path to the within-model epistemic adjustment tables
BASE_PATH = os.path.join(os.path.dirname(__file__), "kuehn_2020_tables")

# Path to the model coefficients
KUEHN_COEFFS = os.path.join(os.path.dirname(__file__), "kuehn_2020_coeffs.csv")

# Regions: Global (GLO), Alaska (ALU), Cascadia (CAS),
#          Central America & Mexico (CAM), Japan (JPN - ISO 3-letter code),
#          New Zealand (NZL), South America (SAM), Taiwan (TWN)
SUPPORTED_REGIONS = ["GLO", "USA-AK", "CAS", "CAM", "JPN", "NZL", "SAM", "TWN"]

# Define inputs according to 3-letter codes
REGION_TERMS_IF = {
    # Global - to be used in any other subduction region
    "GLO": {
        "c1": "mu_c_1_if",
        "c6": "mu_c_6",
        "c7": "mu_c_7",
        "mb": 7.9,
        "file_unc": "kuehn2020_uncertainty_if_Global.hdf5",
    },
    # Alaska
    "USA-AK": {
        "c1": "c_1_if_reg_Al",
        "c6": "c_6_2_reg_Al",
        "c7": "c_7_reg_Al",
        "mb": 8.6,
        "file_unc": "kuehn2020_uncertainty_if_Alaska.hdf5",
        },
    # Cascadia
    "CAS": {
        "c1": "c_1_if_reg_Ca",
        "c6": "c_6_2_reg_Ca",
        "c7": "c_7_reg_Ca",
        "c11": "c_11_Ca",
        "c12": "c_12_Ca",
        "mb": 8.0,
        "file_unc": "kuehn2020_uncertainty_if_Cascadia.hdf5",
        },
    # Central America and Mexico
    "CAM": {
        "c1": "c_1_if_reg_CAM",
        "c6": "c_6_2_reg_CAM",
        "c7": "c_7_reg_CAM",
        "mb": 7.5,
        "file_unc": "kuehn2020_uncertainty_if_CentralAmericaMexico.hdf5"
        },
    # Japan
    "JPN": {
        "c1": "c_1_if_reg_Ja",
        "c6": "c_6_2_reg_Ja",
        "c7": "c_7_reg_Ja",
        "c11": "c_11_Ja",
        "c12": "c_12_Ja",
        "mb": 8.5,
        "file_unc": "kuehn2020_uncertainty_if_Japan.hdf5",
        },
    # New Zealand
    "NZL": {
        "c1": "c_1_if_reg_NZ",
        "c6": "c_6_2_reg_NZ",
        "c7": "c_7_reg_NZ",
        "c11": "c_11_NZ",
        "c12": "c_12_NZ",
        "mb": 8.3,
        "file_unc": "kuehn2020_uncertainty_if_NewZealand.hdf5",
        },
    # South America
    "SAM": {
        "c1": "c_1_if_reg_SA",
        "c6": "c_6_2_reg_SA",
        "c7": "c_7_reg_SA",
        "mb": 8.6,
        "file_unc": "kuehn2020_uncertainty_if_SouthAmerica.hdf5",
        },
    # Taiwan
    "TWN": {
        "c1": "c_1_if_reg_Tw",
        "c6": "c_6_2_reg_Tw",
        "c7": "c_7_reg_Tw",
        "c11": "c_11_Tw",
        "c12": "c_12_Tw",
        "mb": 7.1,
        "file_unc": "kuehn2020_uncertainty_if_Taiwan.hdf5",
        },
}


# Regional terms for the in-slab events
REGION_TERMS_SLAB = {
    # Global - to be used in any other subduction region
    "GLO": {
        "c1": "mu_c_1_slab",
        "c6": "mu_c_6",
        "c7": "mu_c_7",
        "mb": 7.6,
        "file_unc": "kuehn2020_uncertainty_slab_Global.hdf5",
    },
    # Alaska
    "USA-AK": {
        "c1": "c_1_slab_reg_Al",
        "c6": "c_6_2_reg_Al",
        "c7": "c_7_reg_Al",
        "mb": 7.2,
        "file_unc": "kuehn2020_uncertainty_slab_Alaska.hdf5",
        },
    # Cascadia
    "CAS": {
        "c1": "c_1_slab_reg_Ca",
        "c6": "c_6_2_reg_Ca",
        "c7": "c_7_reg_Ca",
        "c11": "c_11_Ca",
        "c12": "c_12_Ca",
        "mb": 7.2,
        "file_unc": "kuehn2020_uncertainty_slab_Cascadia.hdf5",
        },
    # Central America and Mexico
    "CAM": {
        "c1": "c_1_slab_reg_CAM",
        "c6": "c_6_2_reg_CAM",
        "c7": "c_7_reg_CAM",
        "mb": 7.4,
        "file_unc": "kuehn2020_uncertainty_slab_CentralAmericaMexico.hdf5"
        },
    # Japan
    "JPN": {
        "c1": "c_1_slab_reg_Ja",
        "c6": "c_6_2_reg_Ja",
        "c7": "c_7_reg_Ja",
        "c11": "c_11_Ja",
        "c12": "c_12_Ja",
        "mb": 7.6,
        "file_unc": "kuehn2020_uncertainty_slab_Japan.hdf5",
        },
    # New Zealand
    "NZL": {
        "c1": "c_1_slab_reg_NZ",
        "c6": "c_6_2_reg_NZ",
        "c7": "c_7_reg_NZ",
        "c11": "c_11_NZ",
        "c12": "c_12_NZ",
        "mb": 7.6,
        "file_unc": "kuehn2020_uncertainty_slab_NewZealand.hdf5",
        },
    # South America
    "SAM": {
        "c1": "c_1_slab_reg_SA",
        "c6": "c_6_2_reg_SA",
        "c7": "c_7_reg_SA",
        "mb": 7.3,
        "file_unc": "kuehn2020_uncertainty_slab_SouthAmerica.hdf5",
        },
    # Taiwan
    "TWN": {
        "c1": "c_1_slab_reg_Tw",
        "c6": "c_6_2_reg_Tw",
        "c7": "c_7_reg_Tw",
        "c11": "c_11_Tw",
        "c12": "c_12_Tw",
        "mb": 7.7,
        "file_unc": "kuehn2020_uncertainty_slab_Taiwan.hdf5",
        },
}


# Constants independent of region
CONSTS = {"c_10": 0.0,
          "c": 1.88,
          "n": 1.18,
          "delta_m": 0.1,
          "delta_z": 1,
          "Mref": 6.0,
          "z_ref_if": 15.0,
          "z_ref_slab": 50.0,
          "z_b_if": 30.0,
          "z_b_slab": 80.0}


# Basin depth model parameters for each of the regions for which a
# basin response model is defined
Z_MODEL = {
    "GLO": {"c_z_1": 0.0, "c_z_2": 0.0, "c_z_3": 0.0,  "c_z_4": 0.0},
    "CAS": {
        "c_z_1": 8.294049640102028,
        "c_z_2": 2.302585092994046,
        "c_z_3": 6.396929655216146,
        "c_z_4": 0.27081458999999997,
        },
    "JPN": {
        "c_z_1": 7.689368537500001,
        "c_z_2": 2.302585092994046,
        "c_z_3": 6.309186400000001,
        "c_z_4": 0.7528670225000001,
        },
    "NZL": {
        "c_z_1": 6.859789675000001,
        "c_z_2": 2.302585092994046,
        "c_z_3": 5.745692775,
        "c_z_4": 0.91563524375,
        },
    "TWN": {
        "c_z_1": 6.30560665,
        "c_z_2": 2.302585092994046,
        "c_z_3": 6.1104992125,
        "c_z_4": 0.43671101999999995,
    }
}


def get_base_term(C, trt, region):
    """
    Returns the region-dependent base term (c1) as seen in Equation 4.1

    :param C:
        Coefficient table for the specific intensity measure type

    :param str trt:
        Tectonic region type (either const.TRT.SUBDUCTION_INTERFACE or
        const.TRT.SUBDUCTION_INTRASLAB)

    :param str region:
        Supported region
    """
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        return C[REGION_TERMS_IF[region]["c1"]]
    else:
        return C[REGION_TERMS_SLAB[region]["c1"]]


def get_anelastic_attenuation_term(C, trt, region, rrup):
    """
    Returns the regionalised anelastic attenuation term described in equation
    4.9.

    Note that in the full implementation the anelastic attenuation terms
    for the Japan, Central America & Mexico, and South America regions
    contain multiple coefficients based on path distance through each
    sub-region. This is not yet supported in OpenQuake, so in the present
    case the c6,2 coefficient is adopted for all regions. For the other
    regions (Alaska, Cascadia, New Zealand and Taiwan) this is consistent
    with the preferred implementation suggesting by the authors

    param numpy.ndarray rrup:
        Rupture distance (in km)
    """
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        coeff = C[REGION_TERMS_IF[region]["c6"]]
    else:
        coeff = C[REGION_TERMS_SLAB[region]["c6"]]
    return coeff * rrup


def get_geometric_attenuation_term(C, trt, mag, rrup):
    """
    Returns the geometric attenuation term (Eq. 4.5) (as np.ndarray)

    :param float mag:
        Earthquake magnitude
    """
    c_2 = C["c_2_if"] if trt == const.TRT.SUBDUCTION_INTERFACE else\
        C["c_2_slab"]
    h = 10 ** (C["c_nft_1"] + C["c_nft_2"] * (mag - 6))
    return (c_2 + C["c_3"] * mag) * np.log(rrup + h)


def _log_hinge(x, x0, a, b0, b1, delta):
    """
    Returns the logistic hinge function for the magnitude and source-depth
    terms, as described in Equation 4.3
    """
    xdiff = x - x0
    return a + b0 * xdiff + (b1 - b0) * delta * np.log(1 + np.exp(xdiff /
                                                                  delta))


def get_magnitude_scaling_term(C, trt, mbreak, mag):
    """
    Returns the magnitude scaling term (Eq. 4.4)

    :param float mbreak:
        Magnitude scaling breakpoint
    """
    c_4 = C["c_4_if"] if trt == const.TRT.SUBDUCTION_INTERFACE else\
        C["c_4_slab"]
    ref_m = (mbreak - CONSTS["Mref"])
    return _log_hinge(
        mag, mbreak, c_4 * ref_m, c_4, C["c_5"], CONSTS["delta_m"])


def get_depth_term(C, trt, ztor):
    """
    Returns the Z-tor scaling term (Eq. 4.7)

    :param float ztor:
        Top of rupture depth
    """
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        c_9, dz_b = C["c_9_if"], C["dz_b_if"]
        z_b, zref = CONSTS["z_b_if"], CONSTS["z_ref_if"]
    else:
        c_9, dz_b = C["c_9_slab"], C["dz_b_slab"]
        z_b, zref = CONSTS["z_b_slab"], CONSTS["z_ref_slab"]
    z_break = z_b + dz_b
    ref_z = z_break - zref
    return _log_hinge(ztor, z_break, c_9 * ref_z, c_9,
                      CONSTS["c_10"], CONSTS["delta_z"])


def get_shallow_site_response_term(C, region, vs30, pga1100):
    """
    Returns the shallow site response term in Eq. 4.8

    :param numpy.ndarray vs30:
        Array of Vs30 values (m/s)

    :param numpy ndarray pga1100:
        Peak ground acceletaion on reference rock (Vs30 1100 m/s)
    """
    # c7 is the same for interface or inslab - so just read from interface
    c_7 = C[REGION_TERMS_IF[region]["c7"]]
    # Get linear site term
    vs_mod = vs30 / C["k1"]
    f_site_g = c_7 * np.log(vs_mod)
    idx = vs30 > C["k1"]
    f_site_g[idx] = f_site_g[idx] + (C["k2"] * CONSTS["n"] *
                                     np.log(vs_mod[idx]))

    # Get nonlinear site response term
    idx = np.logical_not(idx)
    if np.any(idx):
        f_site_g[idx] = f_site_g[idx] + C["k2"] * (
                np.log(pga1100[idx] +
                       CONSTS["c"] * (vs_mod[idx] ** CONSTS["n"])) -
                np.log(pga1100[idx] + CONSTS["c"])
        )
    return f_site_g


def _get_ln_z_ref(CZ, vs30):
    """
    Computes the reference Z (1.0/2.5) value from Vs30 (Eq. 4.11)

    :param dict CZ:
        Region-specific basin depth model scaling factors
    """
    diff = (np.log(vs30) - CZ["c_z_3"]) / CZ["c_z_4"]
    ln_z_ref = CZ["c_z_1"] + (CZ["c_z_2"] - CZ["c_z_1"]) *\
        np.exp(diff) / (1 + np.exp(diff))
    return ln_z_ref


def get_basin_response_term(C, region, vs30, z_value):
    """
    Returns the basin response term, based on the region and the depth
    to a given velocity layer

    :param numpy.ndarray z_value:
        Basin depth term (Z2.5 for JPN and CAS, Z1.0 for NZL and TWN)
    """
    # Basin term only defined for the four regions: Cascadia, Japan,
    # New Zealand and Taiwan
    assert region in ("CAS", "JPN", "NZL", "TWN")
    # Get c11, c12 and Z-model (same for both interface and inslab events)
    c11 = C[REGION_TERMS_IF[region]["c11"]]
    c12 = C[REGION_TERMS_IF[region]["c12"]]
    CZ = Z_MODEL[region]

    brt = np.zeros_like(z_value)
    mask = z_value > 0.0
    if not np.any(mask):
        # No basin amplification to be applied
        return 0.0
    brt[mask] = c11 + c12 * (np.log(z_value[mask]) -
                             _get_ln_z_ref(CZ, vs30[mask]))
    return brt


def get_mean_values(C, region, trt, m_b, sites, rup, dists, a1100=None):
    """
    Returns the mean ground values for a specific IMT

    :param float m_b:
        Magnitude scaling breakpoint
    """
    if a1100 is None:
        # Refers to the reference rock case - so Vs30 is 1100 and no a1100
        # is defined
        vs30 = 1100.0 * np.ones(sites.vs30.shape)
        a1100 = np.zeros(vs30.shape)
        z_values = np.zeros(vs30.shape)
    else:
        vs30 = sites.vs30.copy()
        if region in ("JPN", "CAS"):
            z_values = sites.z2pt5 * 1000.0
        elif region in ("NZL", "TWN"):
            z_values = sites.z1pt0.copy()
        else:
            z_values = np.zeros(vs30.shape)
    # Get the mean ground motions
    mean = (get_base_term(C, trt, region) +
            get_magnitude_scaling_term(C, trt, m_b, rup.mag) +
            get_geometric_attenuation_term(C, trt, rup.mag, dists.rrup) +
            get_anelastic_attenuation_term(C, trt, region, dists.rrup) +
            get_depth_term(C, trt, rup.ztor) +
            get_shallow_site_response_term(C, region, vs30, a1100))

    # For Cascadia, Japan, New Zealand and Taiwan a basin depth term
    # is included
    if region in ("CAS", "JPN"):
        # For Cascadia and Japan Z2.5 is used as the basin parameter (in m
        # rather than km)
        mean += get_basin_response_term(C, region, vs30, z_values)
    elif region in ("NZL", "TWN"):
        # For New Zealand and Taiwan Z1.0 (m) is used as the basin parameter
        mean += get_basin_response_term(C, region, vs30, z_values)
    else:
        pass
    return mean


def _retrieve_sigma_mu_data(trt, region):
    """
    Extracts the within-model epistemic uncertainty (sigma_mu) from the hdf5
    file corresponding to the specific tectonic region type and region

    :param str trt:
        Tectonic region type (must be either const.TRT.SUBDUCTION_INTERFACE or
        const.TRT.SUBDUCTION_INTRASLAB
    :param str region:
        Name of region (of those supported by the GMPE)

    :returns:
        Dictionary of magnitudes, distance, periods and sigma_mu values for
        the supported imts
    """
    fname = REGION_TERMS_IF[region]["file_unc"] if\
        trt == const.TRT.SUBDUCTION_INTERFACE else \
        REGION_TERMS_SLAB[region]["file_unc"]
    fle = h5py.File(os.path.join(BASE_PATH, fname), "r")
    sigma_mu = {
        "M": fle["M"][:],
        "R": fle["R"][:],
        "periods": fle["T"][:],
        "PGA":  fle["PGA"][:],
        "PGV": fle["PGV"][:],
        "SA": fle["SA"][:],
    }
    fle.close()
    return sigma_mu


def get_sigma_mu_adjustment(model, imt, rup, dists):
    """
    Returns the sigma mu adjustment factor for the given scenario set by
    interpolation from the tables

    :param dict model:
        Sigma mu model as a dictionary containing the sigma mu tables
        (as output from _retrieve_sigma_mu_data)
    :param imt:
        Intensity measure type
    :param rup:
        Rupture properties
    :param dists:
        Distance properties

    :returns:
        sigma_mu for the scenarios (numpy.ndarray)
    """
    if not model:
        return 0.0
    if imt.string in "PGA PGV":
        # PGA and PGV are 2D arrays of dimension [nmags, ndists]
        sigma_mu = model[imt.string]
        if rup.mag <= model["M"][0]:
            sigma_mu_m = sigma_mu[0, :]
        elif rup.mag >= model["M"][-1]:
            sigma_mu_m = sigma_mu[-1, :]
        else:
            intpl1 = interp1d(model["M"], sigma_mu, axis=0)
            sigma_mu_m = intpl1(rup.mag)
        # Linear interpolation with distance
        intpl2 = interp1d(model["R"], sigma_mu_m, bounds_error=False,
                          fill_value=(sigma_mu_m[0], sigma_mu_m[-1]))
        return intpl2(dists.rrup)
    # In the case of SA the array is of dimension [nmags, ndists, nperiods]
    # Get values for given magnitude
    if rup.mag <= model["M"][0]:
        sigma_mu_m = model["SA"][0, :, :]
    elif rup.mag >= model["M"][-1]:
        sigma_mu_m = model["SA"][-1, :, :]
    else:
        intpl1 = interp1d(model["M"], model["SA"], axis=0)
        sigma_mu_m = intpl1(rup.mag)
    # Get values for period - N.B. ln T, linear sigma mu interpolation
    if imt.period <= model["periods"][0]:
        sigma_mu_t = sigma_mu_m[:, 0]
    elif imt.period >= model["periods"][-1]:
        sigma_mu_t = sigma_mu_m[:, -1]
    else:
        intpl2 = interp1d(np.log(model["periods"]), sigma_mu_m, axis=1)
        sigma_mu_t = intpl2(np.log(imt.period))
    intpl3 = interp1d(model["R"], sigma_mu_t, bounds_error=False,
                      fill_value=(sigma_mu_t[0], sigma_mu_t[-1]))
    return intpl3(dists.rrup)


class KuehnEtAl2020SInter(GMPE):
    """
    Implements the NGA Subduction model of Kuehn et al. (2020)
    for subduction interface events.

    Kuehn N, Bozorgnia Y, Campbell KW ad Gregor N (2021) "Partially Non-Ergodic
    Ground-Motion Model for Subduction Regions using the NGA-Subduction
    Database", PEER Technical Report 2020/04, Pacific Earthquake Engineering
    Research Center (PEER)

    The GMM define a "global" model as well as a set of region-specific
    coefficients (and in some cases methods). The coefficients are defined for
    seven specific subduction regions (with their region codes):

    - Alaska (USA-AK)
    - Cascadia (CAS)
    - Central America & Mexico (CAM)
    - Japan (JPM)
    - New Zealand (NZL)
    - South America (SAM)
    - Taiwan (TWN)

    In the original model defined by the authors, three of the regions
    (JPN, CAM, SAM) define a forearc/backarc dependent anelastic attenuation
    term. To implement this one needs to define the travel distance through
    each of the attenuation subregions. As of July 2021 this property is not
    supported by the OQ-engine, so on the author's guidance a fixed anelastic
    attenuation term is used in these regions

    For four of the regions (JPN, CAS, NZL, TWN) a basin response term is
    defined. In these cases either Z2.5 (JPN, CAS) or Z1.0 (NZL, TWN) must be
    specified.

    Two forms of configurable epistemic uncertainty adjustments are supported:

    m_b: The magnitude scaling breakpoint. This term is defined for each region
         and tectonic region type, but this can also be over-ridden by the user

    sigma_mu_epsilon: Within-model epistemic uncertainty (sigma_mu) is
                      described in Chapter 6 of the report by the authors. This
                      uncertainty is region specific and is described by a
                      magnitude- and distance-dependent standard deviation.
                      The term "sigma_mu_epsilon" defines the number of
                      standard deviations above or below the median by which
                      to scale the mean ground motion within a backbone
                      logic tree context. The scenario and period specific
                      sigma_mu values are read in from hdf5 binary files and
                      interpolated to the magnitude and distances required
    """
    experimental = True

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section "Aleatory Variability Model", page 1094.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', }

    #: Required rupture parameters are magnitude and depth-to-top-of-rupture
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = {'rrup', }

    #: Defined for a reference velocity of 1100 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 1100.0

    def __init__(self, region="GLO", m_b=None, sigma_mu_epsilon=0.0, **kwargs):
        super().__init__(**kwargs)
        # Check that if a region is input that it is one of the ones
        # supported by the model
        assert region in SUPPORTED_REGIONS, "Region %s not defined for %s" %\
            (region, self.__class__.__name__)
        self.region = region

        # For some regions a basin depth term is defined
        if self.region in ("CAS", "JAP"):
            # If region is CAS or JAP then the GMPE needs Z2.5
            self.REQUIRES_SITES_PARAMETERS = \
                 self.REQUIRES_SITES_PARAMETERS.union({"z2pt5", })
        elif self.region in ("NZL", "TWN"):
            # If region is NZL or TWN then the GMPE needs Z1.0
            self.REQUIRES_SITES_PARAMETERS = \
                 self.REQUIRES_SITES_PARAMETERS.union({"z1pt0", })
        else:
            pass

        self.m_b = m_b
        # epsilon for epistemic uncertainty
        self.sigma_mu_epsilon = sigma_mu_epsilon
        if self.sigma_mu_epsilon:
            self.sigma_mu_model = _retrieve_sigma_mu_data(
                self.DEFINED_FOR_TECTONIC_REGION_TYPE, self.region)
        else:
            self.sigma_mu_model = {}

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        if self.m_b:
            # Take the user define magnitude scaling breakpoint
            m_b = self.m_b
        else:
            # Take the global m_b for the tectonic region type and region
            m_b = REGION_TERMS_IF[self.region]["mb"] \
                if trt == const.TRT.SUBDUCTION_INTERFACE else \
                REGION_TERMS_SLAB[self.region]["mb"]
        C_PGA = self.COEFFS[PGA()]

        # Get PGA on rock
        pga1100 = np.exp(get_mean_values(C_PGA, self.region, trt, m_b,
                                         ctx, ctx, ctx, None))
        # For PGA and SA ( T <= 0.1 ) we need to define PGA on soil to
        # ensure that SA ( T ) does not fall below PGA on soil
        pga_soil = None
        for imt in imts:
            if ("PGA" in imt.string) or (("SA" in imt.string) and
                                         (imt.period <= 0.1)):
                pga_soil = get_mean_values(C_PGA, self.region, trt, m_b,
                                           ctx, ctx, ctx, pga1100)
                break

        for m, imt in enumerate(imts):
            # Get coefficinets for imt
            C = self.COEFFS[imt]
            m_break = m_b + C["dm_b"] if trt == const.TRT.SUBDUCTION_INTERFACE\
                else m_b

            if imt.string == "PGA":
                mean[m] = pga_soil
            elif ("SA" in imt.string) and (imt.period <= 0.1):
                # If Sa (T) < PGA for T <= 0.1 then set mean Sa(T) to mean PGA
                mean[m] = get_mean_values(C, self.region, trt, m_break,
                                          ctx, ctx, ctx, pga1100)
                idx = mean[m] < pga_soil
                mean[m][idx] = pga_soil[idx]
            else:
                # For PGV and Sa (T > 0.1 s)
                mean[m] = get_mean_values(C, self.region, trt, m_break,
                                          ctx, ctx, ctx, pga1100)
            # Apply the sigma mu adjustment if necessary
            if self.sigma_mu_epsilon:
                sigma_mu_adjust = get_sigma_mu_adjustment(self.sigma_mu_model,
                                                          imt, ctx, ctx)
                mean[m] += (self.sigma_mu_epsilon * sigma_mu_adjust)
            # Get standard deviations
            tau[m] = C["tau"]
            phi[m] = C["phi"]
            sig[m] = np.sqrt(C["tau"] ** 2.0 + C["phi"] ** 2.0)

    # Coefficients in external file - supplied directly by the author
    COEFFS = CoeffsTable(sa_damping=5, table=open(KUEHN_COEFFS).read())


class KuehnEtAl2020SSlab(KuehnEtAl2020SInter):
    """
    Implements NGA Subduction model of Kuehn et al. (2020) for Intraslab events

    This class implements the global model.
    Adjustments with respect to the interface model are:

    - different constant
    - different magnitude scaling coefficent
    - different geometrical spreading coefficient
    - no magnitude break adjustment at long periods
    - different depth scaling and adjustment to break point
    - different depth centering and break point
    - different default magnitude break point
    """

    #: Supported tectonic region type is subduction in-slab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB


# For the aliases use the verbose form of the region name
REGION_ALIASES = {
    "GLO": "",
    "USA-AK": "Alaska",
    "CAS": "Cascadia",
    "CAM": "CentralAmericaMexico",
    "JPN": "Japan",
    "NZL": "NewZealand",
    "SAM": "SouthAmerica",
    "TWN": "Taiwan",
}


for region in SUPPORTED_REGIONS[1:]:
    add_alias("KuehnEtAl2021SInter" + REGION_ALIASES[region],
              KuehnEtAl2020SInter, region=region)
