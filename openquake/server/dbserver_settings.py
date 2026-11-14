# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
"""
Django settings of the DbServer, the service started by `oq dbserver start`.
They are the settings of the WebUI (including local_settings.py), except
that only the v0 routes are served and there are no sessions nor logins,
since the requests are authenticated with the API key.
"""
from openquake.baselib.workerpool import setproctitle
from openquake.server.settings import *  # noqa: F401,F403

setproctitle('oq-dbserver')
ROOT_URLCONF = 'openquake.server.dbserver_urls'
# use the default WSGI application, not the one of the WebUI in wsgi.py,
# which would wait for the DbServer itself
WSGI_APPLICATION = None
MIDDLEWARE = ()
# with authentication enabled the admin application is installed and it
# requires the session, auth and messages middleware; the DbServer does
# not serve the admin pages, so those checks can be silenced
SILENCED_SYSTEM_CHECKS = ['admin.E408', 'admin.E409', 'admin.E410']
