# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
Module exports :class:`AbrahamsonEtAl2018SInter`
               :class:`AbrahamsonEtAl2018SInterHigh`
               :class:`AbrahamsonEtAl2018SInterLow`
               :class:`AbrahamsonEtAl2018SInterCascadia`
               :class:`AbrahamsonEtAl2018SInterCentralAmerica`
               :class:`AbrahamsonEtAl2018SInterJapan`
               :class:`AbrahamsonEtAl2018SInterNewZealand`
               :class:`AbrahamsonEtAl2018SInterSouthAmerica`
               :class:`AbrahamsonEtAl2018SInterTaiwan`
               :class:`AbrahamsonEtAl2018SSlab`
               :class:`AbrahamsonEtAl2018SSlabHigh`
               :class:`AbrahamsonEtAl2018SSlabLow`
               :class:`AbrahamsonEtAl2018SSlabCascadia`
               :class:`AbrahamsonEtAl2018SSlabCentralAmerica`
               :class:`AbrahamsonEtAl2018SSlabJapan`
               :class:`AbrahamsonEtAl2018SSlabNewZealand`
               :class:`AbrahamsonEtAl2018SSlabSouthAmerica`
               :class:`AbrahamsonEtAl2018SSlabTaiwan`
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


#: Period-dependent epistemic adjustment factors, as defined in Table 4.4
EPISTEMIC_FACTORS = CoeffsTable(sa_damping=5.0, table="""\
    imt     SINTER_LOW   SINTER_HIGH   SSLAB_LOW  SSLAB_HIGH
    pga           -0.3           0.3       -0.50        0.50
    0.010         -0.3           0.3       -0.50        0.50
    0.020         -0.3           0.3       -0.50        0.50
    0.030         -0.3           0.3       -0.50        0.50
    0.050         -0.3           0.3       -0.50        0.50
    0.075         -0.3           0.3       -0.50        0.50
    0.100         -0.3           0.3       -0.50        0.50
    0.150         -0.3           0.3       -0.50        0.50
    0.200         -0.3           0.3       -0.50        0.50
    0.250         -0.3           0.3       -0.46        0.46
    0.300         -0.3           0.3       -0.42        0.42
    0.400         -0.3           0.3       -0.38        0.38
    0.500         -0.3           0.3       -0.34        0.34
    0.600         -0.3           0.3       -0.30        0.30
    0.750         -0.3           0.3       -0.30        0.30
    1.000         -0.3           0.3       -0.30        0.30
    1.500         -0.3           0.3       -0.30        0.30
    2.000         -0.3           0.3       -0.30        0.30
    2.500         -0.3           0.3       -0.30        0.30
    3.000         -0.3           0.3       -0.30        0.30
    4.000         -0.3           0.3       -0.30        0.30
    5.000         -0.3           0.3       -0.30        0.30
    6.000         -0.3           0.3       -0.30        0.30
    7.500         -0.3           0.3       -0.30        0.30
    10.00         -0.3           0.3       -0.30        0.30
    """)


