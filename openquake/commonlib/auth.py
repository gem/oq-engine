"""Authentication values shared by the Django and FastAPI layers."""

import os
import secrets


API_KEY = os.environ.get('OQ_API_KEY') or secrets.token_urlsafe(32)
