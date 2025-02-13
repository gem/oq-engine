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
Module exports :class:`SomervilleEtAl2009NonCratonic`,
:class:`SomervilleEtAl2009YilgarnCraton`
:class:`SomervilleEtAl2009NonCratonic_SS14`
:class:`SomervilleEtAl2009YilgarnCraton_SS14`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim import boore_2014

def _compute_mean(C, mag, rjb):
    """
    Compute mean value, see table 2.
    """
    m1 = 6.4
    r1 = 50.
    h = 6.
    R = np.sqrt(rjb ** 2 + h ** 2)
    R1 = np.sqrt(r1 ** 2 + h ** 2)
    less_r1 = rjb < r1
    ge_r1 = rjb >= r1

    mean = (C['c1'] + C['c4'] * (mag - m1) * np.log(R) + C['c5'] * rjb +
            C['c8'] * (8.5 - mag) ** 2)

    mean[less_r1] += C['c3'] * np.log(R[less_r1])
    mean[ge_r1] += (C['c3'] * np.log(R1) +
                    C['c6'] * (np.log(R[ge_r1]) - np.log(R1)))
    mean += np.where(mag < m1, C['c2'] * (mag - m1), C['c7'] * (mag - m1))

    return mean


class SomervilleEtAl2009NonCratonic(GMPE):
    """
    Implements GMPE developed by P. Somerville, R. Graves, N. Collins, S. G.
    Song, S. Ni, and P. Cummins for Non-Cratonic Australia published in "Source
    and Ground Motion Models for Australian Earthquakes", Report to Geoscience
    Australia (2009). Document available at:
    http://www.ga.gov.au/cedda/publications/193?yp=2009
    """
    #: The supported tectonic region type is stable continental region
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: The supported intensity measure types are PGA, PGV, and SA, see table
    #: 3
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: The supported intensity measure component is set to 'average
    #: horizontal', however the original paper does not report this information
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: The supported standard deviations is total, see tables 3
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: no site parameters are defined, the GMPE is calibrated for Vs30 = 865
    #: m/s (provisionally set to 800 for compatibility with SiteTerm class)
    REQUIRES_SITES_PARAMETERS = set()
    DEFINED_FOR_REFERENCE_VELOCITY = 800.

    #: The required rupture parameter is magnitude, see table 2
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: The required distance parameter is 'Joyner-Boore' distance, see table 2
    REQUIRES_DISTANCES = {'rjb'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.

        Implement equations as defined in table 2.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, ctx.mag, ctx.rjb)
            sig[m] = C['sigma']

    #: Coefficients taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT     c1       c2        c3       c4        c5        c6        c7        c8       sigma
    pgv     5.07090  0.52780  -0.85740  0.17700  -0.00501  -0.61190   0.80660  -0.03800  0.6417
    pga     1.03780 -0.03970  -0.79430  0.14450  -0.00618  -0.72540  -0.03590  -0.09730  0.5685
    0.010   1.05360 -0.04190  -0.79390  0.14450  -0.00619  -0.72660  -0.03940  -0.09740  0.5684
    0.020   1.05680 -0.03920  -0.79680  0.14550  -0.00617  -0.73230  -0.03930  -0.09600  0.5684
    0.030   1.13530 -0.04790  -0.80920  0.15000  -0.00610  -0.76410  -0.05710  -0.09210  0.5681
    0.040   1.30000 -0.07020  -0.83150  0.15920  -0.00599  -0.82850  -0.09810  -0.08530  0.5676
    0.050   1.47680 -0.09310  -0.83330  0.15600  -0.00606  -0.86740  -0.12740  -0.09130  0.5670
    0.075   1.70220 -0.05160  -0.80720  0.14560  -0.00655  -0.87690  -0.10970  -0.08690  0.5663
    0.100   1.65720  0.15080  -0.77590  0.13100  -0.00708  -0.77830   0.01690  -0.05980  0.5659
    0.150   1.94440 -0.09620  -0.75000  0.11670  -0.00698  -0.69490  -0.13320  -0.12530  0.5659
    0.200   1.82720 -0.06230  -0.73430  0.11940  -0.00677  -0.64380  -0.09570  -0.11920  0.5669
    0.250   1.74380 -0.02530  -0.72480  0.11950  -0.00646  -0.63740  -0.06250  -0.11650  0.5678
    0.3003  1.80560 -0.27020  -0.73190  0.13490  -0.00606  -0.66440  -0.17470  -0.14340  0.5708
    0.400   1.88750 -0.37820  -0.70580  0.09960  -0.00589  -0.58770  -0.24420  -0.21890  0.5697
    0.500   2.03760 -0.79590  -0.69730  0.11470  -0.00565  -0.59990  -0.48670  -0.29690  0.5739
    0.750   1.93060 -0.80280  -0.74510  0.11220  -0.00503  -0.59460  -0.50120  -0.34990  0.5876
    1.000   1.60380 -0.47800  -0.86950  0.07320  -0.00569  -0.41590   0.06360  -0.33730  0.6269
    1.4993  0.47740  0.90960  -1.02440  0.11060  -0.00652  -0.19000   1.09610  -0.10660  0.7517
    2.000  -0.25810  1.37770  -1.01000  0.10310  -0.00539  -0.27340   1.50330  -0.04530  0.8036
    3.0003 -0.96360  1.14690  -0.88530  0.10380  -0.00478  -0.40420   1.54130  -0.11020  0.8219
    4.000  -1.46140  1.07950  -0.80490  0.10960  -0.00395  -0.46040   1.41960  -0.14700  0.8212
    5.000  -1.61160  0.74860  -0.78100  0.09650  -0.00307  -0.46490   1.24090  -0.22170  0.8240
    7.5019 -2.35310  0.35190  -0.64340  0.09590  -0.00138  -0.68260   0.92880  -0.31230  0.7957
    10.000 -3.26140  0.69730  -0.62760  0.12920  -0.00155  -0.61980   1.01050  -0.24550  0.7602
    """)


class SomervilleEtAl2009YilgarnCraton(SomervilleEtAl2009NonCratonic):
    """
    Implements GMPE developed by P. Somerville, R. Graves, N. Collins, S. G.
    Song, S. Ni, and P. Cummins for Yilgarn Craton published in "Source
    and Ground Motion Models for Australian Earthquakes", Report to Geoscience
    Australia (2009). Document available at:
    http://www.ga.gov.au/cedda/publications/193?yp=2009

    Extends
    :class:`openquake.hazardlib.gsim.somerville_2009.SomervilleEtAl2009NonCratonic`
    because the same functional form is used, only the coefficents differ.
    """

    #: Coefficients taken from table 4
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT     c1        c2        c3       c4        c5        c6        c7        c8       sigma
    pgv     5.23440   1.58530  -1.01540  0.21400  -0.00341  -0.91610   1.12980   0.14810  0.6606
    pga     1.54560   1.45650  -1.11510  0.16640  -0.00567  -1.04900   1.05530   0.20000  0.5513
    0.010   1.55510   1.46380  -1.11460  0.16620  -0.00568  -1.04840   1.05850   0.20140  0.5512
    0.020   2.33800   1.38060  -1.22970  0.18010  -0.00467  -1.39850   0.95990   0.20130  0.5510
    0.030   2.48090   1.37540  -1.17620  0.17120  -0.00542  -1.38720   0.96930   0.19280  0.5508
    0.040   2.31450   1.60250  -1.12600  0.17150  -0.00629  -1.27910   1.07040   0.23560  0.5509
    0.050   2.26860   1.55840  -1.07340  0.14710  -0.00709  -1.08910   1.10750   0.20670  0.5510
    0.075   1.97070   1.68030  -1.01540  0.14560  -0.00737  -0.91930   1.18290   0.22170  0.5514
    0.100   1.71030   1.75070  -0.99330  0.13820  -0.00746  -0.78140   1.29390   0.23790  0.5529
    0.150   1.52310   1.69160  -0.96310  0.13330  -0.00713  -0.67330   1.22430   0.21020  0.5544
    0.200   1.36830   1.57940  -0.94720  0.13640  -0.00677  -0.62690   1.17760   0.18950  0.5558
    0.250   1.40180   1.28940  -0.94410  0.14360  -0.00617  -0.67070   1.05610   0.14590  0.5583
    0.3003  1.45000   1.04630  -0.94880  0.14760  -0.00581  -0.68700   0.94040   0.11040  0.5602
    0.400   1.44150   0.92820  -0.91830  0.11320  -0.00576  -0.59520   0.86280   0.04060  0.5614
    0.500   1.40380   0.69160  -0.91010  0.13480  -0.00557  -0.62390   0.71230   0.00620  0.5636
    0.750   1.50840   0.75800  -0.99010  0.11260  -0.00458  -0.69040   0.68590  -0.05630  0.5878
    1.000   2.10630   0.38180  -1.08680  0.07950  -0.00406  -0.90340   0.61850  -0.18250  0.6817
    1.4993  2.55790  -0.84270  -0.81810  0.07650  -0.00220  -1.35320  -0.25440  -0.46660  0.8514
    2.000   2.39600  -1.39950  -0.70440  0.06770  -0.00366  -0.90860  -0.64320  -0.59600  0.8646
    3.0003  0.96040  -0.46120  -0.70450  0.06450  -0.00429  -0.51190  -0.16430  -0.46310  0.8424
    4.000   0.12190  -0.06980  -0.75910  0.08490  -0.00374  -0.41450   0.12350  -0.39250  0.8225
    5.000  -0.84240   0.53160  -0.79600  0.10330  -0.00180  -0.62130   0.53680  -0.27570  0.8088
    7.5019 -1.92260   0.63760  -0.81900  0.14550  -0.00066  -0.75740   0.69020  -0.23290  0.7808
    10.000 -2.60330   0.59060  -0.80940  0.16090  -0.00106  -0.68550   0.70350  -0.22910  0.7624
    """)

