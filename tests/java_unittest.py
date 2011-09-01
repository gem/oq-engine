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
Tests for the Python-Java code layer.
"""

import cPickle
import os
import unittest

from openquake import java

from tests.utils import helpers
from tests.utils.tasks import jtask_task, failing_jtask_task


class JvmMaxMemTestCase(unittest.TestCase):
    """Tests related to the JVM's maximum memory setting"""

    def test_jvm_memmax_setting_is_not_passed(self):
        """Do not pass -Xmx to the jvm."""
        with helpers.patch("jpype.startJVM") as startjvm_mock:
            with helpers.patch("jpype.isJVMStarted") as isjvmstarted_mock:
                # Make sure that startJVM() gets called.
                isjvmstarted_mock.side_effect = lambda: False
                with helpers.patch("openquake.java.init_logs"):
                    java.jvm()
                    args, _ = startjvm_mock.call_args
                    self.assertFalse(
                        filter(lambda a: a.startswith("-Xmx"), args))


class CeleryJavaExceptionTestCase(unittest.TestCase):
    """Tests the behaviour of Java exceptions in Celery jobs."""

    def test_failing_java_subtask(self):
        """Java exception is propagated correctly."""
        try:
            result = jtask_task.apply_async(args=['foo'])

            result.wait()
        except java.JavaException, exc:
            self.assertEqual('java.lang.NumberFormatException',
                             exc.message.split(':')[0])
        else:
            raise Exception("Exception not raised.")

    def test_failing_python_subtask(self):
        """Java exception is propagated correctly."""
        try:
            result = failing_jtask_task.apply_async(args=['foo'])

            result.wait()
        except Exception, exc:
            self.assertEqual('test exception',
                             exc.args[0].split(':')[0])
        else:
            raise Exception("Exception not raised.")

    def test_successful_java_subtask(self):
        """Task result is correctly propagated"""
        result = jtask_task.apply_async(args=['123'])

        res = result.wait()
        self.assertEqual('123', res)


class JavaExceptionTestCase(unittest.TestCase):
    """Test that java stack trace is retrieved correctly"""

    def _get_exception(self):
        jpype = java.jvm()

        try:
            jpype.java.lang.Integer('foo')
        except jpype.JavaException, e:
            return e

        raise Exception("Can't get there")

    def _get_trace(self):
        return java.JavaException.get_java_stacktrace(self._get_exception())

    def test_get_stack_trace(self):
        trace = self._get_trace()

        # this is a basic sanity test; only Sun^H^H^HOracle knows the
        # correct stack trace...
        self.assertTrue(len(trace) > 2)

        # the stack trace must start in NumberFromatException and
        # finish in Integer.java; order (same as Python traceback)
        # is outer frame first
        self.assertEquals(trace[0][0], 'Integer.java')
        self.assertEquals(trace[-1][0], 'NumberFormatException.java')

        # the stack trace must start in NumberFromatException and
        # finish in Integer constructor
        self.assertEquals(trace[0][2], 'java.lang.Integer.<init>')
        self.assertTrue(trace[-1][2].startswith(
                'java.lang.NumberFormatException'))

    def test_stack_trace_sane(self):
        trace = self._get_trace()

        for frame in trace:
            self.assertTrue(frame[0].endswith(".java"))
            self.assertEquals(int, type(frame[1]))
            self.assertEquals(None, frame[3])

    def test_java_exception_pickleable(self):
        e = self._get_exception()
        exception = java.JavaException(e)

        self.assertRaises(cPickle.PicklingError, cPickle.dumps, e)

        pickled = cPickle.dumps(exception)
        unpickled = cPickle.loads(pickled)

        self.assertTrue(isinstance(unpickled, java.JavaException))
        self.assertTrue(len(unpickled.trace) > 2)
        self.assertTrue(unpickled.message.startswith(
                'java.lang.NumberFormatException'))

    def test_jexception_decorator(self):
        @java.jexception
        def test():
            jpype = java.jvm()

            jpype.java.lang.Integer('foo')

        try:
            test()
        except java.JavaException, e:
            self.assertTrue(e.message.startswith(
                    'java.lang.NumberFormatException'))
            self.assertTrue(len(e.trace) > 2)
