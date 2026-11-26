# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from types import SimpleNamespace
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

from openquake.baselib import config
from openquake.commonlib import auth
from openquake.commands import webui
from openquake.server import apps, internal_api, postinstall


@pytest.mark.parametrize('environ, authkey, expected', [
    ({'OQ_API_KEY': 'env-key'}, 'cfg-key', 'env-key'),
    ({}, 'cfg-key', 'cfg-key'),
    ({}, '', ''),  # no key: the internal API is closed
    # the old public default is treated as no key
    ({}, 'changeme', ''),
    ({'OQ_API_KEY': 'changeme'}, '', '')])
def test_get_api_key(environ, authkey, expected):
    with mock.patch.dict(config.webapi, authkey=authkey):
        assert auth.get_api_key(environ) == expected


def test_no_key_closes_the_internal_api():
    with mock.patch.object(internal_api, 'API_KEY', ''):
        for header in ['', 'anything']:
            request = SimpleNamespace(headers={'X-API-Key': header})
            assert not internal_api.has_api_key(request)
    with mock.patch.object(internal_api, 'API_KEY', 'a-key'):
        request = SimpleNamespace(headers={'X-API-Key': 'a-key'})
        assert internal_api.has_api_key(request)


@pytest.mark.parametrize('server, key, refused', [
    (True, '', True),  # the processes of the users need the key
    (True, 'a-key', False),
    (False, '', False)])  # nobody else uses the internal API
def test_server_installation_requires_key(server, key, refused):
    with mock.patch.object(auth, 'is_server_installation',
                           return_value=server), \
            mock.patch.object(auth, 'API_KEY', key):
        error = auth.api_key_error()
        if refused:
            assert 'authkey' in error
            # the second line of defense, when Django starts
            with pytest.raises(ImproperlyConfigured, match='authkey'):
                apps.check_api_key()
        else:
            assert error is None
            apps.check_api_key()


def test_missing_key_stops_the_webui_before_it_starts():
    # both the ExecStartPre of the gunicorn units and `oq webui start` exit
    # before touching the database or starting the server
    with mock.patch.object(auth, 'is_server_installation',
                           return_value=True), \
            mock.patch.object(auth, 'API_KEY', ''), \
            mock.patch.object(postinstall.actions, 'check_outdated') as chk, \
            mock.patch.object(webui, 'runserver') as runserver:
        with pytest.raises(SystemExit, match='authkey'):
            postinstall.main()
        with pytest.raises(SystemExit, match='authkey'):
            webui.main('start', skip_browser=True)
    chk.assert_not_called()
    runserver.assert_not_called()