class AbrahamsonEtAl2018SInter(GMPE):
    """
    Implements the 2018 updated Abrahamson et al. (2018) "BC Hydro" GMPE for
    application to subduction earthquakes, for the case of subduction interface
    events.

    Abrahamson, N. A., Keuhn, N., Gulerce, Z., Gregor, N., Bozognia, Y.,
    Parker, G., Stewart, J., Chiou, B., Idriss, I. M., Campbell, K. and
    Youngs, R. (2018) "Update of the BC Hydro Subduction Ground-Motion Model
    using the NGA-Subduction Dataset", Pacific Earthquake Engineering
    Research Center (PEER) Technical Report, PEER 2018/02

    The model is regionalised to provide adjustments for Cascadia, Central
    America, Japan, New Zealand, South America and Taiwan, each of which
    will be implemented in various subclasses. Furthermore, scalar adjustments
    are intended to be applied in order to define an "upper", "central" and
    "lower" branch to cover the epistemic uncertainty of the core model.
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section 4.5
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Site amplification is dependent only upon Vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = set(('rrup',))

    #: A "low" and "high" epistemic adjustment factor will be applied to
    #: subclasses of this model
    EPISTEMIC_ADJUSTMENT = None

    #: Regionally adjusted coefficient for linear site amplification
    VS30_COEFF = "a12"

    #: Regionally adjusted coefficient for anelastic attenuation
    LINEAR_R_COEFF = "a6"

    #: Regionally adjusted coefficient for constant (stress drop) scaling
    SCALAR_CONSTANT = "a1"

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type and for PGA
        C = self.COEFFS[imt]
        C_PGA = self.COEFSS[PGA()]
        # compute median pga on rock (vs30=1000), needed for site response
        # term calculation
        pga1000 = np.exp(self._compute_pga_rock(C_PGA, rup, dists))
        # Get full model
        mean = (self.compute_base_term(C) +
                self.compute_magnitude_term(C, rup.mag) +
                self.compute_depth_term(C, rup) +
                self.compute_distance_term(C, dists.rrup, rup.mag) +
                self.compute_site_term(C, sites.vs30, pga1000))

        stddevs = self.get_stddevs(C, C_PGA, pga1000, sites.vs30, stddev_types)
        if self.EPISTEMIC_ADJUSTMENT:
            return mean + EPISTEMIC_FACTORS[imt][self.EPISTEMIC_ADJUSTMENT],\
                stddevs
        else:
            return mean, stddevs

    def _compute_pga_rock(self, C_PGA, rup, dists):
        """
        Returns the PGA on rock (vs30 = 1000 m / s)
        """
        lpga1000 = (self.compute_base_term(C_PGA) +
                    self.compute_magnitude_term(C_PGA, rup.mag) +
                    self.compute_depth_term(C_PGA, rup) +
                    self.compute_distance_term(C_PGA, dists.rrup, rup.mag))
        # Get linear site term for the case where vs30 = 1000.0
        flin = self._get_linear_site_term(
            C_PGA, (1000.0 * np.ones_like(dists.rrup)) / C_PGA["vlin"])
        return lpga1000 + flin

    def compute_base_term(self, C):
        """
        Returns the base coefficient of the GMPE, which for interface events
        is just the coefficient a1 (adjusted regionally)
        """
        return C[self.SCALAR_CONSTANT]

    def compute_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        f_mag = C["a13"] * ((10.0 - mag) ** 2.)
        if mag <= C["C1inter"]:
            return C["a4"] * (mag - C["C1inter"]) + f_mag
        else:
            # C["a5"] is zero so linear term disappears
            return f_mag

    def compute_distance_term(self, C, rrup, mag):
        """
        Returns the distance attenuation
        """
        scale = self._get_magnitude_scale(self, C, mag)
        fdist = scale * np.log(rrup + self.CONSTANTS["C4"] *
                               np.exp(self.CONSTANTS["a9"] * (mag - 6)))
        return fdist + C[self.LINEAR_R_COEFF] * rrup

    def _get_magnitude_scale(self, C, mag):
        """
        Returns the magnitude scaling term that modifies the distance
        attenuation
        """
        return C["a2"] + self.CONSTANTS["a3"] * (mag - 7.8)

    def compute_depth_term(self, C, rup):
        """
        No top of rupture depth term for interface events
        """
        return 0.0

    def compute_site_term(self, C, vs30, pga1000):
        """
        Returns the site amplification
        """
        vsstar = np.copy(vs30)
        vsstar[vs30 >= 1000.0] = 1000.0
        f_site = np.zeros_like(vs30)
        # Consider the cases of only linear amplification
        idx = vs30 >= C["vlin"]
        if np.any(idx):
            f_site[idx] = self._get_linear_site_term(C, vsstar[idx])
        # Consider now only the nonlinear amplification cases
        idx = np.logical_not(idx)
        if np.any(idx):
            # Linear term
            flin = C[self.VS30_COEFF] * np.log(vsstar[idx] / C["vlin"])
            # Nonlinear term
            fnl = (-C["b"] * np.log(pga1000[idx] + self.CONSTANTS["c"])) +\
                (C["b"] * np.log(pga1000[idx] + self.CONSTANTS["c"] *
                 ((vsstar[idx] / C["vlin"]) ** self.CONSTANTS["n"])))
            f_site[idx] = flin + fnl
        return f_site

    def _get_linear_site_term(self, C, vsstar):
        """
        As the linear site scaling is used for both the pga1000 case and the
        general case the relevant common part is returned here
        """
        return (C[self.VS30_COEFF] + C["b"] * self.CONSTANTS["n"]) *\
            np.log(vsstar / C["vlin"])

    def get_stddevs(self, C, C_PGA, pga1000, vs30, stddev_types):
        """
        Returns the standard deviations
        """
        dln = self._get_dln_amp(C, pga1000, vs30)
        tau = self.get_inter_event_stddev(C, C_PGA, dln)
        phi = self.get_intra_event.stddev(C, C_PGA, dln)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(tau ** 2. + phi ** 2.)
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau)
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi)

        return stddevs

    def _get_dln_amp(self, C, pga1000, vs30):
        """
        Returns the partial deriviative of the amplification term with respect
        to pga1000
        """
        dln = np.zeros(vs30.shape)
        idx = vs30 < C["vlin"]
        if np.any(idx):
            dln[idx] = C["b"] * pga1000[idx] * (
                (1. / (pga1000[idx] + self.CONSTANTS["c"] *
                       ((vs30[idx] / C["vlin"]) ** self.CONSTANTS["n"]))) -
                (1. / (pga1000[idx] + self.CONSTANTS["c"])))
        return dln

    def get_within_event_stddev(self, C, C_PGA, dln):
        """
        Returns the within-event aleatory uncertainty, phi
        """
        phi_amp2 = self.CONSTANTS["phiamp"] ** 2.
        phi_b = np.sqrt(C["phi0"] ** 2. - phi_amp2)
        phi_b_pga = np.sqrt((C_PGA["phi0"] ** 2.) - phi_amp2)

        phi = (C["phi0"] ** 2.) +\
              ((dln ** 2.) * (phi_b ** 2.)) +\
              (2.0 * dln * phi_b * phi_b_pga + C["rho_w"])
        return phi

    def get_inter_event_stddev(self, C, C_PGA, dln):
        """
        Returns the between event aleatory uncertainty, tau
        """
        tau = (C["tau0"] ** 2.) +\
              ((dln ** 2.) + (C["tau0"] ** 2.)) +\
              (2.0 * dln * C["tau0"] * C_PGA["tau0"] * C["rho_b"])
        return tau

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt    C1inter     vlin      b   a1     a2    a4       a6   a10    a11    a12     a13    a14     a18  a19       a20      a21      a22      a23      a25      a26      a27      a28     a29     a30      a32      a33      a34      a35      a36      a37   phi0    tau0    rho_w    rho_b
    pga       8.20    865.1 -1.186  0.0 -0.977  0.59  -0.0069  1.73 0.0170  0.983 -0.0135 -0.223  -0.165  0.0  -0.02491  0.08420 -0.00608  0.00250 -0.00015  0.00624 -0.00130  0.00127 0.00074 0.00684  2.34047  2.56703  3.78779  3.27976  3.41037  2.46418   0.61   0.580   1.0000   1.0000
    0.010     8.20    865.1 -1.186  0.0 -0.977  0.59  -0.0069  1.73 0.0170  0.983 -0.0135 -0.223  -0.165  0.0  -0.02491  0.08420 -0.00608  0.00250 -0.00015  0.00624 -0.00130  0.00127 0.00074 0.00684  2.34047  2.56703  3.78779  3.27976  3.41037  2.46418   0.61   0.580   1.0000   1.0000
    0.020     8.20    865.1 -1.219  0.0 -1.004  0.59  -0.0069  1.73 0.0170  1.033 -0.0135 -0.196  -0.176  0.0  -0.02393  0.08297 -0.01628 -0.00102 -0.00017  0.00579 -0.00126  0.00122 0.00058 0.00690  2.36005  2.74496  3.89949  3.34452  3.57615  2.50739   0.61   0.580   1.0000   1.0000
    0.030     8.20    907.8 -1.273  0.0 -1.072  0.59  -0.0069  1.73 0.0170  1.126 -0.0135 -0.128  -0.205  0.0  -0.01426  0.07465 -0.02928 -0.01508 -0.00024  0.00498 -0.00129  0.00114 0.00043 0.00689  2.38396  3.09984  4.19326  3.48006  3.90414  2.60051   0.61   0.580   0.9910   0.9910
    0.050     8.20   1053.5 -1.346  0.0 -1.070  0.59  -0.0076  1.73 0.0180  1.318 -0.0138 -0.130  -0.311  0.0   0.01712  0.02819 -0.11443 -0.05372  0.00030  0.00387 -0.00142  0.00175 0.00066 0.00743  2.44598  3.56942  4.60231  3.68058  4.10552  2.77795   0.61   0.580   0.9730   0.9730
    0.075     8.20   1085.7 -1.471  0.0 -1.070  0.59  -0.0078  1.73 0.0180  1.536 -0.0142 -0.130  -0.311  0.0   0.07345 -0.02338 -0.22336 -0.10950  0.00022  0.00385 -0.00158  0.00137 0.00047 0.00806  2.75111  3.84502  5.09669  3.98561  4.37051  2.96557   0.61   0.580   0.9520   0.9520
    0.100     8.20   1032.5 -1.624  0.0 -1.070  0.59  -0.0077  1.73 0.0180  1.646 -0.0145 -0.130  -0.189  0.0   0.04569  0.02244 -0.23897 -0.04416 -0.00018  0.00374 -0.00150  0.00128 0.00038 0.00795  3.01943  3.92435  5.17563  4.14252  4.48693  3.17350   0.61   0.580   0.9290   0.9290
    0.150     8.20    877.6 -1.931  0.0 -1.044  0.59  -0.0074  1.73 0.0175  1.826 -0.0153 -0.156   0.023  0.0  -0.06173  0.16274 -0.08147  0.07303 -0.00090  0.00318 -0.00125  0.00121 0.00039 0.00712  3.34867  3.91561  4.90983  4.29695  4.56381  3.39419   0.61   0.560   0.8960   0.8960
    0.200     8.20    748.2 -2.188  0.0 -0.987  0.62  -0.0072  1.73 0.0170  1.998 -0.0162 -0.172   0.084  0.0  -0.11608  0.24588  0.05844  0.13722 -0.00115  0.00522 -0.00118  0.00117 0.00031 0.00633  3.28397  3.56999  4.57610  4.22803  4.42074  3.36936   0.61   0.540   0.8740   0.8740
    0.250     8.20    654.3 -2.381  0.0 -0.943  0.64  -0.0070  1.73 0.0160  2.157 -0.0172 -0.184   0.083  0.0  -0.14311  0.25038  0.16598  0.19024 -0.00135  0.00297 -0.00110  0.00119 0.00069 0.00584  3.21131  3.54675  4.32152  4.06742  4.19103  3.30442   0.61   0.520   0.8560   0.8560
    0.300     8.20    587.1 -2.518  0.0 -0.907  0.66  -0.0068  1.73 0.0152  2.266 -0.0183 -0.194   0.075  0.0  -0.17033  0.22557  0.30539  0.21390 -0.00148  0.00458 -0.00111  0.00075 0.00089 0.00527  3.14548  3.34012  4.11569  3.94372  4.00354  3.27353   0.61   0.505   0.8410   0.8410
    0.400     8.20    503.0 -2.657  0.0 -0.850  0.68  -0.0064  1.73 0.0140  2.360 -0.0206 -0.210   0.055  0.0  -0.14964  0.22564  0.43107  0.21364 -0.00157  0.00238 -0.00081  0.00030 0.00123 0.00526  2.99656  3.23275  3.71588  3.68712  3.60204  3.05169   0.61   0.480   0.8180   0.8180
    0.500     8.20    456.6 -2.669  0.0 -0.805  0.68  -0.0061  1.73 0.0130  2.334 -0.0231 -0.223   0.025  0.0  -0.14396  0.23382  0.37207  0.22926 -0.00160  0.00593 -0.00053  0.00033 0.00147 0.00468  2.83921  2.77113  3.33302  3.36636  3.25965  2.87875   0.61   0.460   0.7830   0.7830
    0.600     8.20    430.3 -2.599  0.0 -0.769  0.68  -0.0058  1.73 0.0122  2.217 -0.0256 -0.233   0.010  0.0  -0.13131  0.20359  0.42748  0.21092 -0.00160  0.00454 -0.00051  0.00037 0.00112 0.00372  2.65827  2.56366  3.02101  3.07634  2.97709  2.74091   0.61   0.450   0.7315   0.7315
    0.750     8.15    410.5 -2.401  0.0 -0.725  0.68  -0.0054  1.73 0.0113  1.941 -0.0296 -0.245   0.008  0.0  -0.14464  0.18918  0.41558  0.17024 -0.00158  0.00153 -0.00050  0.00064 0.00111 0.00315  2.34577  2.27053  2.54275  2.60574  2.49354  2.41281   0.61   0.450   0.6800   0.6800
    1.000     8.10    400.0 -1.955  0.0 -0.668  0.68  -0.0050  1.73 0.0100  1.426 -0.0363 -0.261  -0.024  0.0  -0.13797  0.19002  0.44064  0.14684 -0.00145  0.00119 -0.00062  0.00048 0.00133 0.00304  1.85131  1.80535  1.96780  1.98348  1.80191  1.79956   0.61   0.450   0.6070   0.6070
    1.500     8.05    400.0 -1.025  0.0 -0.587  0.68  -0.0046  1.73 0.0082  0.428 -0.0493 -0.285  -0.099  0.0  -0.11467  0.19708  0.45177  0.08021 -0.00110 -0.00177 -0.00085 -0.00013 0.00085 0.00386  1.21559  1.15301  1.09764  1.12793  0.92657  0.96036   0.61   0.450   0.5004   0.5040
    2.000     8.00    400.0 -0.299  0.0 -0.530  0.68  -0.0044  1.73 0.0070 -0.367 -0.0610 -0.301  -0.120  0.0  -0.08972  0.22238  0.50385  0.04480 -0.00070 -0.00188 -0.00061 -0.00083 0.00084 0.00400  0.64875  0.52206  0.43351  0.54356  0.22999  0.32245   0.61   0.450   0.4301   0.4310
    2.500     7.95    400.0  0.000  0.0 -0.486  0.68  -0.0044  1.73 0.0060 -0.684 -0.0711 -0.313  -0.086  0.0  -0.07967  0.14191  0.55427  0.01689 -0.00025 -0.00393 -0.00072 -0.00065 0.00052 0.00427  0.08221  0.16909 -0.05315  0.00697 -0.25430 -0.19175   0.61   0.450   0.3795   0.3795
    3.000     7.90    400.0  0.000  0.0 -0.450  0.68  -0.0044  1.73 0.0052 -0.650 -0.0798 -0.323  -0.050  0.0  -0.09076  0.12443  0.49341  0.02916  0.00010 -0.00444 -0.00088 -0.00051 0.00051 0.00429 -0.36926 -0.28483 -0.45424 -0.37089 -0.66149 -0.61235   0.61   0.450   0.3280   0.3280
    4.000     7.85    400.0  0.000  0.0 -0.450  0.68  -0.0044  1.73 0.0040 -0.596 -0.0935 -0.282  -0.011  0.0  -0.08185  0.13824  0.43194  0.07460  0.00050 -0.00426 -0.00102 -0.00089 0.00038 0.00349 -1.03439 -0.81049 -0.91168 -0.76054 -1.13209 -1.06280   0.61   0.450   0.2505   0.2550
    5.000     7.80    400.0  0.000  0.0 -0.450  0.73  -0.0044  1.73 0.0030 -0.560 -0.0980 -0.250   0.020  0.0  -0.07657  0.17859  0.40136  0.08530  0.00070  0.00165 -0.00092 -0.00067 0.00030 0.00345 -1.51967 -1.30631 -1.34684 -1.14529 -1.53785 -1.55274   0.61   0.450   0.2000   0.2000
    6.000     7.80    400.0  0.000  0.0 -0.450  0.78  -0.0044  1.73 0.0022 -0.533 -0.0980 -0.250   0.054  0.0  -0.07846  0.15581  0.38239  0.11531  0.00083 -0.00068 -0.00043 -0.00013 0.00018 0.00398 -1.81025 -1.49953 -1.70854 -1.45433 -1.78004 -1.90615   0.61   0.450   0.2000   0.2000
    7.500     7.80    400.0  0.000  0.0 -0.450  0.84  -0.0044  1.73 0.0013 -0.505 -0.0980 -0.250   0.112  0.0  -0.06538  0.15743  0.32560  0.11715  0.00100  0.00016 -0.00028  0.00000 0.00023 0.00400 -2.17269 -1.84146 -2.09138 -1.73678 -2.08041 -2.26977   0.61   0.450   0.2000   0.2000
    10.00     7.80    400.0  0.000  0.0 -0.450  0.93  -0.0044  1.73 0.0000 -0.450 -0.0980 -0.250   0.100  0.0  -0.04203  0.09805  0.28296  0.10171  0.00113  0.00466 -0.00080  0.00032 0.00051 0.00317 -2.71182 -2.39409 -2.43297 -2.30083 -2.47903 -2.73541   0.61   0.450   0.2000   0.2000
    """)

    CONSTS = {"n": 1.18,
              "c": 1.88,
              "C4": 10.0,
              "a3": 0.10,
              "a5": 0.0,
              "a9": 0.4,
              "a10": 1.73,
              "C1slab": 7.2,
              "phiamp": 0.3}


