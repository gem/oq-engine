# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
from django.conf import settings
from django.urls import re_path, include, path
from django.views.generic.base import RedirectView

from openquake.server import views
from openquake.server.db.tag_admin import tag_admin_site
from openquake.server.internal_api import ping

urlpatterns = []
# with WEBUI = False the web pages and the default redirect are disabled,
# which is useful if the usage is via API only: 'collectstatic' and the
# related configuration on the reverse proxy are not required anymore
if settings.WEBUI:
    if settings.APPLICATION_MODE == 'TOOLS_ONLY':
        urlpatterns += [
            re_path(r'^$', RedirectView.as_view(
                url='%s/ipt/' % settings.WEBUI_PATHPREFIX,
                permanent=True))]
    else:
        urlpatterns += [
            re_path(r'^$', RedirectView.as_view(
                url='%s/engine/' % settings.WEBUI_PATHPREFIX,
                permanent=True))]
    urlpatterns += [
        re_path(r'^engine/?$', views.web_engine, name="index"),
        re_path(r'^engine/(\d+)/outputs$',
                views.web_engine_get_outputs, name="outputs"),
        re_path(r'^engine/license$', views.license,
                name="license"),
    ]
    if settings.APPLICATION_MODE != 'PUBLIC':
        urlpatterns += [
            path("cookies/", include("cookie_consent.urls")),
        ]
    if settings.APPLICATION_MODE == 'AELO':
        urlpatterns += [
            re_path(r'^engine/(\d+)/outputs_aelo$',
                    views.web_engine_get_outputs_aelo, name="outputs_aelo"),
            re_path(r'^engine/aelo_changelog$',
                    views.aelo_changelog,
                    name="aelo_changelog"),
        ]
    elif settings.APPLICATION_MODE == 'IMPACT':
        urlpatterns += [
            re_path(r'^engine/(\d+)/outputs_impact$',
                    views.web_engine_get_outputs_impact,
                    name="outputs_impact"),
        ]

    for app_full in settings.STANDALONE_APPS:
        app = app_full.split('.')[0]
        if app in settings.STANDALONE_APP_NAME_MAP:
            app_name = settings.STANDALONE_APP_NAME_MAP[app]
        else:
            app_name = app.split('_')[1]
        urlpatterns.append(re_path(r'^%s/' % app_name, include(
            '%s.urls' % app, namespace='%s' % app_name)))

# the public v1 API lives in the webui app
urlpatterns += [path('', include('openquake.server.webui.urls'))]

if settings.APPLICATION_MODE != 'TOOLS_ONLY':
    if settings.LOCKDOWN:
        from django.contrib import admin
        from django.contrib.auth.views import (
            LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
            PasswordResetConfirmView, PasswordResetCompleteView)

        admin.autodiscover()
        admin.site.site_url = '%s/engine/' % settings.WEBUI_PATHPREFIX
        application_mode = settings.APPLICATION_MODE
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        registration_templates_dir = os.path.join(curr_dir, 'templates', 'registration')
        # NOTE: we don't expect to use email notifications when PAM is enabled, so we
        # can avoid forcing the user to actualize the templates
        if 'django_pam.auth.backends.PAMBackend' in settings.AUTHENTICATION_BACKENDS:
            password_reset_email_content_fname = \
                'password_reset_email_content.txt.default.tmpl'
            password_reset_email_subject_fname = \
                'password_reset_email_subject.txt.default.tmpl'
            user_creation_email_content_fname = \
                'user_creation_email_content.txt.default.tmpl'
            user_creation_email_subject_fname = \
                'user_creation_email_subject.txt.default.tmpl'
        else:
            password_reset_email_content_fname = 'password_reset_email_content.txt'
            password_reset_email_subject_fname = 'password_reset_email_subject.txt'
            user_creation_email_content_fname = \
                'user_creation_email_content.txt'
            user_creation_email_subject_fname = \
                'user_creation_email_subject.txt'
        # NOTE: checking here (when starting the webui with authentication enabled)
        # also the existance of actualized files used when creating a new user
        for registration_template_fname in (
                password_reset_email_content_fname,
                password_reset_email_subject_fname,
                user_creation_email_content_fname,
                user_creation_email_subject_fname):
            registration_template_path = os.path.join(
                registration_templates_dir, registration_template_fname)
            assert os.path.isfile(registration_template_path), (
                f'File not found: {registration_template_path}. You can create it'
                ' from one of the available templates.')
        urlpatterns += [
            re_path(r'^admin/', admin.site.urls),
            re_path(r'^tagadmin/', tag_admin_site.urls),
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
                     subject_template_name=os.path.join(
                         'registration', password_reset_email_subject_fname),
                     email_template_name=os.path.join(
                         'registration', password_reset_email_content_fname)),
                 name='reset_password'),
            path('reset_password_sent/',
                 PasswordResetDoneView.as_view(
                     template_name=os.path.join(
                         'registration', 'password_reset_sent.html'),
                     extra_context={'application_mode': application_mode}),
                 name='password_reset_done'),
            path('reset/<uidb64>/<token>',
                 PasswordResetConfirmView.as_view(
                     template_name=os.path.join('registration',
                                                'password_reset_form.html'),
                     extra_context={'application_mode': application_mode}),
                 name='password_reset_confirm'),
            path('reset_password_complete/',
                 PasswordResetCompleteView.as_view(
                     template_name=os.path.join('registration',
                                                'password_reset_done.html'),
                     extra_context={'application_mode': application_mode}),
                 name='password_reset_complete'),
        ]

    if settings.WEBUI_PATHPREFIX != "":
        urlpatterns = [path(r'%s/' % settings.WEBUI_PATHPREFIX.strip('/'),
                            include(urlpatterns))]

    # the v1 routes protected by the internal API key are always served
    # at the root, as before; the v0 API is served by the DbServer (see
    # dbserver_urls.py)
    if settings.WEBUI:
        urlpatterns += [
            re_path(r'^v1/calc_info/(\d+)$', views.v1_calc_info),
            re_path(r'^v1/calc_list/count$', views.v1_calc_list_count),
        ]

    # To enable gunicorn debug without Nginx (to serve static files)
    # uncomment the following lines
    # from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    # urlpatterns += staticfiles_urlpatterns()

# the health check used by `oq webui status`, served in all modes
urlpatterns.append(re_path(r'^v1/ping$', ping))
