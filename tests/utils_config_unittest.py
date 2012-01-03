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
import textwrap
import unittest

from openquake.utils import config

from tests.utils.helpers import ConfigTestMixin, TestMixin, patch


class ConfigTestCase(ConfigTestMixin, unittest.TestCase):
    """Tests the behaviour of the utils.config.Config class."""

    def setUp(self):
        self.setup_config()

    def tearDown(self):
        self.teardown_config()

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

    def test_load_from_file_with_no_config_files(self):
        """In the absence of config files the `cfg` dict will be empty."""
        config.Config().cfg.clear()
        config.Config()._load_from_file()
        self.assertEqual([], config.Config().cfg.keys())

    def test_load_from_file_with_global(self):
        """The config data in the global file is loaded correctly."""
        content = '''
            [A]
            a=1
            b=c

            [B]
            b=2'''
        site_path = self.touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        config.Config().cfg.clear()
        config.Config()._load_from_file()
        self.assertEqual(["A", "B"], sorted(config.Config().cfg.keys()))
        self.assertEqual({"a": "1", "b": "c"}, config.Config().cfg.get("A"))
        self.assertEqual({"b": "2"}, config.Config().cfg.get("B"))

    def test_load_from_file_with_local(self):
        """The config data in the local file is loaded correctly."""
        content = '''
            [C]
            c=3
            d=e

            [D]
            d=4'''
        local_path = self.touch(content=textwrap.dedent(content))
        os.environ["OQ_LOCAL_CFG_PATH"] = local_path
        config.Config().cfg.clear()
        config.Config()._load_from_file()
        self.assertEqual(["C", "D"], sorted(config.Config().cfg.keys()))
        self.assertEqual({"c": "3", "d": "e"}, config.Config().cfg.get("C"))
        self.assertEqual({"d": "4"}, config.Config().cfg.get("D"))

    def test_load_from_file_with_local_and_global(self):
        """
        The config data in the local and global files is loaded correctly.
        """
        content = '''
            [A]
            a=1
            b=c

            [B]
            b=2'''
        site_path = self.touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        content = '''
            [C]
            c=3
            d=e

            [D]
            d=4'''
        local_path = self.touch(content=textwrap.dedent(content))
        os.environ["OQ_LOCAL_CFG_PATH"] = local_path
        config.Config().cfg.clear()
        config.Config()._load_from_file()
        self.assertEqual(["A", "B", "C", "D"],
                         sorted(config.Config().cfg.keys()))
        self.assertEqual({"a": "1", "b": "c"}, config.Config().cfg.get("A"))
        self.assertEqual({"b": "2"}, config.Config().cfg.get("B"))
        self.assertEqual({"c": "3", "d": "e"}, config.Config().cfg.get("C"))
        self.assertEqual({"d": "4"}, config.Config().cfg.get("D"))

    def test_load_from_file_with_local_overriding_global(self):
        """
        The config data in the local and global files is loaded correctly.
        The local data will override the global one.
        """
        content = '''
            [A]
            a=1
            b=c

            [B]
            b=2'''
        site_path = self.touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        content = '''
            [A]
            a=2
            d=e

            [D]
            c=d-1
            d=4'''
        local_path = self.touch(content=textwrap.dedent(content))
        os.environ["OQ_LOCAL_CFG_PATH"] = local_path
        config.Config().cfg.clear()
        config.Config()._load_from_file()
        self.assertEqual(["A", "B", "D"],
                         sorted(config.Config().cfg.keys()))
        self.assertEqual({"a": "2", "b": "c", "d": "e"},
                         config.Config().cfg.get("A"))
        self.assertEqual({"b": "2"}, config.Config().cfg.get("B"))
        self.assertEqual({"c": "d-1", "d": "4"}, config.Config().cfg.get("D"))

    def test_get_with_unknown_section(self):
        """
        get() will return `None` for a section name that is not known.
        """
        config.Config().cfg.clear()
        config.Config()._load_from_file()
        self.assertTrue(config.Config().get("Anything") is None)

    def test_get_with_known_section(self):
        """
        get() will correctly return configuration data for known sections.
        """
        content = '''
            [E]
            f=6
            g=h'''
        site_path = self.touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        config.Config().cfg.clear()
        config.Config()._load_from_file()
        self.assertEqual({"f": "6", "g": "h"}, config.Config().get("E"))


