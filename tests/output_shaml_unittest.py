# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os
import unittest

from opengem import test
from opengem.output import shaml

TEST_FILE = "shaml_test_result.xml"

class OutputShamlTestCase(unittest.TestCase):

    def tearDown(self):
        try:
            os.remove(os.path.join(test.DATA_DIR, TEST_FILE))
        except OSError:
            pass

    # quick learning test
    def test_string_matching(self):
        self.assertTrue("<test>" in "<a><test></a>")
        self.assertFalse("#test>" in "<a><test></a>")
    
    def test_writes_the_file_when_closed(self):
        writer = shaml.ShamlWriter(os.path.join(test.DATA_DIR, TEST_FILE))
        writer.close()
    
        # with no written file we would have an IOError
        result = open(os.path.join(test.DATA_DIR, TEST_FILE))
        result.close()

    def test_writes_the_xml_metadata(self):
        writer = shaml.ShamlWriter(os.path.join(test.DATA_DIR, TEST_FILE))
        writer.close()
        
        self.assertTrue(shaml.XML_METADATA in self._result_as_string())

    def test_writes_an_empty_list_with_no_output(self):
        writer = shaml.ShamlWriter(os.path.join(test.DATA_DIR, TEST_FILE))
        writer.close()

        self.assertTrue(shaml.HEADER in self._result_as_string())
        self.assertTrue(shaml.FOOTER in self._result_as_string())

    def test_writes_a_single_result(self):
        pass

    def test_writes_multiple_results(self):
        pass

    def test_end_to_end_reading_and_writing(self):
        pass

    def _result_as_string(self):
        try:
            result = open(os.path.join(test.DATA_DIR, TEST_FILE))
            return result.read()
        finally:
            result.close()
