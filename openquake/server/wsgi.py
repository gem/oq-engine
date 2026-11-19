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
import logging
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        """Do nothing when setproctitle is unavailable."""

from openquake.baselib import config, use_server
from openquake.commonlib import dbapi
from openquake.server.db import actions
from openquake.server.db.upgrade_manager import VersioningNotInstalled

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openquake.server.settings")
setproctitle('oq-webui')
assert not use_server(), \
    "The webui cannot call itself [can happen if a devel installation is identified as devel server]"

# Check the database before the application starts serving requests.
# The WebUI does not upgrade the database: every gunicorn worker imports this
# module (unless gunicorn runs with --preload), so with N workers there would
# be N upgrades of the same database at the same time. The database must be
# upgraded with `oq engine --upgrade-db` before starting the WebUI: install.py
# does it before starting the service, otherwise it is an explicit action of
# the administrator (see doc/getting-started/installation-instructions/
# server.md); here the WebUI refuses to start telling what to do.
# NB: `oq webui start` upgrades the database by itself before starting the
# server (a single process).
logging.warning(f'Using {config.found[-1]}')
logging.warning(f'Using {dbapi.db.path}')
try:
    outdated = actions.check_outdated(dbapi.db)
except VersioningNotInstalled:  # the database has not been created yet
    outdated = ('The database has not been created yet. You can create it '
                'by running oq engine --upgrade-db')
if outdated:
    raise RuntimeError(
        f'{dbapi.db.path}: {outdated}\nThe command must be run by the owner '
        'of the database (the user openquake in a server installation) '
        'before starting the WebUI.')

from django.core.wsgi import get_wsgi_application  # noqa: E402

# This application object is used by gunicorn and by the development server
# (see WSGI_APPLICATION in the settings) as well as any WSGI server configured
# to use this file.
application = get_wsgi_application()
