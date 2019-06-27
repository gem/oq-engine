# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
Module exports :class:`Bradley2013ChchCBD`,
:class:`Bradley2013ChchWest`, :class:`Bradley2013ChchEast`,
:class:`Bradley2013ChchNorth`,
:class:`Bradley2013ChchCBDAdditionalSigma`,
:class:`Bradley2013ChchWestAdditionalSigma`,
:class:`Bradley2013ChchEastAdditionalSigma`,
:class:`Bradley2013ChchNorthAdditionalSigma`.
:class:`Bradley2013ChchMaps`.
:class:`Bradley2013ChchMapsAdditionalSigma`.
"""
import numpy as np
import shapely.geometry
from openquake.hazardlib.gsim.bradley_2013 import (
    Bradley2013LHC, convert_to_LHC)
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA


class Bradley2013bChchCBD(Bradley2013LHC):
    """
    Implements GMPE developed by Brendon Bradley for Christchurch subregions,
    and published as:
    Bradley, B. (2013). "Systematic ground motion observations in the
    Canterbury earthquakes and region-specific nonergodic empirical ground
    motion modelling"" (2013), University of Canterbury Research Report
    2013-03, Department of Civil Engineering, University of Canterbury,
    Christchurch, New Zealand."

    This model was also published as:
    Bradley, B. (2015). Systematic Ground Motion Observations in the Canterbury
    Earthquakes And Region-Specific Non-Ergodic Empirical Ground Motion
    Modeling. Earthquake Spectra: August 2015, Vol. 31, No. 3, pp. 1735-1761.
    but this implementation has been developed from the information in the 2013
    report.

    The original code by the author could not be made available at the time of
    development of this code. For this reason, this implementation is untested
    and marked as non_verified.

    It appears from the model documentation that the dL2L and dS2S terms are
    relative to a baseline Vs30 value of 250 m/s and a baseline Z1 value of
    330 m, although this is unconfirmed.
    """

    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        if isinstance(imt, PGA):
            imt_per = 0.0
        else:
            imt_per = imt.period
        # Fix site parameters for consistent dS2S application.
        sites.vs30 = np.array([250])
        sites.z1pt0 = np.array([330])
        # intensity on a reference soil is used for both mean
        # and stddev calculations.
        ln_y_ref = self._get_ln_y_ref(rup, dists, C)
        # exp1 and exp2 are parts of eq. 7
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))
        # v1 is the period dependent site term. The Vs30 above which, the
        # amplification is constant
        v1 = self._get_v1(imt)
        # Get log-mean from regular unadjusted model
        b13a_mean = self._get_mean(sites, C, ln_y_ref, exp1, exp2, v1)
        # Adjust mean and standard deviation
        mean = b13a_mean + self._get_dL2L(imt_per) + self._get_dS2S(imt_per)
        mean += convert_to_LHC(imt)
        stddevs = self._get_adjusted_stddevs(sites, rup, C, stddev_types,
                                             ln_y_ref, exp1, exp2, imt_per)

        return mean, stddevs

    def _get_adjusted_stddevs(self, sites, rup, C, stddev_types, ln_y_ref,
                              exp1, exp2, imt_per):
        # aftershock flag is zero, we consider only main shock.
        AS = 0
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 19 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 7.0) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 2 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 20
        NL = b * y_ref / (y_ref + c)
        sigma = (
            # first line of eq. 20
            (C['sig1']
             + 0.5 * (C['sig2'] - C['sig1']) * mag_test
             + C['sig4'] * AS)
            # second line
            * np.sqrt((C['sig3'] * Finferred + 0.7 * Fmeasured)
                      + (1 + NL) ** 2)
        )
        # Get sigma reduction factors
        srf_sigma = self._get_SRF_sigma(imt_per)
        srf_phi = self._get_SRF_phi(imt_per)
        srf_tau = self._get_SRF_tau(imt_per)

        # Add 'additional sigma' specified in the Canterbury Seismic
        # Hazard Model to total sigma. This equals zero for the base model.
        additional_sigma = self._compute_additional_sigma()

        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 21
                scaled_sigma = np.sqrt(((1 + NL) ** 2) * (tau ** 2) +
                                       (sigma ** 2)) * srf_sigma
                ret += [np.sqrt(scaled_sigma ** 2 + additional_sigma ** 2)]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                scaled_phi = sigma * srf_phi
                ret.append(np.sqrt(scaled_phi ** 2 +
                                   additional_sigma ** 2 / 2))
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                scaled_tau = (np.abs((1 + NL) * tau)) * srf_tau
                ret.append(np.sqrt(scaled_tau ** 2 +
                                   additional_sigma ** 2 / 2))

        return ret

    def _interp_function(self, y_ip1, y_i, t_ip1, t_i, imt_per):
        """
        Generic interpolation function used in equation 19 of 2013 report.
        """
        return y_i + (y_ip1 - y_i) / (t_ip1 - t_i) * (imt_per - t_i)

    def _get_SRF_tau(self, imt_per):
        """
        Table 6 and equation 19 of 2013 report.
        """
        if imt_per < 1:
            srf = 0.87
        elif 1 <= imt_per < 5:
            srf = self._interp_function(0.58, 0.87, 5, 1, imt_per)
        elif 5 <= imt_per <= 10:
            srf = 0.58
        else:
            srf = 1

        return srf

    def _get_SRF_phi(self, imt_per):
        """
        Table 7 and equation 19 of 2013 report. NB change in notation,
        2013 report calls this term 'sigma' but it is referred to here
        as phi.
        """
        if imt_per < 0.6:
            srf = 0.8
        elif 0.6 <= imt_per < 1:
            srf = self._interp_function(0.7, 0.8, 1, 0.6, imt_per)
        elif 1 <= imt_per <= 10:
            srf = self._interp_function(0.6, 0.7, 10, 1, imt_per)
        else:
            srf = 1

        return srf

    def _get_SRF_sigma(self, imt_per):
        """
        Table 8 and equation 19 of 2013 report. NB change in notation,
        2013 report calls this term 'sigma_t' but it is referred to
        here as sigma. Note that Table 8 is identical to Table 7 in
        the 2013 report.
        """
        if imt_per < 0.6:
            srf = 0.8
        elif 0.6 <= imt_per < 1:
            srf = self._interp_function(0.7, 0.8, 1, 0.6, imt_per)
        elif 1 <= imt_per <= 10:
            srf = self._interp_function(0.6, 0.7, 10, 1, imt_per)
        else:
            srf = 1

        return srf

    def _get_dL2L(self, imt_per):
        """
        Table 3 and equation 19 of 2013 report.
        """
        if imt_per < 0.18:
            dL2L = -0.06
        elif 0.18 <= imt_per < 0.35:
            dL2L = self._interp_function(0.12, -0.06, 0.35, 0.18, imt_per)
        elif 0.35 <= imt_per <= 10:
            dL2L = self._interp_function(0.65, 0.12, 10, 0.35, imt_per)
        else:
            dL2L = 0

        return dL2L

    def _get_dS2S(self, imt_per):
        """
        Table 4 of 2013 report
        """
        if imt_per == 0:
            dS2S = 0.05
        elif 0 < imt_per < 0.15:
            dS2S = self._interp_function(-0.15, 0.05, 0.15, 0, imt_per)
        elif 0.15 <= imt_per < 0.45:
            dS2S = self._interp_function(0.4, -0.15, 0.45, 0.15, imt_per)
        elif 0.45 <= imt_per < 3.2:
            dS2S = 0.4
        elif 3.2 <= imt_per < 5:
            dS2S = self._interp_function(0.08, 0.4, 5, 3.2, imt_per)
        elif 5 <= imt_per <= 10:
            dS2S = 0.08
        else:
            dS2S = 0

        return dS2S

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model. Not applied to
        regular version of the model
        """
        return 0


