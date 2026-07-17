# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2019, GEM Foundation.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public
#    License along with this program. If not, see
#    <https://www.gnu.org/licenses/agpl.html>.

from django.urls import re_path
from openquake.ipt import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

app_name = 'ipt'
urlpatterns = [
    re_path(r'^(?P<tab_id>\d+)?$', views.view, name='home'),
    re_path(r'^upload/(?P<target>[^?]*)', views.upload, name='upload'),
    re_path(r'^valid$', views.validate_nrml, name='validate_nrml'),
    re_path(r'^sendback$', views.sendback_nrml, name='sendback_nrml'),
    re_path(r'^sendback_er_rupture_surface$',
            views.sendback_er_rupture_surface,
            name='sendback_er_rupture_surface'),
    re_path(r'^prepare/scenario$',
            views.scenario_prepare, name='scenario_prepare'),
    re_path(r'^prepare/event-based$',
            views.event_based_prepare, name='event_based_prepare'),
    re_path(r'^prepare/volcano$',
            views.volcano_prepare, name='volcano_prepare'),
    re_path(r'^download$', views.download, name='download'),
    re_path(r'^clean_all$', views.clean_all, name='clean_all'),
    re_path(r'^shp-fields$', views.shapefile_get_fields,
            name='shapefile_get_fields'),
    re_path(r'^ex-csv-check$', views.ex_csv_check, name='expose_csv_check'),
]