class AbrahamsonEtAl2018SInterHigh(AbrahamsonEtAl2018SInter):
    """
    Abrahamson et al (2018) subduction interface GMPE with the positive
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SINTER_HIGH"


class AbrahamsonEtAl2018SInterLow(AbrahamsonEtAl2018SInter):
    """
    Abrahamson et al (2018) subduction interface GMPE with the negative
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SINTER_LOW"


class AbrahamsonEtAl2018SSlab(AbrahamsonEtAl2018SInter):
    """
    Abrahamson et al. (2018) updated "BC Hydro" subduction GMPE for application
    to subduction in-slab earthquakes.
    """

    #: Required rupture parameters for the in-slab model are magnitude and top
    # of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'ztor'))

    def compute_base_term(self, C):
        """
        The base term has an additional factor applied for the case of in-slab
        eventtd
        """
        return C["a1"] + C["a4"] * (self.CONSTANTS["C1slab"] - C["c1inter"]) +\
            self.CONSTANTS["a10"]

    def compute_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term, this time using the constant
        "C1slab" as the hinge magnitude
        """
        f_mag = C["a13"] * ((10.0 - mag) ** 2.)
        if mag <= self.CONSTANTS["C1slab"]:
            return C["a4"] * (mag - self.CONSTANTS["C1slab"]) + f_mag
        else:
            # parameter "a5" is zero, so linear term disappears
            return f_mag

    def compute_depth_term(self, C, rup):
        """
        Equation on P11
        """
        if rup.ztor <= 100.0:
            return C["a11"] * (rup.ztor - 60.0)
        else:
            return C["a11"] * (60.0 - rup.ztor)


class AbrahamsonEtAl2018SSlabHigh(AbrahamsonEtAl2018SSlab):
    """
    Abrahamson et al (2018) subduction in-slab GMPE with the positive
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SSLAB_HIGH"


