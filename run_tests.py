# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
This utility is deprecated.

Usage Examples:

    # to run the unit tests
    python run_tests.py

    # to run all the unit tests (including the ones requiring a database)
    python run_tests.py --all_tests

    # to run a specific test suite imported here
    python run_tests.py tests:ExampleTestCase

    # to run a specific test imported here
    python run_tests.py tests:ExampleTestCase.testBasic

"""

import os
import sys
import unittest

from openquake import flags
FLAGS = flags.FLAGS

flags.DEFINE_boolean('speed_tests', False, "Run performance tests?")
flags.DEFINE_boolean('bb_suite', False, "Run black box tests suite?")
flags.DEFINE_boolean('all_tests', False, "Run all tests")

if __name__ == '__main__':
    sys.argv = FLAGS(sys.argv)
    sys.path.append("%s/tests" % os.path.abspath(os.path.curdir))
    try:
        import nose

        args = sys.argv
        args.remove('run_tests.py')
        args = ['nosetests', '-x'] + args

        if FLAGS.speed_tests:
            print "Running speed tests with %s" % args
            nose.run(defaultTest='tests.xml_speedtests', argv=args)
        elif FLAGS.bb_suite:
            args = args + ["--testmatch", "bb_.+"]
            print "Running the black box tests suite..."
            nose.run(defaultTest="tests", argv=args)
        elif FLAGS.all_tests:
            import glob

            args += glob.glob('tests/*_unittest.py')
            args += glob.glob('db_tests/*_unittest.py')

            print "Running the complete tests suite..."
            nose.run(argv=args)
        else:
            nose.run(defaultTest='tests', argv=args)

    except ImportError, _e:
        print "Couldn't find nose, using something else"
        unittest.main()
