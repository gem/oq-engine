

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

