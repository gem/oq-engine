"""
This is a basic set of tests for risk engine,
specifically file formats.

"""

import os
import unittest

from shapely import geometry

from opengem import logs
from opengem.risk import engines
from opengem.output import risk as risk_output
from opengem import shapes

log = logs.risk_log

LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')


class RiskEngineTestCase(unittest.TestCase):
    """Basic unit tests of the Risk Engine"""
    
    def test_site_intersections(self):
        """Loss ratios and loss curves can only be computed when we have:
        
         1. A hazard curve for the site
         2. An exposed asset for the site
         3. The vulnerability curve for the asset
         4. A region of interest that includes the site
        
        """
        first_site = shapes.Site(10.0, 10.0)
        second_site = shapes.Site(11.0, 11.0)
        third_site = shapes.Site(12.0, 12.0)
        fourth_site = shapes.Site(13.0, 13.0)
        
        region_of_interest = shapes.Region(geometry.MultiPoint(
                        [second_site.point,
                         third_site.point,
                         fourth_site.point]).convex_hull)
        
        log.debug("Region of interest bounds are %s", 
            str(region_of_interest.bounds))
        
        self.assertRaises(Exception, region_of_interest.grid.point_at, first_site)
        second_gp = region_of_interest.grid.point_at(second_site)
        third_gp = region_of_interest.grid.point_at(third_site)
        fourth_gp = region_of_interest.grid.point_at(fourth_site)
        
        log.debug("Second GP is at %s: %s, %s", 
            str(second_gp), second_gp.row, second_gp.column)
        
        hazard_curves = {}
        # hazard_curves[first_gp] = shapes.FastCurve([('6.0', 0.0), ('7.0', 0.0)])
        hazard_curves[second_gp] = shapes.FastCurve([('6.0', 0.0), ('7.0', 0.0)])
        hazard_curves[third_gp] = shapes.FastCurve([('6.0', 0.0), ('7.0', 0.0)])
        
        ratio_results = {}
        loss_results = {}
        
        vulnerability_curves = {}
        vulnerability_curves['RC/ND-FR-D/HR'] = shapes.FastCurve(
            [(5.0, (0.25, 0.5)),
             (6.0, (0.4, 0.4)),
             (7.0, (0.6, 0.3))])
        
        exposure_portfolio = {}
        exposure_portfolio[fourth_gp] = {'AssetValue': 320000.0, 'PortfolioID': 'PAV01', 
            'VulnerabilityFunction': 'RC/ND-FR-D/HR', 'AssetID': '06', 
            'PortfolioDescription': 'Collection of existing building in downtown Pavia', 
            'AssetDescription': 'Moment-resisting ductile concrete frame high rise'}
        
        risk_engine = engines.ProbabilisticLossRatioCalculator(hazard_curves, 
                                exposure_portfolio)
        
        for gridpoint in region_of_interest.grid:
            ratio_results[gridpoint] = risk_engine.compute_loss_ratio_curve(gridpoint)
            loss_results[gridpoint] = risk_engine.compute_loss_curve(gridpoint, ratio_results[gridpoint])
        
        log.debug("Ratio Results keys are %s" % ratio_results.keys())
        
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