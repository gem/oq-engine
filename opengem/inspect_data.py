#!/usr/bin/env python

# See: http://geodjango.org/docs/tutorial.html#gdal-interface

import os
import time
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.contrib.gis.gdal import *

WORLD_SHP = 'world/data/TM_WORLD_BORDERS-0.3.shp'

print
print

ds = DataSource(WORLD_SHP)
print 'Datasource: %s\n' % ds
print

time.sleep(2)
print 'Number of Layers: %s' % len(ds)
print

lyr = ds[0]
time.sleep(2)
print "Layer 1 Name: '%s'" % lyr
print

time.sleep(2)
print "Layer geometry type: '%s'" % lyr.geom_type
print

time.sleep(2)
print "Layer length (Number of records): %s" % len(lyr)
print

srs = lyr.srs
time.sleep(2)
print 'Layer Spatial Reference System:'
print srs
print
print '\n See http://spatialreference.org for more info'
print

time.sleep(2)
print 'Layer fields: %s' % lyr.fields
print

fld_types = [fld.__name__ for fld in lyr.field_types]
time.sleep(2)
print 'Field Types: %s' % ', '.join(fld_types)
print

print 'Feature name and number of geometrical points...'
time.sleep(2)
for feat in lyr:
    print feat.get('NAME'), feat.geom.num_points
print

print 'Slicing some layer objects as Django fields..'
time.sleep(2)
print lyr[0:2]
print

print 'Grabbing an individual feature...'
time.sleep(2)
feat = lyr[234]
print feat
print feat.get('NAME')
print

geom = feat.geom
time.sleep(2)
print 'That feature geometry as Well Known Text'
print geom.wkt
print

print 'That feature geometry as GeoJson'
time.sleep(2)
print geom.json
print


print 'GeoDjango is cool, huh?'
time.sleep(2)
print

print 'See http://geodjango.org/docs/tutorial.html for more info'