class Bradley2013bChchWest(Bradley2013bChchCBD):

    """
    Extend :class:`Bradley2013bChchCBD` to implement the 'extended western
    suburbs' dS2S model.
    """

    def _get_dS2S(self, imt_per):
        """
        The parameters of this function have been digitised from Figure 8a
        of the Bradley (2013b) report, as the actual parameters are not
        provided in the report, and could not be provided by the author
        (B. Bradley, pers. comm. 01/02/2019).
        """
        if imt_per == 0:
            dS2S = -0.2
        elif 0 < imt_per < 0.85:
            dS2S = self._interp_function(-0.55, -0.2, 0.85, 0, imt_per)
        elif 0.85 <= imt_per < 1.4:
            dS2S = self._interp_function(-0.18, -0.55, 1.4, 0.85, imt_per)
        elif 1.4 <= imt_per < 3.2:
            dS2S = -0.18
        elif 3.2 <= imt_per < 5:
            dS2S = self._interp_function(0.22, -0.18, 5, 3.2, imt_per)
        elif 5 <= imt_per <= 10:
            dS2S = 0.22
        else:
            dS2S = 0

        return dS2S


class Bradley2013bChchEast(Bradley2013bChchCBD):

    """
    Extend :class:`Bradley2013bChchCBD` to implement the 'eastern
    suburbs' dS2S model.
    """

    def _get_dS2S(self, imt_per):
        """
        The parameters of this function have been digitised from Figure 9a
        of the Bradley (2013b) report, as the actual parameters are not
        provided in the report, and could not be provided by the author
        (B. Bradley, pers. comm. 01/02/2019).
        """
        if 0 <= imt_per <= 0.25:
            dS2S = 0.05
        elif 0.25 < imt_per < 1.5:
            dS2S = self._interp_function(0.15, 0.05, 1.5, 0.25, imt_per)
        elif 1.5 <= imt_per <= 10:
            dS2S = self._interp_function(0.1, 0.15, 10, 1.5, imt_per)
        else:
            dS2S = 0

        return dS2S


