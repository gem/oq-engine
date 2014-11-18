# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Test related to code in openquake/utils/config.py
"""


import os
import textwrap
import unittest

from openquake.engine.utils import config

from openquake.engine.tests.utils.helpers import ConfigTestCase
from openquake.engine.tests.utils.helpers import patch
from openquake.engine.tests.utils.helpers import touch


class ConfigTestCase(ConfigTestCase, unittest.TestCase):
    """Tests the behaviour of the utils.config.Config class."""

    def setUp(self):
        self.setup_config()

    def tearDown(self):
        self.teardown_config()

    def test_get_paths_with_global_env_var_set(self):
        # _get_paths() will honour the OQ_SITE_CFG_PATH environment
        # variable
        os.environ["OQ_SITE_CFG_PATH"] = "/a/b/c/d"
        self.assertEqual(
            ["/a/b/c/d", "%s/openquake.cfg" % config.OQDIR],
            config.cfg._get_paths())

    def test_get_paths_with_local_env_var_set(self):
        # _get_paths() will honour the OQ_LOCAL_CFG_PATH
        # variable
        os.environ["OQ_LOCAL_CFG_PATH"] = "/e/f/g/h"
        self.assertEqual(
            ["/etc/openquake/openquake.cfg", "/e/f/g/h"],
            config.cfg._get_paths())

    def test_get_paths_with_no_environ(self):
        # _get_paths() will return the hard-coded paths if the OQ_SITE_CFG_PATH
        # and the OQ_LOCAL_CFG_PATH variables are not set
        self.assertEqual(
            ["/etc/openquake/openquake.cfg",
             "%s/openquake.cfg" % config.OQDIR],
            config.cfg._get_paths())

    def test_load_from_file_with_no_config_files(self):
        # In the absence of config files the `cfg` dict will be empty
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertEqual([], config.cfg.cfg.keys())

    def test_load_from_file_with_global(self):
        # The config data in the global file is loaded correctly
        content = '''
            [A]
            a=1
            b=c

            [B]
            b=2'''
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertEqual(["A", "B"], sorted(config.cfg.cfg))
        self.assertEqual({"a": "1", "b": "c"}, config.cfg.cfg.get("A"))
        self.assertEqual({"b": "2"}, config.cfg.cfg.get("B"))

    def test_load_from_file_with_local(self):
        # The config data in the local file is loaded correctly
        content = '''
            [C]
            c=3
            d=e

            [D]
            d=4'''
        local_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_LOCAL_CFG_PATH"] = local_path
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertEqual(["C", "D"], sorted(config.cfg.cfg))
        self.assertEqual({"c": "3", "d": "e"}, config.cfg.cfg.get("C"))
        self.assertEqual({"d": "4"}, config.cfg.cfg.get("D"))

    def test_load_from_file_with_local_and_global(self):
        # The config data in the local and global files is loaded correctly
        content = '''
            [A]
            a=1
            b=c

            [B]
            b=2'''
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        content = '''
            [C]
            c=3
            d=e

            [D]
            d=4'''
        local_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_LOCAL_CFG_PATH"] = local_path
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertEqual(["A", "B", "C", "D"],
                         sorted(config.cfg.cfg))
        self.assertEqual({"a": "1", "b": "c"}, config.cfg.cfg.get("A"))
        self.assertEqual({"b": "2"}, config.cfg.cfg.get("B"))
        self.assertEqual({"c": "3", "d": "e"}, config.cfg.cfg.get("C"))
        self.assertEqual({"d": "4"}, config.cfg.cfg.get("D"))

    def test_load_from_file_with_local_overriding_global(self):
        # The config data in the local and global files is loaded correctly.
        # The local data will override the global one
        content = '''
            [A]
            a=1
            b=c

            [B]
            b=2'''
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        content = '''
            [A]
            a=2
            d=e

            [D]
            c=d-1
            d=4'''
        local_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_LOCAL_CFG_PATH"] = local_path
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertEqual(["A", "B", "D"],
                         sorted(config.cfg.cfg))
        self.assertEqual({"a": "2", "b": "c", "d": "e"},
                         config.cfg.cfg.get("A"))
        self.assertEqual({"b": "2"}, config.cfg.cfg.get("B"))
        self.assertEqual({"c": "d-1", "d": "4"}, config.cfg.cfg.get("D"))

    def test_get_with_unknown_section(self):
        # get() will return `None` for a section name that is not known
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertTrue(config.cfg.get("Anything") is None)

    def test_get_with_known_section(self):
        # get() will correctly return configuration data for known sections
        content = '''
            [E]
            f=6
            g=h'''
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertEqual({"f": "6", "g": "h"}, config.cfg.get("E"))


class GetSectionTestCase(unittest.TestCase):
    """Tests the behaviour of utils.config.get_section()"""

    def tearDown(self):
        config.cfg.cfg.clear()
        config.cfg._load_from_file()

    def test_get_section_merely_calls_get_on_config_data_dict(self):
        orig_method = config.cfg.get

        def fake_get(section):
            self.assertEqual("f@k3", section)
            return {"this": "is", "so": "fake"}

        config.cfg.get = fake_get
        self.assertEqual({"this": "is", "so": "fake"},
                         config.get_section("f@k3"))
        config.cfg.get = orig_method


class GetTestCase(unittest.TestCase):
    """Tests the behaviour of utils.config.get()"""

    def tearDown(self):
        config.cfg.cfg.clear()
        config.cfg._load_from_file()

    def test_get_with_empty_section_data(self):
        # config.get() returns `None` if the section data dict is empty
        with patch('openquake.engine.utils.config.get_section') as mock:
            mock.return_value = dict()
            self.assertTrue(config.get("whatever", "key") is None)
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("whatever",), {}], mock.call_args)

    def test_get_with_nonempty_section_data_and_known_key(self):
        # config.get() correctly returns the configuration datum for known
        # sections/keys
        with patch('openquake.engine.utils.config.get_section') as mock:
            mock.return_value = dict(a=11)
            self.assertEqual(11, config.get("hmmm", "a"))
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("hmmm",), {}], mock.call_args)

    def test_get_with_unknown_key(self):
        """config.get() returns `None` if the `key` is not known."""
        with patch('openquake.engine.utils.config.get_section') as mock:
            mock.return_value = dict(b=1)
            self.assertTrue(config.get("arghh", "c") is None)
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("arghh",), {}], mock.call_args)


class FlagSetTestCase(ConfigTestCase, unittest.TestCase):
    """
    Tests for openquake.engine.utils.config.flag_set()
    """

    def setUp(self):
        self.setup_config()

    def tearDown(self):
        self.teardown_config()

    def test_flag_set_with_absent_key(self):
        # flag_set() returns False if the setting
        # is not present in the configuration file.
        self.prepare_config("a")
        self.assertFalse(config.flag_set("a", "z"))

    def test_flag_set_with_number(self):
        # flag_set() returns False if the setting is present but
        # not equal to 'true'
        self.prepare_config("b", {"y": "123"})
        self.assertFalse(config.flag_set("b", "y"))

    def test_flag_set_with_text_but_not_true(self):
        """
        flag_set() returns False if the setting is present but
        not equal to 'true'.
        """
        self.prepare_config("c", {"x": "blah"})
        self.assertFalse(config.flag_set("c", "x"))

    def test_flag_set_with_true(self):
        """
        flag_set() returns True if the setting is present and equal to 'true'.
        """
        self.prepare_config("d", {"w": "true"})
        self.assertTrue(config.flag_set("d", "w"))

    def test_flag_set_with_True(self):
        """
        flag_set() returns True if the setting is present and equal to 'true'.
        """
        self.prepare_config("e", {"v": " True 	 "})
        self.assertTrue(config.flag_set("e", "v"))
