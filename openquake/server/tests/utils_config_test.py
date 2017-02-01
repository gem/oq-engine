# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Test related to code in openquake/commonlib.config.py
"""


import os
import shutil
import textwrap
import unittest

from openquake.commonlib import config
from openquake.server.tests.helpers import patch
from openquake.server.tests.helpers import touch


class ConfigTestCase(unittest.TestCase):
    """Tests the behaviour of the config.Config class."""

    def setUp(self):
        self.orig_env = os.environ.copy()
        os.environ.clear()
        # Move the local configuration file out of the way if it exists.
        # Otherwise the tests that follow will break.
        local_path = config.cfg.PKG_PATH
        if os.path.isfile(local_path):
            shutil.move(local_path, "%s.test_bakk" % local_path)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)
        # Move the local configuration file back into place if it was stashed
        # away.
        local_path = config.cfg.PKG_PATH
        if os.path.isfile("%s.test_bakk" % local_path):
            shutil.move("%s.test_bakk" % local_path, local_path)
        config.cfg.cfg.clear()
        config.cfg._load_from_file()

    def prepare_config(self, section, data=None):
        """Set up a configuration with the given `max_mem` value."""
        if data is not None:
            data = '\n'.join("%s=%s" % item for item in data.items())
            content = """
                [%s]
                %s""" % (section, data)
        else:
            content = ""
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_CONFIG_FILE"] = site_path
        config.cfg.cfg.clear()
        config.cfg._load_from_file()

    def test_get_paths_with_env_var_set(self):
        # _paths will honour the OQ_CONFIG_FILE environment
        # variable
        os.environ["OQ_CONFIG_FILE"] = "/a/b/c/d"
        cfg = config._Config()
        self.assertEqual([cfg.PKG_PATH, "/a/b/c/d"], cfg._paths)

    def test_get_paths_with_no_environ(self):
        # _paths will return the hard-coded paths if
        # OQ_CONFIG_FILE variable is not set
        self.assertEqual([config.cfg.PKG_PATH], config.cfg._paths)

    def test_load_from_file_with_no_config_files(self):
        # In the absence of config files the `cfg` dict will be empty
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertEqual([], list(config.cfg.cfg))

    def test_load_from_env_var(self):
        # The config data in the local file is loaded correctly
        content = '''
            [C]
            c=3
            d=e

            [D]
            d=4'''
        local_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_CONFIG_FILE"] = local_path
        cfg = config._Config()
        cfg.cfg.clear()
        cfg._load_from_file()
        self.assertEqual(["C", "D"], sorted(cfg.cfg))
        self.assertEqual({"c": "3", "d": "e"}, cfg.cfg.get("C"))
        self.assertEqual({"d": "4"}, cfg.cfg.get("D"))

    def test_get_with_unknown_section(self):
        # get() will return `None` for a section name that is not known
        config.cfg.cfg.clear()
        config.cfg._load_from_file()
        self.assertIsNone(config.cfg.get("Anything"))

    def test_get_with_known_section(self):
        # get() will correctly return configuration data for known sections
        content = '''
            [E]
            f=6
            g=h'''
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_CONFIG_FILE"] = site_path
        cfg = config._Config()
        cfg.cfg.clear()
        cfg._load_from_file()
        self.assertEqual({"f": "6", "g": "h"}, cfg.get("E"))


class GetSectionTestCase(unittest.TestCase):
    """Tests the behaviour of config.get_section()"""

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
    """Tests the behaviour of config.get()"""

    def tearDown(self):
        config.cfg.cfg.clear()
        config.cfg._load_from_file()

    def test_get_with_empty_section_data(self):
        # config.get() returns `None` if the section data dict is empty
        with patch('openquake.commonlib.config.get_section') as mock:
            mock.return_value = dict()
            self.assertTrue(config.get("whatever", "key") is None)
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("whatever",), {}], mock.call_args)

    def test_get_with_nonempty_section_data_and_known_key(self):
        # config.get() correctly returns the configuration datum for known
        # sections/keys
        with patch('openquake.commonlib.config.get_section') as mock:
            mock.return_value = dict(a=11)
            self.assertEqual(11, config.get("hmmm", "a"))
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("hmmm",), {}], mock.call_args)

    def test_get_with_unknown_key(self):
        # config.get() returns `None` if the `key` is not known
        with patch('openquake.commonlib.config.get_section') as mock:
            mock.return_value = dict(b=1)
            self.assertTrue(config.get("arghh", "c") is None)
            self.assertEqual(1, mock.call_count)
            self.assertEqual([("arghh",), {}], mock.call_args)
