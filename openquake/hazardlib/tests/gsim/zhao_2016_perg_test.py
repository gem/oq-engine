# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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

import os
import unittest
import numpy as np
from matplotlib import pyplot

from openquake.hazardlib.geo import Point
from openquake.hazardlib.source.rupture import get_planar
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.const import TRT
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.gsim.zhao_2016 import ZhaoEtAl2016SSlabPErg
from openquake.hazardlib.gsim.zhao_2016 import ZhaoEtAl2016SSlab

DATA_FOLDER = os.path.join(os.path.dirname(__file__),'data', 'ZHAO16PERG',
                           'unit_test_volc.geojson')


def get_gms_from_ctx(imt, rup, sites, gmm_perg, gmm, azimuth):
    """
    Get ground-motion with and without non-ergodic path effect modifications 
    and create trellis plots to visually inspect
    """
    # Create context for computation of ground-motions
    oqp = {'imtls': {k: [] for k in [str(imt)]}, 'mags': [f'{rup.mag:.2f}']}
    
    # Get perg version ground-motions
    ctxm_perg = ContextMaker(gmm_perg.DEFINED_FOR_TECTONIC_REGION_TYPE,
                             [gmm_perg], oqp)
    
    ctxs_perg = list(ctxm_perg.get_ctx_iter([rup], sites)) 
    ctxs_perg = ctxs_perg[0]
    ctxs_perg.occurrence_rate = 0.0
    mean_perg, std_perg, tau_perg, phi_perg = ctxm_perg.get_mean_stds(
        [ctxs_perg])

    # Get non-perg version ground-motions
    ctxm = ContextMaker(gmm.DEFINED_FOR_TECTONIC_REGION_TYPE, [gmm], oqp)
    ctxs = list(ctxm.get_ctx_iter([rup], sites)) 
    ctxs = ctxs[0]
    
    ctxs.occurrence_rate = 0.0
    mean, std, tau, phi = ctxm.get_mean_stds([ctxs])
    
    # Plot perg vs non-perg predicted gm vs rjb
    dist_x = ctxs.rrup
    mean_perg = mean_perg[0][0]
    mean = mean[0][0]
    pyplot.plot(dist_x, np.exp(mean_perg), 'r', label = 'PErg')
    pyplot.plot(dist_x, np.exp(mean), 'b', label = 'Non-PErg')
    pyplot.semilogy()
    pyplot.ylabel('%s (g)' %(imt))
    pyplot.xlabel('Joyner-Boore distance (km)')
    pyplot.title('Test scenario for imt = %s and site azimuth = %s$^o$' %(
        imt, azimuth))
    pyplot.legend()
    
    return mean_perg, mean
    
        
