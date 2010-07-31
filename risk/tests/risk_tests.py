import unittest
import test

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
        

    def result_path_for(self, filename):
        return this.getClass().getClassLoader().getResource("result_" + filename).getPath();

    def all_values_filled_exposure(self):
        return ESRIBinaryFileExposureReader(self.resource_path("all_values_filled.flt"),
                    self.exposure_definition("all_values_filled.hdr"))

    def no_data_exposure(self):
        return ESRIBinaryFileExposureReader(self.resource_path("no_data.flt"), self.exposure_definition("no_data.hdr"))

    def chilePopulationExposure(self):
        return ESRIBinaryFileExposureReader(self.resource_path("chile_population.flt"),
                    self.exposure_definition("chile_population.hdr"))

    def hazard_MMI(self):
        return AsciiFileHazardIMLReader(self.resource_path("Hazard_MMI.txt"), self.hazard_definition("Hazard_MMI.txt"))

    def hazard_MMI1Km():
        return AsciiFileHazardIMLReader(self.resource_path("Hazard_MMI_1km.txt"), self.hazard_definition("Hazard_MMI_1km.txt"))

    def hazard_MMI6Km():
        return AsciiFileHazardIMLReader(self.resource_path("Hazard_MMI_6km.txt"), self.hazard_definition("Hazard_MMI_6km.txt"))

    def exposure_definition(self, filename):
        return StandardESRIRasterFileDefinitionReader(self.resource_path(filename)).read()

    def hazard_definition(self, filename):
        return HazardIMLESRIRasterFileDefinitionReader(self.resource_path(filename)).read()