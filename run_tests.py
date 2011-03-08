# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.



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

import os
import sys
import unittest

from openquake import logs
from openquake import flags
FLAGS = flags.FLAGS

flags.DEFINE_boolean('speed_tests', False, "Run performance tests?")

if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)  
    sys.path.append("%s/tests" % os.path.abspath(os.path.curdir))
    logs.init_logs()
    try:
        import nose

        args = sys.argv
        args.remove('run_tests.py')
        args = ['nosetests', '-e', 'do_test.+'] + args

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

