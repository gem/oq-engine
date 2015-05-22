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
Module exports :class:`TusaLanger2013`.
"""
from __future__ import division

import numpy as np

from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA


class TusaLanger2013(GMPE):
    """
    Implements GMPE ("INV7") developed by Giuseppina Tusa and Horst Langer 
    (not yet published in Apr 2015), in the frame of V3-2012 INGV-DPC Project 
    as described on page 18 of "Analisi multi-disciplinare delle relazioni tra
    strutture tettoniche e attivita vulcanica. Rapporto scientifico finale, 
    Settembre 2013"

    The GMPE derives from shallow earthquakes at Mt. Etna in the magnitude 
    range 2.5<ML<4.8 for epicentral distances < 15 km, and soil class B stations.
    The functional form includes magnitude and distance functions

    IMPORTANT: This GMPE was originally derived using epicentral distance (for 
    which it passes nosetests using test tables provided by the authors); however, 
    it has been modified below to consider hypocentral distance for the sake of 
    experimenting with PSHA calculations in volcanic areas where topography is 
    taken into consideration (hence dependence on vertical distance is required)

    """

    #: Supported tectonic region type is 'volcanic' because the
    #: equations have been derived from data from Etna (Sicily, Italy)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA
    ])

    #: Supported intensity measure component is the maximum of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation types are total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No required site parameters since we only consider site class B 
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude.
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
        # intensity measure type (pga)

        C = self.COEFFS[imt]

	imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(rup, dists, C)) 
                         
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
        
    #: coefficient table provided in "PerRaff&Laur+lpf.xls", sigma given in log
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT	e1	c1      c2      h      c3      b1      b2		SigmaTot
    pga	1.068	-3.946	0.09056 3.881  0.0784  0.6661  -0.008909	0.354
    """) 

        # B1     B4     B5      h      b7      b2      b3              "epsilon"       