class Bradley2013bChchNorth(Bradley2013bChchCBD):

    """
    Extend :class:`Bradley2013bChchCBD` to implement the 'northern
    suburbs' dS2S model.
    """

    def _get_dS2S(self, imt_per):
        """
        The parameters of this function have been digitised from Figure 10a
        of the Bradley (2013b) report, as the actual parameters are not
        provided in the report, and could not be provided by the author
        (B. Bradley, pers. comm. 01/02/2019).
        """
        if imt_per == 0:
            dS2S = -0.31
        elif 0 < imt_per < 0.2:
            dS2S = self._interp_function(-0.4, -0.31, 0.2, 0, imt_per)
        elif 0.2 <= imt_per < 0.6:
            dS2S = self._interp_function(0.2, -0.4, 0.6, 0.2, imt_per)
        elif 0.6 <= imt_per <= 10:
            dS2S = 0.2
        else:
            dS2S = 0

        return dS2S


class Bradley2013bChchCBDAdditionalSigma(Bradley2013bChchCBD):
    """
    Extend :class:`Bradley2013ChchCBD` to implement the 'additional
    epistemic uncertainty' version of the model in:
    Gerstenberger, M., McVerry, G., Rhoades, D., Stirling, M. 2014.
    "Seismic hazard modelling for the recovery of Christchurch",
    Earthquake Spectra, 30(1), 17-29.
    """

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model. The value
        is not published, only available from G. McVerry
        (pers. communication 9/8/18).
        """
        return 0.35


class Bradley2013bChchWestAdditionalSigma(Bradley2013bChchWest):
    """
    Extend :class:`Bradley2013ChchWest` to implement the 'additional
    epistemic uncertainty' version of the model in:
    Gerstenberger, M., McVerry, G., Rhoades, D., Stirling, M. 2014.
    "Seismic hazard modelling for the recovery of Christchurch",
    Earthquake Spectra, 30(1), 17-29.
    """

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model. The value
        is not published, only available from G. McVerry
        (pers. communication 9/8/18).
        """
        return 0.35


class Bradley2013bChchEastAdditionalSigma(Bradley2013bChchEast):
    """
    Extend :class:`Bradley2013ChchEast` to implement the 'additional
    epistemic uncertainty' version of the model in:
    Gerstenberger, M., McVerry, G., Rhoades, D., Stirling, M. 2014.
    "Seismic hazard modelling for the recovery of Christchurch",
    Earthquake Spectra, 30(1), 17-29.
    """

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model. The value
        is not published, only available from G. McVerry
        (pers. communication 9/8/18).
        """
        return 0.35


class Bradley2013bChchNorthAdditionalSigma(Bradley2013bChchNorth):
    """
    Extend :class:`Bradley2013ChchNorth` to implement the 'additional
    epistemic uncertainty' version of the model in:
    Gerstenberger, M., McVerry, G., Rhoades, D., Stirling, M. 2014.
    "Seismic hazard modelling for the recovery of Christchurch",
    Earthquake Spectra, 30(1), 17-29.
    """

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model. The value
        is not published, only available from G. McVerry
        (pers. communication 9/8/18).
        """
        return 0.35


