# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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

from django.urls import re_path
from openquake.server import views

# each url is prefixed with /v1/calc/
urlpatterns = [
    re_path(r'^list$', views.calc_list),
    re_path(r'^(\d+)/status$', views.calc_list),
    re_path(r'^(\d+)$', views.calc),
    re_path(r'^(\d+)/abort$', views.calc_abort),
    re_path(r'^(\d+)/datastore$', views.calc_datastore),
    re_path(r'^(\d+)/extract/([-/_\.\w]+)$', views.extract),
    re_path(r'^(\d+)/results$', views.calc_results),
    re_path(r'^(\d+)/hmap_(\d+)_(\d+)$', views.hmap_png),
    re_path(r'^(\d+)/traceback$', views.calc_traceback),
    re_path(r'^(\d+)/log/size$', views.calc_log_size),
    re_path(r'^(\d+)/log/(\d*):(\d*)$', views.calc_log),
    re_path(r'^(\d+)/remove$', views.calc_remove),
    re_path(r'^result/(\d+)$', views.calc_result),
    re_path(r'^run$', views.calc_run),
    re_path(r'^validate_zip$', views.validate_zip),
    re_path(r'^(\d+)/result/list$', views.calc_results),
]
