# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.contrib.gis.db import models

class Hazardsoftware(models.Model):
    hscode = models.TextField(primary_key=True) # This field type is a guess.
    hsname = models.CharField(max_length=50)
    hsdesc = models.CharField(max_length=100)
    hsadddate = models.DateTimeField()
    hsremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'hazardsoftware'

class Econstant(models.Model):
    eccode = models.TextField(primary_key=True) # This field type is a guess.
    ectypeid = models.IntegerField()
    ecshortname = models.TextField() # This field type is a guess.
    ecname = models.CharField(max_length=50)
    ecdesc = models.CharField(max_length=100)
    ecremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'econstant'

class Evariable(models.Model):
    evcode = models.TextField(primary_key=True) # This field type is a guess.
    evtypeid = models.IntegerField()
    evshortname = models.TextField() # This field type is a guess.
    evname = models.CharField(max_length=50)
    evdesc = models.CharField(max_length=100)
    evremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'evariable'

class Intensitymeasuretype(models.Model):
    imcode = models.TextField(primary_key=True) # This field type is a guess.
    imname = models.CharField(max_length=50)
    imdesc = models.CharField(max_length=100)
    imvaluemin = models.FloatField()
    imvaluemax = models.FloatField()
    imunittype = models.TextField() # This field type is a guess.
    imunitdescr = models.CharField(max_length=100)
    imremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'intensitymeasuretype'

class Magrupturerelation(models.Model):
    mrrcode = models.TextField() # This field type is a guess.
    mrrname = models.CharField(max_length=50)
    mrrdesc = models.CharField(max_length=100)
    mrrremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'magrupturerelation'

class Logictreestruc(models.Model):
    ltsid = models.IntegerField(primary_key=True)
    ltsshortname = models.TextField() # This field type is a guess.
    ltsname = models.CharField(max_length=50)
    ltsdesc = models.CharField(max_length=100)
    ltsremarks = models.CharField(max_length=255)
    ltsnumlevels = models.IntegerField()
    class Meta:
        db_table = u'logictreestruc'

class Ltreeparamtype(models.Model):
    ltptid = models.IntegerField(primary_key=True)
    ltptshortname = models.TextField() # This field type is a guess.
    ltptname = models.CharField(max_length=50)
    ltptdesc = models.CharField(max_length=100)
    ltptdatatypecode = models.IntegerField()
    ltptpossvalstring = models.TextField() # This field type is a guess.
    ltptvaluemin = models.FloatField()
    ltptvaluemax = models.FloatField()
    ltptmapping = models.CharField(max_length=255)
    ltptremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'ltreeparamtype'

class Gmpefeature(models.Model):
    gfcode = models.TextField(primary_key=True) # This field type is a guess.
    gftypeid = models.IntegerField()
    gfpossvalstring = models.CharField(max_length=2048)
    gfshortname = models.TextField() # This field type is a guess.
    gfname = models.CharField(max_length=50)
    gfdesc = models.CharField(max_length=100)
    gfremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'gmpefeature'

class Gmpeparameter(models.Model):
    gpcode = models.TextField(primary_key=True) # This field type is a guess.
    gptypeid = models.IntegerField()
    gppossvalstring = models.CharField(max_length=2048)
    gpshortname = models.TextField() # This field type is a guess.
    gpname = models.CharField(max_length=50)
    gpdesc = models.CharField(max_length=100)
    gpremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'gmpeparameter'

class Hazardpointvalue(models.Model):
    hpid = models.IntegerField(primary_key=True)
    hpvalue = models.FloatField()
    hpexceedprob = models.FloatField()
    hpexceedyears = models.IntegerField()
    hcid = models.ForeignKey(Hazardcalculation, db_column='hcid')
    gpid = models.ForeignKey(Geopoint, db_column='gpid')
    imcode = models.ForeignKey(Intensitymeasuretype, db_column='imcode')
    class Meta:
        db_table = u'hazardpointvalue'

