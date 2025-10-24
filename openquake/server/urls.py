# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

urlpatterns = []
if settings.WEBUI:
    urlpatterns += [
        re_path(r'^$', RedirectView.as_view(
            url='%s/engine/' % settings.WEBUI_PATHPREFIX,
            permanent=True)),
        re_path(r'^engine/?$', views.web_engine, name="index"),
        re_path(r'^engine/(\d+)/outputs$',
                views.web_engine_get_outputs, name="outputs"),
        re_path(r'^engine/license$', views.license,
                name="license"),
        re_path(r'^v1/valid/', views.validate_nrml),
        re_path(r'^v1/available_gsims$', views.get_available_gsims),
        re_path(r'^v1/ini_defaults$', views.get_ini_defaults,
                name="ini_defaults"),
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
            re_path(r'^v1/aelo_site_classes$', views.aelo_site_classes,
                    name="aelo_site_classes"),
        ]
    elif settings.APPLICATION_MODE == 'ARISTOTLE':
        urlpatterns += [
            re_path(r'^engine/(\d+)/outputs_impact$',
                    views.web_engine_get_outputs_impact,
                    name="outputs_impact"),
            re_path(r'^v1/get_impact_form_defaults$', views.get_impact_form_defaults,
                    name="impact_form_defaults"),
            re_path(r'^v1/impact_get_stations_from_usgs$',
                    views.impact_get_stations_from_usgs,
                    name="impact_get_stations_from_usgs"),
            re_path(r'^v1/impact_get_shakemap_versions$',
                    views.impact_get_shakemap_versions,
                    name="impact_get_shakemap_versions"),
            re_path(r'^v1/impact_get_nodal_planes_and_info$',
                    views.impact_get_nodal_planes_and_info,
                    name="impact_get_nodal_planes_and_info"),
        ]

    for app_full in settings.STANDALONE_APPS:
        app = app_full.split('.')[0]
        if app in settings.STANDALONE_APP_NAME_MAP:
            app_name = settings.STANDALONE_APP_NAME_MAP[app]
        else:
            app_name = app.split('_')[1]
        urlpatterns.append(re_path(r'^%s/' % app_name, include(
            '%s.urls' % app, namespace='%s' % app_name)))

if settings.APPLICATION_MODE == 'TOOLS_ONLY':
    if settings.WEBUI:
        urlpatterns += [
            re_path(r'^$', RedirectView.as_view(
                url='%s/ipt/' % settings.WEBUI_PATHPREFIX,
                permanent=True)),
        ]
else:
    urlpatterns += [
        re_path(r'^v1/engine_version$', views.get_engine_version),
        re_path(r'^v1/engine_latest_version$',
                views.get_engine_latest_version),
        re_path(r'^v1/calc/', include('openquake.server.v1.calc_urls')),
        re_path(r'^v1/valid/', views.validate_nrml),
        re_path(r'^v1/available_gsims$', views.get_available_gsims),
        re_path(r'^v1/on_same_fs$', views.on_same_fs, name="on_same_fs"),
        re_path(r'^v1/ini_defaults$', views.get_ini_defaults,
                name="ini_defaults"),
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
        ]
        if settings.APPLICATION_MODE == 'AELO':
            urlpatterns.append(
                re_path(r'^engine/(\d+)/outputs_aelo$',
                        views.web_engine_get_outputs_aelo,
                        name="outputs_aelo"))

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
            normal_user_creation_email_content_fname = \
                'normal_user_creation_email_content.txt.default.tmpl'
            normal_user_creation_email_subject_fname = \
                'normal_user_creation_email_subject.txt.default.tmpl'
        else:
            password_reset_email_content_fname = 'password_reset_email_content.txt'
            password_reset_email_subject_fname = 'password_reset_email_subject.txt'
            normal_user_creation_email_content_fname = \
                'normal_user_creation_email_content.txt'
            normal_user_creation_email_subject_fname = \
                'normal_user_creation_email_subject.txt'
        # NOTE: checking here (when starting the webui with authentication enabled)
        # also the existance of actualized files used when creating a new user
        for registration_template_fname in (
                password_reset_email_content_fname,
                password_reset_email_subject_fname,
                normal_user_creation_email_content_fname,
                normal_user_creation_email_subject_fname):
            registration_template_path = os.path.join(
                registration_templates_dir, registration_template_fname)
            assert os.path.isfile(registration_template_path), (
                f'File not found: {registration_template_path}. You can create it'
                ' from one of the available templates.')
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
    else:
        urlpatterns = urlpatterns

    # To enable gunicorn debug without Nginx (to serve static files)
    # uncomment the following lines
    # from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    # urlpatterns += staticfiles_urlpatterns()