class AbrahamsonEtAl2018SSLABLow(AbrahamsonEtAl2018SSlab):
    """
    Abrahamson et al (2018) subduction in-slab GMPE with the negative
    epistemic adjustment factor applied
    """
    EPISTEMIC_ADJUSTMENT = "SSLAB_LOW"


class AbrahamsonEtAl2018SInterCascadia(AbrahamsonEtAl2018SInter):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction interface
    model for application to the Cascadia region
    """
    VS30_COEFF = "a18"
    LINEAR_R_COEFF = "a25"
    SCALAR_CONSTANT = "a32"


class AbrahamsonEtAl2018SInterCentralAmerica(AbrahamsonEtAl2018SInter):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction interface
    model for application to the Cental America region
    """
    VS30_COEFF = "a19"
    LINEAR_R_COEFF = "a26"
    SCALAR_CONSTANT = "a33"


class AbrahamsonEtAl2018SInterJapan(AbrahamsonEtAl2018SInter):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction interface
    model for application to the Japan region
    """
    VS30_COEFF = "a20"
    LINEAR_R_COEFF = "a27"
    SCALAR_CONSTANT = "a34"


class AbrahamsonEtAl2018SInterNewZealand(AbrahamsonEtAl2018SInter):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction interface
    model for application to the New Zealand region
    """
    VS30_COEFF = "a21"
    LINEAR_R_COEFF = "a28"
    SCALAR_CONSTANT = "a35"


