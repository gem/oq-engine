# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from opengem import region
from opengem.parser import parser_exposure_portfolio
from opengem.parser import parser_vulnerability_model

TEST_FILE = 'ExposurePortfolioFile-test.xml'
TEST_FILE2 = 'VulnerabilityModelFile-test.xml'

data_dir = os.path.join(os.path.dirname(__file__), 'data')

class VulnerabilityModelFileTestCase(unittest.TestCase):
	
	def test_filter_attribute_constraint(self):
	    """ This test uses the attribute constraint filter to select items
	    from the input file. We assume here that the parser yields the
	    items in the same order as specified in the example XML file. In
	    a general case it would be better not to assume the order of 
	    yielded items to be known, but to locate each yielded result
	    item in a set of expected results.
	    """

	    test_attribute_dicts = [
	        {'ID': 'IR'},
	        {'IntensityMeasureType': 'MMI'},
	        {'ProbabilisticDistribution': 'LN'}
	    ]

	    expected_results = [ [{'ID': 'IR',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
	                            {'ID': 'PK',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'VE',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'MA',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'GT',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'CN',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'IN',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'TR',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'AF',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'EC',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'JP',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'PH',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'ID',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'IT',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'TW',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'CR',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'MX',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'DZ',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'RO',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'PT',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'CL',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'GE',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'GR',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'CO',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'PE',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'SV',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'XF',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
	                            {'ID': 'NZ',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G01',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G02',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G03',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G04',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G05',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G06',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G07',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G08',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G0',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'},
								{'ID': 'G02',
	                            'IntensityMeasureType': 'MMI',
	                            'ProbabilisticDistribution': 'LN'}]
	                       ]

	    # set a region constraint that inlcudes all points 
	    region_constraint = region.RegionConstraint.from_simple((-20.0, 80.0),
	                                                            (40.0, 0.0))
	    for attr_test_counter, curr_attribute_dict in enumerate(
	        test_attribute_dicts):
	        attribute_constraint = \
	            parser_vulnerability_model.VulnerabilityModelConstraint(curr_attribute_dict)
                attr_const = parser_vulnerability_model.VulnerabilityModelConstraint(curr_attribute_dict)

	        vulnerability = parser_vulnerability_model.VulnerabilityModelFile(os.path.join(data_dir, 
																					TEST_FILE2))
																				
	        counter = None
	        for counter, (vulnerability_point, vulnerability_attr) in enumerate(
	            vulnerability.filter(attribute_constraint=attr_const)):

				self.assertEqual(vulnerability_attr, expected_results[
	                attr_test_counter][counter][1],
	                "filter yielded unexpected attribute values at position" \
	                " %s: %s, %s" % (counter, vulnerability_attr, 
	                    expected_results[attr_test_counter][counter][1]))

	        # ensure that generator yielded at least one item
	        self.assertTrue(counter is not None, 
	            "filter yielded nothing although %s item(s) were expected" % \
	            len(expected_results[attr_test_counter]))

	        # ensure that generator returns exactly the number of items of the
	        # expected result list
	        self.assertEqual(counter, 
	            len(expected_results[attr_test_counter])-1,
	            "filter yielded wrong number of items (%s), expected were %s" \
	            % (counter+1, len(expected_results[attr_test_counter])))

class ExposurePortfolioFileTestCase(unittest.TestCase):

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = region.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        ep = parser_exposure_portfolio.ExposurePortfolioFile(
            os.path.join(data_dir, TEST_FILE))

        ctr = None

        # this loop is not expected to be entered - generator should
        # not yield any item
        for ctr, exposure_item in enumerate(ep.filter(
            region_constraint)):
            pass

        # ensure that generator didn't yield an item
        self.assertTrue(ctr is None, 
            "filter yielded item(s) although no items were expected")

    def test_filter_region_constraint_one_site(self):

        # look for sites within specified rectangle
        # constraint is met by one and only one site in the example file 
        # 9.15333 45.12200
        region_constraint = region.RegionConstraint.from_simple(
            (9.15332, 45.12201), (9.15334, 45.12199))
        ep = parser_exposure_portfolio.ExposurePortfolioFile(
            os.path.join(data_dir, TEST_FILE))

        expected_result = [
            (region.Point(9.15333, 45.12200),
            {'PortfolioID': 'PAV01',
             'PortfolioDescription': 'Collection of existing building in ' \
                                     'downtown Pavia',
             'AssetID': '02',
             'AssetDescription': 'Moment-resisting non-ductile concrete ' \
                                 'frame med rise',
             'AssetValue': 250000.0,
             'VulnerabilityFunction': 'RC/DMRF-D/MR'
            })]

        ctr = None
        for ctr, (exposure_point, exposure_attr) in enumerate(
            ep.filter(region_constraint)):

            # check topological equality for points
            self.assertTrue(exposure_point.equals(expected_result[ctr][0]),
                "filter yielded unexpected point at position %s: %s, %s" % (
                ctr, exposure_point, expected_result[ctr][0]))

            self.assertTrue(exposure_attr == expected_result[ctr][1],
                "filter yielded unexpected attribute values at position " \
                "%s: %s, %s" % (ctr, exposure_attr, expected_result[ctr][1]))

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == len(expected_result)-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr+1, len(expected_result)))

    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file 
        region_constraint = region.RegionConstraint.from_simple((-20.0, 80.0),
                                                                (40.0, 0.0))
        ep = parser_exposure_portfolio.ExposurePortfolioFile(
            os.path.join(data_dir, TEST_FILE))

        expected_result_ctr = 6
        ctr = None

        # just loop through iterator in order to count items
        for ctr, (exposure_point, exposure_attr) in enumerate(
            ep.filter(region_constraint)):
            pass

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None, 
            "filter yielded nothing although %s item(s) were expected" % \
            expected_result_ctr)

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == expected_result_ctr-1, 
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr+1, expected_result_ctr))
