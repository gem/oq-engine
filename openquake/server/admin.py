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
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from openquake.server.announcements.models import Announcement
from openquake.server.user_profile.models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'


# NOTE: this customization adds the UserProfileInline and moves the email to a more
#       visible section, as a way to remind to the creator of the user that the email
#       is an important field, being used for email notifications. In order
#       to avoid tricky issues related to the modification of the standard
#       django User model, the email field still remains optional. However,
#       email notifications will be disabled in case the email is not
#       specified.

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email')}
         ),
    )

    def save_model(self, request, obj, form, change):
        """
        When saving a new user avoid duplicating profile creation.
        """
        if not change:  # New user creation
            super().save_model(request, obj, form, change)
            if not hasattr(obj, 'profile'):  # Ensure profile doesn't already exist
                UserProfile.objects.create(user=obj)
        else:
            super().save_model(request, obj, form, change)


try:
    admin.site.unregister(User)
except NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)

admin.site.register(Announcement)
