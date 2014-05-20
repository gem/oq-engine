# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2013, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

"""
Test suite for hazard calculation functions
"""

import unittest
import numpy as np
from copy import deepcopy
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib import gsim
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.calc.hazard_curve import hazard_curves
import hmtk.hazard as haz

SUPPORTED_GSIMS = gsim.get_available_gsims()

class TestCheckSupportedIMTs(unittest.TestCase):
    """
    Checks the pre-processor for ensuring IMT input is correctly formatted
    """
    def setUp(self):
        """

        """
        self.imt_list = None

    def test_correct_input(self):
        """
        Checks the output when a correctly formatted list of IMTs is passed
        """
        self.imt_list = ['PGA', 'PGV', 'SA(0.2)']
        expected_output = [PGA(), PGV(), SA(period=0.2, damping=5.0)]
        output = haz._check_supported_imts(self.imt_list)
        self.assertListEqual(output, expected_output)

    def test_unsupported_imt_input(self):
        """
        Checks that when an unsupported IMT is input then an error is raised
        """
        self.imt_list = ['XXX', 'PGV', 'SA(0.2)']
        with self.assertRaises(ValueError) as ae:
            _ = haz._check_supported_imts(self.imt_list)
            self.assertEqual(ae.exception.message,
                             "IMT XXX not supported in OpenQuake!")

class TestCheckIMTIMLsInput(unittest.TestCase):
    """
    Checks the pre-processor ensuring correct formating of IMT and IML list
    """
    def setUp(self):
        """
        """
        self.imt_list = []
        self.imls = []

    def test_input_with_single_iml(self):
        """
        Checks that when a single IML is input, with multiple IMTs, then the
        same IML is used for all IMTS
        """
        self.imt_list = ['PGA', 'SA(0.2)']
        self.imls = [[0.005, 0.1, 0.5, 1.0]]
        output_imts = haz._check_imts_imls(self.imt_list, self.imls)
        expected_keys = [PGA(), SA(period=0.2, damping=5.0)]
        self.assertListEqual(output_imts.keys(), expected_keys)
        for iloc, iml in enumerate(self.imls[0]):
            self.assertAlmostEqual(output_imts[PGA()][iloc], iml)
            self.assertAlmostEqual(
                output_imts[SA(period=0.2, damping=5.0)][iloc],
                iml)

    def test_input_with_same_imls_imts(self):
        """
        Checks that when the number of imls in the iml list is equal to the
        number of IMTs then the two are mapped correctly
        """
        self.imt_list = ['PGA', 'PGV']
        self.imls = [[0.005, 0.1, 0.5, 1.0], [1.0, 10.0, 50.0, 100.0]]
        output_imts = haz._check_imts_imls(self.imt_list, self.imls)
        expected_keys = [PGA(), PGV()]
        self.assertListEqual(output_imts.keys(), expected_keys)
        for iloc in range(0, 4):
            self.assertAlmostEqual(output_imts[PGA()][iloc],
                                   self.imls[0][iloc])
            self.assertAlmostEqual(output_imts[PGV()][iloc],
                                   self.imls[1][iloc])

    def test_input_with_different_imls_to_imts(self):
        """
        If the number of IMTs and the number of IMLs is different (and IMLs
        is not 1) then the function cannot be mapped. Raise an error.
        """
        self.imt_list = ['PGA', 'PGV', 'SA(0.2)'] # 3 IMTs
        self.imls = [[0.005, 0.1, 0.5, 1.0], [1.0, 10.0, 50.0, 100.0]] # 2 IMLs

        with self.assertRaises(ValueError) as ae:
            _ = haz._check_imts_imls(self.imt_list, self.imls)
            self.assertEqual(
                ae.exception.message,
                'Number of IML sets must be 1 or equal to number of IMTs')


class Dummy(object):
    """
    """
    def __init__(self, trt):
        self.tectonic_region_type = trt

