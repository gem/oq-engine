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

class RevisionInfo(models.Model):
    id = models.IntegerField(primary_key=True)
    artefact = models.CharField(unique=True, max_length=-1)
    revision = models.CharField(max_length=-1)
    step = models.IntegerField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'revision_info'

class SimpleRupture(models.Model):
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    si_type = models.CharField(max_length=-1)
    tectonic_region = models.CharField(max_length=-1)
    rake = models.FloatField()
    magnitude = models.FloatField()
    magnitude_type = models.CharField(max_length=2)
    edge = models.TextField() # This field type is a guess.
    fault_outline = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'simple_rupture'

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
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'magnitude'

class CatalogAllfields(models.Model):
    id = models.IntegerField()
    owner_id = models.IntegerField()
    eventid = models.IntegerField()
    agency = models.CharField(max_length=-1)
    identifier = models.CharField(max_length=-1)
    time = models.DateTimeField()
    time_error = models.FloatField()
    depth = models.FloatField()
    depth_error = models.FloatField()
    event_class = models.CharField(max_length=-1)
    magnitude_id = models.IntegerField()
    surface_id = models.IntegerField()
    last_update = models.DateTimeField()
    point = models.TextField() # This field type is a guess.
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
        db_table = u'catalog_allfields'

class SimpleFault(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
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

class Source(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    input = models.ForeignKey(Input)
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    si_type = models.CharField(max_length=-1)
    tectonic_region = models.CharField(max_length=-1)
    simple_fault = models.ForeignKey(SimpleFault)
    complex_fault = models.ForeignKey(ComplexFault)
    rake = models.FloatField()
    hypocentral_depth = models.FloatField()
    r_depth_distr = models.ForeignKey(RDepthDistr)
    last_update = models.DateTimeField()
    point = models.TextField() # This field type is a guess.
    area = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'source'

class Surface(models.Model):
    id = models.IntegerField(primary_key=True)
    semi_minor = models.FloatField()
    semi_major = models.FloatField()
    strike = models.FloatField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'surface'

class SimpleSource(models.Model):
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    si_type = models.CharField(max_length=-1)
    tectonic_region = models.CharField(max_length=-1)
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
    description = models.CharField(max_length=-1)
    path = models.CharField(unique=True, max_length=-1)
    job_type = models.CharField(max_length=-1)
    status = models.CharField(max_length=-1)
    duration = models.IntegerField()
    job_pid = models.IntegerField()
    oq_params = models.ForeignKey(OqParams)
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'oq_job'

class FaultEdge(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    last_update = models.DateTimeField()
    top = models.TextField() # This field type is a guess.
    bottom = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'fault_edge'

class Input(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    upload = models.ForeignKey(Upload)
    path = models.CharField(unique=True, max_length=-1)
    input_type = models.CharField(max_length=-1)
    size = models.IntegerField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'input'

class ComplexRupture(models.Model):
    id = models.IntegerField()
    owner_id = models.IntegerField()
    input_id = models.IntegerField()
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    si_type = models.CharField(max_length=-1)
    tectonic_region = models.CharField(max_length=-1)
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
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    strike = models.FloatField()
    dip = models.FloatField()
    rake = models.FloatField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'focal_mechanism'

class RDepthDistr(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
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
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    si_type = models.CharField(max_length=-1)
    tectonic_region = models.CharField(max_length=-1)
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
    job_type = models.CharField(max_length=-1)
    upload = models.ForeignKey(Upload)
    region_grid_spacing = models.FloatField()
    min_magnitude = models.FloatField()
    investigation_time = models.FloatField()
    component = models.CharField(max_length=-1)
    imt = models.CharField(max_length=-1)
    period = models.FloatField()
    truncation_type = models.CharField(max_length=-1)
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
    end_branch_label = models.CharField(max_length=-1)
    statistic_type = models.CharField(max_length=-1)
    quantile = models.FloatField()
    class Meta:
        db_table = u'hazard_curve'

class ErrorMsg(models.Model):
    id = models.IntegerField(primary_key=True)
    oq_job = models.ForeignKey(OqJob)
    brief = models.CharField(max_length=-1)
    detailed = models.CharField(max_length=-1)
    class Meta:
        db_table = u'error_msg'

class HazardMap(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    poe = models.FloatField()
    statistic_type = models.CharField(max_length=-1)
    quantile = models.FloatField()
    class Meta:
        db_table = u'hazard_map'

class Organization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    address = models.TextField(null=True)
    url = models.TextField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    def _str__(self):
        return smart_str(":organization: %s" % self.name)

    class Meta:
        db_table = 'admin\".\"organization'

class VulnerabilityFunction(models.Model):
    id = models.IntegerField(primary_key=True)
    vulnerability_model = models.ForeignKey(VulnerabilityModel)
    vf_ref = models.CharField(max_length=-1)
    loss_ratios = models.TextField() # This field type is a guess.
    covs = models.TextField() # This field type is a guess.
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'vulnerability_function'

class LossCurveData(models.Model):
    id = models.IntegerField(primary_key=True)
    loss_curve = models.ForeignKey(LossCurve)
    asset_ref = models.CharField(max_length=-1)
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
    asset_ref = models.CharField(max_length=-1)
    value = models.FloatField()
    std_dev = models.FloatField()
    location = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'loss_map_data'

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
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    category = models.CharField(max_length=-1)
    unit = models.CharField(max_length=-1)
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'exposure_model'

class VulnerabilityModel(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    imt = models.CharField(max_length=-1)
    imls = models.TextField() # This field type is a guess.
    category = models.CharField(max_length=-1)
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'vulnerability_model'

class Catalog(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    eventid = models.IntegerField()
    agency = models.CharField(max_length=-1)
    identifier = models.CharField(max_length=-1)
    time = models.DateTimeField()
    time_error = models.FloatField()
    depth = models.FloatField()
    depth_error = models.FloatField()
    event_class = models.CharField(max_length=-1)
    magnitude = models.ForeignKey(Magnitude)
    surface = models.ForeignKey(Surface)
    last_update = models.DateTimeField()
    point = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'catalog'

class ComplexFault(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
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
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    mfd_tgr = models.ForeignKey(MfdTgr)
    mfd_evd = models.ForeignKey(MfdEvd)
    focal_mechanism = models.ForeignKey(FocalMechanism)
    source = models.ForeignKey(Source)
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'r_rate_mdl'

class Rupture(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    input = models.ForeignKey(Input)
    gid = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1)
    si_type = models.CharField(max_length=-1)
    tectonic_region = models.CharField(max_length=-1)
    rake = models.FloatField()
    magnitude = models.FloatField()
    magnitude_type = models.CharField(max_length=2)
    simple_fault = models.ForeignKey(SimpleFault)
    complex_fault = models.ForeignKey(ComplexFault)
    last_update = models.DateTimeField()
    point = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'rupture'

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
    asset_ref = models.CharField(max_length=-1)
    value = models.FloatField()
    vulnerability_function = models.ForeignKey(VulnerabilityFunction)
    structure_type = models.CharField(max_length=-1)
    retrofitting_cost = models.FloatField()
    last_update = models.DateTimeField()
    site = models.TextField() # This field type is a guess.
    class Meta:
        db_table = u'exposure_data'

class LossCurve(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    aggregate = models.BooleanField()
    end_branch_label = models.CharField(max_length=-1)
    category = models.CharField(max_length=-1)
    unit = models.CharField(max_length=-1)
    class Meta:
        db_table = u'loss_curve'

class LossMap(models.Model):
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey(Output)
    deterministic = models.BooleanField()
    loss_map_ref = models.CharField(max_length=-1)
    end_branch_label = models.CharField(max_length=-1)
    category = models.CharField(max_length=-1)
    unit = models.CharField(max_length=-1)
    poe = models.FloatField()
    class Meta:
        db_table = u'loss_map'

class Output(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    oq_job = models.ForeignKey(OqJob)
    path = models.CharField(unique=True, max_length=-1)
    display_name = models.CharField(max_length=-1)
    db_backed = models.BooleanField()
    output_type = models.CharField(max_length=-1)
    size = models.IntegerField()
    shapefile_path = models.CharField(max_length=-1)
    min_value = models.FloatField()
    max_value = models.FloatField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'output'

class Upload(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(OqUser)
    description = models.CharField(max_length=-1)
    path = models.CharField(unique=True, max_length=-1)
    status = models.CharField(max_length=-1)
    job_pid = models.IntegerField()
    last_update = models.DateTimeField()
    class Meta:
        db_table = u'upload'

