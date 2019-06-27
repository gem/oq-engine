# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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


def get_user(request):
    """
    Returns the users from `request` if authentication is enabled, otherwise
    returns the default user (from settings, or as reported by the OS).
    """
    if settings.LOCKDOWN and hasattr(request, 'user'):
        if request.user.is_authenticated:
            user = request.user.username
        else:
            # This may happen with crafted requests
            user = ''
    else:
        user = getattr(settings, 'DEFAULT_USER', getpass.getuser())

    return user


def get_valid_users(request):
    """"
    Returns a list of `users` based on groups membership.
    Returns a list made of a single user when it is not member of any group.
    """
    users = [get_user(request)]
    if settings.LOCKDOWN and hasattr(request, 'user'):
        if request.user.is_authenticated:
            groups = request.user.groups.all()
            if groups:
                users = list(User.objects.filter(groups__in=groups)
                             .values_list('username', flat=True))
        else:
            # This may happen with crafted requests
            users = []
    return users


def get_acl_on(request):
    """
    Returns `True` if ACL should be honorated, returns otherwise `False`.
    """
    acl_on = settings.ACL_ON
    if settings.LOCKDOWN and hasattr(request, 'user'):
        # ACL is always disabled for superusers
        if request.user.is_superuser:
            acl_on = False
    return acl_on


def user_has_permission(request, owner):
    """
    Returns `True` if user coming from the request has the permission
    to view a resource, returns `false` otherwise.
    """
    return owner in get_valid_users(request) or not get_acl_on(request)


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
    context['server_name'] = settings.SERVER_NAME
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
        logging.warning('Unable to connect to %s within %s retries'
                     % (url, max_retries))
    return success
