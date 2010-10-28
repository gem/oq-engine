# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This is our basic test running framework.

Usage Examples:

    # to run all the tests
    python run_tests.py

    # to run a specific test suite imported here
    python run_tests.py tests:ExampleTestCase

    # to run a specific test imported here
    python run_tests.py tests:ExampleTestCase.testBasic

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

        args = sys.argv
        args.remove('run_tests.py')
        args = ['nosetests'] + args


        if (FLAGS.debug == "debug"):
            pass
        else:
            args.append("--logging-clear-handlers")

        if FLAGS.speed_tests:
            print "Running speed tests with %s" % args
            nose.run(defaultTest='tests.xml_speedtests', argv=args)
        else:
            nose.run(defaultTest='tests', argv=args)

    except ImportError, _e:
        print "Couldn't find nose, using something else"
        unittest.main()

