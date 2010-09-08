# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
This is our basic test running framework.

Usage Examples:

    # to run all the tests
    python run_tests.py

    # to run a specific test suite imported here
    python run_tests.py ExampleTestCase

    # to run a specific test imported here
    python run_tests.py ExampleTestCase.testBasic

"""

import logging
import sys
import unittest

from opengem import flags
FLAGS = flags.FLAGS

flags.DEFINE_boolean('speed_tests', False, "Run performance tests?")

from tests.computation_unittest import *
from tests.example_unittest import *
from tests.flags_unittest import *
from tests.parser_exposure_portfolio_unittest import *
from tests.parser_shaml_output_unittest import *
from tests.parser_vulnerability_model_unittest import *
from tests.probabilistic_scenario_unittest import *
from tests.producer_unittest import *
from tests.region_unittest import *
from tests.risk_tests import *

if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)  
    logging.getLogger().setLevel(logging.DEBUG)
    
    if FLAGS.speed_tests:
        from tests.xml_speedtests import *

    unittest.main()
