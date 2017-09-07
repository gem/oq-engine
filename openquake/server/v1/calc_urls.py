# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
    url(r'^list$', views.calc),
    url(r'^(\d+)$', views.calc_info),
    url(r'^(\d+)/datastore$', views.get_datastore),
    url(r'^(\d+)/oqparam$', views.get_oqparam),
    url(r'^(\d+)/status$', views.calc),
    url(r'^(\d+)/results$', views.calc_results),
    url(r'^(\d+)/traceback$', views.get_traceback),
    url(r'^(\d+)/log/size$', views.get_log_size),
    url(r'^(\d+)/log/(\d*):(\d*)$', views.get_log_slice),
    url(r'^(\d+)/remove$', views.calc_remove),
    url(r'^result/(\d+)$', views.get_result),
    url(r'^run$', views.run_calc),

    url(r'^(\d+)/result/list$', views.calc_results),
    url(r'^\d+/result/(\d+)$', views.get_result),
]
