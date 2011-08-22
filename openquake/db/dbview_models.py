# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


'''
Model representations of views in the OpenQuake DB.
'''

from django.contrib.gis.db import models

from openquake.db.models import FloatArrayField


class CatalogAllfields(models.Model):
    '''
    Global catalog view, needed for GeoNode integration
    '''
    id = models.IntegerField()
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


class SimpleSource(models.Model):
    '''
    Simple source view, needed for GeoNode integration
    '''
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    si_type = models.TextField()
    tectonic_region = models.TextField()
    rake = models.FloatField()
    dip = models.FloatField()
    upper_depth = models.FloatField()
    lower_depth = models.FloatField()
    edge = models.LineStringField(srid=4326)
    outline = models.PolygonField(srid=4326)
    mfd_type = models.TextField()
    magnitude_type = models.CharField(max_length=2)
    min_val = models.FloatField()
    max_val = models.FloatField()
    total_cumulative_rate = models.FloatField()
    total_moment_rate = models.FloatField()
    evd_bin_size = models.FloatField()
    evd_values = FloatArrayField()
    tgr_a_val = models.FloatField()
    tgr_b_val = models.FloatField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"simple_source'


class SimpleRupture(models.Model):
    '''
    Simple rupture view, needed for GeoNode integration
    '''
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    si_type = models.TextField()
    tectonic_region = models.TextField()
    rake = models.FloatField()
    magnitude = models.FloatField()
    magnitude_type = models.CharField(max_length=2)
    edge = models.LineStringField(srid=4326)
    fault_outline = models.PolygonField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"simple_rupture'


class ComplexSource(models.Model):
    '''
    Complex source view, needed for GeoNode integration
    '''
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    si_type = models.TextField()
    tectonic_region = models.TextField()
    rake = models.FloatField()
    top_edge = models.LineStringField(srid=4326)
    bottom_edge = models.LineStringField(srid=4326)
    fault_outline = models.PolygonField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"complex_source'


class ComplexRupture(models.Model):
    '''
    Complex rupture view, needed for GeoNode integration
    '''
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    si_type = models.TextField()
    tectonic_region = models.TextField()
    rake = models.FloatField()
    magnitude = models.FloatField()
    magnitude_type = models.CharField(max_length=2)
    top_edge = models.LineStringField(srid=4326)
    bottom_edge = models.LineStringField(srid=4326)
    fault_outline = models.PolygonField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"complex_rupture'
