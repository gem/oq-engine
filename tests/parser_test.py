# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


# TODO(lp) move parsers and their tests into nrml schemas


import os
import unittest

from openquake.parser import risk
from openquake import shapes
from tests.utils import helpers
import tempfile


EX_TEST_FILE = 'examples/exposure-portfolio.xml'
EX_INVALID_TEST_FILE = helpers.get_data_path("examples/invalid_exposure.xml")
EX_MISMATCHED_TEST_FILE = "examples/exposure-portfolio.xml"

TEST_FILE = "examples/vulnerability-model-discrete.xml"
INVALID_TEST_FILE = helpers.get_data_path("examples/invalid_vulnerability.xml")
MISMATCHED_TEST_FILE = "examples/source-model.xml"
NO_OF_CURVES_IN_TEST_FILE = 4
TEST_FILE_PATH = helpers.get_data_path('config.gem')


class ExposureModelFileTestCase(unittest.TestCase):

    def test_schema_validation(self):
        def _parse_exposure(path):
            ep = risk.ExposureModelFile(path)

            # force parsing the whole file
            for e in ep:
                pass

        self.assertRaises(risk.XMLValidationError,
                          _parse_exposure, EX_INVALID_TEST_FILE)

    def test_filter_region_constraint_known_to_fail(self):

        # set region in which no site is found in input file
        region_constraint = shapes.RegionConstraint.from_simple((170.0, -80.0),
                                                                (175.0, -85.0))
        ep = risk.ExposureModelFile(
            os.path.join(helpers.DATA_DIR, EX_TEST_FILE))
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
        region_constraint = shapes.RegionConstraint.from_simple(
            (9.15332, 45.12201), (9.15334, 45.12199))
        ep = risk.ExposureModelFile(
            os.path.join(helpers.DATA_DIR, EX_TEST_FILE))

        expected_result = [
            (shapes.Site(9.15333, 45.12200),
             [risk.OCCUPANCY(12, "day"), risk.OCCUPANCY(50, "night")],
             {"area": 119.0,
              "areaType": "per_asset",
              "areaUnit": "GBP",
              "assetCategory": "buildings",
              "assetID": "asset_02",
              "coco": 21.95,
              "cocoType": "per_area",
              "cocoUnit": "CHF",
              "deductible": 66.0,
              "limit": 1999.0,
              "listDescription": "Collection of existing building in "
                                 "downtown Pavia",
              "listID": "PAV01",
              "number": 6.0,
              "reco": 205432.0,
              "recoType": "aggregated",
              "recoUnit": "EUR",
              "stco": 250000.0,
              "stcoType": "aggregated",
              "stcoUnit": "USD",
              "taxonomy": "RC/DMRF-D/HR",
              "taxonomySource": "Pavia taxonomy",
              }
            )]

        ctr = None
        for ctr, (exposure_point, occupancy_data, exposure_data) in enumerate(
            ep.filter(region_constraint)):

            # check topological equality for points
            self.assertEqual(expected_result[ctr][0], exposure_point)
            self.assertEqual(expected_result[ctr][1], occupancy_data)
            self.assertEqual(expected_result[ctr][2], exposure_data)

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None,
            "filter yielded nothing although %s item(s) were expected" % \
            len(expected_result))

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == len(expected_result) - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr + 1, len(expected_result)))

    def test_filter_region_constraint_all_sites(self):

        # specified rectangle contains all sites in example file
        region_constraint = shapes.RegionConstraint.from_simple(
            (9.14776, 45.18000), (9.15334, 45.12199))
        ep = risk.ExposureModelFile(
            os.path.join(helpers.DATA_DIR, EX_TEST_FILE))

        expected_result_ctr = 3
        ctr = None

        # just loop through iterator in order to count items
        for ctr, _ in enumerate(ep.filter(region_constraint)):
            pass

        # ensure that generator yielded at least one item
        self.assertTrue(ctr is not None,
            "filter yielded nothing although %s item(s) were expected" % \
            expected_result_ctr)

        # ensure that generator returns exactly the number of items of the
        # expected result list
        self.assertTrue(ctr == expected_result_ctr - 1,
            "filter yielded wrong number of items (%s), expected were %s" % (
                ctr + 1, expected_result_ctr))


class VulnerabilityModelTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = risk.VulnerabilityModelFile(
                os.path.join(helpers.DATA_DIR, TEST_FILE))

    def test_schema_validation(self):
        self.assertRaises(risk.XMLValidationError,
                          risk.VulnerabilityModelFile,
                          INVALID_TEST_FILE)

    def test_loads_all_the_functions_defined(self):
        self.assertEqual(NO_OF_CURVES_IN_TEST_FILE, len(list(self.parser)))

    def test_loads_the_functions_data(self):
        model = self._load_vulnerability_model()

        self.assertEqual("MMI", model["PK"]["IMT"])
        self.assertEqual("fatalities", model["PK"]["lossCategory"])
        self.assertEqual("PAGER", model["PK"]["vulnerabilitySetID"])
        self.assertEqual("population", model["PK"]["assetCategory"])
        self.assertEqual("LN", model["PK"]["probabilisticDistribution"])

        self.assertEqual([0.00, 0.00, 0.00, 0.00, 0.00, 0.01,
                0.06, 0.18, 0.36, 0.36, 0.36],
                model["PK"]["lossRatio"])

        self.assertEqual([0.30, 0.30, 0.30, 0.30, 0.30, 0.30,
                0.30, 0.30, 0.30, 0.30, 0.30],
                model["PK"]["coefficientsVariation"])

        self.assertEqual([5.00, 5.50, 6.00, 6.50, 7.00, 7.50,
                8.00, 8.50, 9.00, 9.50, 10.00],
                model["PK"]["IML"])

        self.assertEqual([0.00, 0.00, 0.00, 0.00, 0.00, 0.01,
                0.06, 0.18, 0.36, 0.36, 0.36],
                model["IR"]["lossRatio"])

        self.assertEqual([0.30, 0.30, 0.30, 0.30, 0.30, 0.30,
                0.30, 0.30, 0.30, 0.30, 0.30],
                model["IR"]["coefficientsVariation"])

        self.assertEqual([5.00, 5.50, 6.00, 6.50, 7.00, 7.50,
                8.00, 8.50, 9.00, 9.50, 10.00],
                model["IR"]["IML"])

        self.assertEqual("NPAGER", model["AA"]["vulnerabilitySetID"])

        self.assertEqual([6.00, 6.50, 7.00, 7.50, 8.00, 8.50,
                9.00, 9.50, 10.00, 10.50, 11.00],
                model["AA"]["IML"])

        self.assertEqual([0.50, 0.50, 0.50, 0.50, 0.50, 0.50,
                0.50, 0.50, 0.50, 0.50, 0.50],
                model["AA"]["coefficientsVariation"])

    def _load_vulnerability_model(self):
        model = {}

        for vulnerability_function in self.parser:
            model[vulnerability_function["ID"]] = vulnerability_function

        return model


def generate_data(prefix):
    for i in xrange(1, 110):
        yield ((i, i), '%s%s' % (prefix, i))


class FileProducerTestCase(unittest.TestCase):
    def setUp(self):
        self.files = []

    def tearDown(self):
        for f in self.files:
            try:
                os.unlink(f)
            except Exception:
                pass

    def _make_data_file(self, prefix):
        fd, path = tempfile.mkstemp(suffix='.test')
        f = open(path, 'w')
        for ((cell_x, cell_y), word) in generate_data(prefix):
            f.write('%d %d %s\n' % (cell_x, cell_y, word))

        f.close()
        self.files.append(path)
        return path

    def test_reset_open_file(self):
        """
        Test the reset() method of a FileProducer object.

        In this case, we want to test the behavior of the reset when the
        producer's file handle is still open.
        """
        fp = risk.FileProducer(TEST_FILE_PATH)

        # the file should be open
        self.assertFalse(fp.file.closed)
        # seek position starts at 0
        self.assertEqual(0, fp.file.tell())

        # change the file seek position to something != 0
        fp.file.seek(1)
        self.assertEqual(1, fp.file.tell())

        fp.reset()

        # the file should be open still
        self.assertFalse(fp.file.closed)
        # verify the file seek position was reset
        self.assertEqual(0, fp.file.tell())

    def test_reset_closed_file(self):
        """
        Test the reset() method of a FileProducer object.

        In this case, we want to test the behavior of the reset when the
        producer's file handle is closed.
        """
        fp = risk.FileProducer(TEST_FILE_PATH)
        file_name = fp.file.name

        # close the file to start the test
        fp.file.close()

        self.assertTrue(fp.file.closed)

        fp.reset()

        # the same file should be open, seek position at 0
        self.assertFalse(fp.file.closed)
        self.assertEqual(file_name, fp.file.name)
        self.assertEqual(0, fp.file.tell())