class Hibmge(models.Model):
    hibmid = models.ForeignKey(Hazardinputbasicmodel, db_column='hibmid')
    gecode = models.ForeignKey(Gmpe, db_column='gecode')
    hibmgeweight = models.FloatField()
    class Meta:
        db_table = u'hibmge'

class Calculationgroup(models.Model):
    cgcode = models.TextField(primary_key=True) # This field type is a guess.
    cgname = models.CharField(max_length=50)
    cgdesc = models.CharField(max_length=100)
    cgauthlevel = models.TextField() # This field type is a guess.
    cgadddate = models.DateTimeField()
    cgremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'calculationgroup'

class Earthquakecatalog(models.Model):
    ecid = models.IntegerField(primary_key=True)
    ecprivatetag = models.BooleanField()
    ecshortname = models.TextField() # This field type is a guess.
    ecname = models.CharField(max_length=50)
    ecdesc = models.CharField(max_length=100)
    ecformattype = models.IntegerField()
    eccattype = models.TextField() # This field type is a guess.
    ecstartdate = models.DateTimeField()
    ecenddate = models.DateTimeField()
    ectimezone = models.TextField() # This field type is a guess.
    eccvrgcd = models.TextField() # This field type is a guess.
    ecorigformatid = models.IntegerField()
    ecareapolygon = models.CharField(max_length=5120)
    ecareamultipolygon = models.CharField(max_length=5120)
    ecremarks = models.CharField(max_length=255)
    ecpgareapolygon = models.PolygonField()
    ecpgareamultipolygon = models.MultiPolygonField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'earthquakecatalog'

class Seismicsource(models.Model):
    ssid = models.IntegerField(primary_key=True)
    sssrctypecode = models.IntegerField()
    ssgeomtypecode = models.IntegerField()
    ssgrdefaulttag = models.BooleanField()
    ssorigid = models.TextField() # This field type is a guess.
    ssshortname = models.TextField() # This field type is a guess.
    ssname = models.CharField(max_length=50)
    ssdesc = models.CharField(max_length=100)
    ssremarks = models.CharField(max_length=255)
    ssarea = models.FloatField()
    ssanormalized = models.FloatField()
    ssdepth = models.FloatField()
    ssmultilinestring = models.CharField(max_length=5120)
    sstopmultilinestring = models.CharField(max_length=5120)
    ssbottommultilinestring = models.CharField(max_length=5120)
    sspolygon = models.CharField(max_length=5120)
    ssmultipolygon = models.CharField(max_length=5120)
    sspoint = models.CharField(max_length=255)
    ssbackgrdzonetag = models.BooleanField()
    sserrorcode = models.IntegerField()
    scid = models.ForeignKey(Sourcegeometrycatalog, db_column='scid')
    secode = models.ForeignKey(Seismotecenvt, db_column='secode')
    sspgpolygon = models.PolygonField()
    sspgmultipolygon = models.MultiPolygonField()
    sspgmultilinestring = models.MultiLineStringField()
    sspgtopmultilinestring = models.MultiLineStringField()
    sspgbottommultilinestring = models.MultiLineStringField()
    sspgpoint = models.PointField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'seismicsource'

class Sourcegeometrycatalog(models.Model):
    scid = models.IntegerField(primary_key=True)
    scprivatetag = models.BooleanField()
    scshortname = models.TextField() # This field type is a guess.
    scname = models.CharField(max_length=50)
    scdesc = models.CharField(max_length=100)
    sctypecode = models.TextField() # This field type is a guess.
    scareapolygon = models.CharField(max_length=5120)
    scareamultipolygon = models.CharField(max_length=5120)
    scstartdate = models.DateTimeField()
    scenddate = models.DateTimeField()
    scsources = models.CharField(max_length=255)
    scorigformatid = models.IntegerField()
    scremarks = models.CharField(max_length=255)
    scpgareapolygon = models.PolygonField()
    scpgareamultipolygon = models.MultiPolygonField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'sourcegeometrycatalog'

