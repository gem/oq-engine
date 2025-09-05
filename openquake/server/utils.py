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
import getpass
import requests
import logging

from time import sleep
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model
from openquake.engine import __version__ as oqversion
from openquake.calculators.base import get_aelo_version


def is_superuser(request):
    """
    Without authentication (settings.LOCKDOW is false) every user is considered
    a superuser, otherwise look at the attribute `request.user.is_superuser`.
    """
    if not settings.LOCKDOWN:
        return True
    return request.user.is_superuser if hasattr(request, 'user') else False


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
    if settings.LOCKDOWN:
        User = get_user_model()
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
    if is_superuser(request):
        # ACL is always disabled for superusers
        acl_on = False

    return acl_on


def user_has_permission(request, owner, job_status):
    """
    Returns `True` if user coming from the request has the permission
    to view a job-related resource, returns `False` otherwise.
    """
    if job_status == 'shared':
        if settings.LOCKDOWN and hasattr(request, 'user'):
            return request.user.is_authenticated
        return True
    else:
        return owner in get_valid_users(request) or not get_acl_on(request)


def oq_server_context_processor(request):
    """
    A custom context processor which allows injection of additional
    context variables.
    """

    # NOTE: defining env variable at runtime, instead of defining it when the
    # engine imports variable from the server module
    os.environ['OQ_APPLICATION_MODE'] = settings.APPLICATION_MODE

    context = {}

    try:
        announcement_model = apps.get_model(app_label='announcements',
                                            model_name='Announcement')
    except LookupError:
        announcements = None
    else:
        announcements = announcement_model.objects.filter(show=True)

    webui_host = request.get_host()
    context['oq_engine_server_url'] = (
        '//' + (webui_host if webui_host else request.META.get(
            'HTTP_HOST', 'localhost:8800')) + settings.WEBUI_PATHPREFIX)
    # this context var is also evaluated by the STANDALONE_APPS to identify
    # the running environment. Keep it as it is
    context['oq_engine_version'] = oqversion
    context['disable_version_warning'] = settings.DISABLE_VERSION_WARNING
    context['server_name'] = settings.SERVER_NAME
    context['external_tools'] = settings.EXTERNAL_TOOLS
    context['application_mode'] = settings.APPLICATION_MODE
    context['announcements'] = announcements
    context['help_url'] = settings.HELP_URL
    if settings.GOOGLE_ANALYTICS_TOKEN is not None:
        context['google_analytics_token'] = settings.GOOGLE_ANALYTICS_TOKEN
    if settings.APPLICATION_MODE == 'AELO':
        context['aelo_version'] = get_aelo_version()

    # setting user_level
    if settings.LOCKDOWN:
        try:
            context['user_level'] = request.user.level
        except AttributeError:  # e.g. AnonymousUser (not authenticated)
            context['user_level'] = 0
    else:
        # NOTE: when authentication is not required, the user interface
        # can assume the user to have the maximum level
        # NOTE: this needs to be the maximum existing user level
        context['user_level'] = 2

    context['lockdown'] = settings.LOCKDOWN

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
        except Exception:
            sleep(1)

        retry += 1

    if not success:
        logging.warning('Unable to connect to %s within %s retries'
                        % (url, max_retries))
    return success
