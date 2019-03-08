# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from openquake.server import views

urlpatterns = [
    url(r'^v1/engine_version$', views.get_engine_version),
    url(r'^v1/engine_latest_version$', views.get_engine_latest_version),
    url(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
    url(r'^v1/valid/', views.validate_nrml),
    url(r'^v1/available_gsims$', views.get_available_gsims),
    url(r'^v1/on_same_fs$', views.on_same_fs, name="on_same_fs"),
]

# it is useful to disable the default redirect if the usage is via API only
# 'collectstatic' and related configurationis on the reverse proxy
# are also not required anymore for an API-only usage
if settings.WEBUI:
    urlpatterns += [
        url(r'^$', RedirectView.as_view(url='/engine/', permanent=True)),
        url(r'^engine/?$', views.web_engine, name="index"),
        url(r'^engine/(\d+)/outputs$',
            views.web_engine_get_outputs, name="outputs"),
        url(r'^engine/license$', views.license,
            name="license"),
    ]
    for app in settings.STANDALONE_APPS:
        app_name = app.split('_')[1]
        urlpatterns.append(url(r'^%s/' % app_name, include('%s.urls' % app,
                               namespace='%s' % app_name)))

if settings.LOCKDOWN:
    from django.contrib import admin
    from django.contrib.auth.views import login, logout

    admin.autodiscover()
    urlpatterns += [
        url(r'^admin/', admin.site.urls),
        url(r'^accounts/login/$', login,
            {'template_name': 'account/login.html'}, name="login"),
        url(r'^accounts/logout/$', logout,
            {'template_name': 'account/logout.html'}, name="logout"),
        url(r'^accounts/ajax_login/$', views.ajax_login),
        url(r'^accounts/ajax_logout/$', views.ajax_logout),
    ]

# To enable gunicorn debug without Nginx (to serve static files)
# uncomment the following lines
# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# urlpatterns += staticfiles_urlpatterns()
