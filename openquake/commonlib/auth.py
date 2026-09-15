"""Authentication values shared by the Django and FastAPI layers."""

import os

from openquake.baselib import config


API_KEY = os.environ.get('OQ_API_KEY') or config.webapi.authkey
