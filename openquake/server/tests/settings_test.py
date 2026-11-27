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

import mimetypes

import pytest
from django.core.exceptions import ImproperlyConfigured

from openquake.server.settings import (
    env_flag, check_x_frame_options, fix_static_content_types)

FLAG = 'OQ_TEST_ENV_FLAG'


@pytest.mark.parametrize('value, expected', [
    ('True', True), ('true', True), ('1', True),
    # with os.environ.get these were non-empty strings, i.e. true
    ('False', False), ('false', False), ('0', False),
    ('', False)])
def test_env_flag(monkeypatch, value, expected):
    monkeypatch.setenv(FLAG, value)
    assert env_flag(FLAG) is expected


def test_env_flag_default(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    assert env_flag(FLAG) is False
    assert env_flag(FLAG, True) is True


def test_env_flag_rejects_invalid_values(monkeypatch):
    monkeypatch.setenv(FLAG, 'maybe')
    with pytest.raises(ValueError):
        env_flag(FLAG)


def test_security_headers(client):
    resp = client.get('/v1/engine_version')
    assert resp['X-Frame-Options'] == 'DENY'
    assert resp['X-Content-Type-Options'] == 'nosniff'
    assert resp['Referrer-Policy'] == 'same-origin'
    assert resp['Cross-Origin-Opener-Policy'] == 'same-origin'


def test_x_frame_options_can_be_changed(client, settings):
    # as in local_settings.py
    settings.X_FRAME_OPTIONS = 'SAMEORIGIN'
    resp = client.get('/v1/engine_version')
    assert resp['X-Frame-Options'] == 'SAMEORIGIN'


@pytest.mark.parametrize('value', ['DENY', 'SAMEORIGIN', 'sameorigin'])
def test_check_x_frame_options(value):
    assert check_x_frame_options(value) == value


@pytest.mark.parametrize('value', ['ALLOW-FROM https://example.org', '', None])
def test_check_x_frame_options_rejects_invalid_values(value):
    with pytest.raises(ImproperlyConfigured):
        check_x_frame_options(value)


def test_static_content_types():
    # as with a Windows registry mapping .js and .css to text/plain
    mimetypes.add_type('text/plain', '.js')
    mimetypes.add_type('text/plain', '.css')
    try:
        fix_static_content_types()
        assert mimetypes.guess_type('engine.js')[0] == 'text/javascript'
        assert mimetypes.guess_type('engine.css')[0] == 'text/css'
    finally:
        fix_static_content_types()
