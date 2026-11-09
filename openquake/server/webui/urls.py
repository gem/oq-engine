# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
from django.urls import re_path, include
from openquake.server import views

# the v1 routes are included at the root of the server URLs, so that
# the WEBUI_PATHPREFIX (if any) applies to them as well
urlpatterns = []

# the validation and the defaults are served also in TOOLS_ONLY mode
# when the webui is enabled
if settings.WEBUI or settings.APPLICATION_MODE != 'TOOLS_ONLY':
    urlpatterns += [
        re_path(r'^v1/valid/', views.validate_nrml),
        re_path(r'^v1/available_gsims$', views.get_available_gsims),
        re_path(r'^v1/ini_defaults$', views.get_ini_defaults,
                name="ini_defaults"),
    ]

if settings.APPLICATION_MODE != 'TOOLS_ONLY':
    urlpatterns += [
        re_path(r'^v1/engine_version$', views.get_engine_version),
        re_path(r'^v1/authentication/status$',
                views.get_authentication_status),
        re_path(r'^v1/engine_latest_version$',
                views.get_engine_latest_version),
        re_path(r'^v1/calc/', include('openquake.server.webui.calc_urls')),
        re_path(r'^v1/on_same_fs$', views.on_same_fs, name="on_same_fs"),
    ]

if settings.WEBUI:
    if settings.APPLICATION_MODE == 'AELO':
        urlpatterns += [
            re_path(r'^v1/aelo_site_classes$', views.aelo_site_classes,
                    name="aelo_site_classes"),
        ]
    elif settings.APPLICATION_MODE == 'IMPACT':
        urlpatterns += [
            re_path(r'^v1/get_impact_form_defaults$',
                    views.get_impact_form_defaults,
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
