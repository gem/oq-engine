# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""
Config for all installed OpenQuake binaries and modules.
Should be installed by setup.py into /etc/openquake
eventually.
"""

import os
import sys
import imp

# just in the case that are you using oq-engine from sources
# with the rest of oq libraries installed into the system (or a
# virtual environment) you must set this environment variable
if os.environ.get("OQ_ENGINE_USE_SRCDIR"):
    sys.modules['openquake'].__dict__["__path__"].insert(
        0, os.path.join(os.path.dirname(__file__), "openquake"))

from openquake.engine.utils import config, get_core_modules
from openquake.engine.calculators import hazard, risk

config.abort_if_no_config_available()

sys.path.insert(0, os.path.dirname(__file__))

amqp = config.get_section("amqp")

BROKER_HOST = amqp.get("host")
BROKER_PORT = int(amqp.get("port"))
BROKER_USER = amqp.get("user")
BROKER_PASSWORD = amqp.get("password")
BROKER_VHOST = amqp.get("vhost")

CELERY_RESULT_BACKEND = "amqp"

# CELERY_ACKS_LATE and CELERYD_PREFETCH_MULTIPLIER settings help evenly
# distribute tasks across the cluster. This configuration is intended
# make worker processes reserve only a single task at any given time.
# (The default settings for prefetching define that each worker process will
# reserve 4 tasks at once. For long running calculations with lots of long,
# heavy tasks, this greedy prefetching is not recommended and can result in
# performance issues with respect to cluster utilization.)
CELERY_ACKS_LATE = True
CELERYD_PREFETCH_MULTIPLIER = 1

HAZARD_MODULES = get_core_modules(hazard)

RISK_MODULES = get_core_modules(risk)

CELERY_IMPORTS = HAZARD_MODULES + RISK_MODULES

try:
    imp.find_module("tasks", [os.path.join(x, "tests/utils")
                              for x in sys.path])
    CELERY_IMPORTS.append("tests.utils.tasks")
except ImportError:
    pass

os.environ["DJANGO_SETTINGS_MODULE"] = "openquake.engine.settings"
