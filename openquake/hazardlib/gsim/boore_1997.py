# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module exports :class:`BooreEtAl1997GeometricMean`,
               :class:'BooreEtAl1997GeometricMeanUnspecified'
               :class:'BooreEtAl1997ArbitraryHorizontal' and
               :class:'BooreEtAl1997ArbitraryHorizontalUnspecfied'
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_distance_scaling(rjb, C):
    """
    Compute distance-scaling term (Page 141, Eq 1)
    """
    # Calculate distance according to Page 141, Eq 2.
    rdist = np.sqrt((rjb ** 2.) + (C['h'] ** 2.))
    return C['B5'] * np.log(rdist)


def _compute_magnitude_scaling(mag, C):
    """
    Compute magnitude-scaling term (Page 141, Eq 1)
    """
    dmag = mag - 6.
    return C['B2'] * dmag + C['B3'] * dmag ** 2.


def _compute_site_term(vs30, C):
    """
    Compute site amplification linear term (Page 141, Eq 1)
    """
    return C['Bv'] * np.log(vs30 / C['Va'])


def _compute_style_of_faulting_term(sof, ctx, C):
    """
    Computes the coefficient to scale for reverse or strike-slip events
    Fault type (Strike-slip, Normal, Thrust/reverse) is
    derived from rake angle.
    Rakes angles within 30 of horizontal are strike-slip,
    angles from 30 to 150 are reverse, and angles from
    -30 to -150 are normal. See paragraph 'Predictor Variables'
    pag 103.
    Note that 'Unspecified' case is used to refer to all other rake
    angles.
    """
    if sof is None:  # unspecified
        return C['B1all']
    res = np.zeros_like(ctx.rake)
    res[(np.abs(ctx.rake) <= 30.) |
        (180.0 - np.abs(ctx.rake) <= 30.)] = C['B1ss']
    res[(ctx.rake > 30.) & (ctx.rake < 150.)] = C['B1rv']
    res[(ctx.rake > -150.) & (ctx.rake < -30.)] = C['B1all']
    return res

def _get_stddevs(horizontal, C):
    """
    Return standard deviations using Page 142 (Eq 4 - 5)
    """
    if horizontal:
        # Return standard deviations as defined in table 8, pag 121.
        return [C['sigma_tot'], C['sigma_e'], C['sigma_r']]
    return [np.sqrt(C['sigma_e'] ** 2 + C['sigma1'] ** 2),
            C['sigma_e'], C['sigma1']]


