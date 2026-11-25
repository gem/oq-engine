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
from openquake.server import apps, internal_api


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
    with mock.patch.object(apps, 'is_server_installation',
                           return_value=server), \
            mock.patch.object(apps.auth, 'API_KEY', key):
        if refused:
            with pytest.raises(ImproperlyConfigured, match='authkey'):
                apps.check_api_key()
        else:
            apps.check_api_key()
