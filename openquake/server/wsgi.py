import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openquake.server.settings")

from openquake.server.db import models
models.getcursor('job_init').execute(
    # cleanup of the flag oq_job.is_running
    'UPDATE uiapi.oq_job SET is_running=false WHERE is_running')

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
application = get_wsgi_application()
