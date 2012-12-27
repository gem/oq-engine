# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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

from openquake.utils import config


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


CELERY_IMPORTS = (
    "openquake.calculators.hazard.classical.core",
    "openquake.calculators.hazard.classical.post_processing",
    "openquake.calculators.hazard.event_based.core_next",
    "openquake.calculators.hazard.event_based.post_processing",
    "openquake.calculators.risk.classical.core",
    "openquake.calculators.risk.classical_bcr.core",
    "tests.utils.tasks")

os.environ["DJANGO_SETTINGS_MODULE"] = "openquake.settings"