class TestCheckGSIMs(unittest.TestCase):
    """
    Tests the method to generate a set of GSIMS
    """
    def setUp(self):
        """
        """
        self.source_model = [Dummy('Active Shallow Crust'),
                             Dummy('Subduction')]
        self.gsims = None

    def test_correct_input(self):
        """
        Tests the input with supported GMPEs and regions
        """
        self.gsims = {'Active Shallow Crust': 'BooreAtkinson2008',
                      'Subduction': 'AtkinsonBoore2003SInter'}
        gsim_output = haz._preprocess_gmpes(self.source_model,
                                            deepcopy(self.gsims))
        self.assertTrue(isinstance(gsim_output['Active Shallow Crust'],
            gsim.boore_atkinson_2008.BooreAtkinson2008))
        self.assertTrue(isinstance(gsim_output['Subduction'],
            gsim.atkinson_boore_2003.AtkinsonBoore2003SInter))

    def test_unsupported_gmpe(self):
        """
        Tests the input with an unsupported GMPE
        """
        self.gsims = {'Active Shallow Crust': 'BooreAtkinson2008',
                      'Subduction': 'Rubbish'}
        with self.assertRaises(ValueError) as ae:
            _ = haz._preprocess_gmpes(self.source_model, self.gsims)
            self.assertEqual(ae.exception.message,
                             'GMPE Rubbish not supported!')

    def test_gmpe_not_defined_for_region_type(self):
        """
        Tests the case when source model contains a GMPE that is not
        defined in the GSIMS
        """
        self.gsims = {'Active Shallow Crust': 'BooreAtkinson2008'}
        with self.assertRaises(ValueError) as ae:
            _ = haz._preprocess_gmpes(self.source_model, self.gsims)
            self.assertEqual(ae.exception.message,
                             'No GMPE defined for region type Subduction!')


class TestSiteArrayToCollection(unittest.TestCase):
    """
    Tests the function to turn a simple 2D array of site parameters into
    an openquake.hazardlib.site.SiteCollection instance
    """
    def setUp(self):
        """
        """
        self.site_array = None

    def test_good_input(self):
        """

        """
        self.site_array = np.array([[1.0, 30.0, 35.0, 500.0, 1.0, 1.0, 100.0],
                                    [2.0, 31.0, 36.0, 200.0, 0.0, 5.0, 500.0],
                                    [3.0, 32.0, 37.0, 900.0, 1.0, 1.0, 200.0]])
        output = haz.site_array_to_collection(self.site_array)
        self.assertTrue(isinstance(output, SiteCollection))
        self.assertEqual(output.total_sites, 3)
        for iloc in range(0, output.total_sites):
            #pnt = Point(self.site_array[iloc, 1], self.site_array[iloc, 2])
            self.assertEqual(output.sids[iloc], iloc + 1)
            self.assertAlmostEqual(output.lons[iloc],
                                   self.site_array[iloc, 1])
            self.assertAlmostEqual(output.lats[iloc],
                                   self.site_array[iloc, 2])
            self.assertAlmostEqual(output._vs30[iloc],
                                   self.site_array[iloc, 3])
            self.assertEqual(output._vs30measured[iloc],
                             self.site_array[iloc, 4].astype(bool))
            self.assertAlmostEqual(output.z1pt0[iloc],
                                   self.site_array[iloc, 5])
            self.assertAlmostEqual(output.z2pt5[iloc],
                                   self.site_array[iloc, 6])

    def test_bad_input(self):
        """
        Tests that an error is raised when the input array does not have 7
        columns
        """
        self.site_array = np.array([[30.0, 35.0, 500.0, 1.0, 1.0, 100.0],
                                    [31.0, 36.0, 200.0, 0.0, 5.0, 500.0],
                                    [32.0, 37.0, 900.0, 1.0, 1.0, 200.0]])
        with self.assertRaises(ValueError) as ae:
             _ = haz.site_array_to_collection(self.site_array)
             self.assertEqual(ae.exception.message,
                              'Site array incorrectly formatted!')


