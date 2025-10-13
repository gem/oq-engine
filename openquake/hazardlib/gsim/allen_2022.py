# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module exports :class:`Allen2022`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def  _get_site_scaling(C, vs30):
    """
    Returns the site scaling term (equation 6)
    on page 1050
    """
    
    return C["s0"] + C["s1"] / (np.log10(vs30) - np.log10(150.))


def _get_magnitude_scaling(C, mag):
    """
    Returns the magnitude scling term defined in equation (3)
    on page 1048
    """
    
    return C["c0"] + C["c1"] * (mag-6.0)**2 + C["c2"] * (mag-6.0)
    
        
def _get_depth_scaling(C, hypo_depth):
    """
    Returns the magnitude scling term defined in equation (4)
    on page 1049
    """
    log_depth = np.log10(hypo_depth)
    
    return C["d0"] + C["d1"] * log_depth**3 + C["d2"] * log_depth**2 + C["d3"] * log_depth
    

def _get_path_scaling(C, rhypo):
    """
    Returns the path scaling term given by equation (2) and (5)
    on page 1047 & 1050
    """
    rx = 600. # hinge distance in km
    
    # get far-field term (eqn 2)
    far_term = np.where(rhypo <= rx,
                        C["c3"] * np.log10(rhypo),
                        C["c3"] * np.log10(rx) + C["c4"] * (np.log10(rhypo) - np.log10(rx)))
    
    # get near-field correction (eqn 5)
    near_term = np.where(rhypo <= rx,
                         C["n0"] * (np.log10(rhypo) - np.log10(rx)),
                         0.)
    
    return near_term + far_term
    

