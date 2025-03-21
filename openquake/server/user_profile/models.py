# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from django.db import models
from django.contrib.auth.models import User


# NOTE: User exists only when authentication is enabled
User.level = property(lambda self: getattr(self.profile, 'level', 0))
User.testdir = property(lambda self: getattr(self.profile, 'testdir', None))


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    LEVEL_CHOICES = [
        (0, 'View Only'),
        (1, 'Simplified'),
        (2, 'Advanced'),
    ]
    level = models.IntegerField(
        choices=LEVEL_CHOICES,
        default=0,
        help_text="Choose the level for the user"
    )