def reference_psha_calculation_openquake():
    """
    Sets up the reference PSHA calculation calling OpenQuake directly. All
    subsequent implementations should match this example
    """
    # Site model - 3 Sites
    site_model = SiteCollection([
        Site(Point(30.0, 30.0), 760., True, 1.0, 1.0, 1),
        Site(Point(30.25, 30.25), 760., True, 1.0, 1.0, 2),
        Site(Point(30.4, 30.4), 760., True, 1.0, 1.0, 2)])
    # Source Model Two Point Sources
    mfd_1 = TruncatedGRMFD(4.5, 8.0, 0.1, 4.0, 1.0)
    mfd_2 = TruncatedGRMFD(4.5, 7.5, 0.1, 3.5, 1.1)
    source_model = [PointSource('001', 'Point1', 'Active Shallow Crust',
                                mfd_1, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                                0.0, 30.0, Point(30.0, 30.5),
                                PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                                PMF([(1.0, 10.0)])),
                    PointSource('002', 'Point2', 'Active Shallow Crust',
                                mfd_2, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                                0.0, 30.0, Point(30.0, 30.5),
                                PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                                PMF([(1.0, 10.0)]))]
    imts = {PGA(): [0.01, 0.1, 0.2, 0.5, 0.8],
            SA(period=0.5, damping=5.0): [0.01, 0.1, 0.2, 0.5, 0.8]}
    # Akkar & Bommer (2010) GMPE
    gsims = {'Active Shallow Crust': gsim.akkar_bommer_2010.AkkarBommer2010()}
    truncation_level = None
    return hazard_curves(source_model, site_model, imts, gsims,
                         truncation_level)


#class NullTest(unittest.TestCase):
#    """
#
#    """
#    def setUp(self):
#        """
#        """
#
#    def test_catch1(self):
#        """
#        """
#        TARGET_HAZARD_OUTPUT = reference_psha_calculation_openquake()
#        print TARGET_HAZARD_OUTPUT
#        self.assertTrue(False)

TARGET_HAZARD_OUTPUT = reference_psha_calculation_openquake()
print TARGET_HAZARD_OUTPUT

class TestHMTKHazardCalculator(unittest.TestCase):
    """
    Tests the basic hazard curve calculator (no parallelisation)
    """
    def setUp(self):
        """
        """
        mfd_1 = TruncatedGRMFD(4.5, 8.0, 0.1, 4.0, 1.0)
        mfd_2 = TruncatedGRMFD(4.5, 7.5, 0.1, 3.5, 1.1)
        self.source_model = [
            PointSource('001', 'Point1', 'Active Shallow Crust',
                        mfd_1, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                        0.0, 30.0, Point(30.0, 30.5),
                        PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                        PMF([(1.0, 10.0)])),
            PointSource('002', 'Point2', 'Active Shallow Crust',
                        mfd_2, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                        0.0, 30.0, Point(30.0, 30.5),
                        PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                        PMF([(1.0, 10.0)]))
                        ]
        self.sites = SiteCollection([
            Site(Point(30.0, 30.0), 760., True, 1.0, 1.0, 1),
            Site(Point(30.25, 30.25), 760., True, 1.0, 1.0, 2),
            Site(Point(30.4, 30.4), 760., True, 1.0, 1.0, 2)
            ])
        self.gsims = {'Active Shallow Crust': 'AkkarBommer2010'}
        self.imts = ['PGA', 'SA(0.5)']
        self.imls = [[0.01, 0.1, 0.2, 0.5, 0.8]]

    def test_good_instantiation(self):
        """
        Tests the case when instatiated with correct data
        """
        haz_curve = haz.HMTKHazardCurve(deepcopy(self.source_model),
                                        deepcopy(self.sites),
                                        deepcopy(self.gsims),
                                        deepcopy(self.imls),
                                        deepcopy(self.imts),
                                        None,
                                        None,
                                        None)
        self.assertFalse(haz_curve.truncation_level)
        #self.assertListEqual(haz_curve.source_model, self.source_model)
        # Check GMPES processed correctly
        self.assertTrue(isinstance(haz_curve.gmpes['Active Shallow Crust'],
                                   gsim.akkar_bommer_2010.AkkarBommer2010))
        # Check IMT dictionary instantiated correctly
        np.testing.assert_array_almost_equal(haz_curve.imts[PGA()],
                                             self.imls[0])
        np.testing.assert_array_almost_equal(
            haz_curve.imts[SA(period=0.5, damping=5.0)],
            self.imls[0])

    def test_bad_sites_input_instantiation(self):
        """
        Tests the case when the site model is instantiated incorrectly
        """
        with self.assertRaises(ValueError) as ae:
            _ = haz.HMTKHazardCurve(deepcopy(self.source_model),
                                    'some rubbish',
                                    deepcopy(self.gsims),
                                    deepcopy(self.imls),
                                    deepcopy(self.imts),
                                    None,
                                    None,
                                    None)
            self.assertEqual(ae.exception.message,
                'Sites must be instance of :class: '
                'openquake.hazardlib.site.SiteCollection')

    def test_setup_poes(self):
        """
        Tests the function to preallocate the POEs list with zeros
        """
        haz_curve = haz.HMTKHazardCurve(deepcopy(self.source_model),
                                        deepcopy(self.sites),
                                        deepcopy(self.gsims),
                                        deepcopy(self.imls),
                                        deepcopy(self.imts))
        poe_set = haz_curve._setup_poe_set()
        expected_array = np.ones([3, 5], dtype=float)
        np.testing.assert_array_almost_equal(poe_set[PGA()], expected_array)
        np.testing.assert_array_almost_equal(
                poe_set[SA(period=0.5, damping=5.0)],
                expected_array)

    def test_hazard_curve(self):
        """
        Tests the hazard curve calculations match those of OpenQuake
        """
        haz_curve = haz.HMTKHazardCurve(deepcopy(self.source_model),
                                        deepcopy(self.sites),
                                        deepcopy(self.gsims),
                                        deepcopy(self.imls),
                                        deepcopy(self.imts))

        poes = haz_curve.calculate_hazard()
        np.testing.assert_array_almost_equal(
            np.log10(poes[PGA()]), np.log10(TARGET_HAZARD_OUTPUT[PGA()]))

        np.testing.assert_array_almost_equal(
            np.log10(poes[SA(period=0.5, damping=5.0)]),
            np.log10(TARGET_HAZARD_OUTPUT[SA(period=0.5, damping=5.0)]))


