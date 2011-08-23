# -*- coding: utf-8 -*-

#   Redis Client from https://github.com/ChristopherMacGown/pynpoint
#   Copyright 2010 Christopher MacGown (http://github.com/ChristopherMacGown)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Modifications by Global Earthquake Model Foundation
#   Copyright 2010 Global Earthquake Model Foundation
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Redis class """

from __future__ import absolute_import
import redis

from openquake.utils import config


class Redis(object):
    """ A Borg-style wrapper for Redis client class. """
    __shared_state = {}

    def __new__(cls, host=config.get("kvs", "host"),
                     port=int(config.get("kvs", "port")),
                     **kwargs):  # pylint: disable=W0613
        self = object.__new__(cls)
        self.__dict__ = cls.__shared_state
        return self

    def __init__(self, host=config.get("kvs", "host"),
                       port=int(config.get("kvs", "port")),
                       **kwargs):
        if not self.__dict__:
            args = {"host": host,
                    "port": port,
                    "db": kwargs.get('db', 0)}

            self.conn = redis.Redis(**args)

    def __getattr__(self, name):
        def call(*args, **kwargs):
            """ Pass through the query to our redis connection """
            cmd = getattr(self.conn, name)
            return cmd(*args, **kwargs)

        if name in self.__dict__:
            return self.__dict__.get(name)

        return call

    def get_multi(self, keys):
        """ Return value of multiple keys identically to the kvs way """
        return dict(zip(keys, self.mget(keys)))
