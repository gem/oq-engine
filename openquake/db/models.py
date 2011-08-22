# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


'''
Model representations of the OpenQuake DB tables.
'''

from datetime import datetime
from django.contrib.gis.db import models


class FloatArrayField(models.Field):  # pylint: disable=R0904
    """This field models a postgres `float` array."""

    def db_type(self, connection):
        return 'float[]'

    def get_prep_value(self, value):
        return "{" + ', '.join(str(v) for v in value) + "}"


## Tables in the 'admin' schema.


class Organization(models.Model):
    '''
    Organizations for grouping users
    '''
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    address = models.TextField(null=True)
    url = models.TextField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'admin\".\"organization'


class OqUser(models.Model):
    '''
    OpenQuake users
    '''
    id = models.IntegerField(primary_key=True)
    user_name = models.TextField()
    full_name = models.TextField()
    organization = models.ForeignKey('Organization')
    data_is_open = models.BooleanField(default=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'admin\".\"oq_user'


class RevisionInfo(models.Model):
    '''
    Revision information
    '''
    id = models.IntegerField(primary_key=True)
    artefact = models.TextField(unique=True)
    revision = models.TextField()
    step = models.IntegerField(default=0)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'admin\".\"revision_info'


## Tables in the 'eqcat' schema.


class Catalog(models.Model):
    '''
    Earthquake catalog
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
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
    magnitude = models.ForeignKey('Magnitude')
    surface = models.ForeignKey('Surface')
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    point = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'eqcat\".\"catalog'


class Magnitude(models.Model):
    '''
    Earthquake event magnitudes
    '''
    id = models.IntegerField(primary_key=True)
    mb_val = models.FloatField(null=True)
    mb_val_error = models.FloatField(null=True)
    ml_val = models.FloatField(null=True)
    ml_val_error = models.FloatField(null=True)
    ms_val = models.FloatField(null=True)
    ms_val_error = models.FloatField(null=True)
    mw_val = models.FloatField(null=True)
    mw_val_error = models.FloatField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'eqcat\".\"magnitude'


class Surface(models.Model):
    '''
    Earthquake event surface (ellipse with an angle)
    '''
    id = models.IntegerField(primary_key=True)
    semi_minor = models.FloatField()
    semi_major = models.FloatField()
    strike = models.FloatField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'eqcat\".\"surface'


## Tables in the 'hzrdi' (Hazard Input) schema.


class Rupture(models.Model):
    '''
    Rupture
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    input = models.ForeignKey('Input')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
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
    rake = models.FloatField(null=True)
    magnitude = models.FloatField()
    MAG_TYPE_CHOICES = (
        (u'Mb', u'Body Wave Magnitude'),
        (u'Md', u'Duration Magnitude'),
        (u'Ml', u'Local Magnitude'),
        (u'Ms', u'Surface Wave Magnitude'),
        (u'Mw', u'Moment Magnitude'),
    )
    magnitude_type = models.CharField(max_length=2, choices=MAG_TYPE_CHOICES,
        default='Mw')
    simple_fault = models.ForeignKey('SimpleFault')
    complex_fault = models.ForeignKey('ComplexFault')
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    point = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"rupture'


class Source(models.Model):
    '''
    Source
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    input = models.ForeignKey('Input')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
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
    simple_fault = models.ForeignKey('SimpleFault')
    complex_fault = models.ForeignKey('ComplexFault')
    rake = models.FloatField(null=True)
    hypocentral_depth = models.FloatField(null=True)
    r_depth_distr = models.ForeignKey('RDepthDistr')
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    point = models.PointField(srid=4326)
    area = models.PolygonField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"source'


class SimpleFault(models.Model):
    '''
    Simple fault geometry
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    dip = models.FloatField()
    upper_depth = models.FloatField()
    lower_depth = models.FloatField()
    mfd_tgr = models.ForeignKey('MfdTgr')
    mfd_evd = models.ForeignKey('MfdEvd')
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    edge = models.LineStringField(srid=4326)
    outline = models.PolygonField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"simple_fault'


class MfdEvd(models.Model):
    '''
    Magnitude Frequency Distribution, evenly discretized
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    MAG_TYPE_CHOICES = (
        (u'Mb', u'Body Wave Magnitude'),
        (u'Md', u'Duration Magnitude'),
        (u'Ml', u'Local Magnitude'),
        (u'Ms', u'Surface Wave Magnitude'),
        (u'Mw', u'Moment Magnitude'),
    )
    magnitude_type = models.CharField(max_length=2, choices=MAG_TYPE_CHOICES,
        default='Mw')
    min_val = models.FloatField()
    max_val = models.FloatField(default=-1.0)
    bin_size = models.FloatField()
    mfd_values = FloatArrayField()
    total_cumulative_rate = models.FloatField(null=True)
    total_moment_rate = models.FloatField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"mfd_evd'


class MfdTgr(models.Model):
    '''
    Magnitude Frequency Distribution, truncated Gutenberg-Richter
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    MAG_TYPE_CHOICES = (
        (u'Mb', u'Body Wave Magnitude'),
        (u'Md', u'Duration Magnitude'),
        (u'Ml', u'Local Magnitude'),
        (u'Ms', u'Surface Wave Magnitude'),
        (u'Mw', u'Moment Magnitude'),
    )
    magnitude_type = models.CharField(max_length=2, choices=MAG_TYPE_CHOICES,
        default='Mw')
    min_val = models.FloatField()
    max_val = models.FloatField()
    a_val = models.FloatField()
    b_val = models.FloatField()
    total_cumulative_rate = models.FloatField(null=True)
    total_moment_rate = models.FloatField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"mfd_tgr'


class ComplexFault(models.Model):
    '''
    Complex fault geometry
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    mfd_tgr = models.ForeignKey('MfdTgr')
    mfd_evd = models.ForeignKey('MfdEvd')
    fault_edge = models.ForeignKey('FaultEdge')
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    outline = models.PolygonField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"complex_fault'


class FaultEdge(models.Model):
    '''
    Fault edge
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    top = models.LineStringField(srid=4326)
    bottom = models.LineStringField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"fault_edge'


class RDepthDistr(models.Model):
    '''
    Rupture Depth Distribution
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    magnitude_type = models.CharField(max_length=2)
    magnitude = FloatArrayField()
    depth = FloatArrayField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"r_depth_distr'


class RRateMdl(models.Model):
    '''
    Rupture Rate Model
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    mfd_tgr = models.ForeignKey('MfdTgr')
    mfd_evd = models.ForeignKey('MfdEvd')
    focal_mechanism = models.ForeignKey('FocalMechanism')
    source = models.ForeignKey('Source')
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"r_rate_mdl'


class FocalMechanism(models.Model):
    '''
    Holds strike, dip and rake values with the respective constraints
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    gid = models.TextField()
    name = models.TextField(null=True)
    description = models.TextField(null=True)
    strike = models.FloatField(null=True)
    dip = models.FloatField(null=True)
    rake = models.FloatField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdi\".\"focal_mechanism'


## Tables in the 'uiapi' schema.


class Upload(models.Model):
    '''
    A batch of OpenQuake input files uploaded by the user
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
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

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"upload'


class Input(models.Model):
    '''
    A single OpenQuake input file uploaded by the user
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    upload = models.ForeignKey('Upload')
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
    # Number of bytes in the file:
    size = models.IntegerField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"input'


class OqJob(models.Model):
    '''
    An OpenQuake engine run started by the user
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    description = models.TextField()
    path = models.TextField(null=True, unique=True)
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
    duration = models.IntegerField(default=0)
    job_pid = models.IntegerField(default=0)
    supervisor_pid = models.IntegerField(default=0)
    oq_params = models.ForeignKey('OqParams')
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"oq_job'


class OqParams(models.Model):
    '''
    Parameters needed to run an OpenQuake job
    '''
    id = models.IntegerField(primary_key=True)
    JOB_TYPE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'event_based', u'Probabilistic Event-Based'),
        (u'deterministic', u'Deterministic'),

    )
    job_type = models.TextField(choices=JOB_TYPE_CHOICES)
    upload = models.ForeignKey('Upload')
    region_grid_spacing = models.FloatField()
    min_magnitude = models.FloatField(null=True)
    investigation_time = models.FloatField(null=True)
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
    period = models.FloatField(null=True)
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
    imls = FloatArrayField(null=True)
    poes = FloatArrayField(null=True)
    realizations = models.IntegerField(null=True)
    histories = models.IntegerField(null=True)
    gm_correlated = models.BooleanField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    region = models.PolygonField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"oq_params'


