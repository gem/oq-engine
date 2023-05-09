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

import pathlib
import unittest
import numpy as np
from matplotlib import pyplot

from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface import PlanarSurface
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.geo import utils as geo_utils
from openquake.hazardlib.geo.geodetic import npoints_towards
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.const import TRT
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.gsim.zhao_2016 import ZhaoEtAl2016SSlabPErg

HERE = pathlib.Path(__file__)

def _get_first_point(rup, from_point):
    """
    :param rup:
    :param from_point:
    """
    sfc = rup.surface
    if from_point == 'TC':
        return sfc._get_top_edge_centroid()
    elif from_point == 'BC':
        lon, lat = geo_utils.get_middle_point(
            sfc.corner_lons[2], sfc.corner_lats[2],
            sfc.corner_lons[3], sfc.corner_lats[3]
        )
        return Point(lon, lat, sfc.corner_depths[2])
    elif from_point == 'TL':
        idx = 0
    elif from_point == 'TR':
        idx = 1
    elif from_point == 'BR':
        idx = 2
    elif from_point == 'BL':
        idx = 3
    else:
        raise ValueError('Unsupported option from first point')
    return Point(sfc.corner_lons[idx],
                 sfc.corner_lats[idx],
                 sfc.corner_depths[idx])

def get_sites_from_rupture(rup, from_point='TC', toward_azimuth=90,
                           direction='positive', hdist=100, step=5.,
                           site_props=''):
    """
    :param rup:
    :param from_point:
        A string. Options: 'TC', 'TL', 'TR'
    :return:
        A :class:`openquake.hazardlib.site.SiteCollection` instance
    """
    from_pnt = _get_first_point(rup, from_point)
    lon = from_pnt.longitude
    lat = from_pnt.latitude
    depth = 0
    vdist = 0
    npoints = hdist / step
    strike = rup.surface.strike
    pointsp = []
    pointsn = []

    if not len(site_props):
        raise ValueError()

    if direction in ['positive', 'both']:
        azi = (strike+toward_azimuth) % 360
        pointsp = npoints_towards(lon, lat, depth, azi, hdist, vdist, npoints)

    if direction in ['negative', 'both']:
        idx = 0 if direction == 'negative' else 1
        azi = (strike+toward_azimuth+180) % 360
        pointsn = npoints_towards(lon, lat, depth, azi, hdist, vdist, npoints)

    sites = []
    keys = set(site_props.keys()) - set(['vs30', 'z1pt0', 'z2pt5'])

    if len(pointsn):
        for lon, lat in reversed(pointsn[0][idx:], pointsn[1])[idx:]:
            site = Site(Point(lon, lat, 0.0), vs30=site_props['vs30'],
                        z1pt0=site_props['z1pt0'], z2pt5=site_props['z2pt5'])
            for key in list(keys):
                setattr(site, key, site_props[key])
            sites.append(site)

    for lon, lat in zip(pointsp[0], pointsp[1]):
        site = Site(Point(lon, lat, 0.0), vs30=site_props['vs30'],
                    z1pt0=site_props['z1pt0'], z2pt5=site_props['z2pt5'])
        for key in list(keys):
            setattr(site, key, site_props[key])
        sites.append(site)

    return SiteCollection(sites)

def get_rupture(lon, lat, dep, msr, mag, aratio, strike, dip, rake, trt,
                ztor=None):
    """
    Creates a rupture given the hypocenter position
    """
    hypoc = Point(lon, lat, dep)
    srf = PlanarSurface.from_hypocenter(hypoc, msr, mag, aratio, strike, dip,
                                        rake, ztor)
    rup = BaseRupture(mag, rake, trt, hypoc, srf)
    rup.hypo_depth = dep
    return rup

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
    
    # Plot perg vs non-perg for distances in sites collection
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
    pyplot.show()
    
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
        lon = 106.86
        lat = 37.95
        dep = 10.0
        msr = WC1994()
        mag = 7.0
        aratio = 2.0
        strike = 270.0
        dip = 30.0
        rake = 90.0
        trt = TRT.SUBDUCTION_INTERFACE
        ztor = 0.0
        self.rup = get_rupture(lon, lat, dep, msr, mag, aratio, strike, dip,
                          rake, trt, ztor)
        
        # Get implementations of Zhao et al. (2016) intra-slab GMM
        volc_arc_fname = HERE.parent / 'data' / 'ZHAO16PERG' / 'test_volc.geojson'
        self.gmm_perg = ZhaoEtAl2016SSlabPErg(volc_arc_fname)
        self.gmm = ZhaoEtAl2016SSlabPErg()
        
    def test01(self):
        """
        Test with azimuth of 90 degrees from rupture strike to sites collection
        in straight line for SA(0.5) through test volcanic zone polygons.
        """
        # General inputs
        imt = 'SA(0.5)'
        
        # Get sites from rupture
        from_point = 'TC'
        azimuth = 90 # relative to strike of slab
        direction = 'positive'
        hdist = 5000
        step = 25
        site_params = {'vs30': 800, 'z1pt0': 31.07, 'z2pt5': 0.57,
                       'backarc': False, 'vs30measured': True}

        sites = get_sites_from_rupture(self.rup, from_point, azimuth, direction,
                                       hdist, step, site_params)

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
        
        # Get sites from rupture
        from_point = 'TC'
        azimuth = 135 # relative to strike of slab
        direction = 'positive'
        hdist = 5000
        step = 25
        site_params = {'vs30': 800, 'z1pt0': 31.07, 'z2pt5': 0.57,
                       'backarc': False, 'vs30measured': True}

        sites = get_sites_from_rupture(self.rup, from_point, azimuth, direction,
                                       hdist, step, site_params)

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
        
        # Get sites from rupture
        from_point = 'TC'
        azimuth = 160 # relative to strike of slab
        direction = 'positive'
        hdist = 5000
        step = 25
        site_params = {'vs30': 800, 'z1pt0': 31.07, 'z2pt5': 0.57,
                       'backarc': False, 'vs30measured': True}

        sites = get_sites_from_rupture(self.rup, from_point, azimuth, direction,
                                       hdist, step, site_params)

        # Get non-ergodic and ergodic results 
        mean_perg, mean = get_gms_from_ctx(imt, self.rup, sites, self.gmm_perg,
                                           self.gmm, azimuth)     
        
    def test04(self):
        """
        Test with azimuth of 0 degrees from rupture strike to sites collection
        in straight line for SA(1.0). This test will generate zero difference
        in PErg and non-PErg because the generated travel paths do not pass
        through any volcanic zones.
        """
        # General inputs
        imt = 'SA(1.0)'
        
        # Get sites from rupture
        from_point = 'TC'
        azimuth = 0 # relative to strike of slab
        direction = 'positive'
        hdist = 5000
        step = 25
        site_params = {'vs30': 800, 'z1pt0': 31.07, 'z2pt5': 0.57,
                       'backarc': False, 'vs30measured': True}

        sites = get_sites_from_rupture(self.rup, from_point, azimuth, direction,
                                       hdist, step, site_params)

        # Get non-ergodic and ergodic results 
        mean_perg, mean = get_gms_from_ctx(imt, self.rup, sites, self.gmm_perg,
                                           self.gmm, azimuth)     
        
        msg = 'PErg and non-PErg GMs should be equal for this test scenario\
            (no volcanic zones are traversed)'
            
        # Check mean_perg and mean are equal
        for idx_mean, val_mean in enumerate(mean_perg):
            if mean_perg[idx_mean] != mean[idx_mean]:
                raise ValueError(msg) 