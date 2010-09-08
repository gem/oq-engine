"""
This is a basic set of tests for risk engine,
specifically file formats.

"""

import os
import unittest

from shapely import geometry

from opengem.risk import engines
from opengem.output import risk as risk_output
from opengem import shapes



LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')


class RiskEngineTestCase(unittest.TestCase):
    """Basic unit tests of the Risk Engine"""
    
    def test_site_intersections(self):
        first_site = shapes.Site(10.0, 10.0)
        second_site = shapes.Site(11.0, 11.0)
        third_site = shapes.Site(12.0, 12.0)
        fourth_site = shapes.Site(13.0, 13.0)
        
        region_of_interest = shapes.Region(geometry.MultiPoint(
                        [first_site.point, 
                         second_site.point,
                         third_site.point,
                         fourth_site.point]).convex_hull)
        
        first_gp = region_of_interest.grid.point_at(first_site)
        second_gp = region_of_interest.grid.point_at(second_site)
        third_gp = region_of_interest.grid.point_at(third_site)
        fourth_gp = region_of_interest.grid.point_at(fourth_site)
        
        hazard_curves = {}
        hazard_curves[first_gp] = ([1.0, 0.0], [1.0, 0.0])
        hazard_curves[second_gp] = ([1.0, 0.0], [1.0, 0.0])
        hazard_curves[third_gp] = ([1.0, 0.0], [1.0, 0.0])
        
        ratio_results = {}
        loss_results = {}
        
        vulnerability_curves = {}
        vulnerability_curves['brick'] = shapes.FastCurve(
            [(5.0, (0.0, 0.0)), (6.0, (0.0, 0.0)), (7.0, (0.0, 0.0)), (8.0, (0.0, 0.0))])
        vulnerability_curves['stone'] = shapes.FastCurve(
                [(5.0, (0.0, 0.0)), (6.0, (0.0, 0.0)), (7.0, (0.0, 0.0)), (8.0, (0.0, 0.0))])
        vulnerability_curves['wood'] = shapes.FastCurve(
                    [(5.0, (0.0, 0.0)), (6.0, (0.0, 0.0)), (7.0, (0.0, 0.0)), (8.0, (0.0, 0.0))])
        
        exposure_portfolio = {}
        # # Pretend there are only two cities in this country
        exposure_portfolio[first_gp] = (200000, 'New York')
        exposure_portfolio[fourth_gp] = (400000, 'London')
        
        risk_engine = engines.ProbabilisticLossRatioCalculator(hazard_curves, 
                                vulnerability_curves, exposure_portfolio)
        
        for gridpoint in region_of_interest.grid:
            ratio_results[gridpoint] = risk_engine.compute_loss_ratio_curve(gridpoint)
            loss_results[gridpoint] = risk_engine.compute_loss_curve(gridpoint, ratio_results[gridpoint])
        
        self.assertFalse(first_gp in ratio_results)
        self.assertEqual(ratio_results[third_gp], None)
        self.assertNotEqual(ratio_results[second_gp], None)
        
        # No exposure at second site, so no loss results
        self.assertEqual(loss_results[second_gp], None)
        self.assertNotEqual(loss_results[fourth_gp], None)


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