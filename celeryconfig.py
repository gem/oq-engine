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
Config for all installed OpenQuake binaries and modules.
Should be installed by setup.py into /etc/openquake
eventually.
"""

import os
import sys

from openquake.utils import config


sys.path.append('.')

amqp = config.get_section("amqp")

BROKER_HOST = amqp.get("host")
BROKER_PORT = int(amqp.get("port"))
BROKER_USER = amqp.get("user")
BROKER_PASSWORD = amqp.get("password")
BROKER_VHOST = amqp.get("vhost")

CELERY_RESULT_BACKEND = "amqp"


CELERY_IMPORTS = (
    "openquake.risk.job", "openquake.hazard.tasks", "tests.utils.tasks")

os.environ["DJANGO_SETTINGS_MODULE"] = "openquake.settings"
