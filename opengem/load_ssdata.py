#!/usr/bin/env python

# For this script to work we must set the Django settings file
# as an environment setting before importing LayerMapping

# Alternatively you can place 
# export DJANGO_SETTINGS_MODULE=settings
# in your .bash_profile
#
# or paste this code into a $ manage.py shell

# load Seismic Sources from shapefile

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from psycopg2 import IntegrityError

from django.contrib.gis.utils import mapping, LayerMapping, add_postgis_srs
from seismicsources.models import SourceGeometryCatalog, SeismicSource

try:
    add_postgis_srs(900913)
except IntegrityError:
    print "The Google Spherical Mercator projection, or a projection with srid 900913, already exists, skipping insert"

SEISMICSOURCE_SHP = 'seismicsources/data/seismicsource.shp'

# Auto-generated `LayerMapping` dictionary for SeismicSource model
seismicsource_mapping = {
    'ssid' : 'SSID',
    'sssrctype' : 'SSSRCTYPECODE',
    'ssgeomtype' : 'SSGEOMTYPE',
    'ssgrdefaulttag' : 'SSGRDEFAULTTAG',
    'ssorigid' : 'SSORIGID',
    'ssshortname' : 'SSSHORTNAM',
    'ssname' : 'SSNAME',
    'ssdesc' : 'SSDESC',
    'ssremarks' : 'SSREMARKS',
    'ssarea' : 'SSAREA',
    'ssanormalized' : 'SSANORMALI',
    'ssdepth' : 'SSDEPTH',
    'sspgmultilinestring' : 'SSMULTILINESTRING',
    'sspgtopmultilinestring' : 'SSTOPMULTILINESTRING',
    'sspgbottommultilinestring' : 'SSBOTTOMMULTILINESTRING',
    'sspgpolygon' : 'SSPOLYGON',
    'sspgmultipolygon' : 'SSMULTIPOLYHON',
    'sspgpoint' : 'SSPOINT',
    'ssbackgrdzonetag' : 'SSBACKGRDZONETAG',
    'sserrorcode' : 'SSERRORCODE',
    'scid' : 'SCID',
    'secode' : 'SECODE',
}

layer = LayerMapping(SeismicSource,
                      SEISMICSOURCE_SHP,
                      seismicsource_mapping,
                      transform=False,
                      encoding='iso-8859-1')
                    
layer.save(verbose=True,strict=True,progress=True)


print 'Fixing invalid polygons...'
num = len(SeismicSource.objects.extra(where=
          ['NOT ST_IsValid(geometry)']))
for item in SeismicSource.objects.extra(where=
          ['NOT ST_IsValid(geometry)']):
    corrected = item.geometry.buffer(0)
    item.geometry = corrected
    item.save()

print '....'
num = len(SeismicSource.objects.extra(where=
         ['NOT ST_IsValid(geometry)']))
if num:
  print '%s invalid polygons remain' % num
  print SeismicSource.objects.extra(where=
         ['NOT ST_IsValid(geometry)'])
