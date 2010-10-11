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
    sys.path.append("tests")
    logs.init_logs()
    
    try:
        import nose
        args = ["nosetests","tests"]
        args.append("-q")
        args.append("--logging-clear-handlers")
        #if (FLAGS.debug == "debug"):
        #    args.append("-v")
        #else:
        # args.append("--verbosity=0")
#         
# FLAGS = flags.FLAGS
# 
# if FLAGS.speed_tests:
#     from xml_speedtests import *

        nose.run(argv=args)
    except ImportError, _e:
        unittest.main()
