# -*- coding: utf-8 -*-
"""
This module contains generic functions to access
the underlying kvs systems.
"""

from __future__ import absolute_import
import redis

from openquake import settings


class Redis(object):
    """ A Borg-style wrapper for Redis client class. """
    __shared_state = {}

    def __new__(cls, host=settings.KVS_HOST, 
                     port=settings.KVS_PORT, 
                     **kwargs): #pylint: disable-msg=W0613
        self = object.__new__(cls)
        self.__dict__ = cls.__shared_state
        return self

    def __init__(self, host=settings.KVS_HOST,
                       port=settings.KVS_PORT,
                       **kwargs):
        if not self.__dict__:
            print "Opening a new redis connection"
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
        """ Return value of multiple keys identically to the memcached way """
        return dict(zip(keys, self.mget(keys)))
