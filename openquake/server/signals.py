# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2025 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import logging
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed)

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info(
        f'User "{user.username}" (IP: {get_client_ip(request)})'
        f' logged in through page {request.META.get("HTTP_REFERER")}')


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username")
    msg = (
        f'User "{username}"'
        f' (IP: {get_client_ip(request)}) failed to log in'
        f' through page {request.META.get("HTTP_REFERER")}')

    User = get_user_model()
    if User.objects.filter(username=username).exists():
        msg += ' (incorrect password)'
    else:
        msg += ' (the username does not exist)'
    logger.warning(msg)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    logger.info(
        f'User "{user.username}" (IP: {get_client_ip(request)})'
        f' logged out through page {request.META.get("HTTP_REFERER")}')
