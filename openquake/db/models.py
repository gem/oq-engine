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
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'hzrdi\".\"r_rate_mdl'


class FocalMechanism(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    strike = models.FloatField()
    dip = models.FloatField()
    rake = models.FloatField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'hzrdi\".\"focal_mechanism'

'''
Tables for the 'uiapi' schema.
'''

class Upload(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    description = models.TextField(default='')
    path = models.TextField(unique=True)
    STATUS_CHOICES = (
        (u'pending', u'Pending'),
        (u'running', u'Running'),
        (u'failed', u'Failed'),
        (u'succeeded', u'Succeeded'),
    )
    status = models.TextField(choices=STATUS_CHOICES, default='pending')
    job_pid = models.IntegerField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"upload'


class Input(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    upload = models.ForeignKey(Upload)
    path = models.TextField(unique=True)
    INPUT_TYPE_CHOICES = (
        (u'unknown', u'Unknown'),
        (u'source', u'Source Model'),
        (u'lt_source', u'Source Model Logic Tree'),
        (u'lt_gmpe', u'GMPE Logic Tree'),
        (u'exposure', u'Exposure'),
        (u'vulnerability', u'Vulnerability'),
    )
    input_type = models.TextField(choices=INPUT_TYPE_CHOICES)
    size = models.IntegerField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"input'


class OqJob(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    description = models.TextField()
    path = models.TextField(unique=True)
    JOB_TYPE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'event_based', u'Probabilistic Event-Based'),
        (u'deterministic', u'Deterministic'),

    )
    job_type = models.TextField(choices=JOB_TYPE_CHOICES)
    STATUS_CHOICES = (
        (u'pending', u'Pending'),
        (u'running', u'Running'),
        (u'failed', u'Failed'),
        (u'succeeded', u'Succeeded'),
    )
    status = models.TextField(choices=STATUS_CHOICES, default='pending')
    duration = models.IntegerField()
    job_pid = models.IntegerField()
    oq_params = models.ForeignKey(OqParams)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"oq_job'


class OqParams(models.Model):
    id = models.IntegerField(primary_key=True)
    JOB_TYPE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'event_based', u'Probabilistic Event-Based'),
        (u'deterministic', u'Deterministic'),

    )
    job_type = models.TextField(choices=JOB_TYPE_CHOICES)
    upload = models.ForeignKey(Upload)
    region_grid_spacing = models.FloatField()
    min_magnitude = models.FloatField()
    investigation_time = models.FloatField()
    COMPONENT_CHOICES = (
        (u'average', u'Average horizontal'),
        (u'gmroti50', u'Average horizontal (GMRotI50)'),
    )
    component = models.TextField(choices=COMPONENT_CHOICES)
    IMT_CHOICES = (
       (u'pga', u'Peak Ground Acceleration'),
       (u'sa', u'Spectral Acceleration'),
       (u'pgv', u'Peak Ground Velocity'),
       (u'pgd', u'Peak Ground Displacement'),
    )
    imt = models.TextField(choices=IMT_CHOICES)
    period = models.FloatField()
    TRUNC_TYPE_CHOICES = (
       (u'none', u'None'),
       (u'onesided', u'One-sided'),
       (u'twosided', u'Two-sided'),
    )
    truncation_type = models.TextField(choices=TRUNC_TYPE_CHOICES)
    # TODO(LB): We should probably find out why (from a science perspective)
    # the default is 3.0 and document it. I definitely don't remember why it's
    # 3.0.
    truncation_level = models.FloatField(default=3.0)
    reference_vs30_value = models.FloatField()
    imls = FloatArrayField()
    poes = FloatArrayField()
    realizations = models.IntegerField()
    histories = models.IntegerField()
    gm_correlated = models.BooleanField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    region = models.PolygonField(srid=4326)

    class Meta:
        db_table = 'uiapi\".\"oq_params'


class Output(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    oq_job = models.ForeignKey(OqJob)
    path = models.TextField(unique=True)
    display_name = models.TextField()
    db_backed = models.BooleanField(default=False)
    OUTPUT_TYPE_CHOICES = (
        (u'unknown', u'Unknown'),
        (u'hazard_curve', u'Hazard Curve'),
        (u'hazard_map', u'Hazard Map'),
        (u'gmf', u'Ground Motion Field'),
        (u'loss_curve', u'Loss Curve'),
        (u'loss_map', u'Loss Map'),
    )
    output_type = models.TextField(choices=OUTPUT_TYPE_CHOICES)
    # Number of bytes in the file
    size = models.IntegerField()
    # TODO(LB): We should consider removing this; as far I know, it's obsolete.
    shapefile_path = models.TextField(null=True)
    min_value = models.FloatField()
    max_value = models.FloatField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"output'


class ErrorMsg(models.Model):
    id = models.IntegerField(primary_key=True)
    oq_job = models.ForeignKey(OqJob)
    brief = models.TextField()
    detailed = models.TextField()

    class Meta:
        db_table = 'uiapi\".\"error_msg'


class HazardMap(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    poe = models.FloatField()
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'quantile', u'Quantile'),
    )
    statistic_type = models.TextField(choices=STAT_CHOICES)
    quantile = models.FloatField()

    class Meta:
        db_table = 'hzrdr\".\"hazard_map'


class HazardMapData(models.Model):
    id = models.IntegerField(primary_key=True)
    hazard_map = models.ForeignKey(HazardMap)
    value = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:
        db_table = 'hzrdr\".\"hazard_map_data'


class HazardCurve(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    end_branch_label = models.TextField()
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'median', u'Median'),
        (u'quantile', u'Quantile'),
    )
    statistic_type = models.TextField(choices=STAT_CHOICES)
    quantile = models.FloatField()

    class Meta:
        db_table = 'hzrdr\".\"hazard_curve'


class HazardCurveData(models.Model):
    id = models.IntegerField(primary_key=True)
    hazard_curve = models.ForeignKey(HazardCurve)
    poes = FloatArrayField()
    location = models.PointField(srid=4326)

    class Meta:
        db_table = 'hzrdr\".\"hazard_curve_data'


class GmfData(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    ground_motion = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:
        db_table = 'hzrdr\".\"gmf_data'
