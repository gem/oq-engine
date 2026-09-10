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
import sys
import json
import time
import socket
import string
import secrets
import random
import threading

import django
import requests
import uvicorn
from django.contrib.auth import get_user_model
from django.test import Client
from openquake.baselib.general import gettemp
from openquake.commonlib.readinput import loadnpz


class UvicornClient:
    """Small requests-based client for the combined ASGI application."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.django_client = Client()

    def login(self, **credentials):
        """Authenticate through Django and copy the session cookie."""
        logged_in = self.django_client.login(**credentials)
        if logged_in:
            cookie = self.django_client.cookies['sessionid'].value
            self.session.cookies.set('sessionid', cookie)
        return logged_in

    def get(self, path, data=None, **kwargs):
        """Send a GET request to the Uvicorn server."""
        return self.session.get(self.base_url + path, params=data)

    def post(self, path, data=None, **kwargs):
        """Send a POST request to the Uvicorn server."""
        if data is None and kwargs:
            data = kwargs
        data = data or {}
        files = {key: value for key, value in data.items()
                 if hasattr(value, 'read')}
        form = {key: value for key, value in data.items() if key not in files}
        return self.session.post(
            self.base_url + path, data=form, files=files or None)

    def head(self, path, **kwargs):
        """Send a HEAD request to the Uvicorn server."""
        return self.session.head(self.base_url + path)


def start_uvicorn():
    """Start a temporary Uvicorn server for an integration test."""
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    server = uvicorn.Server(uvicorn.Config(
        'openquake.server.asgi:app', host='127.0.0.1', port=port,
        log_level='error'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            return server, thread, UvicornClient(
                'http://127.0.0.1:%d' % port)
        time.sleep(0.1)
    server.should_exit = True
    thread.join(timeout=10)
    raise RuntimeError('Unable to start the Uvicorn test server')


def stop_uvicorn(server, thread):
    """Stop a temporary Uvicorn server."""
    server.should_exit = True
    thread.join(timeout=10)


def random_string(length=10):
    letters_or_digits = string.ascii_letters + string.digits
    return ''.join(random.choices(letters_or_digits, k=length))


def get_or_create_user(level):
    # creating/getting a user of the given level
    # and returning the user object and its plain password
    User = get_user_model()
    username = f'django-test-user-level-{level}'
    email = f'django-test-user-level-{level}@email.test'
    password = ''.join((secrets.choice(
        string.ascii_letters + string.digits + string.punctuation)
        for i in range(8)))
    user, created = User.objects.get_or_create(username=username, email=email)
    if created:
        user.set_password(password)
    user.save()
    user.profile.level = level
    user.profile.save()
    return user, password  # user.password is the hashed password instead


class EngineServerTestCase(django.test.TransactionTestCase):
    datadir = os.path.join(os.path.dirname(__file__), 'data')

    # general utilities

    @classmethod
    def post(cls, path, data=None):
        return cls.c.post('/v1/calc/%s' % path, data)

    @classmethod
    def post_nrml(cls, data):
        return cls.c.post('/v1/valid/', dict(xml_text=data))

    @classmethod
    def get(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data,
                         HTTP_HOST='127.0.0.1')
        if hasattr(resp, 'streaming_content'):
            js = bytes(loadnpz(resp.streaming_content)['json'])
        elif any(kind in resp.headers.get('Content-Type', '')
                 for kind in ('json', 'text/')):
            assert resp.content, (
                'No content from http://localhost:8800/v1/calc/%s' % path)
            js = resp.content.decode('utf8')
        else:
            return json.loads(bytes(loadnpz([resp.content])['json']))
        if not js:
            print('Empty json from ')
            return {}
        try:
            return json.loads(js)
        except Exception:
            print('Invalid JSON, see %s' % gettemp(resp.content, remove=False),
                  file=sys.stderr)
            return {}

    @classmethod
    def get_text(cls, path, **data):
        resp = cls.c.get('/v1/calc/%s' % path, data)
        if resp.status_code == 500:
            raise Exception(resp.content.decode('utf8'))
        if hasattr(resp, 'streaming_content'):
            return b''.join(resp.streaming_content)
        return resp.content

    @classmethod
    def wait(cls):
        # wait until all calculations stop
        for _ in range(300):  # 300 seconds of timeout
            time.sleep(1)
            running_calcs = cls.get('list', is_running='true')
            if not running_calcs:
                if os.environ.get('OQ_APPLICATION_MODE') in ('AELO',
                                                             'IMPACT'):
                    # NOTE: some more time is needed in order to wait for the
                    # callback to finish and produce the email notification
                    time.sleep(1)
                return
