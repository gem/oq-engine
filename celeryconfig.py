# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Config for all installed OpenGEM binaries and modules.
Should be installed by setup.py into /etc/opengem 
eventually.
"""

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "myuser"
BROKER_PASSWORD = "mypassword"
BROKER_VHOST = "myvhost"

CELERY_RESULT_BACKEND = "amqp"

CELERY_IMPORTS = ("opengem.tasks", "opengem.risk.tasks", "opengem.hazard.tasks")