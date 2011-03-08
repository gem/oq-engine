# This file is part of OpenQuake.
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

# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Config for all installed OpenGEM binaries and modules.
Should be installed by setup.py into /etc/openquake 
eventually.
"""

import sys

from openquake import flags
from openquake import java
flags.FLAGS.capture_java_debug = True
flags.FLAGS.debug = "warn"
from openquake import logs
logs.init_logs()

sys.path.append('.')

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "celeryuser"
BROKER_PASSWORD = "celery"
BROKER_VHOST = "celeryvhost"

CELERY_RESULT_BACKEND = "amqp"


CELERY_IMPORTS = ("openquake.risk.job", "openquake.hazard.tasks")
