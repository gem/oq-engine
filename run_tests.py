# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

""" Tests for OpenGEM

Usage Examples:

    # to run all the tests
    python run_tests.py

    # to run a specific test suite imported here
    python run_tests.py ExampleTestCase

    # to run a specific test imported here
    python run_tests.py ExampleTestCase.testBasic

"""

import unittest
import sys

from tests.computation_unittest import *
from tests.example_unittest import *
from tests.jobber_unittest import *
from tests.parser_shaml_output_unittest import *
from tests.producer_unittest import *
from tests.region_unittest import *
from tests.flags_unittest import *

if __name__ == '__main__':
  unittest.main()
