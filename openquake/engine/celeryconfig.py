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
    if '--with-doctest' in sys.argv:  # horrible hack for nosetests
        pass  # don't set OQ_DISTRIBUTE
    else:
        os.environ["OQ_DISTRIBUTE"] = "celery"

    # just in the case that are you using oq-engine from sources
    # with the rest of oq libraries installed into the system (or a
    # virtual environment) you must set this environment variable
    if os.environ.get("OQ_ENGINE_USE_SRCDIR"):
        sys.modules['openquake'].__dict__["__path__"].insert(
            0, os.path.join(os.path.dirname(__file__), "openquake"))

    from openquake.commonlib import config

    config.abort_if_no_config_available()

    amqp = config.get_section("amqp")

    # RabbitMQ broker (default)
    BROKER_URL = 'amqp://%(user)s:%(password)s@%(host)s:%(port)s/%(vhost)s' % \
                 amqp
    # Redis broker (works only on Trusty)
    # BROKER_URL = 'redis://%(host)s:6379/0' % amqp

    # BROKER_POOL_LIMIT enables a connections pool so Celery can reuse
    # a single connection to RabbitMQ. Value 10 is the default from
    # Celery 2.5 where this feature is enabled by default.
    # Actually disabled because it's not stable in production.
    # See https://bugs.launchpad.net/oq-engine/+bug/1250402
    BROKER_POOL_LIMIT = None

    # AMQP result backend (default)
    CELERY_RESULT_BACKEND = 'rpc://'
    CELERY_RESULT_PERSISTENT = False

    # Redis result backend (works only on Trusty)
    #CELERY_RESULT_BACKEND = 'redis://%(host)s:6379/0' % amqp

    # CELERY_ACKS_LATE and CELERYD_PREFETCH_MULTIPLIER settings help evenly
    # distribute tasks across the cluster. This configuration is intended
    # make worker processes reserve only a single task at any given time.
    # The default settings for prefetching define that each worker process will
    # reserve 4 tasks at once. For long running calculations with lots of long,
    # heavy tasks, this greedy prefetching is not recommended and can result in
    # performance issues with respect to cluster utilization.
    # CELERY_MAX_CACHED_RESULTS disable the cache on the results: this means
    # that map_reduce will not leak memory by keeping the intermediate results
    CELERY_ACKS_LATE = True
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERY_MAX_CACHED_RESULTS = 1

    CELERY_ACCEPT_CONTENT = ['pickle', 'json']

    CELERY_IMPORTS = ["openquake.baselib.parallel"]
