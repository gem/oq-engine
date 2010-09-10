from django.contrib.gis.db import models
from datetime import datetime

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
        (u'A', u'Ascii Text'),
        (u'E', u'Excel File Format'),
        (u'C', u'Comma Separated Value Format'),
        (u'S', u'ESRI Shapefile'),
        (u'O', u'Others'),
    )
    #Regular django fields to correspond to attributes in srcgeomcat shapefile
    scid = models.AutoField("Source Geometry Catalog Id", primary_key=True)
    scprivatetag = models.BooleanField("Private to Opengem", default=True)
    scshortname = models.CharField(max_length=20)
    scname = models.CharField(max_length=50)
    scdesc = models.CharField(max_length=100,blank = True)
    sctypecode = models.CharField("Seismic Source Catalog Types", max_length=5, 
                      choices=SOURCEGEOMCATTYPE_CHOICES, default='I')
    scstartdate = models.DateTimeField("Catalog Start Date", blank=True)
    scenddate = models.DateTimeField("Catalog End Date", blank=True)
    scsources = models.CharField("Sources of data", max_length=255, blank=True) 
    scorigformatid = models.CharField("Original Format Type", max_length=1,
                     choices=ORIGFORMATTYPE_CHOICES,default=u'O')
    scremarks = models.CharField("Remarks", max_length=255, blank=True)
    scadddate = models.DateTimeField("Catalog Add Date", default=datetime.now())

    #Geodjango-specific: a geometry field, 
    #and overriding the default manager with a GeoManager instance.
    scpgareapolygon = models.PolygonField(blank=True)
    scpgareamultipolygon = models.MultiPolygonField(blank=True)
    objects = models.GeoManager()

    #Returns the string representation of the model.
    def __unicode__(self):
        return self.scname

class SeismicSource(models.Model):
    SEISMICSOURCETYPE_CHOICES = (
        (1, 'Simple Fault'),
        (2, 'Complex/Subduction Fault'),
        (3, 'Area Zone'),
        (4, 'Gridded Seismicity'),
    )
    GEOMTYPE_CHOICES = (
        (1, 'Point'),
        (2, 'Multilinestring'),
        (3, 'Polygon'),
        (4, 'Multipolygon'),
   )
    scid = models.ForeignKey(SourceGeometryCatalog)
    ssid = models.AutoField("Seismic Source Id", primary_key=True)
    sssrctype = models.IntegerField("Seismic Source Type Code", 
                choices=SEISMICSOURCETYPE_CHOICES)
    ssgeomtype = models.IntegerField("Geometry Type Code",
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
    
    #Geodjango-specific: several geometry fields-is this possible?
    #overrideing the default manager with a GeoManager instance

    sspgmultilinestring = models.MultiLineStringField()
    sspgtopmultilinestring = models.MultiLineStringField()
    sspgbottommultilinestring = models.MultiLineStringField()
    sspgpolygon = models.PolygonField()
    sspgmultipolygon = models.MultiPolygonField()
    sspgpoint = models.PointField()

    objects = models.GeoManager()
    
    #Returns string representation of the model.
    def __unicode__(self):
        return self.scname