class Eqcatcompleteness(models.Model):
    ccid = models.IntegerField(primary_key=True)
    cctype = models.TextField() # This field type is a guess.
    ccareapolygon = models.CharField(max_length=5120)
    ccareamultipolygon = models.CharField(max_length=5120)
    ccstartdate = models.DateTimeField()
    ccenddate = models.DateTimeField()
    ccmlevel = models.FloatField()
    ecid = models.ForeignKey(Earthquakecatalog, db_column='ecid')
    ccpgareapolygon = models.PolygonField()
    ccpgareamultipolygon = models.MultiPolygonField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'eqcatcompleteness'

class Event(models.Model):
    evid = models.IntegerField(primary_key=True)
    evshortname = models.TextField() # This field type is a guess.
    evname = models.CharField(max_length=50)
    evdesc = models.CharField(max_length=100)
    evorigid = models.TextField() # This field type is a guess.
    evtimestamp = models.DateTimeField()
    evyear = models.IntegerField()
    evmonth = models.IntegerField()
    evday = models.IntegerField()
    evhour = models.IntegerField()
    evmin = models.IntegerField()
    evsec = models.IntegerField()
    evnanosec = models.IntegerField()
    evlat = models.FloatField()
    evlong = models.FloatField()
    evdepth = models.FloatField()
    evmagnitude = models.FloatField()
    evremarks = models.CharField(max_length=255)
    evothdata1 = models.CharField(max_length=100)
    evothdata2 = models.CharField(max_length=100)
    evref = models.CharField(max_length=100)
    everrorcode = models.IntegerField()
    evpoint = models.CharField(max_length=255)
    ecid = models.ForeignKey(Earthquakecatalog, db_column='ecid')
    evpgpoint = models.PointField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'event'

class GeographyColumns(models.Model):
    f_table_catalog = models.TextField() # This field type is a guess.
    f_table_schema = models.TextField() # This field type is a guess.
    f_table_name = models.TextField() # This field type is a guess.
    f_geography_column = models.TextField() # This field type is a guess.
    coord_dimension = models.IntegerField()
    srid = models.IntegerField()
    type = models.TextField()
    class Meta:
        db_table = u'geography_columns'

class Hilmpath(models.Model):
    hilmpid = models.IntegerField(primary_key=True)
    hilmppathstring = models.CharField(max_length=5120)
    hilmpfinalpathtag = models.BooleanField()
    hilmid = models.ForeignKey(Hazardinputltreemodel, db_column='hilmid')
    hilmpweight = models.FloatField()
    hilmpshortname = models.TextField() # This field type is a guess.
    hilmpname = models.CharField(max_length=50)
    hilmpdesc = models.CharField(max_length=100)
    hilmpremarks = models.CharField(max_length=255)
    scid = models.ForeignKey(Sourcegeometrycatalog, db_column='scid')
    hilmpltree = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'hilmpath'

class Calculationowner(models.Model):
    cocode = models.TextField(primary_key=True) # This field type is a guess.
    coname = models.CharField(max_length=50)
    codesc = models.CharField(max_length=100)
    coauthlevel = models.TextField() # This field type is a guess.
    coadddate = models.DateTimeField()
    coremarks = models.CharField(max_length=255)
    cgcode = models.ForeignKey(Calculationgroup, db_column='cgcode')
    class Meta:
        db_table = u'calculationowner'

class Hibmreference(models.Model):
    rlid = models.ForeignKey(Referenceliterature, db_column='rlid')
    hibmid = models.ForeignKey(Hazardinputbasicmodel, db_column='hibmid')
    hibmradddate = models.DateTimeField()
    class Meta:
        db_table = u'hibmreference'

