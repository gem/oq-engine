"""
This is a basic set of tests for risk engine,
specifically file formats.

"""

import os
import unittest

import numpy.core.multiarray as ncm

from opengem.risk import engines
from opengem.output import risk as risk_output
from opengem import grid
from opengem import region
from opengem.risk import engines
from opengem import shapes


LOSS_XML_OUTPUT_FILE = 'loss-curves.xml'
LOSS_RATIO_XML_OUTPUT_FILE = 'loss-ratio-curves.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')


class RiskEngineTestCase(unittest.TestCase):
    """Basic unit tests of the Risk Engine"""
    
    def test_loss_map_generation(self):
        #get grid of columns and rows from region of coordinates
        
        cellsize = 0.1
        loss_map_region = region.Region.from_coordinates(
            [(10, 100), (100, 100), (100, 10), (10, 10)])
        
        # Fill the region up with loss curve sites
        for site in loss_map_region:
            # TODO(bw): Generate believable data here
            loss_map_region[site] = shapes.Curve([0.0, 0.1, 0.2],[1.0, 0.5, 0.2])
            
        grid = loss_map_region.grid(cellsize)
        losses = ncm.zeros((grid.columns, grid.rows))
        
        #interpolation intervals are defined as [1%, 2%, 5%, 10%] in 50 years
        intervals = [0.01, 0.02, 0.05, 0.10]
        for interval in intervals:
            for point, site in grid:
                (col, row) = point
                loss_value = engines.compute_loss(site, interval)
                losses[col, row] = loss_value
            # TODO(bw): Add asserts that verify the array contents here.
        
    def test_loss_value_interpolation(self):
        pass
    
    def test_loss_value_interpolation_bounds(self):
        # for a set of example loss ratio curves and a single invest. interval,
        interval = 0.01
        zero_curve = Curve(0.0)
        huge_curve = Curve(10.0, 10.0)
        normal_curve = Curve((0.1, 0.2), (0.2, 0.21))
        loss_curves = [zero_curve, normal_curve, huge_curve]
        # interpolate the loss value
        # check that curves of zero produce zero loss (and no error)
        # check that curves with no point < 5 don't throw an error
        # check that the loss is the expected value
        
    
    def test_site_intersections(self):
        first_site = grid.Site(10.0, 10.0)
        second_site = grid.Site(11.0, 11.0)
        third_site = grid.Site(12.0, 12.0)
        fourth_site = grid.Site(13.0, 13.0)
        
        hazard_curves = {}
        hazard_curves[first_site] = ([1.0, 0.0], [1.0, 0.0])
        hazard_curves[second_site] = ([1.0, 0.0], [1.0, 0.0])
        hazard_curves[fourth_site] = ([1.0, 0.0], [1.0, 0.0])
        
        sites_of_interest = {}
        sites_of_interest[second_site] = True
        sites_of_interest[third_site] = True
        sites_of_interest[fourth_site] = True
        
        ratio_results = {}
        loss_results = {}
        
        vulnerability_curves = {}
        vulnerability_curves['brick'] = ([0.2, 0.3, 0.4, 0.9, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        vulnerability_curves['stone'] = ([0.2, 0.21, 0.41, 0.94, 0.95, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        vulnerability_curves['wood'] = ([0.0, 0.0, 0.0, 0.0, 0.0, 0.99], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

        ratio_engine = engines.ProbabilisticLossRatioCalculator(hazard_curves, vulnerability_curves)
        
        exposure_portfolio = {}
        # # Pretend there are only two cities in this country
        exposure_portfolio[first_site] = (200000, 'New York')
        exposure_portfolio[fourth_site] = (400000, 'London')
        loss_engine = engines.ProbabilisticLossCalculator(exposure_portfolio)
        
        for site in sites_of_interest:
            ratio_results[site] = ratio_engine.compute(site)
            loss_results[site] = loss_engine.compute(site, ratio_results[site])
        
        self.assertFalse(first_site in ratio_results)
        self.assertEqual(ratio_results[third_site], None)
        self.assertNotEqual(ratio_results[second_site], None)
        
        # No exposure at second site, so no loss results
        self.assertEqual(loss_results[second_site], None)
        self.assertNotEqual(loss_results[fourth_site], None)


class RiskOutputTestCase(unittest.TestCase):
    """Confirm that XML output from risk engine is valid against schema,
    as well as correct given the inputs."""
    
    def setUp(self):
        pass
    
    def test_xml_is_valid(self):
        xml_writer = risk_output.RiskXMLWriter(
            os.path.join(data_dir, LOSS_XML_OUTPUT_FILE))
        first_site = grid.Site(10.0, 10.0)
        site_attributes = {}
        site_attributes['loss_ratio'] = ([0.0, 0.1, 0.2],[1.0, 0.9, 0.8])
        xml_writer.write(first_site, site_attributes)
        xml_writer.close()
        
        # TODO(jmc): Validate that the contents of this xml file match schema

    # 
    # def test_find_test_resources(self):
    #     """Should resolve a file within the resources folder"""
    #     chile_path = self.resource_path("chile.txt")
    #     chile_file = file(chile_path, "r")
    # 
    # def exposure_definition(self, filename):
    #     return reader.ESRIRasterMetadata.load_esri_header(self.resource_path(filename))
    # 
    # def hazard_definition(self, filename):
    #     return reader.ESRIRasterMetadata.load_hazard_iml(self.resource_path(filename))
#         
# class RiskInputTestCase(RiskBaseTestCase):
#     """Tests of file format input readers"""
#         
#     def test_all_file_formats(self):
#         iml_loader = lambda x: reader.ESRIRasterMetadata.load_hazard_iml(self.resource_path(x))
#         esri_loader = lambda x: reader.ESRIRasterMetadata.load_esri_header(self.resource_path(x))
#         formats = [(ESRIBinaryFileExposureReader, "all_values_filled.flt", esri_loader, "all_values_filled.hdr", "result_all_values_filled.txt"),
#                     (ESRIBinaryFileExposureReader, "no_data.flt", esri_loader, "no_data.hdr", "result_no_data.txt"),
#                     (ESRIBinaryFileExposureReader, "chile_population.flt", esri_loader, "chile_population.hdr", "result_chile_population.txt"),
#                     (AsciiFileHazardIMLReader, "Hazard_MMI.txt", iml_loader, "Hazard_MMI.txt", "result_Hazard_MMI.txt"),
#                     (AsciiFileHazardIMLReader, "Hazard_MMI_1km.txt", iml_loader, "Hazard_MMI_1km.txt", "result_Hazard_MMI_1km.txt"),
#                     (AsciiFileHazardIMLReader, "Hazard_MMI_6km.txt", iml_loader, "Hazard_MMI_6km.txt", "result_Hazard_MMI_6km.txt"),
#                     ]
#         for (loader, data_file, header_loader, header_file, result_file) in formats:
#             exposure = loader(self.resource_path(data_file), header_loader(header_file))
#             self._validate_exposure_file(exposure, result_file)
#     
#     def _validate_exposure_file(self, exposure, result_file):
#         separator = " "
#         def exposure_value(line):
#             return float(line.partition(separator)[0])
#         def site_from_line(line):
#             return esri.Site(float(line.split(separator)[1]), float(line.split(separator)[2]))
#             
#         with open(self.resource_path(result_file)) as results:
#             for line in results.readlines():
#                 print line
#                 (exposure_value, site_lat, site_long) = map(float, line.split(separator)[:3])
#                 self.assertAlmostEqual(exposure_value, exposure.read_at(esri.Site(site_lat, site_long)), places=5)