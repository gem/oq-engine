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

from django.contrib import admin
from django.apps import apps
from openquake.server.db.tag_site import tag_admin_site


def get_models():
    """
    Lazy model getter that only resolves models once Django apps are ready.
    Returns (Job, JobTag).
    """
    try:
        Job = apps.get_model("db", "Job")
        JobTag = apps.get_model("db", "JobTag")
        return Job, JobTag
    except (LookupError, Exception):
        return None, None


Job, JobTag = get_models()


if Job and JobTag:

    @admin.register(Job, site=tag_admin_site)
    class JobAdmin(admin.ModelAdmin):
        search_fields = ["description"]
        list_display = ["id", "description"]

        # Not even superusers should be able to alter the Job table through this admin
        # interface, but superusers and level 2 users should have permission to
        # visualize them in the JobTag admin interface

        def has_view_permission(self, request, obj=None):
            user = request.user
            if user.is_active and user.is_authenticated and (
                    user.is_superuser or user.level >= 2):
                return True
            return False

        def has_add_permission(self, request):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

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
            Extend the default search to include both job descriptions and job IDs.
            """
            queryset, use_distinct = super().get_search_results(
                request, queryset, search_term)

            if search_term:
                from django.db.models import Q

                # If the term is numeric, try matching job ID directly
                job_filter = Q(description__icontains=search_term)
                if search_term.isdigit():
                    job_filter |= Q(id=int(search_term))

                # Find matching Job IDs
                Job = self.model._meta.get_field("job").remote_field.model
                job_ids = list(Job.objects.filter(job_filter).values_list(
                    "id", flat=True))

                if job_ids:
                    queryset |= self.model.objects.filter(job_id__in=job_ids)

            return queryset, use_distinct

        def has_module_permission(self, request):
            user = request.user
            user = request.user
            if user.is_active and user.is_authenticated and (
                    user.is_superuser or user.level >= 2):
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
