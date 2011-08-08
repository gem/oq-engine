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


"""SQLAlchemy utility functions."""


import os
import sqlalchemy
import sqlalchemy.orm

from openquake.utils import general


@general.singleton
class SessionCache(object):
    """Share alchemy sessions per database user."""

    __sessions__ = dict()

    def get(self, user, password=None):
        """Return SQLAlchemy session if ready or initialize it otherwise."""
        session = self.__sessions__.get(user, None)

        if not session:
            self._init_session(user, password)
            session = self.__sessions__.get(user, None)
            assert session, "Internal error: db session not initialized"

        return session

    def _init_session(self, user, password):
        """Initialize SQLAlchemy session.

        :param str user: the database user
        :param str password: the database user's password, may be `None`.
        """
        assert user, "Empty database user name"
        assert user not in self.__sessions__, \
            "Internal error: repeated initialization for user '%s'" % user

        db_name = os.environ.get("OQ_ENGINE_DB_NAME", "openquake")
        assert db_name, "No db name set for the OpenQuake engine"

        db_host = os.environ.get("OQ_ENGINE_DB_HOST", "localhost")
        assert db_host, "No db host set for the OpenQuake engine"

        password = "" if password is None else password

        data = (user, password, db_host, db_name)
        engine = sqlalchemy.create_engine(
            "postgresql+psycopg2://%s:%s@%s/%s" % data)
        session_class = sqlalchemy.orm.sessionmaker(bind=engine)
        self.__sessions__[user] = session_class()


def get_db_session(schema, role=None):
    """Return the session for the db 'schema' and 'role' in question.

    :param str schema: the database schema e.g. "hzrdi"
    :param str role: the role desired e.g. "writer"
    :return: a SQLAlchemy session object
    """
    if role is None:
        role_suffix = ''
    else:
        role_suffix = '_%s' % role
    env_var = "OQ_DB_%s%s" % (schema, role_suffix)
    env_var = env_var.upper()
    pwd_var = env_var + "_PWD"
    user_name = "oq_%s%s" % (schema, role_suffix)
    db_user = os.environ.get(env_var, user_name)
    return SessionCache().get(db_user, os.environ.get(pwd_var, "openquake"))
