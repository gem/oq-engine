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
Test related to code in openquake/utils/config.py
"""


import os
import unittest

from openquake.utils import config


class ConfigTestCase(unittest.TestCase):
    """Tests the behaviour of the utils.config.Config class."""

    def setUp(self):
        self.orig_env = os.environ.copy()
        os.environ.clear()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_get_paths_with_global_env_var_set(self):
        """
        _get_paths() will honour the OQ_SITE_CFG_PATH environment
        variable.
        """
        os.environ["OQ_SITE_CFG_PATH"] = "/a/b/c/d"
        self.assertEqual(
            ["/a/b/c/d", "%s/openquake.cfg" % os.path.abspath(os.getcwd())],
            config.Config()._get_paths())

    def test_get_paths_with_local_env_var_set(self):
        """
        _get_paths() will honour the OQ_LOCAL_CFG_PATH
        variable.
        """
        os.environ["OQ_LOCAL_CFG_PATH"] = "/e/f/g/h"
        self.assertEqual(
            ["/etc/openquake/openquake.cfg", "/e/f/g/h"],
            config.Config()._get_paths())

    def test_get_paths_with_no_environ(self):
        """
        _get_paths() will return the hard-coded paths if the OQ_SITE_CFG_PATH
        and the OQ_LOCAL_CFG_PATH variables are not set.
        """
        self.assertEqual(
            ["/etc/openquake/openquake.cfg",
             "%s/openquake.cfg" % os.path.abspath(os.getcwd())],
            config.Config()._get_paths())
