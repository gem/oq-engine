# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
import matplotlib.pyplot as plt

from openquake.hazardlib.geo import Point
from openquake.hazardlib.source.rupture import get_planar
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.const import TRT
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.gsim.zhao_2016 import ZhaoEtAl2016SSlabPErg
from openquake.hazardlib.gsim.zhao_2016 import ZhaoEtAl2016SSlab


DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'ZHAO16PERG',
                           'unit_test_volc.geojson')

PLOTTING = False # Checking locally if the results make sense

EXP = {
    "test01": {
        "mean_perg_exp": np.array([
             0.50978636, -0.73282322, -1.9922466 , -2.91597163, -3.58452487,
            -3.95891937, -4.25968319, -4.51153023, -4.72903257, -4.92139866,
            -5.09476288, -5.25338466, -5.40032202, -5.53783171, -5.66761804,
            -5.79099371, -5.90898709, -6.02241584, -6.13193862, -6.23809216,
            -6.34131843, -6.44198473, -6.54039893, -6.63682104, -6.73147222,
            -6.82454179, -6.91619275, -7.00656626, -7.09578512, -7.18395674,
            -7.27117541, -7.35752429, -7.44307696, -7.52789883, -7.61204816,
            -7.69557706, -7.77853227, -7.86095582, -7.94288562, -8.02435592,
            -8.10539779]),
        "mean_exp": np.array([
             0.50978636, -0.63166322, -1.70631981, -2.41609631, -2.91012487,
            -3.28451937, -3.58528319, -3.83713023, -4.05463257, -4.24699866,
            -4.42036288, -4.57898466, -4.72592202, -4.86343171, -4.99321804,
            -5.11659371, -5.23458709, -5.34801584, -5.45753862, -5.56369216,
            -5.66691843, -5.76758473, -5.86599893, -5.96242104, -6.05707222,
            -6.15014179, -6.24179275, -6.33216626, -6.42138512, -6.50955674,
            -6.59677541, -6.68312429, -6.76867696, -6.85349883, -6.93764816,
            -7.02117706, -7.10413227, -7.18655582, -7.26848562, -7.34995592,
            -7.43099779]),
    },
    "test02": {
        "mean_perg_exp": np.array([
             0.90265217, -0.14413423, -1.38900669, -2.63340665, -3.62036963,
            -4.14915887, -4.53109497, -4.85691431, -5.14318463, -5.40025894,
            -5.63500093, -5.85217462, -6.0552097 , -6.24665007, -6.42843   ,
            -6.60205138, -6.7687015 , -6.92933372, -7.08472406, -7.2355118 ,
            -7.3822293 , -7.52532412, -7.66517579, -7.80210872, -7.93640212,
            -8.06829794, -8.19800702, -8.32571418, -8.4515822 , -8.57575514,
            -8.69836105, -8.81951423, -8.93931707, -9.05786162, -9.17523093,
            -9.29150014, -9.40673745, -9.52100492, -9.6343592 , -9.74685208,
            -9.85853106]),
        "mean_exp": np.array([
             0.90265217,  0.03574577, -1.01204443, -1.87652767, -2.48322564,
            -2.94995887, -3.33189497, -3.65771431, -3.94398463, -4.20105894,
            -4.43580093, -4.65297462, -4.8560097 , -5.04745007, -5.22923   ,
            -5.40285138, -5.5695015 , -5.73013372, -5.88552406, -6.0363118 ,
            -6.1830293 , -6.32612412, -6.46597579, -6.60290872, -6.73720212,
            -6.86909794, -6.99880702, -7.12651418, -7.2523822 , -7.37655514,
            -7.49916105, -7.62031423, -7.74011707, -7.85866162, -7.97603093,
            -8.09230014, -8.20753745, -8.32180492, -8.4351592 , -8.54765208,
            -8.65933106]),
    },
    "test03": {
        "mean_perg_exp": np.array([
             1.20864268,  0.66173141, -1.0041104 , -2.116025  , -3.03994548,
            -3.4985904 , -3.85870347, -4.17401784, -4.45799618, -4.71909425,
            -4.96291449, -5.1933301 , -5.41311263, -5.62430254, -5.82843837,
            -6.02670396, -6.22002635, -6.40914261, -6.59464672, -6.77702305,
            -6.95667082, -7.13392221, -7.30905601, -7.48230804, -7.65387921,
            -7.82394182, -7.99264449, -8.16011616, -8.32646924, -8.49180225,
            -8.65620186, -8.81974465, -8.98249856, -9.14452407, -9.30587521,
            -9.46660038, -9.62674309, -9.78634256, -9.94543421, -10.10405016,
            -10.26221955]),
        "mean_exp": np.array([
             1.20864268,  0.66173141, -0.56530201, -1.30331405, -1.84114812,
            -2.2689904 , -2.62910347, -2.94441784, -3.22839618, -3.48949425,
            -3.73331449, -3.9637301 , -4.18351263, -4.39470254, -4.59883837,
            -4.79710396, -4.99042635, -5.17954261, -5.36504672, -5.54742305,
            -5.72707082, -5.90432221, -6.07945601, -6.25270804, -6.42427921,
            -6.59434182, -6.76304449, -6.93051616, -7.09686924, -7.26220225,
            -7.42660186, -7.59014465, -7.75289856, -7.91492407, -8.07627521,
            -8.23700038, -8.39714309, -8.55674256, -8.71583421, -8.87445016,
            -9.03261955]),
    },
}


