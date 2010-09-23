# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import sys
import unittest

from opengem import logs
from opengem import flags
FLAGS = flags.FLAGS

flags.DEFINE_boolean('speed_tests', False, "Run performance tests?")

if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)  
    
    logs.init_logs()
    
    from tests.example_unittest import *
    from tests.flags_unittest import *
    from tests.geo_unittest import *
    from tests.jobber_unittest import *
    from tests.loss_output_unittest import *
    from tests.output_unittest import *
    from tests.parser_exposure_portfolio_unittest import *
    from tests.parser_shaml_output_unittest import *
    from tests.parser_vulnerability_model_unittest import *
    from tests.producer_unittest import *
    from tests.risk_tests import *
    from tests.classical_psha_based_unittest import *
    from tests.output_shaml_unittest import *
    
    if FLAGS.speed_tests:
        from tests.xml_speedtests import *
    
    unittest.main()