class SomervilleEtAl2009NonCratonic_SS14(SomervilleEtAl2009NonCratonic):
    """
    SomervilleEtAl2009NonCratonic model updated to apply the linear and non-linear amplification factors of Sayhan & 
    Stewart (2014) as applied in the Boore et al (2014) NGE-West 2 GMMfor use in Geoscience Australia ShakeMap
    """
    
    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # get coefficients for rock PGA
        C_PGA = self.COEFFS[PGA()]
        BEA14_C_PGA = boore_2014.BooreEtAl2014.COEFFS[PGA()]
        
        # get rock PGA - correct from PGA(865 m/s) to PGA(760 m/s)
        pga_rock = _compute_mean(C_PGA, ctx.mag, ctx.rjb)
        
        # make array like ctx.vs30 of 865 m/s
        sites_865 = 865. * np.ones_like(ctx.vs30)
        
        # use Boore et al (2014) amplification factors
        flin_865_760 = boore_2014._get_linear_site_term(BEA14_C_PGA, sites_865)
        fnl_865_760  = boore_2014._get_nonlinear_site_term(BEA14_C_PGA, sites_865, np.exp(pga_rock))
        
        # apply correction to get PGA(760 m/s)
        pga_rock_760 = pga_rock - flin_865_760 - fnl_865_760
        
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            
            # get amplification model coefficients from Boore et al, 2014
            BEA14_C = boore_2014.BooreEtAl2014.COEFFS[imt]
            
            # correction from 865 m/s to 760 m/s
            flin_865_760 = boore_2014._get_linear_site_term(BEA14_C, sites_865)
            fnl_865_760 = boore_2014._get_nonlinear_site_term(BEA14_C, sites_865, np.exp(pga_rock))
            
            # correction from 760 m/s to target vs30
            flin = boore_2014._get_linear_site_term(BEA14_C, ctx.vs30)
            fnl  = boore_2014._get_nonlinear_site_term(BEA14_C, ctx.vs30, np.exp(pga_rock_760))
            
            mean[m] = _compute_mean(C, ctx.mag, ctx.rjb) - flin_865_760 - fnl_865_760 + flin + fnl 
            
            sig[m] = C['sigma']

            
