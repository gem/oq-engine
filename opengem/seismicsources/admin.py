#admin.py
#revised from /geographic_admin/world/admin.py

#verbatim:
# This file controls the look adn feel of the models within the Admin App
# They appear in the admin app once they are registered at the bottom of
# this code (same goes for the databrowse app)

from django.conf import settings 
# needed if we use the GOOGLE_MAPS_API_KEY from settings  

# Import the admin site reference from django.contrib.admin
from django.contrib import admin

# Grab the Admin Manager that automatically initializes an OpenLayers map
# for any geometry field using the in Google Mercator projection with
# OpenStreet Map basedata
from django.contrib.gis.admin import OSMGeoAdmin

# Note, another simpler manager that does not reproject the data on 
# OpenStreetMap is available with 
# from django.contrib.gis.admin import GeoModelAdmin

# Finally, import our model from the working project
# the geographic_admin folder must be on your python path

from seismicsources.models import SourceGeometryCatalog, SeismicSource

# Import the Databrowse app so we can register our models to display
# via the databrowse
from django.contrib import databrowse
databrowse.site.register(SourceGeometryCatalog)
databrowse.site.register(SeismicSource)

USE_GOOGLE_TERRAIN_TILES = False

class SourceGeometryCatalogAdmin(OSMGeoAdmin):
    """
    The class that determines the display of the SourceGeometryCatalog model
    within the Admin App.
   
    This class uses some sample options and provides a bunch more in commented
    form below to show the various options GeoDjango provides to customize 
    OpenLayers.
    
    For a look at all the GeoDjango options dive into the source code available
    at:  http://code.djangoproject.com/browser/django/trunk/django/contrib/gis/
         admin/options.py
    
    """
    # Standard Django Admin Options
    list_display = ('scname','scshortname','sctypecode','scprivatetag',)
    search_fields = ('scname',)
    ordering = ('scname',)
    list_filter = ('scprivatetag','sctypecode',)
    save_as = True
    search_fields = ['scname','scshortname']
    list_select_related = True
    fieldsets = (
      ('Source Geometry Catalog Attributes', 
        {'fields': (('scname','scshortname')), 'classes': ('collapse',)}),
      ('Source Geometry Catalog Codes', 
        {'fields': ('sctypecode',), 'classes': ('collapse',)}),
      ('Edit Dates', {'fields': ('scstartdate','scenddate',), 
        'classes': ('collapse', 'wide')}),
      ('Editable Map View', 
        {'fields': ('scpgareapolygon',), 'classes': ('show', 'wide')}),
    )

    if USE_GOOGLE_TERRAIN_TILES:
      map_template = 'gis/admin/google.html'
      extra_js = ['http://openstreetmap.org/openlayers/OpenStreetMap.js', \
               'http://maps.google.com/maps?file=api&amp;v=2&amp;key=%s'\
                % settings.GOOGLE_MAPS_API_KEY]
    else:
      pass # defaults to OSMGeoAdmin presets of OpenStreetMap tiles
    # Default GeoDjango OpenLayers map options
    # Uncomment and modify as desired
    # To learn more about this jargon visit:
    # www.openlayers.org

    #default_lon = 0
    #default_lat = 0
    #default_zoom = 4
    #display_wkt = False
    #display_srid = False
    #extra_js = []
    #num_zoom = 18
    #max_zoom = False
    #min_zoom = False
    #units = False
    #max_resolution = False
    #max_extent = False
    #modifiable = True
    #mouse_position = True
    #scale_text = True
    #layerswitcher = True
    scrollable = False
    #admin_media_prefix = settings.ADMIN_MEDIA_PREFIX
    map_width = 700
    map_height = 325
    #map_srid = 4326
    #map_template = 'gis/admin/openlayers.html'
    #openlayers_url = 'http://openlayers.org/api/2.6/OpenLayers.js'
    #wms_url = 'http://labs.metacarta.com/wms/vmap0'
    #wms_layer = 'basic'
    #wms_name = 'OpenLayers WMS'
    #debug = False
    #widget = OpenLayersWidget

class SeismicSourceAdmin(OSMGeoAdmin):
    """
    
    The class that determines the display of the SeismicSource model
    within the Admin App.
    
    This class uses some sample options and provides a bunch more in commented
    form below to show the various options GeoDjango provides to customize 
    OpenLayers.
    
    For a look at all the GeoDjango options dive into the source code available
    at:  http://code.djangoproject.com/browser/django/trunk/django/contrib/gis/
         admin/options.py
 
    """
    # Standard Django Admin Options
    list_display = ('ssname','scid','sssrctypecode','ssgeomtypecode',)
    search_fields = ('ssname',)
    ordering = ('ssname',)
    list_filter = ('scid','sssrctypecode','ssgeomtypecode')
    save_as = True
    search_fields = ['ssname','ssshortname']
    list_select_related = True
    fieldsets = (
      ('Seismic Source Attributes', {'fields': (('ssname','ssshortname')), 
          'classes': ('collapse',)}),
      ('Seismic Source Type Codes', {'fields': 
          ('sssrctypecode','ssgeomtypecode'), 'classes': ('collapse',)}),
      ('Seismic Source Values', {'fields': 
          ('ssbackgrdzonetag','ssarea','ssanormalized','ssdepth'), 
          'classes': ('collapse',)}), 
      ('Editable Map View', {'fields': 
          ('sspgpolygon','sspgmultipolygon','sspgmultilinestring','sspgpoint',
           'sspgtopmultilinestring','sspgbottommultilinestring'), 
          'classes': ('show', 'wide')}),
    )

    if USE_GOOGLE_TERRAIN_TILES:
      map_template = 'gis/admin/google.html'
      extra_js = ['http://openstreetmap.org/openlayers/OpenStreetMap.js',\
          'http://maps.google.com/maps?file=api&amp;v=2&amp;key=%s'\
           % settings.GOOGLE_MAPS_API_KEY]
    else:
      pass # defaults to OSMGeoAdmin presets of OpenStreetMap tiles
    # Default GeoDjango OpenLayers map options
    # Uncomment and modify as desired
    # To learn more about this jargon visit:
    # www.openlayers.org

    #default_lon = 0
    #default_lat = 0
    #default_zoom = 4
    #display_wkt = False
    #display_srid = False
    #extra_js = []
    #num_zoom = 18
    #max_zoom = False
    #min_zoom = False
    #units = False
    #max_resolution = False
    #max_extent = False
    #modifiable = True
    #mouse_position = True
    #scale_text = True
    #layerswitcher = True
    scrollable = False
    #admin_media_prefix = settings.ADMIN_MEDIA_PREFIX
    map_width = 700
    map_height = 325
    #map_srid = 4326
    #map_template = 'gis/admin/openlayers.html'
    #openlayers_url = 'http://openlayers.org/api/2.6/OpenLayers.js'
    #wms_url = 'http://labs.metacarta.com/wms/vmap0'
    #wms_layer = 'basic'
    #wms_name = 'OpenLayers WMS'
    #debug = False
    #widget = OpenLayersWidget

# Finally, with these options set now register the model
# associating the Options with the actual model
admin.site.register(SourceGeometryCatalog, SourceGeometryCatalogAdmin)
admin.site.register(SeismicSource, SeismicSourceAdmin)