class Bradley2013AdditionalSigma(Bradley2013LHC):
    """
    Extend :class:`Bradley2013LHC` to implement the 'additional
    epistemic uncertainty' version of the model in:
    Gerstenberger, M., McVerry, G., Rhoades, D., Stirling, M. 2014.
    "Seismic hazard modelling for the recovery of Christchurch",
    Earthquake Spectra, 30(1), 17-29.
    """

    def _get_stddevs(self, sites, rup, C, stddev_types, ln_y_ref, exp1, exp2):
        # aftershock flag is zero, we consider only main shock.
        AS = 0
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 19 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 7.0) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 2 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 20
        NL = b * y_ref / (y_ref + c)
        sigma = (
            # first line of eq. 20
                (C['sig1']
                 + 0.5 * (C['sig2'] - C['sig1']) * mag_test
                 + C['sig4'] * AS)
                # second line
                * np.sqrt((C['sig3'] * Finferred + 0.7 * Fmeasured)
                          + (1 + NL) ** 2)
        )

        # Add 'additional sigma' specified in the Canterbury Seismic
        # Hazard Model to total sigma
        additional_sigma = self._compute_additional_sigma()

        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 21
                unscaled_sigma_tot = np.sqrt(((1 + NL) ** 2) * (tau ** 2) +
                                             (sigma ** 2))
                ret += [np.sqrt(unscaled_sigma_tot ** 2 +
                                additional_sigma ** 2)]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                ret.append(np.sqrt(sigma ** 2 +
                                   additional_sigma ** 2 / 2))
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                unscaled_tau = (np.abs((1 + NL) * tau))
                ret.append(np.sqrt(unscaled_tau ** 2 +
                                   additional_sigma ** 2 / 2))

        return ret

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model. The value
        is not published, only available from G. McVerry
        (pers. communication 9/8/18).
        """
        return 0.35


class Bradley2013bChchMaps(Bradley2013bChchCBD):
    """
    Implements GMPE developed by Brendon Bradley for Christchurch subregions,
    and published as ""Systematic ground motion observations in the Canterbury
    earthquakes and region-specific nonergodic empirical ground motion
    modelling"" (2013), University of Canterbury Research Report 2013-03,
    Department of Civil Engineering, University of Canterbury, Christchurch,
    New Zealand.

    The original code by the author was not made available at the time of
    development of this code. For this reason, this implementation is untested.

    It appears from the model documentation that the CBD dL2L and dS2S are
    relative to a baseline Vs30 value of 250 m/s and a baseline Z1 value of
    330 m, although this is unconfirmed.

    Only the CBD subregion dS2S term is implemented here, because of
    difficulties defining the boundaries of other subregions. Full details
    behind the choices here are detailed in:
    Van Houtte and Abbott (2019), "Implementation of the GNS Canterbury
    Seismic Hazard Model in the OpenQuake Engine", Lower Hutt (NZ): GNS
    Science. 38 p. (GNS Science report; 2019/11). doi:10.21420/1AEM-PZ85.
    """
    #: Required site parameters are Vs30 (eq. 13b), Vs30 measured flag (eq. 20)
    #: and Z1.0 (eq. 13b), longitude and latitude.
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'vs30measured', 'z1pt0', 'lon',
                                     'lat'))

    #: This implementation is non-verified because the author of the model does
    #: not have code that can be made available.
    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        if isinstance(imt, PGA):
            imt_per = 0.0
        else:
            imt_per = imt.period
        # Check if any part of source is located within CSHM region
        in_cshm = self._check_in_cshm_polygon(rup)
        # Check if site is located in the CBD polygon
        in_cbd = self._check_in_cbd_polygon(sites.lon, sites.lat)
        # Fix CBD site terms before dS2S modification.
        sites.vs30[in_cbd == True] = 250
        sites.z1pt0[in_cbd == True] = 330
        # intensity on a reference soil is used for both mean
        # and stddev calculations.
        ln_y_ref = self._get_ln_y_ref(rup, dists, C)
        # exp1 and exp2 are parts of eq. 7
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))
        # v1 is the period dependent site term. The Vs30 above which, the
        # amplification is constant
        v1 = self._get_v1(imt)
        # Get log-mean from regular unadjusted model
        b13_mean = self._get_mean(sites, C, ln_y_ref, exp1, exp2, v1)
        # Adjust mean and standard deviation
        mean = self._adjust_mean_model(in_cshm, in_cbd, imt_per, b13_mean)
        mean += convert_to_LHC(imt)
        stddevs = self._get_adjusted_stddevs(sites, rup, C, stddev_types,
                                             ln_y_ref, exp1, exp2, in_cshm,
                                             in_cbd, imt_per)

        return mean, stddevs

    def _get_adjusted_stddevs(self, sites, rup, C, stddev_types, ln_y_ref,
                              exp1, exp2, in_cshm, in_cbd, imt_per):
        # aftershock flag is zero, we consider only main shock.
        AS = 0
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 19 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 7.0) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 2 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 20
        NL = b * y_ref / (y_ref + c)
        sigma = (
            # first line of eq. 20
            (C['sig1']
             + 0.5 * (C['sig2'] - C['sig1']) * mag_test
             + C['sig4'] * AS)
            # second line
            * np.sqrt((C['sig3'] * Finferred + 0.7 * Fmeasured)
                      + (1 + NL) ** 2)
        )
        # Get sigma reduction factors if site is in CBD polygon.
        srf_sigma = np.array(np.ones(np.shape(in_cbd)))
        srf_phi = np.array(np.ones(np.shape(in_cbd)))
        srf_tau = np.array(np.ones(np.shape(in_cbd)))
        if in_cshm is True:
            srf_sigma[in_cbd == True] = self._get_SRF_sigma(imt_per)
            srf_phi[in_cbd == True] = self._get_SRF_phi(imt_per)
            # The tau reduction term is not used in this implementation
            # srf_tau[in_cbd == True] = self._get_SRF_tau(imt_per)

        # Add 'additional sigma' specified in the Canterbury Seismic
        # Hazard Model to total sigma
        additional_sigma = self._compute_additional_sigma()

        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 21
                scaled_sigma = np.sqrt(((1 + NL) ** 2) *
                                       (tau ** 2) + (sigma ** 2)) * srf_sigma
                ret += [np.sqrt(scaled_sigma ** 2 + additional_sigma ** 2)]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                scaled_phi = sigma * srf_phi
                ret.append(np.sqrt(
                    scaled_phi ** 2 + additional_sigma ** 2 / 2))
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                scaled_tau = (np.abs((1 + NL) * tau)) * srf_tau
                ret.append(np.sqrt(
                    scaled_tau ** 2 + additional_sigma ** 2 / 2))

        return ret

    def _adjust_mean_model(self, in_cshm, in_cbd, imt_per, b13_mean):

        dL2L = dS2S = np.array(np.zeros(np.shape(b13_mean)))
        # If the site is in the CBD polygon, get dL2L and dS2S terms
        if in_cshm is True:
            # Only apply the dL2L term only to sites located in the CBD.
            dL2L[in_cbd == True] = self._get_dL2L(imt_per)
            dS2S[in_cbd == True] = self._get_dS2S(imt_per)

        mean = b13_mean + dL2L + dS2S

        return mean

    def _check_in_cbd_polygon(self, lons, lats):
        """
        Checks if site is located within the CBD polygon. The boundaries of
        the polygon implemented here are from the 'Central City' Zoning Map
        in the Christchurch District Plan. See Figure 4.4 of Van Houtte and
        Abbott (2019).
        """
        polygon = shapely.geometry.Polygon(
            [(172.6259, -43.5209), (172.6505, -43.5209),
             (172.6505, -43.5399), (172.6124, -43.5400),
             (172.6123, -43.5289), (172.6124, -43.5245),
             (172.6220, -43.5233)]
        )
        points = [shapely.geometry.Point(lons[ind], lats[ind])
                  for ind in np.arange(len(lons))]
        in_cbd = np.asarray([polygon.contains(point)
                             for point in points])

        return in_cbd

    def _check_in_cshm_polygon(self, rup):
        """
        Checks if any part of the rupture surface mesh is located within the
        intended boundaries of the Canterbury Seismic Hazard Model in
        Gerstenberger et al. (2014), Seismic hazard modelling for the recovery
        of Christchurch, Earthquake Spectra, 30(1), 17-29.
        """
        lats = np.ravel(rup.surface.mesh.array[1])
        lons = np.ravel(rup.surface.mesh.array[0])
        # These coordinates are provided by M Gerstenberger (personal
        # communication, 10 August 2018)
        polygon = shapely.geometry.Polygon([(171.6, -43.3), (173.2, -43.3),
                                            (173.2, -43.9), (171.6, -43.9)])
        points_in_polygon = [
            shapely.geometry.Point(lons[i], lats[i]).within(polygon)
            for i in np.arange(len(lons))
        ]
        in_cshm = any(points_in_polygon)

        return in_cshm


class Bradley2013bChchMapsAdditionalSigma(Bradley2013bChchMaps):
    """
    Extend :class:`Bradley2013ChchNorth` to implement the 'additional
    epistemic uncertainty' version of the model in:
    Gerstenberger, M., McVerry, G., Rhoades, D., Stirling, M. 2014.
    "Seismic hazard modelling for the recovery of Christchurch",
    Earthquake Spectra, 30(1), 17-29.
    """

    def _compute_additional_sigma(self):
        """
        Additional "epistemic" uncertainty version of the model.
        """
        return 0.35
