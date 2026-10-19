# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        """Do nothing when setproctitle is unavailable."""

from openquake.commonlib import dbapi
from openquake.server.db import actions

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openquake.server.settings")
setproctitle('oq-webui')
# Initialize the database before the application starts serving requests
actions.upgrade_db(dbapi.db)

from django.core.wsgi import get_wsgi_application  # noqa: E402

# This application object is used by gunicorn and by the development server
# (see WSGI_APPLICATION in the settings) as well as any WSGI server configured
# to use this file.
application = get_wsgi_application()
