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

from django.conf.urls import url

from openquake.server import views

# each url is prefixed with /v1/calc/
urlpatterns = [
    url(r'^list$', views.calc_list),
    url(r'^(\d+)/status$', views.calc_list),
    url(r'^(\d+)$', views.calc),
    url(r'^(\d+)/abort$', views.calc_abort),
    url(r'^(\d+)/datastore$', views.calc_datastore),
    url(r'^(\d+)/extract/([-/_\.\w]+)$', views.extract),
    url(r'^(\d+)/oqparam$', views.calc_oqparam),
    url(r'^(\d+)/results$', views.calc_results),
    url(r'^(\d+)/traceback$', views.calc_traceback),
    url(r'^(\d+)/log/size$', views.calc_log_size),
    url(r'^(\d+)/log/(\d*):(\d*)$', views.calc_log),
    url(r'^(\d+)/remove$', views.calc_remove),
    url(r'^result/(\d+)$', views.calc_result),
    url(r'^run$', views.calc_run),
    url(r'^(\d+)/result/list$', views.calc_results),
]