class Ecreference(models.Model):
    rlid = models.ForeignKey(Referenceliterature, db_column='rlid')
    ecid = models.ForeignKey(Earthquakecatalog, db_column='ecid')
    eradddate = models.DateTimeField()
    class Meta:
        db_table = u'ecreference'

class Siteamplification(models.Model):
    sacode = models.TextField() # This field type is a guess.
    saname = models.CharField(max_length=50)
    sadesc = models.CharField(max_length=100)
    savs30min = models.IntegerField()
    savs30max = models.IntegerField()
    savs30descstring = models.CharField(max_length=50)
    sanehrp = models.TextField() # This field type is a guess.
    saintampl = models.FloatField()
    saremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'siteamplification'

class Soilclass(models.Model):
    socode = models.TextField() # This field type is a guess.
    soname = models.CharField(max_length=50)
    sodesc = models.CharField(max_length=100)
    sovalue = models.TextField() # This field type is a guess.
    soremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'soilclass'

class Gmpe(models.Model):
    gecode = models.TextField() # This field type is a guess.
    geprivatetag = models.BooleanField()
    geshortname = models.TextField() # This field type is a guess.
    gename = models.CharField(max_length=50)
    gedesc = models.CharField(max_length=100)
    geremarks = models.CharField(max_length=255)
    geequation = models.CharField(max_length=5120)
    geeqndbdefntag = models.BooleanField()
    geeqntypecode = models.TextField() # This field type is a guess.
    geareapolygon = models.CharField(max_length=5120)
    geareamultipolygon = models.CharField(max_length=5120)
    secode = models.ForeignKey(Seismotecenvt, db_column='secode')
    gepgareapolygon = models.PolygonField()
    gepgareamultipolygon = models.MultiPolygonField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'gmpe'

class SpatialRefSys(models.Model):
    srid = models.IntegerField(primary_key=True)
    auth_name = models.CharField(max_length=256)
    auth_srid = models.IntegerField()
    srtext = models.CharField(max_length=2048)
    proj4text = models.CharField(max_length=2048)
    class Meta:
        db_table = u'spatial_ref_sys'

class GeometryColumns(models.Model):
    f_table_catalog = models.CharField(max_length=256)
    f_table_schema = models.CharField(max_length=256)
    f_table_name = models.CharField(max_length=256)
    f_geometry_column = models.CharField(max_length=256)
    coord_dimension = models.IntegerField()
    srid = models.IntegerField()
    type = models.CharField(max_length=30)
    class Meta:
        db_table = u'geometry_columns'

class Hazardinputbasicmodel(models.Model):
    hibmid = models.IntegerField()
    hibmshortname = models.TextField() # This field type is a guess.
    hibmname = models.CharField(max_length=50)
    hibmdesc = models.CharField(max_length=100)
    hibmremarks = models.CharField(max_length=255)
    hibmcvrgtypecode = models.TextField() # This field type is a guess.
    hibmareapolygon = models.CharField(max_length=5120)
    hibmareamultipolygon = models.CharField(max_length=5120)
    scid = models.ForeignKey(Sourcegeometrycatalog, db_column='scid')
    hibmpgareapolygon = models.PolygonField()
    hibmpgareamultipolygon = models.MultiPolygonField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'hazardinputbasicmodel'

class Hazardinputltreemodel(models.Model):
    hilmid = models.IntegerField(primary_key=True)
    hilmshortname = models.TextField() # This field type is a guess.
    hilmname = models.CharField(max_length=50)
    hilmdesc = models.CharField(max_length=100)
    hilmremarks = models.CharField(max_length=255)
    hilmcvrgtypecode = models.IntegerField()
    hilmareapolygon = models.CharField(max_length=5120)
    hilmareamultipolygon = models.CharField(max_length=5120)
    ltsid = models.ForeignKey(Logictreestruc, db_column='ltsid')
    hilmpgareapolygon = models.PolygonField()
    hilmpgareamultipolygon = models.MultiPolygonField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'hazardinputltreemodel'