class AbrahamsonEtAl2018SInterSouthAmerica(AbrahamsonEtAl2018SInter):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction interface
    model for application to the SouthAmerica region
    """
    VS30_COEFF = "a22"
    LINEAR_R_COEFF = "a29"
    SCALAR_CONSTANT = "a36"


class AbrahamsonEtAl2018SInterTaiwan(AbrahamsonEtAl2018SInter):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction interface
    model for application to the Taiwan region
    """
    VS30_COEFF = "a23"
    LINEAR_R_COEFF = "a30"
    SCALAR_CONSTANT = "a37"


class AbrahamsonEtAl2018SSlabCascadia(AbrahamsonEtAl2018SSlab):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction in-slab
    model for application to the Cascadia region
    """
    VS30_COEFF = "a18"
    LINEAR_R_COEFF = "a25"
    SCALAR_CONSTANT = "a32"


class AbrahamsonEtAl2018SSlabCentralAmerica(AbrahamsonEtAl2018SSlab):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction in-slab
    model for application to the Cental America region
    """
    VS30_COEFF = "a19"
    LINEAR_R_COEFF = "a26"
    SCALAR_CONSTANT = "a33"


class AbrahamsonEtAl2018SSlabJapan(AbrahamsonEtAl2018SSlab):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction in-slab
    model for application to the Japan region
    """
    VS30_COEFF = "a20"
    LINEAR_R_COEFF = "a27"
    SCALAR_CONSTANT = "a34"


class AbrahamsonEtAl2018SSlabNewZealand(AbrahamsonEtAl2018SSlab):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction in-slab
    model for application to the New Zealand region
    """
    VS30_COEFF = "a21"
    LINEAR_R_COEFF = "a28"
    SCALAR_CONSTANT = "a35"


class AbrahamsonEtAl2018SSlabSouthAmerica(AbrahamsonEtAl2018SSlab):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction in-slab
    model for application to the SouthAmerica region
    """
    VS30_COEFF = "a22"
    LINEAR_R_COEFF = "a29"
    SCALAR_CONSTANT = "a36"


class AbrahamsonEtAl2018SSlabTaiwan(AbrahamsonEtAl2018SSlab):
    """
    Calibration of the Abrahamson et al. (2018) "BC Hydro" subduction in-slab
    model for application to the Taiwan region
    """
    VS30_COEFF = "a23"
    LINEAR_R_COEFF = "a30"
    SCALAR_CONSTANT = "a37"