class Output(models.Model):
    '''
    A single artifact which is a result of an OpenQuake calculation.
    The data may reside in a file or in the database.
    '''
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('OqUser')
    oq_job = models.ForeignKey('OqJob')
    path = models.TextField(null=True, unique=True)
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
    # Number of bytes in the file:
    size = models.IntegerField(default=0)
    # TODO(LB): We should consider removing shapefile_path; as far I know, it's
    # obsolete.
    shapefile_path = models.TextField(null=True)
    min_value = models.FloatField(null=True)
    max_value = models.FloatField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"output'


class ErrorMsg(models.Model):
    '''
    Error information associated with a job failure
    '''
    id = models.IntegerField(primary_key=True)
    oq_job = models.ForeignKey('OqJob')
    brief = models.TextField()
    detailed = models.TextField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"error_msg'


## Tables in the 'hzrdr' schema.


class HazardMap(models.Model):
    '''
    Hazard Map header (information which pertains to entire map)
    '''
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey('Output')
    poe = models.FloatField()
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'quantile', u'Quantile'),
    )
    statistic_type = models.TextField(choices=STAT_CHOICES)
    quantile = models.FloatField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"hazard_map'


class HazardMapData(models.Model):
    '''
    Hazard Map data (data for a single point in the map)
    '''
    id = models.IntegerField(primary_key=True)
    hazard_map = models.ForeignKey('HazardMap')
    value = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"hazard_map_data'


