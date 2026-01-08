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

from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from django.apps import apps
from django.db.models import Q
from openquake.server.db.tag_site import tag_admin_site


def get_models():
    """
    Lazy model getter that only resolves models once Django apps are ready.
    Returns (Job, Tag, JobTag).
    """
    try:
        Job = apps.get_model("db", "Job")
        Tag = apps.get_model("db", "Tag")
        JobTag = apps.get_model("db", "JobTag")
        return Job, Tag, JobTag
    except (LookupError, Exception):
        return None, None, None


Job, Tag, JobTag = get_models()

if Job and JobTag and Tag:

    @admin.register(Job, site=tag_admin_site)
    class JobAdmin(admin.ModelAdmin):
        search_fields = ["description"]
        list_display = ["id", "description"]

        # Not even superusers should be able to alter the Job table through this admin
        # interface, but superusers and level 2 users should have permission to
        # visualize them in the JobTag admin interface

        def has_view_permission(self, request, obj=None):
            user = request.user
            return (
                user.is_active and user.is_authenticated and
                (user.is_superuser or user.level >= 2)
            )

        def has_add_permission(self, request):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

    @admin.register(Tag, site=tag_admin_site)
    class TagAdmin(admin.ModelAdmin):
        list_display = ("name",)
        search_fields = ("name",)
        ordering = ("name",)

    @admin.register(JobTag, site=tag_admin_site)
    class JobTagAdmin(admin.ModelAdmin):
        list_display = ("job_display", "tag", "is_preferred")
        list_filter = ("is_preferred", "tag__name")
        search_fields = ("tag__name",)
        autocomplete_fields = ("job", "tag")

        def job_display(self, obj):
            return str(obj.job)
        job_display.short_description = "Job"

        def tag_display(self, obj):
            return str(obj.obg)
        tag_display.short_description = "Tag"

        def get_search_results(self, request, queryset, search_term):
            """
            Extend the default search to include both job descriptions and job IDs.
            """
            queryset, use_distinct = super().get_search_results(
                request, queryset, search_term
            )

            if search_term:
                job_filter = Q(description__icontains=search_term)
                if search_term.isdigit():
                    job_filter |= Q(id=int(search_term))

                JobModel = self.model._meta.get_field("job").remote_field.model
                job_ids = list(
                    JobModel.objects
                    .filter(job_filter)
                    .values_list("id", flat=True)
                )

                if job_ids:
                    queryset |= self.model.objects.filter(job_id__in=job_ids)
                    use_distinct = True

            return queryset, use_distinct

        def has_module_permission(self, request):
            user = request.user
            return (
                user.is_active and user.is_authenticated and
                (user.is_superuser or user.level >= 2)
            )

        def has_view_permission(self, request, obj=None):
            return self.has_module_permission(request)

        def has_add_permission(self, request):
            return self.has_module_permission(request)

        def has_change_permission(self, request, obj=None):
            return self.has_module_permission(request)

        def has_delete_permission(self, request, obj=None):
            return self.has_module_permission(request)

        def save_model(self, request, obj, form, change):
            """
            Ensure that uniqueness constraints are respected and show friendly messages
            """
            try:
                with transaction.atomic():
                    # If marking as preferred, unset any other
                    # preferred job for this tag
                    if obj.is_preferred:
                        JobTag.objects.filter(
                            tag=obj.tag,
                            is_preferred=True
                        ).exclude(pk=obj.pk).update(is_preferred=False)
                    super().save_model(request, obj, form, change)
            except IntegrityError as exc:
                self.message_user(
                    request,
                    f"Cannot save JobTag: {exc}",
                    level=messages.ERROR
                )

        def delete_model(self, request, obj):
            try:
                with transaction.atomic():
                    super().delete_model(request, obj)
            except IntegrityError as exc:
                self.message_user(
                    request,
                    f"Cannot delete JobTag: {exc}",
                    level=messages.ERROR
                )
