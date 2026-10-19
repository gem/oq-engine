"""Authentication values shared by the WebUI views and the internal API."""

import os

from openquake.baselib import config


API_KEY = os.environ.get('OQ_API_KEY') or config.webapi.authkey
