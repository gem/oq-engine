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

from db.alchemy.db_utils import (
    SessionCache, get_eqcat_writer_session, get_pshai_writer_session,
    get_uiapi_writer_session, get_eqcat_etl_session, get_pshai_etl_session)


class SessionCacheInitSessionTestCase(unittest.TestCase):
    """Tests the behaviour of alchemy.db_utils.SessionCache.init_session()."""

    def setUp(self):
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
        self.assertRaises(AssertionError, SessionCache()._init_session,
                          "oq_uiapi_writer", "")

    def test_init_session_with_oq_engine_db_name(self):
        """
        _init_session() observes the `OQ_ENGINE_DB_NAME` environment variable.
        """
        os.environ["OQ_ENGINE_DB_NAME"] = "abc123"
        self._perform_test(
            "usr1", "", ("postgresql+psycopg2://usr1:@localhost/abc123",))
        del os.environ["OQ_ENGINE_DB_NAME"]

    def test_init_session_without_oq_engine_db_name(self):
        """
        In the absence of the `OQ_ENGINE_DB_NAME` environment variable
        the session will be established for the "geonode" database.
        """
        self._perform_test(
            "usr2", "", ("postgresql+psycopg2://usr2:@localhost/geonode",))

    def test_init_session_with_oq_engine_db_host(self):
        """
        _init_session() observes the `OQ_ENGINE_DB_HOST` environment variable.
        """
        os.environ["OQ_ENGINE_DB_HOST"] = "bcd234"
        self._perform_test(
            "usr3", "", ("postgresql+psycopg2://usr3:@bcd234/geonode",))
        del os.environ["OQ_ENGINE_DB_HOST"]

    def test_init_session_without_oq_engine_db_host(self):
        """
        In the absence of the `OQ_ENGINE_DB_HOST` environment variable
        the session will be established for the `localhost`.
        """
        self._perform_test(
            "usr4", "", ("postgresql+psycopg2://usr4:@localhost/geonode",))

    def test_init_session_with_none_password(self):
        """
        _init_session() will use an empty string for `None` passwords.
        """
        self._perform_test(
            "usr5", None, ("postgresql+psycopg2://usr5:@localhost/geonode",))

    def test_init_session_with_empty_password(self):
        """
        _init_session() will use an empty password properly.
        """
        self._perform_test(
            "usr6", "", ("postgresql+psycopg2://usr6:@localhost/geonode",))

    def test_init_session_with_non_empty_password(self):
        """
        _init_session() will use a non-empty password correctly.
        """
        self._perform_test(
            "usr7", "s3cr3t",
            ("postgresql+psycopg2://usr7:s3cr3t@localhost/geonode",))

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

    def _perform_test(self, user, password, expected_args, expected_kwargs={}):
        """
        Mocks the alchemy functions and calls the method under test.

        The method under test is `SessionCache._init_session()`.

        :param str user: the user parameter for the method under test
        :param str password: the password parameter for the method under test
        :param tuple expected_args: a string tuple with parameters that we
            expect will be passed to `sqlalchemy.create_engine()`
        :param dict expected_kwargs: a dictionary with keyword parameters that
            we expect will be passed to `sqlalchemy.create_engine()`
        """
        with mock.patch('sqlalchemy.create_engine') as ce_mock:
            with mock.patch('sqlalchemy.orm.sessionmaker') as sm_mock:
                sm_mock.return_value = object
                SessionCache()._init_session(user, password)
                self.assertEqual(1, ce_mock.call_count)
                args, kwargs = ce_mock.call_args
                self.assertEqual(expected_args, args)
                self.assertEqual(expected_kwargs, kwargs)


