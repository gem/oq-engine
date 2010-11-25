#!/usr/bin/env python

# For this script to work we must set the Django settings file
# as an environment setting before importing LayerMapping

# Alternatively you can place 
# export DJANGO_SETTINGS_MODULE=settings
# in your .bash_profile
#
# or paste this code into a $ manage.py shell

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from psycopg2 import IntegrityError

from django.contrib.gis.utils import mapping, LayerMapping, add_postgis_srs
from seismicsources.models import SourceGeometryCatalog, SeismicSource
from openquake import settings

try:
    add_postgis_srs(900913)
except IntegrityError:
    print "The Google Spherical Mercator projection, or a projection with srid 900913, already exists, skipping insert"


#13Sep2010: Use manual mapping in models.py -- sourcegeometrycatalog_mapping
sourcegeometrycatalog_mapping = {
    'scid' : 'SCID',
    'scprivatetag' : 'SCPRIVATETAG',
    'scshortname' : 'SCSHORTNAME',
    'scname' : 'SCNAME',
    'scdesc' : 'SCDESC',
    'sctypecode' : 'SCTYPECODE',
    'scpgareapolygon' : 'SCAREAPOLYGON',
    'scpgareamultipolygon' : 'SCAREAMULTILINESTRING',
    'scstartdate' : 'SCSTARTDATE',
    'scenddate' : 'SCENDDATE',
    'scsources' : 'SCSOURCES',
    'scorigformatid' : 'SCORIGFORMATID',
    'scremarks' : 'SCREMARKS',
    'scadddate' : 'SCADDDATE',
}



layer = LayerMapping(SourceGeometryCatalog,
                      settings.SOURCEGEOM_SHP,
                      sourcegeometrycatalog_mapping,
                      transform=False,
                      encoding='iso-8859-1')
                    
layer.save(verbose=True,strict=True,progress=True)


print 'Fixing invalid polygons...'
num = len(SourceGeometryCatalog.objects.extra(where=
          ['NOT ST_IsValid(geometry)']))
for item in SourceGeometryCatalog.objects.extra(where=
          ['NOT ST_IsValid(geometry)']):
    corrected = item.geometry.buffer(0)
    item.geometry = corrected
    item.save()

print '....'
num = len(SourceGeometryCatalog.objects.extra(where=
         ['NOT ST_IsValid(geometry)']))
if num:
  print '%s invalid polygons remain' % num
  print SourceGeometryCatalog.objects.extra(where=
         ['NOT ST_IsValid(geometry)'])
