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

import os
import unittest

from openquake.parser import risk
from tests.utils import helpers
import tempfile


TEST_FILE = "examples/vulnerability-model-discrete.xml"
INVALID_TEST_FILE = helpers.get_data_path("examples/invalid_vulnerability.xml")
MISMATCHED_TEST_FILE = "examples/source-model.xml"
NO_OF_CURVES_IN_TEST_FILE = 4
TEST_FILE_PATH = helpers.get_data_path('config.gem')


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