class Seismotecenvt(models.Model):
    secode = models.TextField(primary_key=True) # This field type is a guess.
    sename = models.CharField(max_length=50)
    sedesc = models.CharField(max_length=100)
    seremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'seismotecenvt'

class Hazardcalculation(models.Model):
    hcid = models.IntegerField(primary_key=True)
    hcshortname = models.TextField() # This field type is a guess.
    hcname = models.CharField(max_length=50)
    hcdesc = models.CharField(max_length=100)
    hcstarttimestamp = models.DateTimeField()
    hcendtimestamp = models.DateTimeField()
    hcprobdettag = models.TextField() # This field type is a guess.
    hcgemgentag = models.BooleanField()
    hcareapolygon = models.CharField(max_length=5120)
    hcareamultipolygon = models.CharField(max_length=5120)
    hcremarks = models.CharField(max_length=255)
    hibmid = models.ForeignKey(Hazardinputbasicmodel, db_column='hibmid')
    hilmid = models.ForeignKey(Hazardinputltreemodel, db_column='hilmid')
    hilmpid = models.ForeignKey(Hilmpath, db_column='hilmpid')
    evid = models.ForeignKey(Event, db_column='evid')
    hscode = models.ForeignKey(Hazardsoftware, db_column='hscode')
    cocode = models.ForeignKey(Calculationowner, db_column='cocode')
    hcpgareapolygon = models.PolygonField()
    hcpgareamultipolygon = models.MultiPolygonField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'hazardcalculation'

class Hilmruleset(models.Model):
    hilmrid = models.IntegerField(primary_key=True)
    hilmrcvrgtypecode = models.IntegerField()
    hilmractiontypecode = models.IntegerField()
    hilmrvalstring = models.TextField() # This field type is a guess.
    hilmrprobpctstring = models.TextField() # This field type is a guess.
    ltptid = models.ForeignKey(Ltreeparamtype, db_column='ltptid')
    ltpvid = models.ForeignKey(Ltreeparamvalue, db_column='ltpvid')
    hilmid = models.ForeignKey(Hazardinputltreemodel, db_column='hilmid')
    class Meta:
        db_table = u'hilmruleset'

class Ltreeparamvalue(models.Model):
    ltpvid = models.IntegerField(primary_key=True)
    ltpvshortname = models.TextField() # This field type is a guess.
    ltpvname = models.CharField(max_length=50)
    ltpvdesc = models.CharField(max_length=100)
    ltpvremarks = models.CharField(max_length=255)
    ltptid = models.ForeignKey(Ltreeparamtype, db_column='ltptid')
    class Meta:
        db_table = u'ltreeparamvalue'

class Ltreeparamtypelevel(models.Model):
    ltptid = models.ForeignKey(Ltreeparamtype, db_column='ltptid')
    ltsid = models.ForeignKey(Logictreestruc, db_column='ltsid')
    ltptlevel = models.IntegerField()
    ltptnumbranches = models.IntegerField()
    ltptbranchsettag = models.BooleanField()
    class Meta:
        db_table = u'ltreeparamtypelevel'

class Gmparamvalue(models.Model):
    gpcode = models.ForeignKey(Gmpeparameter, db_column='gpcode')
    gecode = models.ForeignKey(Gmpe, db_column='gecode')
    gepvalstring = models.TextField() # This field type is a guess.
    gepremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'gmparamvalue'

class Hilmreference(models.Model):
    rlid = models.ForeignKey(Referenceliterature, db_column='rlid')
    hilmid = models.ForeignKey(Hazardinputltreemodel, db_column='hilmid')
    hilmradddate = models.DateTimeField()
    class Meta:
        db_table = u'hilmreference'

