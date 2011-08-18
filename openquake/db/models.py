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
    si_type = models.TextField()
    tectonic_region = models.TextField()
    rake = models.FloatField()
    magnitude = models.FloatField()
    magnitude_type = models.CharField(max_length=2)
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
    si_type = models.TextField()
    tectonic_region = models.TextField()
    simple_fault = models.ForeignKey(SimpleFault)
    complex_fault = models.ForeignKey(ComplexFault)
    rake = models.FloatField()
    hypocentral_depth = models.FloatField()
    r_depth_distr = models.ForeignKey(RDepthDistr)
    last_update = models.DateTimeField()
    point = models.PointField(srid=4326)
    area = models.PolygonField(srid=4326)

    class Meta:
        db_table = 'hzrdi.\".\"source'


# View
class SimpleRupture(models.Model):
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
    edge = models.TextField() # This field type is a guess.
    fault_outline = models.TextField() # This field type is a guess.

    class Meta:
        db_table = 'hzrdi\".\"simple_rupture'



class SimpleFault(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    dip = models.FloatField()
    upper_depth = models.FloatField()
    lower_depth = models.FloatField()
    mfd_tgr = models.ForeignKey(MfdTgr)
    mfd_evd = models.ForeignKey(MfdEvd)
    last_update = models.DateTimeField()
    edge = models.TextField() # This field type is a guess.
    outline = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'simple_fault'


class SimpleSource(models.Model):
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
    edge = models.TextField() # This field type is a guess.
    outline = models.TextField() # This field type is a guess.
    mfd_type = models.TextField()
    magnitude_type = models.CharField(max_length=2)
    min_val = models.FloatField()
    max_val = models.FloatField()
    total_cumulative_rate = models.FloatField()
    total_moment_rate = models.FloatField()
    evd_bin_size = models.FloatField()
    evd_values = models.TextField() # This field type is a guess.
    tgr_a_val = models.FloatField()
    tgr_b_val = models.FloatField()
    class Meta:
        db_table = u'simple_source'

class OqJob(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    description = models.TextField()
    path = models.TextField(unique=True)
    job_type = models.TextField()
    status = models.TextField()
    duration = models.IntegerField()
    job_pid = models.IntegerField()
    oq_params = models.ForeignKey(OqParams)
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'oq_job'

class FaultEdge(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    last_update = models.DateTimeField()
    top = models.TextField() # This field type is a guess.
    bottom = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'fault_edge'

class Input(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    upload = models.ForeignKey(Upload)
    path = models.TextField(unique=True)
    input_type = models.TextField()
    size = models.IntegerField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'input'

class ComplexRupture(models.Model):
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
    top_edge = models.TextField() # This field type is a guess.
    bottom_edge = models.TextField() # This field type is a guess.
    fault_outline = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'complex_rupture'

class FocalMechanism(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    strike = models.FloatField()
    dip = models.FloatField()
    rake = models.FloatField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'focal_mechanism'

class RDepthDistr(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    magnitude_type = models.CharField(max_length=2)
    magnitude = models.TextField() # This field type is a guess.
    depth = models.TextField() # This field type is a guess.
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'r_depth_distr'

class ComplexSource(models.Model):
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    si_type = models.TextField()
    tectonic_region = models.TextField()
    rake = models.FloatField()
    top_edge = models.TextField() # This field type is a guess.
    bottom_edge = models.TextField() # This field type is a guess.
    fault_outline = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'complex_source'

class GmfData(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    ground_motion = models.FloatField()
    location = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'gmf_data'

class HazardMapData(models.Model):
    id = models.IntegerField(primary_key=True)
    hazard_map = models.ForeignKey(HazardMap)
    value = models.FloatField()
    location = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'hazard_map_data'

class OqParams(models.Model):
    id = models.IntegerField(primary_key=True)
    job_type = models.TextField()
    upload = models.ForeignKey(Upload)
    region_grid_spacing = models.FloatField()
    min_magnitude = models.FloatField()
    investigation_time = models.FloatField()
    component = models.TextField()
    imt = models.TextField()
    period = models.FloatField()
    truncation_type = models.TextField()
    truncation_level = models.FloatField()
    reference_vs30_value = models.FloatField()
    imls = models.TextField() # This field type is a guess.
    poes = models.TextField() # This field type is a guess.
    realizations = models.IntegerField()
    histories = models.IntegerField()
    gm_correlated = models.BooleanField()
    last_update = models.DateTimeField()
    region = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'oq_params'

class HazardCurve(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    end_branch_label = models.TextField()
    statistic_type = models.TextField()
    quantile = models.FloatField()
    class Meta:
        db_table = u'hazard_curve'

class ErrorMsg(models.Model):
    id = models.IntegerField(primary_key=True)
    oq_job = models.ForeignKey(OqJob)
    brief = models.TextField()
    detailed = models.TextField()
    class Meta:
        db_table = u'error_msg'

class HazardMap(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    poe = models.FloatField()
    statistic_type = models.TextField()
    quantile = models.FloatField()
    class Meta:
        db_table = u'hazard_map'


class VulnerabilityFunction(models.Model):
    id = models.IntegerField(primary_key=True)
    vulnerability_model = models.ForeignKey(VulnerabilityModel)
    vf_ref = models.TextField()
    loss_ratios = models.TextField() # This field type is a guess.
    covs = models.TextField() # This field type is a guess.
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'vulnerability_function'

class LossCurveData(models.Model):
    id = models.IntegerField(primary_key=True)
    loss_curve = models.ForeignKey(LossCurve)
    asset_ref = models.TextField()
    losses = models.TextField() # This field type is a guess.
    poes = models.TextField() # This field type is a guess.
    location = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'loss_curve_data'

class AggregateLossCurveData(models.Model):
    id = models.IntegerField(primary_key=True)
    loss_curve = models.ForeignKey(LossCurve)
    losses = models.TextField() # This field type is a guess.
    poes = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'aggregate_loss_curve_data'

class LossMapData(models.Model):
    id = models.IntegerField(primary_key=True)
    loss_map = models.ForeignKey(LossMap)
    asset_ref = models.TextField()
    value = models.FloatField()
    std_dev = models.FloatField()
    location = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'loss_map_data'


class MfdEvd(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    magnitude_type = models.CharField(max_length=2)
    min_val = models.FloatField()
    max_val = models.FloatField()
    bin_size = models.FloatField()
    mfd_values = models.TextField() # This field type is a guess.
    total_cumulative_rate = models.FloatField()
    total_moment_rate = models.FloatField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'mfd_evd'

class MfdTgr(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    magnitude_type = models.CharField(max_length=2)
    min_val = models.FloatField()
    max_val = models.FloatField()
    a_val = models.FloatField()
    b_val = models.FloatField()
    total_cumulative_rate = models.FloatField()
    total_moment_rate = models.FloatField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'mfd_tgr'

class ExposureModel(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    name = models.TextField()
    description = models.TextField()
    category = models.TextField()
    unit = models.TextField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'exposure_model'

class VulnerabilityModel(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    name = models.TextField()
    description = models.TextField()
    imt = models.TextField()
    imls = models.TextField() # This field type is a guess.
    category = models.TextField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'vulnerability_model'


class ComplexFault(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    mfd_tgr = models.ForeignKey(MfdTgr)
    mfd_evd = models.ForeignKey(MfdEvd)
    fault_edge = models.ForeignKey(FaultEdge)
    last_update = models.DateTimeField()
    outline = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'complex_fault'

class RRateMdl(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.TextField()
    name = models.TextField()
    description = models.TextField()
    mfd_tgr = models.ForeignKey(MfdTgr)
    mfd_evd = models.ForeignKey(MfdEvd)
    focal_mechanism = models.ForeignKey(FocalMechanism)
    source = models.ForeignKey(Source)
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'r_rate_mdl'


class HazardCurveData(models.Model):
    id = models.IntegerField(primary_key=True)
    hazard_curve = models.ForeignKey(HazardCurve)
    poes = models.TextField() # This field type is a guess.
    location = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'hazard_curve_data'

class ExposureData(models.Model):
    id = models.IntegerField(primary_key=True)
    exposure_model = models.ForeignKey(ExposureModel)
    asset_ref = models.TextField()
    value = models.FloatField()
    vulnerability_function = models.ForeignKey(VulnerabilityFunction)
    structure_type = models.TextField()
    retrofitting_cost = models.FloatField()
    last_update = models.DateTimeField()
    site = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'exposure_data'

class LossCurve(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    aggregate = models.BooleanField()
    end_branch_label = models.TextField()
    category = models.TextField()
    unit = models.TextField()
    class Meta:
        db_table = u'loss_curve'

class LossMap(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    deterministic = models.BooleanField()
    loss_map_ref = models.TextField()
    end_branch_label = models.TextField()
    category = models.TextField()
    unit = models.TextField()
    poe = models.FloatField()
    class Meta:
        db_table = u'loss_map'

class Output(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    oq_job = models.ForeignKey(OqJob)
    path = models.TextField(unique=True)
    display_name = models.TextField()
    db_backed = models.BooleanField()
    output_type = models.TextField()
    size = models.IntegerField()
    shapefile_path = models.TextField()
    min_value = models.FloatField()
    max_value = models.FloatField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'output'

class Upload(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    description = models.TextField()
    path = models.TextField(unique=True)
    status = models.TextField()
    job_pid = models.IntegerField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'upload'

