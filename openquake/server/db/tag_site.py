# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025 GEM Foundation
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

from django.contrib.admin import AdminSite


class TagAdminSite(AdminSite):
    site_header = "Tag Management"
    site_title = "Tag Management"
    index_title = "Manage Job Tags"

    def has_permission(self, request):
        user = request.user
        if user.is_active and user.is_authenticated and request.user.is_superuser:
            return True
        if user.is_active and user.is_authenticated and user.level >= 2:
            return True
        return False


tag_admin_site = TagAdminSite(name="tagadmin")
