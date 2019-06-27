# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2019 GEM Foundation
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
Config for all installed OpenQuake binaries and modules.
Should be installed by setup.py into /etc/openquake
eventually.
"""

import os
import sys
try:
    import celery
except ImportError:
    pass
else:
    # just in the case that are you using oq-engine from sources
    # with the rest of oq libraries installed into the system (or a
    # virtual environment) you must set this environment variable
    if os.environ.get("OQ_ENGINE_USE_SRCDIR"):
        sys.modules['openquake'].__dict__["__path__"].insert(
            0, os.path.join(os.path.dirname(__file__), "openquake"))

    from openquake.baselib import config

    task_serializer = 'pickle'
    result_serializer = 'pickle'
    accept_content = ['pickle']

    # RabbitMQ broker (default)
    broker_url = 'amqp://%(user)s:%(password)s@%(host)s:%(port)s/%(vhost)s' % \
                 config.amqp

    # broker_pool_limit enables a connections pool so Celery can reuse
    # a single connection to RabbitMQ. Value 10 is the default from
    # Celery 2.5 where this feature is enabled by default.
    # Actually disabled because it's not stable in production.
    # See https://bugs.launchpad.net/oq-engine/+bug/1250402
    broker_pool_limit = None

    # AMQP result backend (default)
    result_backend = 'rpc://'
    result_persistent = False

    # task_acks_late and worker_prefetch_multiplier settings help evenly
    # distribute tasks across the cluster. This configuration is intended
    # make worker processes reserve only a single task at any given time.
    # The default settings for prefetching define that each worker process will
    # reserve 4 tasks at once. For long running calculations with lots of long,
    # heavy tasks, this greedy prefetching is not recommended and can result in
    # performance issues with respect to cluster utilization.
    # result_cache_max disable the cache on the results: this means
    # that map_reduce will not leak memory by keeping the intermediate results
    task_acks_late = True
    worker_prefetch_multiplier = 1
    result_cache_max = 1
    task_ignore_result = True

    imports = ["openquake.baselib.parallel"]
