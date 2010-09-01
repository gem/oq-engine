"""
This is a basic set of tests for risk engine,
specifically file formats.

"""

import unittest
from opengem.risk import engines
from opengem import grid

class RiskBaseTestCase(unittest.TestCase):
    """Basic unit tests of the Risk Engine"""
    
    def test_tests_work(self):
        """The ultimate bootstrap"""
        self.assertTrue(True)
        self.assertFalse(False)
        
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