class SessionCacheGetTestCase(unittest.TestCase):
    """Tests the behaviour of alchemy.db_utils.SessionCache.get()."""

    def setUp(self):
        # Save the original _init_session() method.
        self.original_method = SessionCache()._init_session
        SessionCache().__sessions__.clear()

    def tearDown(self):
        # Restore the original _init_session() method.
        SessionCache()._init_session = self.original_method

    def test_get_with_no_session_for_user(self):
        """
        get() will call _init_session() if this is the first time a session
        is requested for the given database user.
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

    def test_get_with_cached_session(self):
        """
        get() will not call _init_session() if the session for the
        given database user is in the cache already.
        """
        sc = SessionCache()
        expected_session = object()
        sc.__sessions__["usr2"] = expected_session

        # Prepare mock.
        mock_method = mock.Mock()

        # Replace the original mathod with the mock.
        sc._init_session = mock_method

        # We do have a session in the cache for the user at hand.
        self.assertTrue(sc.__sessions__.get("usr2") is expected_session)

        # The actual method under test is called.
        self.assertTrue(sc.get("usr2", "") is expected_session)

        # The method under test did *not* call the mock.
        self.assertEqual(0, mock_method.call_count)

    def test_get_with_no_session_and_init_failure(self):
        """
        get() will call _init_session() if the session for the given
        database user is not in the cache already.
        When _init_session() fails to add a session to the cache an
        `AssertionError` is raised.
        """
        sc = SessionCache()

        # Prepare mock.
        mock_method = mock.Mock()

        # Replace the original mathod with the mock.
        sc._init_session = mock_method

        # We do not have a session in the cache for the user at hand.
        self.assertTrue(sc.__sessions__.get("usr3") is None)

        # The _init_session() mock will get called but fail to add a session to
        # the cache,
        self.assertRaises(AssertionError, sc.get, "usr3", "")

        # The method under test did call the mock..
        self.assertEqual(1, mock_method.call_count)
        (user, passwd), kwargs = mock_method.call_args
        self.assertEqual("usr3", user)
        self.assertEqual("", passwd)
        # ..but no session was added to the cache.
        self.assertTrue(sc.__sessions__.get("usr3") is None)


class GetSessionTestCase(unittest.TestCase):
    """
    Tests the various alchemy.db_utils.get_xxxxx_xxxx_session() functions.
    """

    test_data = (
        ("OQ_DB_EQCAT_WRITER", "OQ_DB_EQCAT_WRITER_PWD",
         get_eqcat_writer_session),
        ("OQ_DB_PSHAI_WRITER", "OQ_DB_PSHAI_WRITER_PWD",
         get_pshai_writer_session),
        ("OQ_DB_UIAPI_WRITER", "OQ_DB_UIAPI_WRITER_PWD",
         get_uiapi_writer_session),
        ("OQ_DB_EQCAT_ETL", "OQ_DB_EQCAT_ETL_PWD",
         get_eqcat_etl_session),
        ("OQ_DB_PSHAI_ETL", "OQ_DB_PSHAI_ETL_PWD",
         get_pshai_etl_session))

    def setUp(self):
        # Save the original get() method.
        self.original_method = SessionCache().get
        # Prepare mock.
        self.expected_session = object()
        self.mock_method = mock.Mock()
        self.mock_method.return_value = self.expected_session
        SessionCache().get = self.mock_method

    def tearDown(self):
        # Restore the original get() method.
        SessionCache().get = self.original_method

    def test_get_session_with_no_env(self):
        """
        An `AssertionError` is raised if the `OQ_DB_<ns>_<access>` environment
        variable is not set.
        """
        for env_user, _, function in self.test_data:
            if os.environ.get(env_user):
                del os.environ[env_user]
            self.assertRaises(AssertionError, function)

    def test_get_session(self):
        """
        SessionCache.get() is called with the appropriate environment
        variables.
        """
        for env_user, env_passwd, function in self.test_data:
            os.environ[env_user] = "usr1"
            os.environ[env_passwd] = "pwd1"

            session = function()
            self.assertTrue(session is self.expected_session)
            (user, passwd), _ = self.mock_method.call_args
            self.assertEqual("usr1", user)
            self.assertEqual("pwd1", passwd)

    def test_get_session_with_none_passwd(self):
        """
        SessionCache.get() is called with the appropriate environment
        variables.
        """
        for env_user, env_passwd, function in self.test_data:
            os.environ[env_user] = "usr2"
            if os.environ.get(env_passwd):
                del os.environ[env_passwd]

            session = function()
            self.assertTrue(session is self.expected_session)
            (user, passwd), _ = self.mock_method.call_args
            self.assertEqual("usr2", user)
            self.assertTrue(passwd is None)
