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
Implements the suite of GMPEs used for the 2018 German National Seismic Hazard
Model of Gruenthal et al. (2018)

"Gruenthal, G., Strometer, D., Bosse, C., Cotton, F. and Bindi, D. (2018)
The probabilistic seismic hazard assessment of Germany - version 2016,
considering the range or epistemic uncertainties and aleatory variability."
Bulletin of Earthquake Engineering, 16(10), 4339-4395

Module Exports :class: `AkkarEtAlRhyp2014LSD`,
                       `AkkarEtAlRhyp2014MSD`,
                       `AkkarEtAlRhyp2014HSD`,
                       `BindiEtAl2014RhypLSD`,
                       `BindiEtAl2014RhypMSD`,
                       `BindiEtAl2014RhypHSD`,
                       `CauzziEtAl2014Rhypo`,
                       `CauzziEtAl2014RhypoLSD`,
                       `CauzziEtAl2014RhypoMSD`,
                       `CauzziEtAl2014RhypoHSD`,
                       `DerrasEtAl2014Rhypo`,
                       `DerrasEtAl2014RhypoLSD`,
                       `DerrasEtAl2014RhypoMSD`,
                       `DerrasEtAl2014RhypoHSD`,
                       `BindiEtAl2017RhypoLSD,
                       `BindiEtAl2017RhypoMSD,
                       `BindiEtAl2017RhypoHSD
"""
import numpy as np
from scipy.constants import g
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.akkar_2014 import AkkarEtAlRhyp2014
from openquake.hazardlib.gsim.bindi_2014 import BindiEtAl2014Rhyp
from openquake.hazardlib.gsim.cauzzi_2014 import CauzziEtAl2014
from openquake.hazardlib.gsim.derras_2014 import DerrasEtAl2014
from openquake.hazardlib.gsim.bindi_2017 import BindiEtAl2017Rhypo


STRESS_DROP_ADJUST = {
    "L": np.log(0.75),
    "M": np.log(1.25),
    "H": np.log(1.5)}


def adjustment_fact(median, branch):
    """
    Applies stress drop adjustment factors from the STRESS_DROP_ADJ dictionary

    :param numpy.ndarray median:
        Median ground motions

    :param str branch:
        Key to indicate the branch
    """
    return median + STRESS_DROP_ADJUST[branch]


class AkkarEtAlRhyp2014LSD(AkkarEtAlRhyp2014):
    """
    Akkar et al. (2014) "Rhypo" model with the "Low" stress drop adjustment
    for Germany
    """
    SD_BRANCH = "L"

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns the adjusted mean and standard deviation
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        return mean + STRESS_DROP_ADJUST[self.SD_BRANCH], stddevs


class AkkarEtAlRhyp2014MSD(AkkarEtAlRhyp2014LSD):
    """
    Akkar et al. (2014) "Rhypo" model with the "Middle" stress drop adjustment
    for Germany
    """
    SD_BRANCH = "M"


class AkkarEtAlRhyp2014HSD(AkkarEtAlRhyp2014LSD):
    """
    Akkar et al. (2014) "Rhypo" model with the "High" stress drop adjustment
    for Germany
    """
    SD_BRANCH = "H"


# Bindi et al 2014
class BindiEtAl2014RhypLSD(BindiEtAl2014Rhyp):
    """
    Bindi et al. (2014) "Rhypo" model with the "Low" stress drop adjustment for
    Germany
    """
    SD_BRANCH = "L"

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns the adjusted mean and standard deviation
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        return mean + STRESS_DROP_ADJUST[self.SD_BRANCH], stddevs


class BindiEtAl2014RhypMSD(BindiEtAl2014RhypLSD):
    """
    Bindi et al. (2014) "Rhypo" model with the "Middle" stress drop adjustment
    for Germany
    """
    SD_BRANCH = "M"


class BindiEtAl2014RhypHSD(BindiEtAl2014RhypLSD):
    """
    Bindi et al. (2014) "Rhypo" model with the "High" stress drop adjustment
    for Germany
    """
    SD_BRANCH = "H"


def rhypo_to_rrup(rhypo, mag):
    """
    Converts hypocentral distance to an equivalent rupture distance
    dependent on the magnitude
    """
    rrup = rhypo - (0.7108 + 2.496E-6 * (mag ** 7.982))
    rrup[rrup < 3.0] = 3.0
    return rrup


def rhypo_to_rjb(rhypo, mag):
    """
    Converts hypocentral distance to an equivalent Joyner-Boore distance
    dependent on the magnitude
    """
    epsilon = rhypo - (4.853 + 1.347E-6 * (mag ** 8.163))
    rjb = np.zeros_like(rhypo)
    idx = epsilon >= 3.
    rjb[idx] = np.sqrt((epsilon[idx] ** 2.) - 9.0)
    rjb[rjb < 0.0] = 0.0
    return rjb


# Cauzzi et al. 2014 - Converted from Rhypo
class CauzziEtAl2014Rhypo(CauzziEtAl2014):
    """
    Implements the Cauzzi et al. (2015) GMPE applying the rhypo to rrup
    adjustment factor adopted for Germany
    """
    REQUIRES_DISTANCES = set(("rhypo", ))

    def _compute_mean(self, C, rup, dists, sites, imt):
        """
        Returns the mean ground motion acceleration and velocity
        """
        # Convert rhypo to rrup
        rrup = rhypo_to_rrup(dists.rhypo, rup.mag)
        mean = (self._get_magnitude_scaling_term(C, rup.mag) +
                self._get_distance_scaling_term(C, rup.mag, rrup) +
                self._get_style_of_faulting_term(C, rup.rake) +
                self._get_site_amplification_term(C, sites.vs30))
        # convert from cm/s**2 to g for SA and from cm/s**2 to g for PGA (PGV
        # is already in cm/s) and also convert from base 10 to base e.
        if isinstance(imt, PGA):
            mean = np.log((10 ** mean) * ((2 * np.pi / 0.01) ** 2) *
                          1e-2 / g)
        elif isinstance(imt, SA):
            mean = np.log((10 ** mean) * ((2 * np.pi / imt.period) ** 2) *
                          1e-2 / g)
        else:
            mean = np.log(10 ** mean)

        return mean


class CauzziEtAl2014RhypoLSD(CauzziEtAl2014Rhypo):
    """
    Cauzzi et al. (2014) model adapted for rhypo, with the "Low" stress
    drop adjustment for Germany
    """
    SD_BRANCH = "L"

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        return mean + STRESS_DROP_ADJUST[self.SD_BRANCH], stddevs


class CauzziEtAl2014RhypoMSD(CauzziEtAl2014RhypoLSD):
    """
    Cauzzi et al. (2014) model adapted for rhypo, with the "Middle" stress
    drop adjustment for Germany
    """
    SD_BRANCH = "M"


class CauzziEtAl2014RhypoHSD(CauzziEtAl2014RhypoLSD):
    """
    Cauzzi et al. (2014) model adapted for rhypo, with the "High" stress drop
    adjustment for Germany
    """
    SD_BRANCH = "H"


# Derras et al 2014
class DerrasEtAl2014Rhypo(DerrasEtAl2014):
    """
    Re-calibration of the Derras et al. (2014) GMPE taking hypocentral
    distance as an input and converting to Rjb
    """
    #: The required distance parameter is hypocentral distance
    REQUIRES_DISTANCES = set(('rhypo', ))

    def get_mean(self, C, rup, sites, dists):
        """
        Returns the mean ground motion in terms of log10 m/s/s, implementing
        equation 2 (page 502)
        """
        # W2 needs to be a 1 by 5 matrix (not a vector
        w_2 = np.array([
            [C["W_21"], C["W_22"], C["W_23"], C["W_24"], C["W_25"]]
            ])
        # Gets the style of faulting dummy variable
        sof = self._get_sof_dummy_variable(rup.rake)
        # Get the normalised coefficients
        p_n = self.get_pn(rup, sites, dists, sof)
        mean = np.zeros_like(dists.rhypo)
        # Need to loop over sites - maybe this can be improved in future?
        # ndenumerate is used to allow for application to 2-D arrays
        for idx, rval in np.ndenumerate(p_n[0]):
            # Place normalised coefficients into a single array
            p_n_i = np.array([rval, p_n[1], p_n[2][idx], p_n[3], p_n[4]])
            # Executes the main ANN model
            mean_i = np.dot(w_2, np.tanh(np.dot(self.W_1, p_n_i) + self.B_1))
            mean[idx] = (0.5 * (mean_i + C["B_2"] + 1.0) *
                         (C["tmax"] - C["tmin"])) + C["tmin"]
        return mean

    def get_pn(self, rup, sites, dists, sof):
        """
        Normalise the input parameters within their upper and lower
        defined range
        """
        # List must be in following order
        p_n = []
        # Rjb
        # Note that Rjb must be clipped at 0.1 km
        rjb = rhypo_to_rjb(dists.rhypo, rup.mag)
        rjb[rjb < 0.1] = 0.1
        p_n.append(self._get_normalised_term(np.log10(rjb),
                                             self.CONSTANTS["logMaxR"],
                                             self.CONSTANTS["logMinR"]))
        # Magnitude
        p_n.append(self._get_normalised_term(rup.mag,
                                             self.CONSTANTS["maxMw"],
                                             self.CONSTANTS["minMw"]))
        # Vs30
        p_n.append(self._get_normalised_term(np.log10(sites.vs30),
                                             self.CONSTANTS["logMaxVs30"],
                                             self.CONSTANTS["logMinVs30"]))
        # Depth
        p_n.append(self._get_normalised_term(rup.hypo_depth,
                                             self.CONSTANTS["maxD"],
                                             self.CONSTANTS["minD"]))
        # Style of Faulting
        p_n.append(self._get_normalised_term(sof,
                                             self.CONSTANTS["maxFM"],
                                             self.CONSTANTS["minFM"]))
        return p_n


class DerrasEtAl2014RhypoLSD(DerrasEtAl2014Rhypo):
    """
    Derras et al. (2014) with Rhypo adjustment plus "Low" stress drop
    adjustment factor for Germany
    """
    SD_BRANCH = "L"

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns the adjusted mean and standard deviation
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        return mean + STRESS_DROP_ADJUST[self.SD_BRANCH], stddevs


class DerrasEtAl2014RhypoMSD(DerrasEtAl2014RhypoLSD):
    """
    Derras et al. (2014) with Rhypo adjustment plus "Middle" stress drop
    adjustment factor for Germany
    """
    SD_BRANCH = "M"


class DerrasEtAl2014RhypoHSD(DerrasEtAl2014RhypoLSD):
    """
    Derras et al. (2014) with Rhypo adjustment plus "High" stress drop
    adjustment factor for Germany
    """
    SD_BRANCH = "H"


# Bindi et al. (2017)
class BindiEtAl2017RhypoLSD(BindiEtAl2017Rhypo):
    """
    Bindi et al. 2017 with "Low" stress drop adjustment factor for Germany
    """
    SD_BRANCH = "L"

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns the adjusted mean and standard deviation
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        return mean + STRESS_DROP_ADJUST[self.SD_BRANCH], stddevs


class BindiEtAl2017RhypoMSD(BindiEtAl2017RhypoLSD):
    """
    Bindi et al. 2017 with "Middle" stress drop adjustment factor for Germany
    """
    SD_BRANCH = "M"


class BindiEtAl2017RhypoHSD(BindiEtAl2017RhypoLSD):
    """
    Bindi et al. 2017 with "High" stress drop adjustment factor for Germany
    """
    SD_BRANCH = "H"
