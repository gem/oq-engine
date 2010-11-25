from django.contrib.gis.db import models
from datetime import datetime

# Used to display html 'help text' links within Admin App
from django.utils.safestring import mark_safe

# Create your models here.
class SourceGeometryCatalog(models.Model):
    SOURCEGEOMCATTYPE_CHOICES = ( 
        (u'H', u'Historical'),
        (u'I', u'Instrumental'),
        (u'HI', u'Combination Historical and Instrumental'),
        (u'S', u'Synthetic'),
        (u'O', u'Others'),
    )
    ORIGFORMATTYPE_CHOICES = (
        ( 1, u'Ascii Text'),
        ( 2, u'Excel File Format'),
        ( 3, u'Comma Separated Value Format'),
        ( 4, u'ESRI Shapefile'),
        ( 5, u'Others'),
    )
    scid = models.AutoField("Source Geometry Catalog Id", primary_key=True)
    scprivatetag = models.BooleanField("Private to Opengem", default=True)
    scshortname = models.CharField(max_length=20)
    scname = models.CharField(max_length=50)
    scdesc = models.CharField(max_length=100,blank = True)
    sctypecode = models.CharField("Seismic Source Catalog Types", 
              max_length=5, choices=SOURCEGEOMCATTYPE_CHOICES, default='I')
    scareapolygon = models.CharField("Polygon WKT", max_length=5120)
    scareamultipolygon = models.CharField("Multipolygon WKT", 
              max_length=5120)
    scstartdate = models.DateTimeField("Catalog Start Date", blank=True)
    scenddate = models.DateTimeField("Catalog End Date", blank=True)
    scsources = models.CharField("Sources of data", max_length=255, 
              blank=True) 
    scorigformatid = models.IntegerField("Original Format Type",
              choices=ORIGFORMATTYPE_CHOICES,default=u'O')
    scremarks = models.CharField("Remarks", max_length=255, blank=True)

    #Geodjango-specific: a geometry field, 
    #and overriding the default manager with a GeoManager instance.
    scpgareapolygon = models.PolygonField(blank=True)
    scpgareamultipolygon = models.MultiPolygonField(blank=True)
    objects = models.GeoManager()
    class Meta:
        db_table = u'sourcegeometrycatalog'

    #Returns the string representation of the model.
    def __unicode__(self):
        return self.scname

class SeismicSource(models.Model):
    SEISMICSOURCETYPE_CHOICES = (
        (1, 'Simple Fault'),
        (5, 'Complex/Subduction Fault'),
        (2, 'Area Source Zone'),
        (3, 'Gridded Seismicity Point'),
        (4, 'Seismic Point'),
    )
    GEOMTYPE_CHOICES = (
        (1, 'Point'),
        (2, 'Multilinestring'),
        (3, 'Polygon'),
        (4, 'Multipolygon'),
    )
    scid = models.ForeignKey(SourceGeometryCatalog, db_column = 'scid')
    ssid = models.AutoField("Seismic Source Id", primary_key=True)
    sssrctypecode = models.IntegerField("Seismic Source Type Code", 
                choices=SEISMICSOURCETYPE_CHOICES)
    ssgeomtypecode = models.IntegerField("Geometry Type Code",
                choices=GEOMTYPE_CHOICES)
    ssgrdefaulttag = models.BooleanField("Gutenberg-Richter Default?")
    ssorigid = models.CharField("Original Seismic Source Id", max_length=50)
    ssshortname = models.CharField("Short Name", max_length = 20)
    ssname = models.CharField("Name", max_length = 50)
    ssdesc = models.CharField("Description", max_length = 100)
    ssremarks = models.CharField("Remarks", max_length = 255)
    ssarea = models.FloatField("Area")
    ssanormalized = models.FloatField("Normalized a value")
    ssdepth = models.FloatField("Depth")
    ssbackgrdzonetag = models.BooleanField("Background Zone?")
    sserrorcode = models.IntegerField("Error Code")
    ssmultilinestring = models.CharField(max_length = 5120)
    sstopmultilinestring = models.CharField(max_length = 5120)
    ssbottommultilinestring = models.CharField(max_length = 5120)
    sspolygon = models.CharField(max_length = 5120)
    ssmultipolygon = models.CharField(max_length = 5120)
    sspoint = models.CharField(max_length = 255)
   
    #Geodjango-specific: several geometry fields-is this possible?
    #overriding the default manager with a GeoManager instance
    sspgmultilinestring = models.MultiLineStringField()
    sspgtopmultilinestring = models.MultiLineStringField()
    sspgbottommultilinestring = models.MultiLineStringField()
    sspgpolygon = models.PolygonField()
    sspgmultipolygon = models.MultiPolygonField()
    sspgpoint = models.PointField()

    objects = models.GeoManager()
    class Meta:
        db_table = u'seismicsource'
    
    #Returns string representation of the model.
    def __unicode__(self):
        return self.ssname

