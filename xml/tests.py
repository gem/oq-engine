import unittest

from lxml import etree
from XMLParse import function_at
from XMLParse import asset_at

class XMLParseTestCase(unittest.TestCase):

    def setUp(self):
        self.functions = etree.parse('functions_Pager.xml').getroot()
        self.assets = etree.parse('Portfolio_Assets.xml').getroot()

    def assertListEqual(self, expected, actual):
        """Tests if two lists are equal."""

        self.failIf(len(expected) is not len(actual), "Lists are not of the same size, expected <%s>, got <%s>" % (len(expected), len(actual)))
        [self.fail("Lists are not equal, expected <%s>, got <%s>" % (expected[index], actual[index])) for index in range(len(expected)) if expected[index] != actual[index]]

    """
    Values used in test:
    
    <VulnerabilityFunction ID="IR" IntensityMeasureType="MMI" ProbabilisticDistribution="LN">
        <IntensityMeasureValues> 5.00 5.50 6.00 6.50 7.00 7.50 8.00 8.50 9.00 9.50 10.00</IntensityMeasureValues>
        <LossRatioValues> 0.00 0.00 0.00 0.00 0.00 0.01 0.06 0.18 0.36 0.36 0.36</LossRatioValues>
        <CoefficientVariationValues> 0.30 0.30 0.30 0.30 0.30 0.30 0.30 0.30 0.30 0.30 0.30</CoefficientVariationValues>
    </VulnerabilityFunction>
    """
    def test_should_read_a_single_vulnerability_function(self):
        function = function_at(self.functions, 0)
        
        self.assertEqual('IR', function.id)
        self.assertEqual('MMI', function.imt)
        self.assertEqual('LN', function.distribution)

        self.assertListEqual([0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.06, 0.18, 0.36, 0.36, 0.36], function.loss_ratio_values)
        self.assertListEqual([5.00, 5.50, 6.00, 6.50, 7.00, 7.50, 8.00, 8.50, 9.00, 9.50, 10.00], function.intensity_measure_values)
        self.assertListEqual([0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30], function.coefficient_variation_values)
    
    def test_should_read_all_the_vulnerability_functions_defined(self):
        pass

    def test_should_read_a_single_asset_instance(self):
        asset = asset_at(self.assets, 0)

        self.assertEqual('01', asset.AssetID)
        self.assertEqual('Moment-resisting non-ductile concrete frame low rise', asset.AssetDescription)
        self.assertEqual('150000', asset.AssetValue)
        self.assertEqual('RC/DMRF-D/LR', asset.VulnerabilityFunction)
        self.assertEqual('45.16667', asset.Latitude)
        self.assertEqual('9.15000', asset.Longitude)

if __name__ == '__main__':
    unittest.main()