class Allen2022(GMPE):
    """
    Implements GMPE developed by Allen and published as
    "Allen, T. I. (2022). A farfield groundmotion model for the North Australian 
    Craton from platemargin earthquakes, Bull. Seismol. Soc. Am., doi: 10.1785/0120210191.
    """

    #: Supported tectonic region type is subduction interface.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see table 1, pages 227 and 228.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components.
    #DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL # no GEOMETRIC_MEAN option

    #: Supported standard deviation types is total, see equations 9-10 page 1051.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {                                                                              
          const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
    
    #DEFINED_FOR_REFERENCE_VELOCITY = 760

    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, and focal depth, see
    #: equation 10 page 226.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is hypocentral distance, see equation 10
    #: page 226.
    REQUIRES_DISTANCES = {'rhypo'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (_get_magnitude_scaling(C, ctx.mag) +
                       _get_path_scaling(C, ctx.rhypo) +
                       _get_depth_scaling(C, ctx.hypo_depth) +
                       _get_site_scaling(C, ctx.vs30))
            
            tau[m] = C['tau']
            phi[m] = C['phi']
            
            # cannot use np.sqrt(tau**2 + phi**2) because of additional PGA conversion factor (see equation 10 on P 1051)
            # must read from table
            sig[m] = C['sigma'] 
            

    #: Coefficient table (see table 1 page 1047.)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         c0        c1        c2        c3        c4        d0         d1       d2          d3         n0         s0        s1       tau       phi     sigma
    pgv     5.1394    0.0000    1.9713   -2.6644    -7.336    5.2107    -1.8808    9.459     -13.949    -1.0181    -0.5880    0.2536    0.6361    0.4883    0.8019
    pga    -4.5508    0.0000    1.6129   -0.4923    -10.167   4.8787    -2.5207    12.070    -16.388    -1.3651    -1.0254    0.4008    0.7066    0.5094    0.9118
    0.1    -5.3000    0.0000    1.4672    0.0000    -10.513   4.3555    -2.7260    12.699    -16.557    -2.6602    -1.0022    0.4258    0.7532    0.5038    0.9061
    0.15   -5.2557    0.0000    1.4638    0.0456    -10.580   5.7681    -2.9707    14.147    -19.169    -1.2049    -0.9190    0.4239    0.7578    0.5252    0.9220
    0.2    -5.1597    0.0000    1.4603    0.0284    -10.382   6.0008    -3.0078    14.372    -19.594    -1.2446    -0.8846    0.4066    0.7568    0.5343    0.9264
    0.25   -5.0958    0.0000    1.4502   -0.0069    -10.080   6.0464    -3.0019    14.338    -19.567    -1.3811    -0.8669    0.3822    0.7436    0.5291    0.9127
    0.3    -4.9242    0.0000    1.4988   -0.0897    -9.920    6.5203    -3.0348    14.583    -20.160    -1.4749    -0.7987    0.3619    0.7172    0.5286    0.8910
    0.4    -4.2365   -0.0213    1.6047   -0.3716    -9.728    6.1641    -2.8040    13.533    -18.818    -1.5512    -0.7893    0.3403    0.7019    0.5499    0.8917
    0.5    -1.6262   -0.0192    1.6542   -1.4501    -8.792    6.7588    -2.7780    13.581    -19.326    -1.0315    -0.6889    0.3084    0.7046    0.5530    0.8957
    0.6     0.1424   -0.0670    1.7420   -2.2296    -7.931    5.3677    -2.4344    11.765    -16.380    -1.1632    -0.6341    0.2919    0.6765    0.5214    0.8541
    0.75    1.8210   -0.1674    1.9003   -3.0099    -6.912    4.4379    -2.0824    10.083    -13.980    -1.0232    -0.7019    0.2781    0.6455    0.4849    0.8073
    1.0     3.4777   -0.2088    1.9943   -3.8107    -6.044    4.8745    -1.9619    9.702     -13.938    -1.0307    -0.6230    0.2654    0.6146    0.4532    0.7636
    1.25    4.7348   -0.1776    2.1150   -4.4348    -5.403    5.2371    -1.8821    9.451     -13.950    -0.8072    -0.5700    0.2509    0.6223    0.4257    0.7540
    1.5     5.6353   -0.2334    2.2245   -4.8971    -4.781    5.9873    -1.9196    9.800     -14.879    -0.9129    -0.5587    0.2342    0.6233    0.4387    0.7622
    2.0     6.0524   -0.3545    2.4366   -5.2236    -4.348    5.0004    -1.5450    7.960     -12.217    -0.6695    -0.4756    0.2230    0.5910    0.4394    0.7365
    2.5     5.7973   -0.3619    2.4976   -5.2934    -4.005    5.0432    -1.4210    7.407     -11.637    -0.6849    -0.4486    0.2183    0.5689    0.4162    0.7049
    3.0     5.4552   -0.3484    2.5378   -5.3066    -3.734    5.0210    -1.3028    6.860     -11.007    -0.6495    -0.4330    0.2095    0.5618    0.4033    0.6915
    4.0     4.8483   -0.3590    2.6446   -5.2890    -3.656    5.0015    -1.1239    6.057     -10.102    -0.4710    -0.3915    0.2042    0.6152    0.3843    0.7254
    5.0     4.1446   -0.3549    2.7324   -5.1969    -3.636    5.0599    -1.0292    5.628     -9.653     -0.5199    -0.4377    0.1985    0.6352    0.3917    0.7463
    6.0     3.4946   -0.3247    2.7833   -5.1162    -3.547    4.6695    -0.9160    5.042     -8.744     -0.5526    -0.4253    0.1910    0.6207    0.4018    0.7394
    7.5     2.8095   -0.3034    2.7654   -5.0636    -3.453    4.7249    -0.8061    4.540     -8.204     -0.5132    -0.4327    0.1820    0.5969    0.4066    0.7222
    10.0    2.0278   -0.3459    2.7722   -5.0168    -3.368    5.0737    -0.7276    4.187     -7.966     -0.2645    -0.4564    0.1736    0.5880    0.4185    0.7217
    """)