class GetSectionTestCase(unittest.TestCase):
    """Tests the behaviour of utils.config.get_section()"""

    def tearDown(self):
        config.Config().cfg.clear()
        config.Config()._load_from_file()

    def test_get_section_merely_calls_get_on_config_data_dict(self):
        "config.get_section() merely makes use of Config().get()"""
        orig_method = config.Config().get

        def fake_get(section):
            self.assertEqual("f@k3", section)
            return {"this": "is", "so": "fake"}

        config.Config().get = fake_get
        self.assertEqual({"this": "is", "so": "fake"},
                         config.get_section("f@k3"))
        config.Config().get = orig_method


class GetTestCase(unittest.TestCase):
    """Tests the behaviour of utils.config.get()"""

    def tearDown(self):
        config.Config().cfg.clear()
        config.Config()._load_from_file()

    def test_get_with_empty_section_data(self):
        """config.get() returns `None` if the section data dict is empty."""
        with patch('openquake.utils.config.get_section') as mock:
            mock.return_value = dict()
            self.assertTrue(config.get("whatever", "key") is None)
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("whatever",), {}], mock.call_args)

    def test_get_with_nonempty_section_data_and_known_key(self):
        """
        config.get() correctly returns the configuration datum for known
        sections/keys.
        """
        with patch('openquake.utils.config.get_section') as mock:
            mock.return_value = dict(a=11)
            self.assertEqual(11, config.get("hmmm", "a"))
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("hmmm",), {}], mock.call_args)

    def test_get_with_unknown_key(self):
        """config.get() returns `None` if the `key` is not known."""
        with patch('openquake.utils.config.get_section') as mock:
            mock.return_value = dict(b=1)
            self.assertTrue(config.get("arghh", "c") is None)
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("arghh",), {}], mock.call_args)


class IsReadableTestCase(TestMixin, unittest.TestCase):
    """Tests the behaviour of utils.config.Config.is_readable()."""

    def setUp(self):
        self.orig_env = os.environ.copy()
        os.environ.clear()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_is_readable_no_file_present(self):
        """When no config file is present is_readable() returns `False`."""
        os.environ["OQ_SITE_CFG_PATH"] = "/this/does/not/exist.cfg"
        os.environ["OQ_LOCAL_CFG_PATH"] = "/nor/does/this.cfg"
        self.assertFalse(config.Config().is_readable())

    def test_is_readable_all_files_lack_permissions(self):
        """
        When we miss read permissions for all config files is_readable()
        returns `False`.
        """
        os.environ["OQ_SITE_CFG_PATH"] = "/etc/sudoers"
        os.environ["OQ_LOCAL_CFG_PATH"] = "/etc/passwd-"
        self.assertFalse(config.Config().is_readable())

    def test_is_readable_one_plus_files_have_permissions(self):
        """
        When at least one config file is present and we have permission to
        read it is_readable() returns `True`.
        """
        os.environ["OQ_SITE_CFG_PATH"] = "/etc/passwd"
        os.environ["OQ_LOCAL_CFG_PATH"] = "/etc/passwd-"
        self.assertTrue(config.Config().is_readable())


class HazardBlockSizeTestCase(unittest.TestCase):
    """Tests the behaviour of utils.config.hazard_block_size()."""

    def test_not_configured(self):
        """
        The hazard block size was not set in openquake.cfg, the default
        is returned.
        """
        with patch("openquake.utils.config.get") as mget:
            mget.return_value = None
            self.assertEqual(8192, config.hazard_block_size())

    def test_not_configured_default_overriden(self):
        """
        The hazard block size was not set in openquake.cfg, the default
        is specified by the caller is returned.
        """
        with patch("openquake.utils.config.get") as mget:
            mget.return_value = None
            self.assertEqual(333, config.hazard_block_size(333))

    def test_configured(self):
        """The hazard block size *was* configured in openquake.cfg"""
        with patch("openquake.utils.config.get") as mget:
            mget.return_value = "33"
            self.assertEqual(33, config.hazard_block_size())

    def test_configuration_invalid(self):
        """
        The hazard block size *was* configured in openquake.cfg but
        the setting is not a valid number.
        """
        with patch("openquake.utils.config.get") as mget:
            mget.return_value = "not a number"
            self.assertRaises(ValueError, config.hazard_block_size)