def get_gms_from_ctx(imt, rup, sites, gmm_perg, gmm, azimuth):
    """
    Get ground-motion with and without non-ergodic path effect modifications
    and create trellis plots to visually inspect
    """
    # Create context for computation of ground-motions
    oqp = {'imtls': {k: [] for k in [str(imt)]}, 'mags': [f'{rup.mag:.2f}']}

    # Get perg version ground-motions
    ctxm_perg = ContextMaker(
        gmm_perg.DEFINED_FOR_TECTONIC_REGION_TYPE, [gmm_perg], oqp)

    ctxs_perg = ctxm_perg.get_ctxs([rup], sites)
    ctxs_perg = ctxs_perg[0]
    mean_perg, _std_perg, _tau_perg, _phi_perg = ctxm_perg.get_mean_stds(
        [ctxs_perg])

    # Get non-perg version ground-motions
    ctxm = ContextMaker(gmm.DEFINED_FOR_TECTONIC_REGION_TYPE, [gmm], oqp)
    ctxs = ctxm.get_ctxs([rup], sites)
    ctxs = ctxs[0]

    ctxs.occurrence_rate = 0.0
    mean, _std, _tau, _phi = ctxm.get_mean_stds([ctxs])

    # Plot perg and non-perg ground-motions vs rrup
    dist_x = ctxs.rrup
    mean_perg = mean_perg[0][0]
    mean = mean[0][0]

    if PLOTTING:
        _fig, _axs = plt.subplots(1, 1)
        plt.plot(dist_x, np.exp(mean_perg), 'r', label='PErg')
        plt.plot(dist_x, np.exp(mean), 'b', label='Non-PErg')
        plt.ylabel('%s (g)' % (imt))
        plt.xlabel('Rupture Distance (km)')
        plt.title('Test scenario for imt = %s and site azimuth = %s$^o$' % (
            imt, azimuth))
        plt.legend()
        plt.xscale('log')
        plt.show()

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
    configurations through these volcanic zone polygons.
    """
    def setUp(self):
        """
        Create rupture context and setup non-ergodic and ergodic
        implementations of Zhao et al. (2016) intra-slab GMM.
        """
        # Get rupture
        hypo = Site(Point(108.08, 28.328, 10.0))
        self.rup = get_planar(hypo, msr=WC1994(), mag=7.0, aratio=2.0,
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
        self.gmm_perg = ZhaoEtAl2016SSlabPErg(volc_arc_file=volc_arc_fname)
        self.gmm = ZhaoEtAl2016SSlab()

    def test01(self):
        """
        Test with azimuth of 90 degrees from rupture strike to sites collection
        in straight line for SA(0.5) through test volcanic zone polygons.
        """
        # General inputs
        imt = 'SA(0.5)'
        azimuth = 90  # relative to strike of slab
        sites = SiteCollection.from_planar(self.rup, self.from_point, azimuth,
                                           self.direction, self.hdist,
                                           self.step, self.site_params)

        # Get non-ergodic and ergodic results
        mean_perg, mean = get_gms_from_ctx(
            imt, self.rup, sites, self.gmm_perg, self.gmm, azimuth)

        # Check getting expected results        
        np.testing.assert_allclose(mean_perg, EXP["test01"]["mean_perg_exp"], rtol=1e-6)
        np.testing.assert_allclose(mean, EXP["test01"]["mean_exp"], rtol=1e-6)

    def test02(self):
        """
        Test with azimuth of 135 degrees from rupture strike to sites
        collection in straight line for PGA through test volcanic zone
        polygons.
        """
        # General inputs
        imt = 'PGA'
        azimuth = 135  # relative to strike of slab
        sites = SiteCollection.from_planar(self.rup, self.from_point, azimuth,
                                           self.direction, self.hdist,
                                           self.step, self.site_params)

        # Get non-ergodic and ergodic results
        mean_perg, mean = get_gms_from_ctx(
            imt, self.rup, sites, self.gmm_perg, self.gmm, azimuth)
        
        # Check getting expected results        
        np.testing.assert_allclose(mean_perg, EXP["test02"]["mean_perg_exp"], rtol=1e-6)
        np.testing.assert_allclose(mean, EXP["test02"]["mean_exp"], rtol=1e-6)


    def test03(self):
        """
        Test with azimuth of 160 degrees from rupture strike to sites
        collection in straight line for SA(0.2) through test volcanic zone
        polygons.
        """
        # General inputs
        imt = 'SA(0.2)'
        azimuth = 160  # relative to strike of slab
        sites = SiteCollection.from_planar(self.rup, self.from_point, azimuth,
                                           self.direction, self.hdist,
                                           self.step, self.site_params)
        # Get non-ergodic and ergodic results
        mean_perg, mean = get_gms_from_ctx(
            imt, self.rup, sites, self.gmm_perg, self.gmm, azimuth)
        
        # Check getting expected results        
        np.testing.assert_allclose(mean_perg, EXP["test03"]["mean_perg_exp"], rtol=1e-6)
        np.testing.assert_allclose(mean, EXP["test03"]["mean_exp"], rtol=1e-6)

    def test04(self):
        """
        Test with azimuth of 350 degrees from rupture strike to sites
        collection in straight line for SA(1.0). This test will generate zero
        difference in PErg and non-PErg because the generated travel paths do
        not pass through any volcanic zones.
        """
        # General inputs
        imt = 'SA(1.0)'
        azimuth = 350  # relative to strike of slab
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
