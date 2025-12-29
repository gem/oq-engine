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

from django.db import models


class Job(models.Model):
    # NOTE: mapping only a subset of the fields of the Job table, that are needed to
    # manage tags via the Django admin interface
    id = models.IntegerField(primary_key=True)
    description = models.TextField()

    class Meta:
        managed = False  # the schema is not managed by Django
        db_table = 'job'

    def __str__(self):
        return f"{self.id} – {self.description[:80]}"  # show first 80 chars


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "tag"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class JobTag(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        db_column="job_id",
        related_name="job_tags",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        db_column="tag_id",
        related_name="job_tags",
    )
    is_preferred = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'job_tag'

        # composite primary key at DB level; Django cannot model it directly
        unique_together = ("job", "tag")

        indexes = [
            models.Index(
                fields=["tag_id"],
                name="uq_preferred_per_tag",
                condition=models.Q(is_preferred=True),
            )
        ]

        verbose_name = "Job Tag"
        verbose_name_plural = "Job Tags"

    def __str__(self):
        return (
            f"{self.tag.name} (job_id={self.job_id}, "
            f"{'preferred' if self.is_preferred else 'not preferred'})"
        )
