"""
    09/16/2020:
        started implementation
Module exports :class:`SiEtAl2020SInter`
               :class:`SiEtAl2020SSlab`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

class SiEtAl2020SInter(GMPE):
    """
    Implements NGA Subduction model Si, Midorikawa, Kishida (2020)
    For Interface events.
    
    Implementation is based on preliminary PEER report and R implementation
        obtained from T. Kishida on 09/16/2020
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.GMRotI50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section "Aleatory Variability Model", page 1094.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters are Vs30 and Z2.5
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z2pt5'}

    #: Required rupture parameters are magnitude and hypocentral deph
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'zhyp'}

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = {'rrup'}
    
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type and for PGA
        C = self.COEFFS[imt]
        C_PGA = self.COEFFS[PGA()]

        # Get mean and standard deviation of PGA on rock (Vs30 760 m/s)
        pga760 = self._get_pga_rock(C_PGA, PGA(), sites, rup, dists)

        # Get mean and standard deviations for IMT
        mean = self.get_mean_values(C, imt, sites, rup, dists, pga760)

        # Get standard deviations
        stddevs = self.get_stddevs(
            C, stddev_types, num_sites=len(sites.vs30)
        )
        return mean, stddevs
    
    def get_stddevs(self, C, stddev_types, num_sites):
        """
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sigma_tot = np.sqrt(C["phi"] ** 2 + C["tau"] ** 2)
                stddevs.append(sigma_tot + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C["phi"] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C["tau"] + np.zeros(num_sites))
        return stddevs

    def _get_pga_rock(self, C, imt, sites, rup, dists):
        """
        Returns the PGA on rock for site response
        """
        mean = (self.get_base_term(C) +
                self.get_magnitude_scaling_term(C, imt, rup.mag) +
                self.get_geometric_attenuation_term(C, rup, dists.rrup) +
                self.get_basin_response_term(C, sites.z2pt5) +
                self.get_depth_scaling_term(C, rup.zhyp) +
                self.get_anelastic_attenuation_term(C, dists.rrup)) 
        return 10 ** mean
    
    def get_mean_values(self, C, imt, sites, rup, dists, a760):
        """
        Returns the mean values for a specific IMT
        """
        
        mean = np.log(10) * (self.get_base_term(C) +
                             self.get_magnitude_scaling_term(C, imt, rup.mag) +
                             self.get_depth_scaling_term(C, rup.zhyp) + 
                             self.get_geometric_attenuation_term(C, rup, dists.rrup) +
                             self.get_anelastic_attenuation_term(C, dists.rrup) +
                             self.get_basin_response_term(C, sites.z2pt5) +
                             self.get_shallow_site_response_term(C, sites.vs30, a760))

        return(mean)

    def get_base_term(self, C):
        """
        Returns the constant term of the GMM.
        Depends on tectonic type
        """
        return C["e"] + C["d0"]

    def get_magnitude_scaling_term(self, C, imt, mag):
        """
        Returns the magnitude scaling term (Equation 3.16)
        """
        if imt.name == "SA" and imt.period < 2.:
            m_ref = 8.3
        elif imt.name == "PGA" or imt.name == "PGV":
            m_ref = 8.3
        else:
            m_ref = 7.5
        
        fmag = np.where(mag < m_ref,
                        C["a1"] * mag,
                        C["a1"] * mag + (C["a2"] - C["a1"]) * (mag - m_ref)
        )
        return fmag

    def get_depth_scaling_term(self, C, zhyp):
        """
        Returns the depth scaling term (Eqation 3.16)
        """
        return C["h"] * zhyp

    def get_anelastic_attenuation_term(self, C, rrup):
        """
        Returns the anelastic attenuation term (Eq. 3.15)
        The period dependent coefficients are calculated and added to the coefficients table.
        """
        return C["c_attn"] * rrup
    
    def get_geometric_attenuation_term(self, C, rup, rrup):
        """
        Returns the geometric attenuation term (Eq. 3.13/3.14)
        Period dependent coefficients are calculated and added to he coefficients table.
        """
        mref = np.where(rup.mag < 8.3,
                 rup.mag,
                 8.3
                 )
        c = C["c_gs"] * 10 ** (0.5 * mref)

        zmoho = self.get_moho_depth(rup)
        fgs = np.where(np.all([rup.zhyp > zmoho, rrup >= 1.7 * rup.zhyp]),
                       0.6 * np.log10(1.7 * rup.zhyp + c) - 1.6 * np.log10(rrup + c),
                       -1 *  np.log10(rrup + c)
                       )
        return fgs
    
    def get_shallow_site_response_term(self, C, vs30, pga760):
        """
        Returns the shallow site response term (Eq. 3.2 tp 3.4)
        """
        vs30_comp = np.where(vs30 < 760, vs30, 760)
        f2 = 0.5 * C["f4"] * (np.exp(C["f5"] * (vs30_comp - 360)) - np.exp(C["f5"] * (760 - 360)))
        f_site_lin = np.where(vs30 <= C["Vc"],
                              C["c"] * np.log(vs30 / C["Vref"]),
                              C["c"] * np.log(C["Vc"] / C["Vref"])
                              )

        f_site_nl = np.full_like(vs30, C["f1"])
        idx = f2 != 0
        f_site_nl[idx] = f_site_nl[idx] + f2[idx] * np.log((pga760[idx] + C["f3"]) / C["f3"]) 

        return (f_site_lin + f_site_nl) / np.log(10)

    def get_basin_response_term(self, C, z_value):
        """
        Returns the basin response term (Eq. 3.10)
        """
        return C["Cd"] + C["Dd"] * z_value
    
    def get_moho_depth(self, rup):
        """
        get Moho depth dependent on hypocenter location
        for now, return 30km everywhere 
        """
        return 30.

    COEFFS = CoeffsTable(sa_damping=5, table="""\
