# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

import getpass
import requests
import logging
import django

from time import sleep
from django.conf import settings
from openquake.engine import __version__ as oqversion

if settings.LOCKDOWN:
    django.setup()
    from django.contrib.auth.models import User


def get_user_data(request):
    """
    Returns a dictionary with `name`, `group_members` and `acl_on` keys.
    `name` is the real username if authentication support is enabled and user
    is authenticated, otherwise it is None.
    """
    acl_on = settings.ACL_ON
    group_members = []
    if settings.LOCKDOWN and hasattr(request, 'user'):
        if request.user.is_authenticated():
            name = request.user.username
            groups = request.user.groups.values_list('name', flat=True)
            if groups:
                group_members = list(User.objects.filter(groups__name=groups)
                                     .values_list('username', flat=True))
        if request.user.is_superuser:
            acl_on = False
    else:
        name = (settings.DEFAULT_USER if
                hasattr(settings, 'DEFAULT_USER') else getpass.getuser())

    return {'name': name, 'group_members': group_members, 'acl_on': acl_on}


def oq_server_context_processor(request):
    """
    A custom context processor which allows injection of additional
    context variables.
    """

    context = {}

    context['oq_engine_server_url'] = ('//' +
                                       request.META.get('HTTP_HOST',
                                                        'localhost:8800'))
    # this context var is also evaluated by the STANDALONE_APPS to identify
    # the running environment. Keep it as it is
    context['oq_engine_version'] = oqversion

    return context


def check_webserver_running(url="http://localhost:8800", max_retries=30):
    """
    Returns True if a given URL is responding within a given timeout.
    """

    retry = 0
    response = ''
    success = False

    while response != requests.codes.ok and retry < max_retries:
        try:
            response = requests.head(url, allow_redirects=True).status_code
            success = True
        except:
            sleep(1)

        retry += 1

    if not success:
        logging.warn('Unable to connect to %s within %s retries'
                     % (url, max_retries))
    return success