class Ssourcemfd(models.Model):
    ssid = models.ForeignKey(Seismicsource, db_column='ssid')
    mfdcode = models.ForeignKey(Magfreqdistn, db_column='mfdcode')
    ssmfdseqnum = models.IntegerField()
    ssmfdmagnitudemax = models.FloatField()
    ssmfdmagnitudemin = models.FloatField()
    ssmfdvala = models.FloatField()
    ssmfdvalb = models.FloatField()
    ssmfdlambda = models.FloatField()
    ssmfdbeta = models.FloatField()
    ssmfdvalaorig = models.FloatField()
    ssmfdcharmagnitude = models.FloatField()
    ssmfdcharrate = models.FloatField()
    ssmfdcharmagsd = models.FloatField()
    ssmfdtrunclevel = models.FloatField()
    ssmfdmodelweight = models.FloatField()
    ssmfdmomentrate = models.FloatField()
    ssmfdstrike = models.IntegerField()
    ssmfddip = models.IntegerField()
    ssmfdrake = models.IntegerField()
    ssmfddipdirection = models.TextField() # This field type is a guess.
    ssmfddowndipwidth = models.FloatField()
    ssmfdtopoffault = models.FloatField()
    ssmfdfaultlength = models.FloatField()
    ssmfdsliptypecode = models.IntegerField()
    mrrcode = models.ForeignKey(Magrupturerelation, db_column='mrrcode')
    ssmfderrorcode = models.IntegerField()
    ssmfdremarks = models.CharField(max_length=255)
    ssmfddisctag = models.BooleanField()
    ssmfddeltamag = models.FloatField()
    ssmfdnumintervals = models.IntegerField()
    ssmfddiscvalsstring = models.CharField(max_length=2048)
    class Meta:
        db_table = u'ssourcemfd'

class Hilmpge(models.Model):
    hilmpid = models.ForeignKey(Hilmpath, db_column='hilmpid')
    gecode = models.ForeignKey(Gmpe, db_column='gecode')
    hilmpgeweight = models.FloatField()
    class Meta:
        db_table = u'hilmpge'

class Sfaultchar(models.Model):
    ssfcid = models.IntegerField(primary_key=True)
    ssfcstatus = models.TextField() # This field type is a guess.
    ssfcsliprate = models.FloatField()
    ssfcslipratesd = models.FloatField()
    ssfcfloattypeid = models.IntegerField()
    ssfcfloatingruptureflag = models.BooleanField()
    ssfcfloatoffsetalongstrike = models.IntegerField()
    ssfcfloatoffsetalongdip = models.IntegerField()
    ssfcrupturetop = models.IntegerField()
    ssfcrupturebottom = models.IntegerField()
    ssid = models.ForeignKey(Seismicsource, db_column='ssid')
    class Meta:
        db_table = u'sfaultchar'

class Magfreqdistn(models.Model):
    mfdcode = models.TextField(primary_key=True) # This field type is a guess.
    mfdname = models.CharField(max_length=50)
    mfddesc = models.CharField(max_length=100)
    mfdremarks = models.CharField(max_length=255)
    mfddisctag = models.BooleanField()
    class Meta:
        db_table = u'magfreqdistn'

class Gefeaturevalue(models.Model):
    gfcode = models.ForeignKey(Gmpefeature, db_column='gfcode')
    gecode = models.ForeignKey(Gmpe, db_column='gecode')
    gefvalstring = models.TextField() # This field type is a guess.
    gefremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'gefeaturevalue'

class Hazardmap(models.Model):
    hmapid = models.IntegerField(primary_key=True)
    hmapshortname = models.TextField() # This field type is a guess.
    hmapname = models.CharField(max_length=50)
    hmapdesc = models.CharField(max_length=100)
    hmaptimestamp = models.DateTimeField()
    hmaptimedepstartdate = models.DateTimeField()
    hmaptimedependdate = models.DateTimeField()
    hmapexceedprob = models.IntegerField()
    hmapexceedyears = models.IntegerField()
    hmapdamping = models.IntegerField()
    hmapgridsize = models.FloatField()
    hmapremarks = models.CharField(max_length=255)
    hcid = models.ForeignKey(Hazardcalculation, db_column='hcid')
    imcode = models.ForeignKey(Intensitymeasuretype, db_column='imcode')
    class Meta:
        db_table = u'hazardmap'