class SomervilleEtAl2009YilgarnCraton_SS14(SomervilleEtAl2009YilgarnCraton):
    """
    SomervilleEtAl2009YilgarnCraton model updated to apply the linear and non-linear amplification factors of Sayhan & 
    Stewart (2014) as applied in the Boore et al (2014) NGE-West 2 GMM for use in Geoscience Australia ShakeMap
    """
    
    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # get coefficients for rock PGA
        C_PGA = self.COEFFS[PGA()]
        BEA14_C_PGA = boore_2014.BooreEtAl2014.COEFFS[PGA()]
        
        # get rock PGA - correct from PGA(865 m/s) to PGA(760 m/s)
        pga_rock = _compute_mean(C_PGA, ctx.mag, ctx.rjb)
        
        # make array like ctx.vs30 of 865 m/s
        sites_865 = 865. * np.ones_like(ctx.vs30)
        
        # use Boore et al (2014) amplification factors
        flin_865_760 = boore_2014._get_linear_site_term(BEA14_C_PGA, sites_865)
        fnl_865_760  = boore_2014._get_nonlinear_site_term(BEA14_C_PGA, sites_865, np.exp(pga_rock))
        
        # apply correction to get PGA(760 m/s)
        pga_rock_760 = pga_rock - flin_865_760 - fnl_865_760
        
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            
            # get amplification model coefficients from Boore et al, 2014
            BEA14_C = boore_2014.BooreEtAl2014.COEFFS[imt]
            
            # correction from 865 m/s to 760 m/s
            flin_865_760 = boore_2014._get_linear_site_term(BEA14_C, sites_865)
            fnl_865_760 = boore_2014._get_nonlinear_site_term(BEA14_C, sites_865, np.exp(pga_rock))
            
            # correction from 760 m/s to target vs30
            flin = boore_2014._get_linear_site_term(BEA14_C, ctx.vs30)
            fnl  = boore_2014._get_nonlinear_site_term(BEA14_C, ctx.vs30, np.exp(pga_rock_760))
            
            mean[m] = _compute_mean(C, ctx.mag, ctx.rjb) - flin_865_760 - fnl_865_760 + flin + fnl 
            
            sig[m] = C['sigma']