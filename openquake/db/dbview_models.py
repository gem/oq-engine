# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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


'''
Model representations of views in the OpenQuake DB.
'''

from django.contrib.gis.db import models

from openquake.db.models import FloatArrayField


class CatalogAllfields(models.Model):
    '''
    Global catalog view, needed for GeoNode integration
    '''
    owner_id = models.IntegerField()
    eventid = models.IntegerField()
    agency = models.TextField()
    identifier = models.TextField()
    depth = models.FloatField()
    depth_error = models.FloatField()
    time = models.DateTimeField()
    time_error = models.FloatField()
    event_class = models.TextField()
    magnitude_id = models.IntegerField()
    surface_id = models.IntegerField()
    last_update = models.DateTimeField()
    point = models.PointField(srid=4326)
    semi_minor = models.FloatField()
    semi_major = models.FloatField()
    strike = models.FloatField()
    ms_val = models.FloatField()
    ms_val_error = models.FloatField()
    mw_val = models.FloatField()
    mw_val_error = models.FloatField()
    ml_val = models.FloatField()
    ml_val_error = models.FloatField()
    mb_val = models.FloatField()
    mb_val_error = models.FloatField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'eqcat\".\"catalog_allfields'