class Geopoint(models.Model):
    gpid = models.IntegerField(primary_key=True)
    gppoint = models.TextField() # This field type is a guess.
    gpname = models.CharField(max_length=50)
    gpdesc = models.CharField(max_length=100)
    sacode = models.ForeignKey(Siteamplification, db_column='sacode')
    socode = models.ForeignKey(Soilclass, db_column='socode')
    gppgpoint = models.PointField()
    objects = models.GeoManager()
    class Meta:
        db_table = u'geopoint'

class Screference(models.Model):
    rlid = models.ForeignKey(Referenceliterature, db_column='rlid')
    scid = models.ForeignKey(Sourcegeometrycatalog, db_column='scid')
    scradddate = models.DateTimeField()
    class Meta:
        db_table = u'screference'

class Gmeconstant(models.Model):
    gecode = models.ForeignKey(Gmpe, db_column='gecode')
    eccode = models.ForeignKey(Econstant, db_column='eccode')
    gmecvalue = models.TextField() # This field type is a guess.
    gmecremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'gmeconstant'

class Referenceliterature(models.Model):
    rlid = models.IntegerField()
    rlmajorreftag = models.BooleanField()
    rlshortname = models.TextField() # This field type is a guess.
    rlmainauthorfname = models.TextField() # This field type is a guess.
    rlmainauthorlname = models.TextField() # This field type is a guess.
    rlotherauthor = models.CharField(max_length=512)
    rltitle = models.CharField(max_length=512)
    rlmediatype = models.TextField() # This field type is a guess.
    rlperiodicaltitle = models.CharField(max_length=512)
    rlpublishercity = models.CharField(max_length=100)
    rlpublishername = models.CharField(max_length=512)
    rlpubnyear = models.IntegerField()
    rlvolnum = models.IntegerField()
    rlissuenum = models.IntegerField()
    rlpagenums = models.CharField(max_length=100)
    rllastaccessdate = models.DateField()
    rltype = models.TextField() # This field type is a guess.
    rlurl = models.CharField(max_length=1024)
    rlremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'referenceliterature'

class Gmevariable(models.Model):
    gecode = models.ForeignKey(Gmpe, db_column='gecode')
    evcode = models.ForeignKey(Evariable, db_column='evcode')
    gmevremarks = models.CharField(max_length=255)
    class Meta:
        db_table = u'gmevariable'

class Hazardcurve(models.Model):
    hcrvid = models.IntegerField(primary_key=True)
    hcrvshortname = models.TextField() # This field type is a guess.
    hcrvname = models.CharField(max_length=50)
    hcrvdesc = models.CharField(max_length=100)
    hcrvtimestamp = models.DateTimeField()
    hcrvmingrdmotion = models.FloatField()
    hcrvmaxgrdmotion = models.FloatField()
    hcrvtimeperiod = models.IntegerField()
    hcrvsadamping = models.FloatField()
    hcrvsaperiod = models.IntegerField()
    hcrvremarks = models.CharField(max_length=255)
    hcid = models.ForeignKey(Hazardcalculation, db_column='hcid')
    gpid = models.ForeignKey(Geopoint, db_column='gpid')
    imcode = models.ForeignKey(Intensitymeasuretype, db_column='imcode')
    class Meta:
        db_table = u'hazardcurve'

class Gereference(models.Model):
    rlid = models.ForeignKey(Referenceliterature, db_column='rlid')
    gecode = models.ForeignKey(Gmpe, db_column='gecode')
    gradddate = models.DateTimeField()
    class Meta:
        db_table = u'gereference'

