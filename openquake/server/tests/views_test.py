# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
import string
import secrets
import random
import django
from django.contrib.auth import get_user_model
from openquake.baselib.general import gettemp
from openquake.commonlib.readinput import loadnpz


def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


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


class EngineServerTestCase(django.test.TestCase):
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
        if hasattr(resp, 'content'):
            assert resp.content, (
                'No content from http://localhost:8800/v1/calc/%s' % path)
            js = resp.content.decode('utf8')
        else:
            js = bytes(loadnpz(resp.streaming_content)['json'])
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
        return b''.join(resp.streaming_content)

    @classmethod
    def wait(cls):
        # wait until all calculations stop
        for i in range(300):  # 300 seconds of timeout
            time.sleep(1)
            running_calcs = cls.get('list', is_running='true')
            if not running_calcs:
                if os.environ.get('OQ_APPLICATION_MODE') in ('AELO',
                                                             'ARISTOTLE'):
                    # NOTE: some more time is needed in order to wait for the
                    # callback to finish and produce the email notification
                    time.sleep(1)
                return