class HazardCurve(models.Model):
    '''
    Hazard Curve header information
    '''
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey('Output')
    end_branch_label = models.TextField(null=True)
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'median', u'Median'),
        (u'quantile', u'Quantile'),
    )
    statistic_type = models.TextField(null=True, choices=STAT_CHOICES)
    quantile = models.FloatField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"hazard_curve'


class HazardCurveData(models.Model):
    '''
    Hazard Curve data

    Contains an list of PoE (Probability of Exceedance)
    values and the geographical point associated with the curve
    '''
    id = models.IntegerField(primary_key=True)
    hazard_curve = models.ForeignKey('HazardCurve')
    poes = FloatArrayField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"hazard_curve_data'


class GmfData(models.Model):
    '''
    Ground Motion Field data
    '''
    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey('Output')
    ground_motion = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"gmf_data'


## Tables in the 'riskr' schema.


class LossMap(models.Model):
    '''
    Holds metadata for loss maps
    '''

    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey("Output")
    deterministic = models.BooleanField()
    loss_map_ref = models.TextField(null=True)
    end_branch_label = models.TextField(null=True)
    category = models.TextField(null=True)
    unit = models.TextField(null=True)
    poe = models.FloatField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"loss_map'


class LossMapData(models.Model):
    '''
    Holds an asset, its position and a value plus (for
    non-deterministic maps) the standard deviation for its loss
    '''

    id = models.IntegerField(primary_key=True)
    loss_map = models.ForeignKey("LossMap")
    asset_ref = models.TextField()
    value = models.FloatField()
    std_dev = models.FloatField(default=0.0)
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"loss_map_data'


class LossCurve(models.Model):
    '''
    Holds the parameters common to a set of loss curves
    '''

    id = models.IntegerField(primary_key=True)
    output = models.ForeignKey("Output")
    aggregate = models.BooleanField(default=False)
    end_branch_label = models.TextField(null=True)
    category = models.TextField(null=True)
    unit = models.TextField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"loss_curve'


class LossCurveData(models.Model):
    '''
    Holds the probabilities of exceedance for a given loss curve
    '''

    id = models.IntegerField(primary_key=True)
    loss_curve = models.ForeignKey("LossCurve")
    asset_ref = models.TextField()
    losses = FloatArrayField()
    poes = FloatArrayField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"loss_curve_data'


class AggregateLossCurveData(models.Model):
    '''
    Holds the probabilities of exceedance for the whole exposure model
    '''

    id = models.IntegerField(primary_key=True)
    loss_curve = models.ForeignKey("LossCurve")
    losses = FloatArrayField()
    poes = FloatArrayField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"aggregate_loss_curve_data'


## Tables in the 'oqmif' schema.


class ExposureModel(models.Model):
    '''
    A risk exposure model
    '''

    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey("OqUser")
    name = models.TextField()
    description = models.TextField(null=True)
    category = models.TextField()
    unit = models.TextField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'oqmif\".\"exposure_model'


class ExposureData(models.Model):
    '''
    Per-asset risk exposure data
    '''

    id = models.IntegerField(primary_key=True)
    exposure_model = models.ForeignKey("ExposureModel")
    asset_ref = models.TextField()
    value = models.FloatField()
    vulnerability_function = models.ForeignKey("VulnerabilityFunction")
    structure_type = models.TextField(null=True)
    retrofitting_cost = models.FloatField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)
    site = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'oqmif\".\"exposure_data'


## Tables in the 'riski' schema.


class VulnerabilityModel(models.Model):
    '''
    A risk vulnerability model
    '''

    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey("OqUser")
    name = models.TextField()
    description = models.TextField(null=True)
    IMT_CHOICES = (
        ('pga', 'Peak Ground Acceleration'),
        ('sa', 'Spectral Acceleration'),
        ('pgv', 'Peak Ground Velocity'),
        ('pgd', 'Peak Ground Displacement'),
    )
    imt = models.TextField(choices=IMT_CHOICES)
    imls = FloatArrayField()
    category = models.TextField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riski\".\"vulnerability_model'


class VulnerabilityFunction(models.Model):
    '''
    A risk vulnerability function
    '''

    id = models.IntegerField(primary_key=True)
    vulnerability_model = models.ForeignKey("VulnerabilityModel")
    vf_ref = models.TextField()
    loss_ratios = FloatArrayField()
    covs = FloatArrayField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riski\".\"vulnerability_function'
