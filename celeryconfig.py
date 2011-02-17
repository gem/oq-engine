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
