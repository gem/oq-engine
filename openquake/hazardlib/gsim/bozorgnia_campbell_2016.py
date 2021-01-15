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
Module exports :class:`BozorgniaCampbell2016`
               :class:`BozorgniaCampbell2016HighQ`
               :class:`BozorgniaCampbell2016LowQ`
               :class:`BozorgniaCampbell2016AveQJapanSite`
               :class:`BozorgniaCampbell2016HighQJapanSite`
               :class:`BozorgniaCampbell2016LowQJapanSite`
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import \
                                          CampbellBozorgnia2014 as CB14
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class BozorgniaCampbell2016(GMPE):
    """
    Implements the BC15 GMPE by Bozorgnia & Campbell (2016) for
    vertical-component ground motions from the PEER NGA-West2 Project

    This model follows the same functional form as in CB14 by
    Campbell & Bozorgnia (2014) with minor modifications to the underlying
    parameters.

    Note that this is a more updated version than the GMPE described in the
    original PEER Report 2013/24.

    **Reference:**

    Bozorgnia, Y. & Campbell, K. (2016). Vertical Ground Motion Model for PGA,
    PGV, and Linear Response Spectra Using the NGA-West2 Database.
    *Earthquake Spectra*, 32(2), 979-1004.

    Implements the global model that uses datasets from California, Taiwan,
    the Middle East, and other similar active tectonic regions to represent
    a typical or average Q region.

    Applies the average attenuation case (Dc20=0)
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the
    #: :attr:`~openquake.hazardlib.const.IMC.Vertical` direction component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total; see the section for "Aleatory Variability Model".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters are Vs30, Vs30 type (measured or inferred),
    #: and depth (km) to the 2.5 km/s shear wave velocity layer (z2pt5)
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z2pt5'}

    #: Required rupture parameters are magnitude, rake, dip, ztor, rupture
    #: width and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = {
        'mag', 'rake', 'dip', 'ztor', 'width', 'hypo_depth'}

    #: Required distance measures are Rrup, Rjb and Rx
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Extract dictionary of coefficients specific to required IMT and PGA
        C = self.COEFFS[imt]
        C_PGA = self.COEFFS[PGA()]
        # Get mean and standard deviations for IMT
        mean = self.get_mean_values(C, sites, rup, dists)
        if imt.name == "SA" and imt.period < 0.25:
            # If Sa (T) < PGA for T < 0.25 then set mean Sa(T) to mean PGA
            # Get PGA on given sites
            pga = self.get_mean_values(C_PGA, sites, rup, dists)
            idx = mean < pga
            mean[idx] = pga[idx]
        # Get standard deviations
        stddevs = self._get_stddevs(C, rup, sites, stddev_types)
        return mean, stddevs

    def get_mean_values(self, C, sites, rup, dists):
        """
        Returns the mean values for a specific IMT
        """
        if isinstance(sites.z2pt5, np.ndarray):
            # Site model defined
            temp_z2pt5 = sites.z2pt5
        else:
            # Estimate unspecified sediment depth according to
            # equations 33 and 34 of CB14
            temp_z2pt5 = self._select_basin_model(sites.vs30)

        return (self._get_magnitude_term(C, rup.mag) +
                self._get_geometric_attenuation_term(C, rup.mag, dists.rrup) +
                self._get_style_of_faulting_term(C, rup) +
                self._get_hanging_wall_term(C, rup, dists) +
                self._get_shallow_site_response_term(C, sites.vs30) +
                self._get_basin_response_term(C, temp_z2pt5) +
                self._get_hypocentral_depth_term(C, rup) +
                self._get_fault_dip_term(C, rup) +
                self._get_anelastic_attenuation_term(C, dists.rrup))

    def _get_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term, f_mag, defined in equation 2
        """
        return CB14._get_magnitude_term(self, C, mag)

    def _get_geometric_attenuation_term(self, C, mag, rrup):
        """
        Returns the geometric attenuation term, f_dis, defined in equation 3
        """
        return CB14._get_geometric_attenuation_term(self, C, mag, rrup)

    def _get_style_of_faulting_term(self, C, rup):
        """
        Returns the style-of-faulting scaling term, f_flt, defined in
        equations 4 to 6
        """
        if (rup.rake > 30.0) and (rup.rake < 150.):
            frv = 1.0
            fnm = 0.0
        elif (rup.rake > -150.0) and (rup.rake < -30.0):
            fnm = 1.0
            frv = 0.0
        else:
            fnm = 0.0
            frv = 0.0
        # Re-defined this method to replace c8, which is now
        # IMT-dependent in BC15
        fflt_f = (C["c8"] * frv) + (C["c9"] * fnm)
        if rup.mag <= 4.5:
            fflt_m = 0.0
        elif rup.mag > 5.5:
            fflt_m = 1.0
        else:
            fflt_m = rup.mag - 4.5
        return fflt_f * fflt_m

    def _get_hanging_wall_term(self, C, rup, dists):
        """
        Returns the hanging wall scaling term, f_hng, defined in equation 7
        """
        return CB14._get_hanging_wall_term(self, C, rup, dists)

    def _get_hanging_wall_coeffs_rx(self, C, rup, r_x):
        """
        Returns the hanging wall r-x scaling term, f_hng_Rx defined in
        equation 8
        """
        return CB14._get_hanging_wall_coeffs_rx(self, C, rup, r_x)

    def _get_f1rx(self, C, r_x, r_1):
        """
        Defines the f1 scaling coefficient defined in equation 9
        """
        return CB14._get_f1rx(self, C, r_x, r_1)

    def _get_f2rx(self, C, r_x, r_1, r_2):
        """
        Defines the f2 scaling coefficient defined in equation 10
        """
        return CB14._get_f2rx(self, C, r_x, r_1, r_2)

    def _get_hanging_wall_coeffs_rrup(self, dists):
        """
        Returns the hanging wall rrup term, f_hng_Rrup, defined in equation 13
        """
        return CB14._get_hanging_wall_coeffs_rrup(self, dists)

    def _get_hanging_wall_coeffs_mag(self, C, mag):
        """
        Returns the hanging wall magnitude term, f_hng_M defined in equation 14
        """
        return CB14._get_hanging_wall_coeffs_mag(self, C, mag)

    def _get_hanging_wall_coeffs_ztor(self, ztor):
        """
        Returns the hanging wall ztor term, f_hng_Z, defined in equation 15
        """
        return CB14._get_hanging_wall_coeffs_ztor(self, ztor)

    def _get_hanging_wall_coeffs_dip(self, dip):
        """
        Returns the hanging wall dip term, f_hng_delta, defined in equation 16
        """
        return CB14._get_hanging_wall_coeffs_dip(self, dip)

    def _get_shallow_site_response_term(self, C, vs30):
        """
        Returns the shallow site response term, f_site, defined in
        equations 17, 18, and 19

        Note that the effects of nonlinear soil response for the vertical
        component were not included in this model
        """
        vs_mod = vs30 / C["k1"]
        # Get linear global site response term
        f_site_g = C["c11"] * np.log(vs_mod)

        # For Japan sites (SJ = 1) further scaling is needed (equation 19)
        if self.CONSTS["SJ"]:
            fsite_j = C["c13"] * np.log(vs_mod)
            # additional term activated for soft sites (Vs30 <= 200m/s)
            # in Japan data
            idx = vs30 <= 200.0
            add_soft = C["c12"] * (np.log(vs_mod) - np.log(200.0 / C["k1"]))
            # combine terms
            fsite_j[idx] += add_soft[idx]
            return f_site_g + fsite_j
        else:
            return f_site_g

    def _select_basin_model(self, vs30):
        """
        Select the preferred basin model (California or Japan) to scale
        basin depth with respect to Vs30
        """
        return CB14._select_basin_model(self, vs30)

    def _get_basin_response_term(self, C, z2pt5):
        """
        Returns the basin response term, f_sed, defined in equation 20

        The deep basin response (z2.5 > 1km) is not included in this model
        """
        f_sed = np.zeros(len(z2pt5))
        idx = z2pt5 < 1.0
        f_sed[idx] = (C["c14"] + C["c15"] * float(self.CONSTS["SJ"])) *\
                     (z2pt5[idx] - 1.0)
        return f_sed

    def _get_hypocentral_depth_term(self, C, rup):
        """
        Returns the hypocentral depth scaling term, f_hyp, defined in
        equations 21 to 23
        """
        return CB14._get_hypocentral_depth_term(self, C, rup)

    def _get_fault_dip_term(self, C, rup):
        """
        Returns the fault dip term, f_dip, defined in equation 24
        """
        return CB14._get_fault_dip_term(self, C, rup)

    def _get_anelastic_attenuation_term(self, C, rrup):
        """
        Returns the anelastic attenuation term, f_atn, defined in equation 25
        """
        Dc20 = self._get_delta_c20(C)
        f_atn = np.zeros(len(rrup))
        idx = rrup > 80.0
        f_atn[idx] = (C["c20"] + Dc20) * (rrup[idx] - 80.0)
        return f_atn

    def _get_delta_c20(self, C):
        """
        Retrieve regional-dependent coefficient accounting for differences in
        anelastic attenuation in path scaling

        This is to derive a reference/base-case c20 that includes
        California, Taiwan, the Middle East, and other similar active tectonic
        regions to represent a typical or average Q region.
        """
        return 0.

    def _get_stddevs(self, C, rup, sites, stddev_types):
        """
        Returns the inter-event, intra-event, and total standard deviations

        Note that it is assumed here that the soil response of the vertical
        component is linear (i.e. nonlinear site response effects not
        included). Thus, the expressions for the aleatory std devs for the
        vertical component is much simpler than in the horizontal component,
        since the site response- and IMT-correlation functions are neglected.
        """
        num_sites = len(sites.vs30)
        # Evaluate tau according to equation 27
        tau = self._get_taulny(C, rup.mag)
        # Evaluate phi according to equation 28
        phi = self._get_philny(C, rup.mag)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt((tau ** 2.) + (phi ** 2.)) +
                               np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(num_sites))
        # return std dev values for each stddev type in site collection
        return stddevs

    def _get_taulny(self, C, mag):
        """
        Returns the inter-event random effects coefficient (tau) defined in
        Equation 29.
        """
        return CB14._get_taulny(self, C, mag)

    def _get_philny(self, C, mag):
        """
        Returns the intra-event random effects coefficient (phi) defined in
        Equation 30.
        """
        return CB14._get_philny(self, C, mag)

    #: Table of regression coefficients obtained from supplementary material
    #: published together with the EQS paper
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      c0           c1       c2        c3        c4        c5          c6         c7          c8         c9         c10      c11         c12         c13        c14        c15        c17         c18         c19         c20        Dc20_JP    Dc20_CH    a2       h1       h2       h3        h5        h6        k1      phi1     phi2     tau1     tau2
    pgv      -3.86        1.51     0.27      -1.299    -0.379    -2.383      0.196      6.274       0.111      -0.128     0.14     -0.395      0.338       0.407      -0.0016    0.382      0.0581      0.0294      0.00761     -0.0019    0.0005     0.0019     0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.608    0.442    0.334    0.24
    pga      -4.729       0.984    0.537     -1.499    -0.443    -2.666      0.214      7.166       0          -0.23      0.759    -0.356      1.019       0.373      -0.1172    -0.097     0.102       0.0442      0.00784     -0.0053    -0.0018    0.0039     0.167    0.241    1.474    -0.715    -0.337    -0.27     865     0.694    0.493    0.461    0.347
    0.01     -4.674       0.977    0.533     -1.485    -0.445    -2.665      0.214      7.136       0          -0.229     0.759    -0.354      1.015       0.372      -0.1193    -0.094     0.1026      0.0452      0.00784     -0.0053    -0.0018    0.0039     0.168    0.242    1.471    -0.714    -0.336    -0.27     865     0.695    0.494    0.462    0.345
    0.02     -4.548       0.976    0.549     -1.488    -0.453    -2.699      0.215      6.936       0          -0.27      0.768    -0.344      0.95        0.4        -0.1454    -0.081     0.1059      0.0427      0.00786     -0.0052    -0.0018    0.0036     0.166    0.244    1.467    -0.711    -0.339    -0.263    865     0.7      0.508    0.474    0.375
    0.03     -4.05        0.931    0.628     -1.494    -0.464    -2.772      0.216      7.235       0          -0.315     0.766    -0.297      1.056       0.394      -0.1957    -0.091     0.1175      0.041       0.00815     -0.0052    -0.002     0.0033     0.167    0.246    1.467    -0.713    -0.338    -0.259    908     0.722    0.536    0.529    0.416
    0.05     -3.435       0.887    0.674     -1.388    -0.552    -2.76       0.202      8.334       0          -0.329     0.764    -0.363      1.316       0.422      -0.187     -0.29      0.1238      0.0408      0.00783     -0.0062    -0.0026    0.0039     0.173    0.251    1.449    -0.701    -0.338    -0.263    1054    0.751    0.584    0.576    0.468
    0.075    -3.435       0.902    0.726     -1.469    -0.543    -2.575      0.177      8.761       0          -0.29      0.795    -0.427      1.758       0.336      -0.095     -0.261     0.1088      0.0516      0.00726     -0.0072    -0.0021    0.0048     0.198    0.26     1.435    -0.695    -0.347    -0.219    1086    0.74     0.578    0.523    0.427
    0.1      -3.93        0.993    0.698     -1.572    -0.47     -2.461      0.166      9.049       0          -0.203     0.842    -0.429      1.411       0.314      -0.0999    -0.091     0.0918      0.0559      0.00644     -0.0072    -0.0018    0.005      0.174    0.259    1.449    -0.708    -0.391    -0.201    1032    0.723    0.57     0.461    0.39
    0.15     -5.505       1.267    0.51      -1.669    -0.452    -2.349      0.164      8.633       0          -0.203     0.736    -0.421      1.227       0.289      0.0017     -0.092     0.072       0.0447      0.00745     -0.0066    -0.0018    0.0048     0.198    0.254    1.461    -0.715    -0.449    -0.099    878     0.731    0.536    0.391    0.343
    0.2      -6.28        1.366    0.447     -1.75     -0.435    -2.335      0.175      8.742       0          -0.203     0.801    -0.429      0.987       0.29       0.0402     -0.081     0.0602      0.0485      0.00789     -0.0056    -0.0022    0.0041     0.204    0.237    1.484    -0.721    -0.393    -0.198    748     0.701    0.51     0.363    0.308
    0.25     -6.789       1.458    0.274     -1.711    -0.41     -2.332      0.183      8.4         0          -0.203     0.715    -0.438      0.577       0.303      0.0468     0.011      0.05        0.0416      0.00629     -0.0049    -0.0025    0.0034     0.185    0.206    1.581    -0.787    -0.339    -0.21     654     0.687    0.507    0.355    0.288
    0.3      -7.4         1.528    0.193     -1.77     -0.305    -2.297      0.19       7.643       0          -0.203     0.708    -0.421      0.279       0.336      0.0255     0.092      0.0382      0.0438      0.00524     -0.0046    -0.0027    0.0031     0.164    0.21     1.586    -0.795    -0.447    -0.121    587     0.668    0.514    0.355    0.265
    0.4      -8.75        1.739    -0.02     -1.594    -0.446    -2.219      0.185      7.059       0          -0.203     0.683    -0.401      0.358       0.358      0.0606     0.122      0.0264      0.0307      0.00522     -0.0037    -0.0024    0.0024     0.16     0.226    1.544    -0.77     -0.525    -0.086    503     0.628    0.521    0.36     0.28
    0.5      -9.74        1.872    -0.121    -1.577    -0.489    -2.205      0.191      6.375       0          -0.203     0.704    -0.417      0.229       0.432      0.0904     0.287      0.0163      0.0287      0.00539     -0.0031    -0.0025    0.0021     0.184    0.217    1.554    -0.77     -0.407    -0.281    457     0.606    0.526    0.376    0.284
    0.75     -11.05       2.021    -0.042    -1.757    -0.53     -2.143      0.188      5.166       0.016      -0.203     0.602    -0.49       0.574       0.459      0.1776     0.292      -0.0016     0.0277      0.00501     -0.0021    -0.0025    0.002      0.216    0.154    1.626    -0.78     -0.371    -0.285    410     0.568    0.536    0.416    0.322
    1        -12.184      2.18     -0.069    -1.707    -0.624    -2.092      0.176      5.642       0.032      -0.115     0.394    -0.539      0.98        0.442      0.2389     0.316      -0.0072     0.0277      0.00506     -0.0012    -0.0023    0.0012     0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.536    0.55     0.472    0.311
    1.5      -13.451      2.27     0.047     -1.621    -0.686    -1.913      0.144      5.963       0.128      -0.005     0.328    -0.611      0.819       0.52       0.2758     0.45       -0.0262     0.0293      0.00353     -0.0004    -0.0013    0.0004     0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.511    0.559    0.507    0.329
    2        -13.7        2.271    0.149     -1.512    -0.84     -1.882      0.126      7.584       0.255      0.12       0.112    -0.63       0.044       0.566      0.3051     0.424      -0.0408     0.0221      0.0022      0          -0.0004    0          0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.507    0.571    0.539    0.345
    3        -13.9        2.15     0.368     -1.315    -0.89     -1.789      0.105      8.645       0.284      0.17       0.011    -0.562      -0.396      0.562      0.3482     0.3        -0.0512     0.0321      -0.00137    0          0          0          0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.474    0.557    0.515    0.335
    4        -14.59387    2.132    0.726     -1.506    -0.885    -1.78139    0.10009    10.20357    0.26112    0.17       0        -0.53663    0.00115     0.51499    0.35267    0.25726    -0.0567     0.02249     0.00053     0          0          0          0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.466    0.566    0.553    0.331
    5        -15.63449    2.116    1.027     -1.721    -0.878    -1.68982    0.098      8.38571     0.28229    0.17747    0        -0.44173    -0.59234    0.51133    0.30443    0.17039    -0.04288    0.02372     0.00233     0          0          0          0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.43     0.568    0.578    0.294
    7.5      -17.12864    2.223    0.169     -0.756    -1.077    -1.72135    0.125      5.77927     0.38692    0.38278    0        -0.3428     -1.13827    0.57479    0.16789    0.21872    -0.0308     0.0171      -0.00298    0          0          0          0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.386    0.527    0.6      0.379
    10       -17.65672    2.132    0.367     -0.8      -1.282    -1.948      0.163      4.13478     0.32216    0.33417    0        -0.19908    -0.32493    0.32431    0.16858    0.12681    0.00668     -0.00165    0.00092     0          0          0          0.596    0.117    1.616    -0.733    -0.128    -0.756    400     0.395    0.481    0.495    0.442
    """)

    #: Equation constants (that are IMT-independent) for global model
    CONSTS = {  # hanging-wall model coefficient
                "h4": 1.0,
                # flag variable for Japan site data
                "SJ": 0
              }


class BozorgniaCampbell2016HighQ(BozorgniaCampbell2016):
    """
    Implements the BC15 GMPE by Bozorgnia & Campbell (2016) for
    vertical-component ground motions from the PEER NGA-West2 Project

    Applies regional corrections in path scaling term for regions with
    low attenuation (high quality factor, Q) (e.g. eastern China)
    """
    def _get_delta_c20(self, C):
        """
        Retrieve regional-dependent coefficient accounting for differences in
        anelastic attenuation
        """
        return C['Dc20_CH']


class BozorgniaCampbell2016LowQ(BozorgniaCampbell2016):
    """
    Implements the BC15 GMPE by Bozorgnia & Campbell (2016) for
    vertical-component ground motions from the PEER NGA-West2 Project

    Applies regional corrections in path scaling term for regions with
    high attenuation (low quality factor, Q) (e.g. Japan and Italy)
    """
    def _get_delta_c20(self, C):
        """
        Retrieve regional-dependent coefficient accounting for differences in
        anelastic attenuation
        """
        return C['Dc20_JP']


class BozorgniaCampbell2016AveQJapanSite(BozorgniaCampbell2016):
    """
    Implements the BC15 GMPE by Bozorgnia & Campbell (2016) for
    vertical-component ground motions from the PEER NGA-West2 Project

    Incorporates the difference in linear Vs30 scaling for sites in Japan by
    activating the flag variable in shallow site reponse scaling

    Applies the average attenuation case (Dc20=0)
    """
    #: Equation constants (that are IMT-independent) for Japan sites
    CONSTS = {  # hanging-wall model coefficient
                "h4": 1.0,
                # flag variable for Japan site data
                "SJ": 1
              }


class BozorgniaCampbell2016HighQJapanSite(BozorgniaCampbell2016AveQJapanSite):
    """
    Implements the BC15 GMPE by Bozorgnia & Campbell (2016) for
    vertical-component ground motions from the PEER NGA-West2 Project

    Incorporates the difference in linear Vs30 scaling for sites in Japan by
    activating the flag variable in shallow site reponse scaling

    Applies regional corrections in path scaling term for regions with
    low attenuation (high quality factor, Q)
    """
    def _get_delta_c20(self, C):
        """
        Retrieve regional-dependent coefficient accounting for differences in
        anelastic attenuation
        """
        return C['Dc20_CH']


class BozorgniaCampbell2016LowQJapanSite(BozorgniaCampbell2016AveQJapanSite):
    """
    Implements the BC15 GMPE by Bozorgnia & Campbell (2016) for
    vertical-component ground motions from the PEER NGA-West2 Project

    Incorporates the difference in linear Vs30 scaling for sites in Japan by
    activating the flag variable in shallow site reponse scaling

    Applies regional corrections in path scaling term for regions with
    high attenuation (low quality factor, Q)
    """
    def _get_delta_c20(self, C):
        """
        Retrieve regional-dependent coefficient accounting for differences in
        anelastic attenuation
        """
        return C['Dc20_JP']
