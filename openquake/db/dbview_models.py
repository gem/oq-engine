
# View
# TODO(LB): check all of these fields
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
        db_table = 'hzrdi\".\"simple_source'

# View
# TODO(LB): check all of these fields
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

# View
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
        db_table = 'hzrdi\".\"complex_source'


# View
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
        db_table = 'hzrdi\".\"complex_rupture'