class BooreEtAl1997GeometricMean(GMPE):
    """
    Implements GMPE developed by David M. Boore and William B. Joyner and
    Thomas E. Fumal (1997). "Equations for Estimating Horizontal Response
    Spectra and Peak Acceleration form Western North American Earthquakes:
    A Summary of Recent Work". Seismological Research Letters. 68(1). 128 - 153
    """
    #: Supported tectonic region type is active shallow crust, see
    #: paragraph 'Introduction', page 99.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see table 3
    #: pag. 110
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters is Vs30.
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, and rake.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is Rjb.
    REQUIRES_DISTANCES = {'rjb'}

    sof = True
    horizontal = False

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (_compute_style_of_faulting_term(self.sof, ctx, C) +
                       _compute_magnitude_scaling(ctx.mag, C) +
                       _compute_distance_scaling(ctx.rjb, C) +
                       _compute_site_term(ctx.vs30, C))
            sig[m], tau[m], phi[m] = _get_stddevs(self.horizontal, C)

    #: Coefficient table is constructed from values in Table 8
    #: Note that for periods between 0.1 s and 0.18s the inter-event term
    #: is originally 0. As this was causing test warnings we have set this
    #: to an arbitrarily infinitesimal number
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      B1ss      B1rv      B1all     B2       B3        B5        Bv        Va          h        sigma1  sigma_c  sigma_r  sigma_e sigma_tot
    pga      -0.3130   -0.1170   -0.2420   0.5270    0.0000   -0.7780   -0.3710   1396.0000   5.5700   0.4310   0.1600   0.4600   0.1840    0.4950
    0.1000    1.0060    1.0870    1.0590   0.7530   -0.2260   -0.9340   -0.2120   1112.0000   6.2700   0.4400   0.1340   0.4600    1E-20    0.4600
    0.1100    1.0720    1.1640    1.1300   0.7320   -0.2300   -0.9370   -0.2110   1291.0000   6.6500   0.4370   0.1410   0.4590    1E-20    0.4590
    0.1200    1.1090    1.2150    1.1740   0.7210   -0.2330   -0.9390   -0.2150   1452.0000   6.9100   0.4370   0.1480   0.4610    1E-20    0.4610
    0.1300    1.1280    1.2460    1.2000   0.7110   -0.2330   -0.9390   -0.2210   1596.0000   7.0800   0.4350   0.1530   0.4610    1E-20    0.4610
    0.1400    1.1350    1.2610    1.2080   0.7070   -0.2300   -0.9380   -0.2280   1718.0000   7.1800   0.4350   0.1580   0.4630    1E-20    0.4630
    0.1500    1.1280    1.2640    1.2040   0.7020   -0.2280   -0.9370   -0.2380   1820.0000   7.2300   0.4350   0.1630   0.4650    1E-20    0.4650
    0.1600    1.1120    1.2570    1.1920   0.7020   -0.2260   -0.9350   -0.2480   1910.0000   7.2400   0.4350   0.1660   0.4660    1E-20    0.4660
    0.1700    1.0900    1.2420    1.1730   0.7020   -0.2210   -0.9330   -0.2580   1977.0000   7.2100   0.4350   0.1690   0.4670    1E-20    0.4670
    0.1800    1.0630    1.2220    1.1510   0.7050   -0.2160   -0.9300   -0.2700   2037.0000   7.1600   0.4350   0.1730   0.4680   0.0020    0.4680
    0.1900    1.0320    1.1980    1.1220   0.7090   -0.2120   -0.9270   -0.2810   2080.0000   7.1000   0.4350   0.1760   0.4690   0.0050    0.4690
    0.2000    0.9990    1.1700    1.0890   0.7110   -0.2070   -0.9240   -0.2920   2118.0000   7.0200   0.4350   0.1770   0.4700   0.0090    0.4700
    0.2200    0.9250    1.1040    1.0190   0.7210   -0.1980   -0.9180   -0.3150   2158.0000   6.8300   0.4370   0.1820   0.4730   0.0160    0.4740
    0.2400    0.8470    1.0330    0.9410   0.7320   -0.1890   -0.9120   -0.3380   2178.0000   6.6200   0.4370   0.1850   0.4750   0.0250    0.4750
    0.2600    0.7640    0.9580    0.8610   0.7440   -0.1800   -0.9060   -0.3600   2173.0000   6.3900   0.4370   0.1890   0.4760   0.0320    0.4770
    0.2800    0.6810    0.8810    0.7800   0.7580   -0.1680   -0.8990   -0.3810   2158.0000   6.1700   0.4400   0.1920   0.4800   0.0390    0.4820
    0.3000    0.5980    0.8030    0.7000   0.7690   -0.1610   -0.8930   -0.4010   2133.0000   5.9400   0.4400   0.1950   0.4810   0.0480    0.4840
    0.3200    0.5180    0.7250    0.6190   0.7830   -0.1520   -0.8880   -0.4200   2104.0000   5.7200   0.4420   0.1970   0.4840   0.0550    0.4870
    0.3400    0.4390    0.6480    0.5400   0.7940   -0.1430   -0.8820   -0.4380   2070.0000   5.5000   0.4440   0.1990   0.4870   0.0640    0.4910
    0.3600    0.3610    0.5700    0.4620   0.8060   -0.1360   -0.8770   -0.4560   2032.0000   5.3000   0.4440   0.2000   0.4870   0.0710    0.4920
    0.3800    0.2860    0.4950    0.3850   0.8200   -0.1270   -0.8720   -0.4720   1995.0000   5.1000   0.4470   0.2020   0.4910   0.0780    0.4970
    0.4000    0.2120    0.4230    0.3110   0.8310   -0.1200   -0.8670   -0.4870   1954.0000   4.9100   0.4470   0.2040   0.4910   0.0850    0.4990
    0.4200    0.1400    0.3520    0.2390   0.8400   -0.1130   -0.8620   -0.5020   1919.0000   4.7400   0.4490   0.2050   0.4940   0.0920    0.5020
    0.4400    0.0730    0.2820    0.1690   0.8520   -0.1080   -0.8580   -0.5160   1884.0000   4.5700   0.4490   0.2060   0.4940   0.0990    0.5040
    0.4600    0.0050    0.2170    0.1020   0.8630   -0.1010   -0.8540   -0.5290   1849.0000   4.4100   0.4510   0.2090   0.4970   0.1040    0.5080
    0.4800   -0.0580    0.1510    0.0360   0.8730   -0.0970   -0.8500   -0.5410   1816.0000   4.2600   0.4510   0.2100   0.4970   0.1110    0.5100
    0.5000   -0.1220    0.0870   -0.0250   0.8840   -0.0900   -0.8460   -0.5530   1782.0000   4.1300   0.4540   0.2110   0.5010   0.1150    0.5140
    0.5500   -0.2680   -0.0630   -0.1760   0.9070   -0.0780   -0.8370   -0.5790   1710.0000   3.8200   0.4560   0.2140   0.5040   0.1290    0.5200
    0.6000   -0.4010   -0.2030   -0.3140   0.9280   -0.0690   -0.8300   -0.6020   1644.0000   3.5700   0.4580   0.2160   0.5060   0.1430    0.5260
    0.6500   -0.5230   -0.3310   -0.4400   0.9460   -0.0600   -0.8230   -0.6220   1592.0000   3.3600   0.4610   0.2180   0.5100   0.1540    0.5330
    0.7000   -0.6340   -0.4520   -0.5550   0.9620   -0.0530   -0.8180   -0.6390   1545.0000   3.2000   0.4630   0.2200   0.5130   0.1660    0.5390
    0.7500   -0.7370   -0.5620   -0.6610   0.9790   -0.0460   -0.8130   -0.6530   1507.0000   3.0700   0.4650   0.2210   0.5150   0.1750    0.5440
    0.8000   -0.8290   -0.6660   -0.7600   0.9920   -0.0410   -0.8090   -0.6660   1476.0000   2.9800   0.4670   0.2230   0.5180   0.1840    0.5490
    0.8500   -0.9150   -0.7610   -0.8510   1.0060   -0.0370   -0.8050   -0.6760   1452.0000   2.9200   0.4670   0.2260   0.5190   0.1910    0.5530
    0.9000   -0.9930   -0.8480   -0.9330   1.0180   -0.0350   -0.8020   -0.6850   1432.0000   2.8900   0.4700   0.2280   0.5220   0.2000    0.5590
    0.9500   -1.0660   -0.9320   -1.0100   1.0270   -0.0320   -0.8000   -0.6920   1416.0000   2.8800   0.4720   0.2300   0.5250   0.2070    0.5640
    1.0000   -1.1330   -1.0090   -1.0800   1.0360   -0.0320   -0.7980   -0.6980   1406.0000   2.9000   0.4740   0.2300   0.5270   0.2140    0.5690
    1.1000   -1.2490   -1.1450   -1.2080   1.0520   -0.0300   -0.7950   -0.7060   1396.0000   2.9900   0.4770   0.2330   0.5310   0.2260    0.5770
    1.2000   -1.3450   -1.2650   -1.3150   1.0640   -0.0320   -0.7940   -0.7100   1400.0000   3.1400   0.4790   0.2360   0.5340   0.2350    0.5830
    1.3000   -1.4280   -1.3700   -1.4070   1.0730   -0.0350   -0.7930   -0.7110   1416.0000   3.3600   0.4810   0.2390   0.5370   0.2440    0.5900
    1.4000   -1.4950   -1.4600   -1.4830   1.0800   -0.0390   -0.7940   -0.7090   1442.0000   3.6200   0.4840   0.2410   0.5410   0.2510    0.5960
    1.5000   -1.5520   -1.5380   -1.5500   1.0850   -0.0440   -0.7960   -0.7040   1479.0000   3.9200   0.4860   0.2440   0.5440   0.2560    0.6010
    1.6000   -1.5980   -1.6080   -1.6050   1.0870   -0.0510   -0.7980   -0.6970   1524.0000   4.2600   0.4880   0.2460   0.5460   0.2620    0.6060
    1.7000   -1.6340   -1.6680   -1.6520   1.0890   -0.0580   -0.8010   -0.6890   1581.0000   4.6200   0.4900   0.2490   0.5500   0.2670    0.6110
    1.8000   -1.6630   -1.7180   -1.6890   1.0870   -0.0670   -0.8040   -0.6790   1644.0000   5.0100   0.4930   0.2510   0.5530   0.2690    0.6150
    1.9000   -1.6850   -1.7630   -1.7200   1.0870   -0.0740   -0.8080   -0.6670   1714.0000   5.4200   0.4930   0.2540   0.5550   0.2740    0.6190
    2.0000   -1.6990   -1.8010   -1.7430   1.0850   -0.0850   -0.8120   -0.6550   1795.0000   5.8500   0.4950   0.2560   0.5570   0.2760    0.6220
    """)


class BooreEtAl1997GeometricMeanUnspecified(BooreEtAl1997GeometricMean):
    """
    Where the faulting mechanism need not be specified it is preferable to use
    this instance of the Boore et al (1997) GMPE, which omits the need for
    rake to be defined.
    """
    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}
    sof = None


class BooreEtAl1997ArbitraryHorizontal(BooreEtAl1997GeometricMean):
    """
    Returns the ground motion values for the arbitrary horizontal component,
    rather than the geometric mean.
    This version includes the corrected intra-event terms, as defined in
    an erratum to the original paper:
    Boore, DM (2005). "Erratum: Equations for Estimating
    Horizontal Response Spectra and Peak Acceleration from Western North
    American Earthquakes: A Summary of Recent Work." Seismological Research
    Letters, 76(3), 368-369
    """
    #: Supported intensity measure component is the arbitrary horizontal
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL
    horizontal = True


class BooreEtAl1997ArbitraryHorizontalUnspecified(
        BooreEtAl1997ArbitraryHorizontal):
    """
    As for the :class:'BooreEtAl1997Arbitrary', here defined for the case
    when the style of faulting is not specified
    """
    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}
    sof = None
