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
Test related to code in db/alchemy/db_utils.py
"""


import mock
import os
import unittest

from db.alchemy.db_utils import SessionCache


class SessionCacheInitSessionTestCase(unittest.TestCase):
    """Tests the behaviour of alchemy.db_utils.SessionCache.init_session()."""

    def tearDown(self):
        SessionCache().__sessions__.clear()

    def test_init_session_with_empty_user(self):
        """
        _init_session() raises an `AssertionError` if the user name parameter
        is empty or `None`.
        """
        self.assertRaises(AssertionError, SessionCache()._init_session, "", "")
        self.assertRaises(
            AssertionError, SessionCache()._init_session, None, "")

    def test_init_session_with_repeated_initialization(self):
        """
        _init_session() raises an `AssertionError` upon repeated
        initialization.
        """
        sc = SessionCache()
        sc.__sessions__["oq_uiapi_writer"] = object()
        self.assertRaises(
            AssertionError, SessionCache()._init_session, "oq_uiapi_writer", "")

    def test_init_session_with_oq_engine_db_name(self):
        """
        _init_session() observes the `OQ_ENGINE_DB_NAME` environment variable.
        """
        os.environ["OQ_ENGINE_DB_NAME"] = "abc123"
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session("usr1", "")
                self.assertEqual(1, ce_mock.call_count)
                (arg,), kwargs = ce_mock.call_args
                self.assertEqual(
                    'postgresql+psycopg2://usr1:@localhost/abc123', arg)
                self.assertEqual({}, kwargs)
        del os.environ["OQ_ENGINE_DB_NAME"]

    def test_init_session_without_oq_engine_db_name(self):
        """
        In the absence of the `OQ_ENGINE_DB_NAME` environment variable
        the session will be established for the "geonode" database.
        """
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session("usr2", "")
                self.assertEqual(1, ce_mock.call_count)
                (arg,), kwargs = ce_mock.call_args
                self.assertEqual(
                    'postgresql+psycopg2://usr2:@localhost/geonode', arg)
                self.assertEqual({}, kwargs)

    def test_init_session_with_oq_engine_db_host(self):
        """
        _init_session() observes the `OQ_ENGINE_DB_HOST` environment variable.
        """
        os.environ["OQ_ENGINE_DB_HOST"] = "bcd234"
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session("usr3", "")
                self.assertEqual(1, ce_mock.call_count)
                (arg,), kwargs = ce_mock.call_args
                self.assertEqual(
                    'postgresql+psycopg2://usr3:@bcd234/geonode', arg)
                self.assertEqual({}, kwargs)
        del os.environ["OQ_ENGINE_DB_HOST"]

    def test_init_session_without_oq_engine_db_host(self):
        """
        In the absence of the `OQ_ENGINE_DB_HOST` environment variable
        the session will be established for the `localhost`.
        """
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session("usr4", "")
                self.assertEqual(1, ce_mock.call_count)
                (arg,), kwargs = ce_mock.call_args
                self.assertEqual(
                    'postgresql+psycopg2://usr4:@localhost/geonode', arg)
                self.assertEqual({}, kwargs)

    def test_init_session_with_none_password(self):
        """
        _init_session() will use an empty string for `None` passwords.
        """
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session("usr5", None)
                self.assertEqual(1, ce_mock.call_count)
                (arg,), kwargs = ce_mock.call_args
                self.assertEqual(
                    'postgresql+psycopg2://usr5:@localhost/geonode', arg)
                self.assertEqual({}, kwargs)

    def test_init_session_with_empty_password(self):
        """
        _init_session() will use an empty password properly.
        """
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session("usr6", "")
                self.assertEqual(1, ce_mock.call_count)
                (arg,), kwargs = ce_mock.call_args
                self.assertEqual(
                    'postgresql+psycopg2://usr6:@localhost/geonode', arg)
                self.assertEqual({}, kwargs)

    def test_init_session_with_non_empty_password(self):
        """
        _init_session() will use a non-empty password correctly.
        """
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session("usr7", "s3cr3t")
                self.assertEqual(1, ce_mock.call_count)
                (arg,), kwargs = ce_mock.call_args
                self.assertEqual(
                    'postgresql+psycopg2://usr7:s3cr3t@localhost/geonode', arg)
                self.assertEqual({}, kwargs)

    def test_init_session_updates_internal_dict(self):
        """
        _init_session() will add newly created sessions to the internal
        `__sessions__` dictionary.
        """
        session = object()
        sc = SessionCache()
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = lambda: session
                self.assertTrue(sc.__sessions__.get("usr8") is None)
                sc._init_session("usr8", "t0ps3cr3t")
                self.assertEqual(session, sc.__sessions__.get("usr8"))


class SessionCacheGetTestCase(unittest.TestCase):
    """Tests the behaviour of alchemy.db_utils.SessionCache.get()."""

    def tearDown(self):
        SessionCache().__sessions__.clear()

    def test_get_with_no_session_for_user(self):
        """
        get() will call _init_session() if this is the first time a session is
        requested for the given database user.
        """
        sc = SessionCache()
        expected_session = object()

        def fake_init_session(user, password):
            """
            When the mock method is called this will set the session for the
            given user to `expected_session`.
            """
            sc.__sessions__[user] = expected_session

        # Prepare mock.
        mock_method = mock.Mock()
        mock_method.side_effect = fake_init_session

        # Save the original _init_session() method.
        original_method = sc._init_session

        # Replace the original mathod with the mock.
        sc._init_session = mock_method

        # We don't have a session in the cache for the user at hand.
        self.assertTrue(sc.__sessions__.get("usr1") is None)

        # The actual method under test is called.
        self.assertEqual(expected_session, sc.get("usr1", ""))

        # The method under test called the mock once and with the parameters
        # we passed.
        self.assertEqual(1, mock_method.call_count)
        (user, passwd), kwargs = mock_method.call_args
        self.assertEqual("usr1", user)
        self.assertEqual("", passwd)

        # Restore the original _init_session() method.
        sc._init_session = original_method
