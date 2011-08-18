# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.


from datetime import datetime
from django.contrib.gis.db import models
from django.utils.encoding import smart_str


class FloatArrayField(models.Field):
    """This field models a postgres `float` array."""

    def db_type(self, connection):
        return 'float[]'

    def get_prep_value(self, value):
        return "{" + ', '.join(str(v) for v in value) + "}"


'''
Tables in the 'admin' schema.
'''

class OqUser(models.Model):
    id = models.IntegerField(primary_key=True)
    user_name = models.TextField()
    full_name = models.TextField()
    organization = models.ForeignKey(Organization)
    data_is_open = models.BooleanField(default=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    def __str__(self):
        return smart_str(
            ":oq_user: %s (%s)" % (self.full_name, self.user_name))

    class Meta:
        db_table = 'admin\".\"oq_user'


class Organization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    address = models.TextField(null=True)
    url = models.TextField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    def __str__(self):
        return smart_str(":organization: %s" % self.name)

    class Meta:
        db_table = 'admin\".\"organization'


# TODO: delete this model?
class RevisionInfo(models.Model):
    id = models.IntegerField(primary_key=True)
    artefact = models.TextField(unique=True)
    revision = models.TextField()
    step = models.IntegerField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'admin\".\"revision_info'


'''
Tables in the 'eqcat' schema.
'''

class Catalog(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    eventid = models.IntegerField()
    agency = models.TextField()
    identifier = models.TextField()
    time = models.DateTimeField()
    time_error = models.FloatField()
    depth = models.FloatField()
    depth_error = models.FloatField()
    EVENT_CLASS_CHOICES = (
        (u'aftershock', u'Aftershock'),
        (u'foreshock', u'Foreshock'),
    )
    event_class = models.TextField(null=True, choices=EVENT_CLASS_CHOICES)
    magnitude = models.ForeignKey(Magnitude)
    surface = models.ForeignKey(Surface)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    point = models.PointField(srid=4326)

    class Meta:
        db_table = 'eqcat\".\"catalog' 


class Magnitude(models.Model):
    id = models.IntegerField(primary_key=True)
    mb_val = models.FloatField()
    mb_val_error = models.FloatField()
    ml_val = models.FloatField()
    ml_val_error = models.FloatField()
    ms_val = models.FloatField()
    ms_val_error = models.FloatField()
    mw_val = models.FloatField()
    mw_val_error = models.FloatField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'eqcat\".\"magnitude' 


class Surface(models.Model):
    id = models.IntegerField(primary_key=True)
    semi_minor = models.FloatField()
    semi_major = models.FloatField()
    strike = models.FloatField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'eqcat\".\"surface'


# View
class CatalogAllfields(models.Model):
    id = models.IntegerField()
    owner_id = models.IntegerField()
    eventid = models.IntegerField()
    agency = models.TextField()
    identifier = models.TextField()
    time = models.DateTimeField()
    time_error = models.FloatField()
    depth = models.FloatField()
    depth_error = models.FloatField()
    event_class = models.TextField()
    magnitude_id = models.IntegerField()
    surface_id = models.IntegerField()
    last_update = models.DateTimeField()
    point = models.PointField(srid=4326)
    semi_minor = models.FloatField()
    semi_major = models.FloatField()
    strike = models.FloatField()
    mb_val = models.FloatField()
    mb_val_error = models.FloatField()
    ml_val = models.FloatField()
    ml_val_error = models.FloatField()
    ms_val = models.FloatField()
    ms_val_error = models.FloatField()
    mw_val = models.FloatField()
    mw_val_error = models.FloatField()

    class Meta:
        db_table = 'eqcat\".\"catalog_allfields'


'''
Tables for the 'hzrdi' (Hazard Input) schema.
'''

class Rupture(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    input = models.ForeignKey(Input)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    SI_TYPE_CHOICES = (
        (u'complex', u'Complex'),
        (u'point', u'Point'),
        (u'simple', u'Simple'),
    )
    si_type = models.TextField(choices=SI_TYPE_CHOICES, default='simple')
    TECT_REG_CHOICES = (
        (u'active', u'Active Shallow Crust'),
        (u'stable', u'Stable Shallow Crust'),
        (u'interface', u'Subduction Interface'),
        (u'intraslab', u'Subduction Intraslab'),
        (u'volcanic', u'Volcanic'),
    )
    tectonic_region = models.TextField(choices=TECT_REG_CHOICES)
    rake = models.FloatField()
    magnitude = models.FloatField()
    MAG_TYPE_CHOICES = (
        (u'Mb', u'Body Wave Magnitude'),
        (u'Md', u'Duration Magnitude'),
        (u'Ml', u'Local Magnitude'),
        (u'Ms', u'Surface Wave Magnitude'),
        (u'Mw', u'Moment Magnitude'),
    )
    magnitude_type = models.CharField(max_length=2, choices=MAG_TYPE_CHOICES, default='Mw')
    simple_fault = models.ForeignKey(SimpleFault)
    complex_fault = models.ForeignKey(ComplexFault)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    point = models.PointField(srid=4326)

    class Meta:
        db_table = 'hzrdi\".\"rupture'


class Source(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    input = models.ForeignKey(Input)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    SI_TYPE_CHOICES = (
        (u'area', u'Area'),
        (u'point', u'Point'),
        (u'complex', u'Complex'),
        (u'simple', u'Simple'),
    )
    si_type = models.TextField(choices=SI_TYPE_CHOICES, default='simple')
    TECT_REG_CHOICES = (
        (u'active', u'Active Shallow Crust'),
        (u'stable', u'Stable Shallow Crust'),
        (u'interface', u'Subduction Interface'),
        (u'intraslab', u'Subduction Intraslab'),
        (u'volcanic', u'Volcanic'),
    )
    tectonic_region = models.TextField(choices=TECT_REG_CHOICES)
    simple_fault = models.ForeignKey(SimpleFault)
    complex_fault = models.ForeignKey(ComplexFault)
    # TODO(LB): Consider adding validation constraints to the model for rake.
    # Check the database schema for more information.
    rake = models.FloatField() 
    hypocentral_depth = models.FloatField()
    r_depth_distr = models.ForeignKey(RDepthDistr)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    point = models.PointField(srid=4326)
    area = models.PolygonField(srid=4326)

    class Meta:
        db_table = 'hzrdi.\".\"source'


class SimpleFault(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    dip = models.FloatField()  # TODO(LB): Add constraints to model?
    upper_depth = models.FloatField()  # TODO(LB): Add constraints to model?
    lower_depth = models.FloatField()  # TODO(LB): Add constraints to model?
    mfd_tgr = models.ForeignKey(MfdTgr)
    mfd_evd = models.ForeignKey(MfdEvd)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    edge = models.LineStringField(srid=4326)
    outline = models.PolygonField(srid=4326)

    class Meta:
        db_table = 'hzrdi\".\"simple_fault'


class MfdEvd(models.Model):
    '''
    Magnitude Frequency Distribution, Evenly Discretized.
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    MAG_TYPE_CHOICES = (
        (u'Mb', u'Body Wave Magnitude'),
        (u'Md', u'Duration Magnitude'),
        (u'Ml', u'Local Magnitude'),
        (u'Ms', u'Surface Wave Magnitude'),
        (u'Mw', u'Moment Magnitude'),
    )
    magnitude_type = models.CharField(max_length=2, choices=MAG_TYPE_CHOICES, default='Mw')
    min_val = models.FloatField()
    max_val = models.FloatField(default=-1.0)
    bin_size = models.FloatField()
    mfd_values = FloatArrayField()
    total_cumulative_rate = models.FloatField()
    total_moment_rate = models.FloatField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'hzrdi\".\"mfd_evd'


class MfdTgr(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    MAG_TYPE_CHOICES = (
        (u'Mb', u'Body Wave Magnitude'),
        (u'Md', u'Duration Magnitude'),
        (u'Ml', u'Local Magnitude'),
        (u'Ms', u'Surface Wave Magnitude'),
        (u'Mw', u'Moment Magnitude'),
    )
    magnitude_type = models.CharField(max_length=2, choices=MAG_TYPE_CHOICES, default='Mw')
    min_val = models.FloatField()
    max_val = models.FloatField()
    a_val = models.FloatField()
    b_val = models.FloatField()
    total_cumulative_rate = models.FloatField()
    total_moment_rate = models.FloatField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'hzrdi\".\"mfd_tgr'


class ComplexFault(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    mfd_tgr = models.ForeignKey(MfdTgr)
    mfd_evd = models.ForeignKey(MfdEvd)
    fault_edge = models.ForeignKey(FaultEdge)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    outline = models.PolygonField(srid=4326)

    class Meta:
        db_table = 'hzrdi\".\"complex_fault'

class RDepthDistr(models.Model):
    '''
    Rupture Depth Distribution
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    magnitude_type = models.CharField(max_length=2)
    magnitude = FloatArrayField()
    depth = FloatArrayField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'hzrdi\".\"r_depth_distr'


class RRateMdl(models.Model):
    '''
    Rupture Rate Model
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    mfd_tgr = models.ForeignKey(MfdTgr)
    mfd_evd = models.ForeignKey(MfdEvd)
    focal_mechanism = models.ForeignKey(FocalMechanism)
    source = models.ForeignKey(Source)
    last_update = models.DateTimeField(editable=False)

    class Meta:
        db_table = 'hzrdi\".\"r_rate_mdl'


