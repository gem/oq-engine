# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from re import compile

try:
    reverse_login = reverse('login')
    white_list_paths = (reverse_login,)
except:  # caused by nosetests3 openquake/server/ --with-doctest (??)
    reverse_login = None
    white_list_paths = ()


class LoginRequiredMiddleware(object):

    white_list = map(
        compile,
        white_list_paths +
        getattr(
            settings,
            "AUTH_EXEMPT_URLS",
            ()))
    redirect_to = reverse_login

    def process_request(self, request):
        if not request.user.is_authenticated():
            if not any(path.match(request.path) for path in self.white_list):
                return HttpResponseRedirect(
                    '{login_path}?next={request_path}'.format(
                        login_path=self.redirect_to,
                        request_path=request.path))
