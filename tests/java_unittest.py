# This file is part of OpenQuake.
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
Tests for the Python-Java code layer.
"""

import os
import unittest

from openquake import java


class JvmMaxMemTestCase(unittest.TestCase):
    """Tests related to the JVM's maximum memory setting"""

    def setUp(self):
        try:
            del os.environ["OQ_JVM_MAXMEM"]
        except KeyError:
            # Make sure all tests start with a clean environment
            pass

    def test_jvm_maxmem_with_no_environ_var_and_no_param(self):
        """
        If the OQ_JVM_MAXMEM environment variable is not set and the `max_mem`
        parameter is not passed the default value should be used to determine
        the maximum.
        """
        self.assertTrue(os.environ.get("OQ_JVM_MAXMEM") is None)
        self.assertEqual(java.DEFAULT_JVM_MAX_MEM, java.get_jvm_max_mem(None))

    def test_jvm_maxmem_without_maxmem_environ_var_but_with_param(self):
        """
        If the OQ_JVM_MAXMEM environment variable is not set and the `max_mem`
        parameter is passed its value should be used to determine the maximum.
        """
        self.assertTrue(os.environ.get("OQ_JVM_MAXMEM") is None)
        self.assertEqual(1111, java.get_jvm_max_mem(1111))

    def test_jvm_maxmem_environ_var_honoured_without_param(self):
        """
        The value of the OQ_JVM_MAXMEM environment variable is honoured
        when no `max_mem` parameter is passed.
        """
        os.environ["OQ_JVM_MAXMEM"] = "2222"
        self.assertEqual("2222", os.environ.get("OQ_JVM_MAXMEM"))
        self.assertEqual(2222, java.get_jvm_max_mem(None))

    def test_jvm_maxmem_passed_param_trumps_environ_var(self):
        """
        If both the OQ_JVM_MAXMEM environment variable as well as the `max_mem`
        parameter are present the latter wins.
        """
        os.environ["OQ_JVM_MAXMEM"] = "2222"
        self.assertEqual("2222", os.environ.get("OQ_JVM_MAXMEM"))
        self.assertEqual(1111, java.get_jvm_max_mem(1111))

    def test_jvm_maxmem_invalid_environ_var(self):
        """
        If the OQ_JVM_MAXMEM environment variable has an invalid/non-numeric
        value a :class:`ValueError` will be raised.
        """
        os.environ["OQ_JVM_MAXMEM"] = "I hate numbers!"
        self.assertRaises(ValueError, java.get_jvm_max_mem, None)
