# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
from django.urls import re_path, include, path
from django.views.generic.base import RedirectView

from openquake.server import views

urlpatterns = [
    re_path(r'^v1/engine_version$', views.get_engine_version),
    re_path(r'^v1/engine_latest_version$', views.get_engine_latest_version),
    re_path(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
    re_path(r'^v1/valid/', views.validate_nrml),
    re_path(r'^v1/available_gsims$', views.get_available_gsims),
    re_path(r'^v1/on_same_fs$', views.on_same_fs, name="on_same_fs"),
    re_path(r'^v1/ini_defaults$', views.get_ini_defaults, name="ini_defaults"),
    re_path(
        r"^announcements/",
        include("pinax.announcements.urls", namespace="pinax_announcements")),
]

# it is useful to disable the default redirect if the usage is via API only
# 'collectstatic' and related configurationis on the reverse proxy
# are also not required anymore for an API-only usage
if settings.WEBUI:
    urlpatterns += [
        re_path(r'^$', RedirectView.as_view(
            url='%s/engine/' % settings.WEBUI_PATHPREFIX,
            permanent=True)),
        re_path(r'^engine/?$', views.web_engine, name="index"),
        re_path(r'^engine/(\d+)/outputs$',
                views.web_engine_get_outputs, name="outputs"),
        re_path(r'^engine/(\d+)/outputs_aelo$',
                views.web_engine_get_outputs_aelo, name="outputs_aelo"),
        re_path(r'^engine/license$', views.license,
                name="license"),
    ]
    for app in settings.STANDALONE_APPS:
        app_name = app.split('_')[1]
        urlpatterns.append(re_path(r'^%s/' % app_name, include(
            '%s.urls' % app, namespace='%s' % app_name)))

if settings.LOCKDOWN:
    from django.contrib import admin
    from django.contrib.auth.views import (
        LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
        PasswordResetConfirmView, PasswordResetCompleteView)

    admin.autodiscover()
    admin.site.site_url = '%s/engine/' % settings.WEBUI_PATHPREFIX
    application_mode = settings.APPLICATION_MODE.upper()
    if application_mode == 'AELO':
        email_template_name = (
            'registration/password_reset_email_aelo.txt')
        subject_template_name = (
            'registration/password_reset_subject_aelo.txt')
    else:
        email_template_name = (
            'registration/password_reset_email.txt')
        subject_template_name = (
            'registration/password_reset_subject.txt')
    urlpatterns += [
        re_path(r'^admin/', admin.site.urls),
        re_path(r'accounts/login/$',
                LoginView.as_view(
                    template_name='account/login.html',
                    extra_context={'application_mode': application_mode},
                ),
                name="login"),
        re_path(r'^accounts/logout/$', LogoutView.as_view(
            template_name='account/logout.html'), name="logout"),
        re_path(r'^accounts/ajax_login/$', views.ajax_login),
        re_path(r'^accounts/ajax_logout/$', views.ajax_logout),
        path('reset_password/',
             PasswordResetView.as_view(
                 template_name='registration/reset_password.html',
                 extra_context={'application_mode': application_mode},
                 subject_template_name=subject_template_name,
                 email_template_name=email_template_name),
             name='reset_password'),
        path('reset_password_sent/',
             PasswordResetDoneView.as_view(
                 template_name='registration/password_reset_sent.html',
                 extra_context={'application_mode': application_mode}),
             name='password_reset_done'),
        path('reset/<uidb64>/<token>',
             PasswordResetConfirmView.as_view(
                 template_name='registration/password_reset_form.html',
                 extra_context={'application_mode': application_mode}),
             name='password_reset_confirm'),
        path('reset_password_complete/',
             PasswordResetCompleteView.as_view(
                 template_name='registration/password_reset_done.html',
                 extra_context={'application_mode': application_mode}),
             name='password_reset_complete'),
    ]

if settings.WEBUI_PATHPREFIX != "":
    urlpatterns = [path(r'%s/' % settings.WEBUI_PATHPREFIX.strip('/'),
                        include(urlpatterns))]
else:
    urlpatterns = urlpatterns

# To enable gunicorn debug without Nginx (to serve static files)
# uncomment the following lines
# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# urlpatterns += staticfiles_urlpatterns()
