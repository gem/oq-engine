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
Utility functions related to keeping job progress information and statistics.
"""


import redis
from openquake.utils import config


def _redis():
    host = config.get("kvs", "host")
    port = config.get("kvs", "port")
    port = int(port) if port else 6379
    stats_db = config.get("kvs", "stats_db")
    stats_db = int(stats_db) if stats_db else 15
    args = {"host": host, "port": port, "db": stats_db}
    return redis.Redis(**args)


def progress_indicator(f):
    """Count successful/failed inviocations of the wrapped function."""
    template = "oqs:i:%%s:%s" % f.__name__
    def wrapper(*args, **kwargs):
        # The first argument is always the job_id
        key = template % args[0]
        with _redis() as conn:
            try:
                f(*args, **args)
            except:
                # Count failure
                conn.incr(key + ":f")
                raise
            else:
                # Count success
                conn.incr(key + ":s")

    return wrapper
