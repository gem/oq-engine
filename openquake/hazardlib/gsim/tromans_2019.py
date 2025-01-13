# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`TromansEtAl2019`
"""
import numpy as np
from openquake.hazardlib.gsim.base import registry, GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import from_string


#: Coefficient tables as per annex B of Abrahamson et al. (2014)
ASK_TAU_COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT       s3     s4
    pga     0.47   0.36
    pgv     0.38   0.38
    0.010   0.47   0.36
    0.020   0.47   0.36
    0.030   0.47   0.36
    0.050   0.47   0.36
    0.075   0.47   0.36
    0.100   0.47   0.36
    0.150   0.47   0.36
    0.200   0.47   0.36
    0.250   0.47   0.36
    0.300   0.47   0.36
    0.400   0.47   0.36
    0.500   0.47   0.36
    0.750   0.47   0.36
    1.000   0.47   0.36
    1.500   0.47   0.36
    2.000   0.47   0.36
    3.000   0.47   0.36
    4.000   0.47   0.36
    5.000   0.47   0.36
    6.000   0.47   0.36
    7.500   0.47   0.36
    10.00   0.47   0.36
    """)


#: Single station intra-event term for the constant and magnitude-dependent
#: model, as provided in Table 4 of Rodriguez-Marek et al (2013)
PHI_SS_COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT   const_phiss   phi1m  phi2m
    pgv          0.46    0.49   0.37
    pga          0.46    0.49   0.35
    0.01         0.46    0.49   0.35
    0.1          0.45    0.45   0.43
    0.2          0.48    0.51   0.37
    0.3          0.48    0.51   0.37
    0.5          0.46    0.49   0.37
    1.0          0.45    0.46   0.40
    3.0          0.41    0.41   0.41
    """)


#: Single ststion dfS2S model
DELTA_PHI_S2S = CoeffsTable(sa_damping=5, table="""\
    IMT          dfs2s
    pga         0.0000
    0.01000     0.0000
    0.99999     0.0000
    1.00000     0.0001
    2.00000     0.0069
    3.00000     0.0131
    10.0000     0.0131
    """)


def get_heteroskedastic_tau(imt, mag):
    """
    Returns the magnitude dependent inter-event variability using the
    model of Abrahamson et al (2014).

    :param dict C:
        Coefficients dictionary
    :param float mag:
        Magnitude
    """
    C = ASK_TAU_COEFFS[imt]
    tau = C['s3'] + (C['s4'] - C['s3']) / 2. * (mag - 5.)
    tau[mag < 5] = C['s3']
    tau[mag > 7] = C['s4']
    return tau


def get_heteroskedastic_phi(imt, mag):
    """
    Returns the heteroskedastic intra-event term, taken as the maximum
    of the constant single-station phi and the magnitude dependent
    single-station phi provided in Table 4 of Rodriguez-Marek et al (2014)
    """
    C = PHI_SS_COEFFS[imt]
    mag_phi = C["phi1m"] + (C["phi2m"] - C["phi1m"]) * (mag - 5.0) / 2.0
    mag_phi[mag < 5.0] = C["phi1m"]
    mag_phi[mag > 7.0] = C["phi2m"]
    mag_phi[mag_phi <= C["const_phiss"]] = C["const_phiss"]
    return mag_phi


HETEROSKEDASTIC_PHI = {
    "upper": lambda imt, mag: 1.16 * get_heteroskedastic_phi(imt, mag),
    "central": lambda imt, mag: get_heteroskedastic_phi(imt, mag),
    "lower": lambda imt, mag: 0.84 * get_heteroskedastic_phi(imt, mag)}

HOMOSKEDASTIC_PHI = {
    "upper": lambda imt: 1.16 * PHI_SS_COEFFS[imt]["const_phiss"],
    "central": lambda imt: PHI_SS_COEFFS[imt]["const_phiss"],
    "lower": lambda imt: 0.84 * PHI_SS_COEFFS[imt]["const_phiss"]}


HETEROSKEDASTIC_TAU = {
    "upper": lambda imt, mag: get_heteroskedastic_tau(imt, mag) + 0.075,
    "central": lambda imt, mag: get_heteroskedastic_tau(imt, mag),
    "lower": lambda imt, mag: get_heteroskedastic_tau(imt, mag) - 0.075}

SIX = np.array([6.0])
HOMOSKEDASTIC_TAU = {
    "upper": lambda imt: get_heteroskedastic_tau(imt, SIX) + 0.075,
    "central": lambda imt: get_heteroskedastic_tau(imt, SIX),
    "lower": lambda imt: get_heteroskedastic_tau(imt, SIX) - 0.075}


uppernames = '''
DEFINED_FOR_INTENSITY_MEASURE_TYPES
DEFINED_FOR_STANDARD_DEVIATION_TYPES
REQUIRES_SITES_PARAMETERS
REQUIRES_RUPTURE_PARAMETERS
REQUIRES_DISTANCES
'''.split()


def get_alatik_youngs_sigma_mu(mag, rake, imt):
    """
    Implements the statistical uncertainty model of Al Atik & Youngs (2014)
    given in equations 9 to 11 in the manuscript.
    """
    if str(imt) == "PGA":
        period = 0.01
    elif str(imt).startswith("SA"):
        period = imt.period
    else:
        raise ValueError("Al Atik & Youngs (2014) Model not supported "
                         "for %s" % str(imt))
    sigma_mu = np.where(mag >= 7., 0.056 * (mag - 7.0) + 0.083, 0.083)
    if period >= 1.0:
        sigma_mu += 0.0171 * np.log(period)
    # Normal faulting case
    sigma_mu[(rake >= -135.) & (rake <= -45.)] += 0.038
    return sigma_mu


def get_stddevs(branch, phi_ds2s, homoskedastic_sigma, imt, mag):
    """
    Returns the standard deviations as described in Figure 10 and
    section 4 of Tromans et al. (2019).
    """
    if homoskedastic_sigma:
        # Homoskedastic sigma branch
        tau = HOMOSKEDASTIC_TAU[branch](imt)
        phi = HOMOSKEDASTIC_PHI[branch](imt)
    else:
        # Heteroskedastic sigma branch
        tau = HETEROSKEDASTIC_TAU[branch](imt, mag)
        phi = HETEROSKEDASTIC_PHI[branch](imt, mag)
    # Add on the delta phi_d2s
    if phi_ds2s:
        phi = np.sqrt(phi ** 2 + DELTA_PHI_S2S[imt]["dfs2s"] ** 2)
    return [np.sqrt(tau ** 2 + phi ** 2), tau, phi]


class TromansEtAl2019(GMPE):
    """
    Implements a modifiable GMPE to apply the standard deviation model and
    adjustments described in Tromans et al. (2019), for application to
    a nuclear power plant site in the UK:

    Tromans, I. J., Aldama-Bustos, G., Douglas, J., Lessi-Cheimariou, A.,
    Hunt, S., Davi, M., Musson, R. M. W., Garrard, G., Strasser, F. and
    Robertson, C. (2019) "Probabilistic seismic hazard assessment for a
    new-build nuclear power plant site in the UK", Bulletin of Earthquake
    Engineering, 17: 1- 36

    :param gmpe:
        The GMPE for calculation of the medeian ground motion model

    :param string branch:
        The model defines three branches for the different aleatory
        uncertainty models "lower", "central" and "upper"

    :param float scaling_factor:
        Factor to scale the median values of the GMPE to account for, for
        example, stress drop uncertainty

    :param bool homoskedastic sigma:
        Determines whether to use the homoskedastic uncertainty model (True)
        or the heteroskedastic model (False)

    :param vskappa:
        Apply vs-kappa adjustment factors defined using a dictionary organised
        by IMT, or else none.

    :param phi_ds2s:
        Adds the phi_ds2s term to the sigma model (True) or retains the
        single station model
    """
    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude, others will be taken from
    #: the GMPE
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure will be set by the GMPE
    REQUIRES_DISTANCES = set()

    def __init__(self, gmpe_name, branch="central", sigma_mu_epsilon=0.0,
                 homoskedastic_sigma=False,  scaling_factor=None,
                 vskappa=None, phi_ds2s=True):
        self.gmpe = registry[gmpe_name]()
        # Update the required_parameters
        for name in uppernames:
            setattr(self, name,
                    frozenset(getattr(self, name) | getattr(self.gmpe, name)))

        # If the scaling factor take the natural log
        if scaling_factor:
            self.scaling_factor = np.log(scaling_factor)
        else:
            self.scaling_factor = None

        # If vs-kappa is passed as a dictionary then transform to CoeffsTable
        if isinstance(vskappa, dict):
            in_vskappa = {}
            for key in vskappa:
                in_vskappa[from_string(key)] = {"vskappa":
                                                np.log(vskappa[key])}
            self.vskappa = CoeffsTable.fromdict(in_vskappa)
        else:
            self.vskappa = None
        self.branch = branch
        self.sigma_mu_epsilon = sigma_mu_epsilon
        self.homoskedastic_sigma = homoskedastic_sigma
        self.phi_ds2s = phi_ds2s

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations applying, where specified,
        scalar adjustment and vs-kappa adjustment to the mean from the
        original GMPE.
        """
        # Retrieve the mean values from the GMPE
        self.gmpe.compute(ctx, imts, mean, sig, tau, phi)
        # Apply scaling factor
        if self.scaling_factor:
            mean += self.scaling_factor
        for m, imt in enumerate(imts):
            # Apply sigma_mu epsilon factor
            if self.sigma_mu_epsilon:
                mean += (self.sigma_mu_epsilon *
                         get_alatik_youngs_sigma_mu(ctx.mag, ctx.rake, imt))
            # Apply vs-kappa correction
            if self.vskappa:
                mean += self.vskappa[imt]["vskappa"]
            # Get stddevs
            sig[m], tau[m], phi[m] = get_stddevs(
                self.branch, self.phi_ds2s, self.homoskedastic_sigma,
                imt, ctx.mag)


class TromansEtAl2019SigmaMu(TromansEtAl2019):
    """
    Extension of the Tromans et al. (2019) to facilitate the application
    of the statistical uncertainty (sigma_mu) adjustment using the factors
    described by Al Atik & Youngs (2014)

    Al Atik, L. and Youngs, R. R. (2014) "Epistemic Uncertainty for
    NGA-West 2 Models", Earthquake Spectra, 30(3): 1301 - 1318
    """
    #: Required rupture parameters are magnitude and style of faulting, others
    #: will be taken from the GMPE
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}
