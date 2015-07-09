# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Module exports :class:`TusaLanger2015`.
"""
from __future__ import division

import numpy as np

from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class TusaLanger2015(GMPE):
    """
    Implements GMPE developed by Giuseppina Tusa and Horst Langer 
    (not yet published in June 2015), in the frame of V3-2012 INGV-DPC Project 
    
    The GMPE in terms of SA derives from shallow earthquakes at Mt. Etna in the 
    magnitude range 3<ML<4.3 for hypocentral distances < 100 km, and soil classes A, 
    B, and D. The GMPE in terms of PGA is for hypocentral distances < 30 km, and 
    soil class B ONLY. 

    The functional form includes magnitude, distance, and site amplification terms.
    Infomation was provided via email by Giuseppina Tusa dated May 29, 2015. 
    """

    #: Supported tectonic region type is 'volcanic' because the
    #: equations have been derived from data from Etna (Sicily, Italy)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
	PGA,       
	SA
    ])

    #: Supported intensity measure component is the maximum of two horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameter is Vs30 
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is Rhypo
    REQUIRES_DISTANCES = set(('rhypo',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type 

        C = self.COEFFS[imt]

	imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(rup, dists, C)+
		 self._get_site_amplification(sites, C)) 
                    	
        istddevs = self._get_stddevs(C, stddev_types, dists.rhypo.shape[0])


        # convert from log10 to ln and from cm/s**2 to g
        mean = np.log((10.0 ** (imean - 2.0)) / g)
        
        # Return stddevs in terms of natural log scaling
        stddevs = np.log(10.0 ** np.array(istddevs))
       
        
        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 1
        """
       
	assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)
        stddevs = [np.zeros(num_sites) + C['SigmaTot'] for _ in stddev_types]
        return stddevs


    def _compute_distance(self, rup, dists, C):
        """
        Compute the distance function:
        ``c1 + c2 * (M-Mref) * log(sqrt(rhypo ** 2 + h ** 2)/Rref) -
             c3*(sqrt(rhypo ** 2 + h ** 2)-Rref)``
        """
        mref = 3.6
        rref = 1.0
        rval = np.sqrt(dists.rhypo ** 2 + C['h'] ** 2)
        return (C['c1'] + C['c2'] * (rup.mag - mref)) *\
            np.log10(rval / rref) + C['c3'] * (rval - rref)



    def _compute_magnitude(self, rup, C):
        """
        Compute the magnitude function:
        e1 + b1 * (M) + b2 * (M)**2 for M<=Mh
         """
        
        return C['e1'] + (C['b1'] * (rup.mag)) +\
                (C['b2'] * (rup.mag) ** 2)


    def _get_site_amplification(self, sites, C):
	
	"""
	Compute the site amplification function given by FS = eiSi,
        for i = 1,2,3 where Si are the coefficients determined through 
        regression analysis, and ei are dummy variables (0 or 1) used 
        to denote the different EC8 site classes.
  
	Note: for SA, ei=0 for site class A (no site amplification term)
        and for PGA, ei=0 for all site classes (never site amplification term)
	"""

	ssa, ssb, ssd = self._get_site_type_dummy_variables(sites)
	
	return (C['sA'] * ssa) + (C['sB'] * ssb) + (C['sD'] * ssd) 

	
    def _get_site_type_dummy_variables(self, sites):

	"""
	Get site type dummy variables, which classified the sites into different
        site classes based on the shear wave velocity in the upper 30 m (Vs30)
	according to the EC8 (CEN 2003):
	class A: Vs30 > 800 m/s
	class B: Vs30 = 360 - 800 m/s
	class C*: Vs30 = 180 - 360 m/s
	class D: Vs30 < 180 m/s
	class E*: 5-20m of C- or D-type alluvium underlain by material with Vs30 > 800 m/s.

        *Not computed by this GMPE

	"""
	ssa = np.zeros(len(sites.vs30))
	ssb = np.zeros(len(sites.vs30))
	ssd = np.zeros(len(sites.vs30))
	

	# Class D; Vs30 < 180 m/s.
	idx = (sites.vs30 >= 1E-10) & (sites.vs30 < 180.0)
	ssd[idx] = 1.0
	# Class B; 360 m/s <= Vs30 <= 800 m/s.
	idx = (sites.vs30 >= 360.0) & (sites.vs30 < 800)
	ssb[idx] = 1.0
	# Class A; Vs30 > 800 m/s.
	idx = (sites.vs30 >= 800.0)
	ssa[idx] = 1.0
	

	return ssa, ssb, ssd
        
    # coefficient table for SA provided in "SpectralAccXLaura.xlsx" and for PGA in "SpectralAccXRobin.xlsx"
    # sigma values provided in ln and converted to log (below)

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT		e1	c1      c2      h      c3      		b1      b2	sA	sB	sD 	SigmaTot
    pga		-0.0333	-2.2379	0.3107	2.696	-0.0062911	0.9542	-0.0829	0	0	0	0.4017 
    0.10	0.8594	-2.2258	0.0066	1.8689	0.006867	0.0525	0.0790	0	0.41397	0.42120	0.4424	
    0.20	1.0619	-2.2684	0.0194	2.6969	0.007245	0.0418	0.0804	0	0.47176	0.56672	0.3960
    0.25	0.9928	-2.2318	0.0067	3.1724	0.006746	0.0316	0.0904	0	0.47069	0.51751	0.3779
    0.40	-1.8031	-1.9414	0.0496	3.0608	0.004712	1.4272	-0.1051	0	0.49105	0.54594	0.3353
    0.50	-1.4907	-1.9292	0.1235	3.3918	0.004911	1.2390	-0.0806	0	0.48505	0.50924	0.3401
    1.00	-0.6283	-1.5327	0.2391	2.7319	0.0005733	0.3082	0.0638	0	0.46483	0.40585	0.3549
    1.25	-1.8557	-1.4873	0.1883	3.0522	-0.0006545	0.7888	0.0174	0	0.43149	0.36715	0.3426
    2.00	-4.8586	-1.1999	0.0767	2.8470	-0.004367	1.7503	-0.0610	0	0.36832	0.34906 0.3567
    """) 
       		 # a     c1      c2      h      c3     		 b1      b2    				"RMS"    