class TestZhao2016PErg(unittest.TestCase):
    """
    Test implementation of non-ergodic path modifications as described within
    the Zhao et al. (2016) GMMs. 5 volcanic zone polygons including complex
    shapes (i.e. ones which may be traversed multiple times by the same travel
    path) are considered here. The test volcanic zone polygons are in 
    openquake.hazardlib.tests.gsim.data.ZHAO16PERG. Multiple spectral ordinates
    are also considered.
    
    The test scenarios below consider sites generated w.r.t. the same rupture,
    but with different site azimuths, resulting in different travel path
    configurations through these volcanic zone polygons. The expected distances
    for many scenarios also not considered here were measured using QGIS, and
    excellent matches were observed when compared against the values computed
    using the ray tracing functions implemented here. These ray-tracing functions
    are found within openquake.hazardlib.gsim.zhao_2016_volc_perg.volc_perg
    
    The tests below test the execution of the non-ergodic implementation
    of ZhaoEtAlSSlabPErg, and demonstrate the difference in predicted
    ground-motion if these path modifications are considered.
    """
    def setUp(self):
        """
        Create rupture context and setup non-ergodic and ergodic implementations
        of Zhao et al. (2016) intra-slab GMM.
        """
        # Get rupture
        hypo = Site(Point(108.08, 28.328, 10.0))
        self.rup = get_planar(hypo, msr=WC1994(), mag=7.0,aratio=2.0,
                              strike=270.0, dip=30.0, rake=90.0,
                              trt=TRT.SUBDUCTION_INTERFACE, ztor=0.0)
        
        # Set site params
        self.site_params = {'vs30': 800, 'z1pt0': 31.07, 'z2pt5': 0.57,
                       'backarc': False, 'vs30measured': True}
        
        # Constants throughout tests
        self.from_point = 'TC'
        self.direction = 'positive'
        self.hdist = 5000
        self.step = 25
        
        # Get implementations of Zhao et al. (2016) intra-slab GMM
        volc_arc_fname = DATA_FOLDER
        self.gmm_perg = ZhaoEtAl2016SSlabPErg(volc_arc_fname)
        self.gmm = ZhaoEtAl2016SSlab()
        
    def test01(self):
        """
        Test with azimuth of 90 degrees from rupture strike to sites collection
        in straight line for SA(0.5) through test volcanic zone polygons.
        """
        # General inputs
        imt = 'SA(0.5)'
        azimuth = 90 # relative to strike of slab
        sites = SiteCollection.from_planar(self.rup, self.from_point, azimuth,
                                           self.direction, self.hdist,
                                           self.step, self.site_params)
        
        # Get non-ergodic and ergodic results 
        mean_perg, mean = get_gms_from_ctx(imt, self.rup, sites, self.gmm_perg,
                                           self.gmm, azimuth)
        
    def test02(self):
        """
        Test with azimuth of 135 degrees from rupture strike to sites collection
        in straight line for PGA through test volcanic zone polygons.
        """
        # General inputs
        imt = 'PGA'
        azimuth = 135 # relative to strike of slab
        sites = SiteCollection.from_planar(self.rup, self.from_point, azimuth,
                                           self.direction, self.hdist,
                                           self.step, self.site_params)

        # Get non-ergodic and ergodic results 
        mean_perg, mean = get_gms_from_ctx(imt, self.rup, sites, self.gmm_perg,
                                           self.gmm, azimuth)
        
    def test03(self):
        """
        Test with azimuth of 160 degrees from rupture strike to sites collection
        in straight line for SA(0.2) through test volcanic zone polygons.
        """
        # General inputs
        imt = 'SA(0.2)'
        azimuth = 160 # relative to strike of slab
        sites = SiteCollection.from_planar(self.rup, self.from_point, azimuth,
                                           self.direction, self.hdist,
                                           self.step, self.site_params)
        # Get non-ergodic and ergodic results 
        mean_perg, mean = get_gms_from_ctx(imt, self.rup, sites, self.gmm_perg,
                                           self.gmm, azimuth)     
        
    def test04(self):
        """
        Test with azimuth of 350 degrees from rupture strike to sites collection
        in straight line for SA(1.0). This test will generate zero difference
        in PErg and non-PErg because the generated travel paths do not pass
        through any volcanic zones.
        """
        # General inputs
        imt = 'SA(1.0)'
        azimuth = 350 # relative to strike of slab
        sites = SiteCollection.from_planar(self.rup, self.from_point, azimuth,
                                           self.direction, self.hdist,
                                           self.step, self.site_params)

        # Get non-ergodic and ergodic results 
        mean_perg, mean = get_gms_from_ctx(imt, self.rup, sites, self.gmm_perg,
                                           self.gmm, azimuth)     
        
        msg = 'PErg and non-PErg GMs should be equal for this test scenario\
            (no volcanic zones are traversed)'
            
        # Check mean_perg and mean are equal
        for idx_mean, val_mean in enumerate(mean_perg):
            if mean_perg[idx_mean] != mean[idx_mean]:
                raise ValueError(msg) 