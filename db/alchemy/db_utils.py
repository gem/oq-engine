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
SQLAlchemy utility functions.
"""

import os
import sqlalchemy


class Session(object):
    __session__ = None

    @classmethod
    def get(cls):
        """Return SQLAlchemy session if ready and initialize it otherwise."""
        if cls.__session__:
            return cls.__session__
        else:
            return cls.init_session()

    @classmethod
    def init_session(cls):
        """Initialize SQLAlchemy session."""
        user = os.environ.get("OQ_ENGINE_DB_USER")
        assert user, "No db user set for the OpenQuake engine"

        password = os.environ.get("OQ_ENGINE_DB_PASSWORD")
        assert password, "No db password set for the OpenQuake engine"

        db_name = os.environ.get("OQ_ENGINE_DB_NAME", "geonode")
        assert db_name, "No db name set for the OpenQuake engine"

        db_host = os.environ.get("OQ_ENGINE_DB_HOST", "localhost")
        assert db_host, "No db host set for the OpenQuake engine"

        data = (user, password, db_host, db_name)
        engine = sqlalchemy.create_engine(
            "postgresql+psycopg2://%s:%s@%s/%s" % data)
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        cls.__session__ = Session()
        return cls.__session__
