# -*- coding: utf-8 -*-
"""
This is a basic set of tests for risk engine,
specifically file formats.

"""

import os
import numpy
import unittest

from shapely import geometry

from opengem import identifiers
from opengem import logs
from opengem import memcached
from opengem import shapes
from opengem import test

from opengem.risk import engines
from opengem.output import risk as risk_output

logger = logs.RISK_LOG

LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'

EXPOSURE_INPUT_FILE = 'FakeExposurePortfolio.xml'
VULNERABILITY_INPUT_FILE = 'VulnerabilityModelFile-jobber-test.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')

class RiskEngineTestCase(unittest.TestCase):
    """Basic unit tests of the Risk Engine"""

    def test_loss_map_generation(self):
        # get grid of columns and rows from region of coordinates
        loss_map_region = shapes.Region.from_coordinates(
            [(10, 20), (20, 20), (20, 10), (10, 10)])
        loss_map_region.cell_size = 1.0

        # Fill the region up with loss curve sites
        loss_curves = {}
        for site in loss_map_region:
            loss_curves[site] = shapes.FastCurve([
                ('0.0', 0.24105392741891271), 
                ('1280.0', 0.23487103910274165), 
                ('2560.0', 0.22617525423987336), 
                ('3840.0', 0.21487350918336773), 
                ('5120.0', 0.20130828974113113), 
                ('6400.0', 0.18625699583339819), 
                ('8320.0', 0.16321642950263798), 
                ('10240.0', 0.14256493660395209), 
                ('12160.0', 0.12605402369513649), 
                ('14080.0', 0.11348740908284834), 
                ('16000.0', 0.103636128778507), 
                ('21120.0', 0.083400493736596762), 
                ('26240.0', 0.068748634724073318), 
                ('31360.0', 0.059270296098829112), 
                ('36480.0', 0.052738173061141945), 
                ('41600.0', 0.047128144517224253), 
                ('49280.0', 0.039134392774233986), 
                ('56960.0', 0.032054271427490524), 
                ('64640.0', 0.026430436298219544), 
                ('72320.0', 0.022204123970325802), 
                ('80000.0', 0.018955490690565201), 
                ('90240.0', 0.01546384521034673), 
                ('100480.0', 0.01253420544337625), 
                ('110720.0', 0.010091272074791734), 
                ('120960.0', 0.0081287946107584975), 
                ('131200.0', 0.0065806376555058105), 
                ('140160.0', 0.0054838330271587809), 
                ('149120.0', 0.0045616733509618087), 
                ('158080.0', 0.0037723441973124923), 
                ('167040.0', 0.0030934392072837253), 
                ('176000.0', 0.0025140588978909578), 
                ('189440.0', 0.0018158701863753069), 
                ('202880.0', 0.0012969740515868437), 
                ('216320.0', 0.00092183863089347865), 
                ('229760.0', 0.00065389822562465858), 
                ('243200.0', 0.00046282828510792824)])
            
        grid = loss_map_region.grid

        # NOTE(fab): in numpy, the order of axes in a 2-dim array 
        # is (rows, columns)
        losses = numpy.zeros((grid.rows, grid.columns), dtype=float)
        probability = 0.01
        
        # check that the loss is the expected value
        self.assertAlmostEqual(111196.24804, engines.compute_loss(loss_curves[site], 0.01))
        self.assertAlmostEqual(77530.7057443, engines.compute_loss(loss_curves[site], 0.02))
        self.assertAlmostEqual(38978.9972802, engines.compute_loss(loss_curves[site], 0.05))
        self.assertAlmostEqual(16920.0096418, engines.compute_loss(loss_curves[site], 0.10))
        
        #interpolation intervals are defined as [1%, 2%, 5%, 10%] in 50 years
        intervals = [0.01, 0.02, 0.05, 0.10]
        for interval in intervals:
            for gridpoint in grid:
                loss_value = engines.compute_loss(loss_curves[site], interval)
                losses[gridpoint.row-1][gridpoint.column-1] = loss_value

        logger.debug('%s= losses', losses)
        logger.debug('%s = loss_value', loss_value)
        logger.debug('%s = gridpoint', gridpoint)
        logger.debug('%s = interval', interval)
        logger.debug('%s = loss_value', loss_value)
        logger.debug('%s = loss_curves', loss_curves[site])

    def test_zero_curve_produces_zero_loss(self):
        # check that curves of zero produce zero loss (and no error)
        zero_curve = shapes.FastCurve([('0.0', 0.0), ('0.0', 0.0),])        
        loss_value = engines.compute_loss(zero_curve, 0.01)
        self.assertEqual(0.0, loss_value)
        
    def test_loss_value_interpolation_bounds(self):
        # for a set of example loss ratio curves and a single invest. interval,
        interval = 0.01
        zero_curve = shapes.EMPTY_CURVE
        huge_curve = shapes.FastCurve([(10.0, 10.0)])
        normal_curve = shapes.FastCurve([(0.1, 0.2), (0.2, 0.21)])
        loss_curves = [zero_curve, normal_curve, huge_curve]
    
        # check that curves with no point < 5 don't throw an error
            
    @test.skipit
    def test_site_intersections(self):
        """Loss ratios and loss curves can only be computed when we have:
        
         1. A hazard curve for the site
         2. An exposed asset for the site
         3. The vulnerability curve for the asset
         4. A region of interest that includes the site

        TODO(fab): This test should be split, and the fragments should be
        assigned to tests for other modules:
        1) The first part that asserts that the first point is not contained 
           in the convex hull of the three other points should be moved to 
           the tests for the 'shapes' module.
        2) The second part that asserts that exceptions are raised if hazard
           and exposure are not given for the same sites should be moved to
           tests for the 'jobber' module.
        """

        # NOTE(fab): these points are all on a line, so the convex hull of
        # their union will be a LINESTRING
        first_site = shapes.Site(10.0, 10.0)
        second_site = shapes.Site(11.0, 11.0)
        third_site = shapes.Site(12.0, 12.0)
        fourth_site = shapes.Site(13.0, 13.0)
        
        multi_point = \
            second_site.point.union(third_site.point).union(fourth_site.point)
        region_of_interest = shapes.Region(multi_point.convex_hull)
        
        logger.debug("Region of interest bounds are %s", 
            str(region_of_interest.bounds))
        
        self.assertRaises(Exception, region_of_interest.grid.point_at, first_site)

        second_gp = region_of_interest.grid.point_at(second_site)
        third_gp = region_of_interest.grid.point_at(third_site)
        fourth_gp = region_of_interest.grid.point_at(fourth_site)
        
        logger.debug("Second GP is at %s: %s, %s", 
            str(second_gp), second_gp.row, second_gp.column)
        
        hazard_curves = {}
        # hazard_curves[first_gp] = shapes.FastCurve([('6.0', 0.0), ('7.0', 0.0)])
        hazard_curves[second_gp] = shapes.FastCurve([('6.0', 0.0), ('7.0', 0.0)])
        hazard_curves[third_gp] = shapes.FastCurve([('6.0', 0.0), ('7.0', 0.0)])
        
        ratio_results = {}
        loss_results = {}
        
        # TODO(fab): use vulnerability file for tests, 
        vulnerability_curves = {}
        vulnerability_curves['RC/ND-FR-D/HR'] = shapes.FastCurve(
            [(5.0, (0.25, 0.5)),
             (6.0, (0.4, 0.4)),
             (7.0, (0.6, 0.3))])
        
        # TODO(fab): use exposure file for tests
        exposure_portfolio = {}
        exposure_portfolio[fourth_gp] = {'AssetValue': 320000.0, 'PortfolioID': 'PAV01', 
            'VulnerabilityFunction': 'RC/ND-FR-D/HR', 'AssetID': '06', 
            'PortfolioDescription': 'Collection of existing building in downtown Pavia', 
            'AssetDescription': 'Moment-resisting ductile concrete frame high rise'}
        
        # TODO(fab): use memcached-enabled engine, through jobber
        risk_engine = engines.ProbabilisticLossRatioCalculator(hazard_curves, 
                                exposure_portfolio)
                                  
        for gridpoint in region_of_interest.grid:
            ratio_results[gridpoint] = \
                risk_engine.compute_loss_ratio_curve(gridpoint)
            loss_results[gridpoint] = \
                risk_engine.compute_loss_curve(gridpoint, 
                                               ratio_results[gridpoint])
        
        logger.debug("Ratio Results keys are %s" % ratio_results.keys())
        
        #self.assertFalse(first_gp in ratio_results.keys())
        self.assertEqual(ratio_results[third_gp], None)
        self.assertEqual(ratio_results[second_gp], None) # No asset, 
        
        # No exposure at second site, so no loss results
        self.assertEqual(loss_results[second_gp], None)
        # self.assertNotEqual(loss_results[fourth_gp], None)


class RiskOutputTestCase(unittest.TestCase):
    """Confirm that XML output from risk engine is valid against schema,
    as well as correct given the inputs."""
    
    def setUp(self):
        pass
    
    # def test_xml_is_valid(self):
    #     xml_writer = risk_output.RiskXMLWriter(
    #         os.path.join(data_dir, LOSS_XML_OUTPUT_FILE))
    #     first_site = shapes.Site(10.0, 10.0)
    #     
    #     loss_ratio_curves = {}
    #     loss_ratio_curves[first_gp] = shapes.FastCurve([(0.0, 0.1), (1.0, 0.9)])
    #     
    #     xml_writer.write(first_site, loss_ratio_curves[first_gp])
    #     xml_writer.close()
