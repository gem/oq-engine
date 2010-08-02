import unittest
import test
from greek import reader, esri
from greek.reader import ESRIBinaryFileExposureReader, AsciiFileHazardIMLReader

class RiskBaseTestCase(test.BaseTestCase):
    """Basic unit tests of the Risk Engine"""
    
    def test_tests_work(self):
        """The ultimate bootstrap"""
        self.assertTrue(True)
        self.assertFalse(False)

    def test_find_test_resources(self):
        """Should resolve a file within the resources folder"""
        chile_path = self.resource_path("chile.txt")
        chile_file = file(chile_path, "r")

    def exposure_definition(self, filename):
        return reader.ESRIRasterMetadata.load_esri_header(self.resource_path(filename))

    def hazard_definition(self, filename):
        return reader.ESRIRasterMetadata.load_hazard_iml(self.resource_path(filename))
        
class RiskInputTestCase(RiskBaseTestCase):
    """Tests of file format input readers"""
        
    def test_all_file_formats(self):
        iml_loader = lambda x: reader.ESRIRasterMetadata.load_hazard_iml(self.resource_path(x))
        esri_loader = lambda x: reader.ESRIRasterMetadata.load_esri_header(self.resource_path(x))
        formats = [(ESRIBinaryFileExposureReader, "all_values_filled.flt", esri_loader, "all_values_filled.hdr", "result_all_values_filled.txt"),
                    (ESRIBinaryFileExposureReader, "no_data.flt", esri_loader, "no_data.hdr", "result_no_data.txt"),
                    (ESRIBinaryFileExposureReader, "chile_population.flt", esri_loader, "chile_population.hdr", "result_chile_population.txt"),
                    (AsciiFileHazardIMLReader, "Hazard_MMI.txt", iml_loader, "Hazard_MMI.txt", "result_Hazard_MMI.txt"),
                    (AsciiFileHazardIMLReader, "Hazard_MMI_1km.txt", iml_loader, "Hazard_MMI_1km.txt", "result_Hazard_MMI_1km.txt"),
                    (AsciiFileHazardIMLReader, "Hazard_MMI_6km.txt", iml_loader, "Hazard_MMI_6km.txt", "result_Hazard_MMI_6km.txt"),
                    ]
        for (loader, data_file, header_loader, header_file, result_file) in formats:
            exposure = loader(self.resource_path(data_file), header_loader(header_file))
            self._validate_exposure_file(exposure, result_file)
    
    def _validate_exposure_file(self, exposure, result_file):
        separator = " "
        def exposure_value(line):
            return float(line.partition(separator)[0])
        def site_from_line(line):
            return esri.Site(float(line.split(separator)[1]), float(line.split(separator)[2]))
            
        with open(self.resource_path(result_file)) as results:
            for line in results.readlines():
                print line
                (exposure_value, site_lat, site_long) = map(float, line.split(separator)[:3])
                self.assertAlmostEqual(exposure_value, exposure.read_at(esri.Site(site_lat, site_long)), places=5)