imt     e         a1        d0  d1        a2        h         Cd     Dd     c        Vc       Vref   f1   f3   f4        f5       phi    tau    sigma  Mb   c_gs     c_attn  
   pgv -1.895274  0.638198  0   0.194161  0.000000  0.005350  0.000  0.000 -0.84000  1300.00  760.0  0.0  0.1 -0.100000 -0.00844  0.557  0.445  0.713  8.3  0.00550 -0.003000
   pga -2.685641  0.485385  0   0.224236  0.000000  0.006963  0.000  0.000 -0.60000  1500.00  760.0  0.0  0.1 -0.150000 -0.00701  0.646  0.593  0.877  8.3  0.00550 -0.003000
  0.01 -2.646637  0.493277  0   0.225570  0.000000  0.007054  0.000  0.000 -0.60372  1500.20  760.0  0.0  0.1 -0.148330 -0.00701  0.632  0.565  0.848  8.3  0.00550 -0.003000
  0.02 -2.646100  0.494915  0   0.232876  0.000000  0.007012  0.000  0.000 -0.57388  1500.40  760.0  0.0  0.1 -0.147100 -0.00728  0.630  0.564  0.845  8.3  0.00550 -0.003000
  0.03 -2.629178  0.496553  0   0.240181  0.000000  0.007138  0.000  0.000 -0.53414  1503.00  760.0  0.0  0.1 -0.154850 -0.00735  0.633  0.578  0.857  8.3  0.00550 -0.003000
  0.05 -2.567020  0.499829  0   0.250252  0.000000  0.007786  0.000  0.000 -0.45795  1501.40  760.0  0.0  0.1 -0.196330 -0.00647  0.664  0.634  0.918  8.3  0.00550 -0.003000
 0.075 -2.484857  0.503105  0   0.258333  0.000000  0.008437  0.000  0.000 -0.44411  1494.00  760.0  0.0  0.1 -0.228660 -0.00573  0.714  0.688  0.992  8.3  0.00550 -0.003000
   0.1 -2.456607  0.508019  0   0.265100  0.000000  0.008569  0.000  0.000 -0.48724  1479.10  760.0  0.0  0.1 -0.249160 -0.00560  0.743  0.666  0.998  8.3  0.00550 -0.003000
  0.15 -2.485473  0.516208  0   0.266446  0.000000  0.008411  0.000  0.000 -0.57962  1442.90  760.0  0.0  0.1 -0.257130 -0.00585  0.748  0.563  0.936  8.3  0.00550 -0.003000
   0.2 -2.545081  0.524393  0   0.261442  0.000000  0.007341  0.000  0.000 -0.68762  1392.60  760.0  0.0  0.1 -0.246580 -0.00614  0.736  0.532  0.908  8.3  0.00550 -0.003000
  0.25 -2.636311  0.532568  0   0.255371  0.000000  0.006546  0.000  0.000 -0.77177  1356.20  760.0  0.0  0.1 -0.235740 -0.00644  0.713  0.496  0.868  8.3  0.00550 -0.003000
   0.3 -2.757882  0.540729  0   0.245784  0.000000  0.006321  0.000  0.000 -0.84165  1308.50  760.0  0.0  0.1 -0.219120 -0.00670  0.694  0.469  0.838  8.3  0.00550 -0.002996
   0.4 -3.026741  0.556994  0   0.232084  0.000000  0.005857  0.000  0.000 -0.91092  1252.70  760.0  0.0  0.1 -0.195820 -0.00713  0.669  0.440  0.801  8.3  0.00438 -0.002581
   0.5 -3.273455  0.573162  0   0.219238  0.000000  0.005350  0.000  0.000 -0.96930  1203.90  760.0  0.0  0.1 -0.170410 -0.00744  0.654  0.417  0.776  8.3  0.00351 -0.002259
  0.75 -3.784828  0.613050  0   0.204750  0.000000  0.004290  0.000  0.000 -1.01540  1147.60  760.0  0.0  0.1 -0.138660 -0.00812  0.659  0.419  0.781  8.3  0.00280 -0.002000
     1 -4.168096  0.651986  0   0.195413  0.044000  0.003904  0.008  0.056 -1.05000  1109.90  760.0  0.0  0.1 -0.105210 -0.00844  0.670  0.425  0.794  8.3  0.00280 -0.002000
   1.5 -4.952279  0.725900  0   0.188847  0.134000  0.003848  0.030  0.067 -1.04540  1072.40  760.0  0.0  0.1 -0.067941 -0.00771  0.701  0.448  0.832  8.3  0.00280 -0.002000
     2 -5.573430  0.792692  0   0.188157  0.397000  0.004260  0.037  0.081 -1.03920  1009.50  760.0  0.0  0.1 -0.036136 -0.00479  0.714  0.469  0.854  7.5  0.00280 -0.002000
     3 -6.603707  0.898490  0   0.180567  0.442428  0.005716  0.022  0.108 -1.01120   922.43  760.0  0.0  0.1 -0.013577 -0.00183  0.699  0.498  0.858  7.5  0.00280 -0.002000
     4 -7.279363  0.967563  0   0.171225  0.484387  0.005425 -0.021  0.142 -0.96938   844.48  760.0  0.0  0.1 -0.003212 -0.00152  0.669  0.547  0.864  7.5  0.00280 -0.002000
     5 -7.708043  1.008058  0   0.163298  0.521126  0.005093 -0.072  0.181 -0.91954   793.13  760.0  0.0  0.1 -0.000255 -0.00144  0.641  0.564  0.854  7.5  0.00280 -0.002000
   7.5 -8.163116  1.040264  0   0.151111  0.574112  0.004597 -0.114  0.198 -0.77665   771.01  760.0  0.0  0.1 -0.000055 -0.00137  0.638  0.581  0.863  7.5  0.00280 -0.002000
    10 -8.366713  1.058093  0   0.132831  0.554450  0.001817 -0.133  0.190 -0.65575   775.00  760.0  0.0  0.1  0.000000 -0.00136  0.615  0.614  0.869  7.5  0.00280 -0.002000
    """)

class SiEtAl2020SSlab(SiEtAl2020SInter):
    """
    Implements NGA Subduction model Si, Midorikawa, Kishida (2020)
    For Intraslab events.
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    
    def get_base_term(self, C):
        """
        Returns the constant term of the GMM.
        Depends on tectonic type
        """
        return C["e"] + C["d1"]
    
