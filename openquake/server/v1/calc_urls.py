# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

from django.conf.urls import patterns, url

# each url is prefixed with /v1/calc/
urlpatterns = patterns(
    'openquake.server.views',
    url(r'^list$', 'calc'),
    url(r'^(\d+)$', 'calc_info'),
    url(r'^(\d+)/datastore$', 'get_datastore'),
    url(r'^(\d+)/status$', 'calc'),
    url(r'^(\d+)/results$', 'calc_results'),
    url(r'^(\d+)/traceback$', 'get_traceback'),
    url(r'^(\d+)/log/size$', 'get_log_size'),
    url(r'^(\d+)/log/(\d*):(\d*)$', 'get_log_slice'),
    url(r'^(\d+)/remove$', 'calc_remove'),
    url(r'^result/(\d+)$', 'get_result'),
    url(r'^run$', 'run_calc'),

    url(r'^(\d+)/result/list$', 'calc_results'),
    url(r'^\d+/result/(\d+)$', 'get_result'),
)
