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
Unit tests for the tools/dbmaint.py tool.
"""


import unittest


class PsqlTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.psql()."""

    def __init__(self, *args, **kwargs):
        super(PsqlTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None


class FindScriptsTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.find_scripts()."""

    def __init__(self, *args, **kwargs):
        super(FindScriptsTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None


class ScriptsToRunTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.scripts_to_run()."""

    def __init__(self, *args, **kwargs):
        super(ScriptsToRunTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None


class ErrorOccuredTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.error_occurred()."""

    def __init__(self, *args, **kwargs):
        super(ErrorOccuredTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None


class RunScriptsTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.run_scripts()."""

    def __init__(self, *args, **kwargs):
        super(RunScriptsTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None
