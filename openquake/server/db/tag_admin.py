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

from django.db import connection
from django.contrib import admin
from openquake.server.db.models import JobTag
from openquake.server.db.tag_site import tag_admin_site


@admin.register(JobTag, site=tag_admin_site)
class JobTagAdmin(admin.ModelAdmin):
    list_display = ('job_display', 'tag', 'is_preferred')
    list_filter = ('is_preferred',)
    search_fields = ('tag',)
    autocomplete_fields = ["job"]

    def job_display(self, obj):
        return str(obj.job)
    job_display.short_description = "Job"

    def job_description(self, obj):
        return obj.job_description
    job_description.admin_order_field = "job_id"
    job_description.short_description = "Job Description"

    def get_search_results(self, request, queryset, search_term):
        """
        Extend the default search to include job descriptions from the job table.
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term)

        if search_term:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM job WHERE description LIKE %s",
                    [f"%{search_term}%"],
                )
                job_ids = [row[0] for row in cursor.fetchall()]

            if job_ids:
                queryset |= self.model.objects.filter(job_id__in=job_ids)

        return queryset, use_distinct

    def has_module_permission(self, request):
        user = request.user
        if user.is_active and user.is_authenticated and request.user.is_superuser:
            return True
        if user.is_active and user.is_authenticated and user.level >= 2:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