class TestHMTKHazardCurvesBySource(unittest.TestCase):
    """
    Tests the basic hazard curve calculator (parallelised by source)
    """
    def setUp(self):
        """
        """
        mfd_1 = TruncatedGRMFD(4.5, 8.0, 0.1, 4.0, 1.0)
        mfd_2 = TruncatedGRMFD(4.5, 7.5, 0.1, 3.5, 1.1)
        self.source_model = [
            PointSource('001', 'Point1', 'Active Shallow Crust',
                        mfd_1, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                        0.0, 30.0, Point(30.0, 30.5),
                        PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                        PMF([(1.0, 10.0)])),
            PointSource('002', 'Point2', 'Active Shallow Crust',
                        mfd_2, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                        0.0, 30.0, Point(30.0, 30.5),
                        PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                        PMF([(1.0, 10.0)]))
                        ]
        self.sites = SiteCollection([
            Site(Point(30.0, 30.0), 760., True, 1.0, 1.0, 1),
            Site(Point(30.25, 30.25), 760., True, 1.0, 1.0, 2),
            Site(Point(30.4, 30.4), 760., True, 1.0, 1.0, 2)
            ])
        self.gsims = {'Active Shallow Crust': 'AkkarBommer2010'}
        self.imts = ['PGA', 'SA(0.5)']
        self.imls = [[0.01, 0.1, 0.2, 0.5, 0.8]]

    def test_hazard_curve(self):
        """
        Tests the hazard curve calculations match those of OpenQuake
        """
        haz_curve = haz.HMTKHazardCurveParallelSource(
            deepcopy(self.source_model),
            deepcopy(self.sites),
            deepcopy(self.gsims),
            deepcopy(self.imls),
            deepcopy(self.imts))

        poes = haz_curve.calculate_hazard()
        np.testing.assert_array_almost_equal(
            np.log10(poes[PGA()]), np.log10(TARGET_HAZARD_OUTPUT[PGA()]))

        np.testing.assert_array_almost_equal(
            np.log10(poes[SA(period=0.5, damping=5.0)]),
            np.log10(TARGET_HAZARD_OUTPUT[SA(period=0.5, damping=5.0)]))
