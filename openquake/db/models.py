# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=C0302

'''
Model representations of the OpenQuake DB tables.
'''

from collections import namedtuple
from datetime import datetime
from django.contrib.gis.db import models
from django.contrib.gis.geos.geometry import GEOSGeometry


def profile4job(job_id):
    """Return the job profile for the given job.

    :param int job_id: identifier of the job in question
    :returns: a :py:class:`openquake.db.models.OqJobProfile` instance
    """
    [j2p] = Job2profile.objects.extra(where=["oq_job_id=%s"], params=[job_id])
    return j2p.oq_job_profile


def inputs4job(job_id, input_type=None, path=None):
    """Return the inputs for the given job, input type and path.

    :param int job_id: identifier of the job in question
    :param str input_type: a valid input type
    :param str path: the path of the desired input.
    :returns: a list of :py:class:`openquake.db.models.Input` instances
    """
    i2js = Input2job.objects.extra(where=["oq_job_id=%s"], params=[job_id])
    if not input_type and not path:
        return list(i.input for i in i2js.all())
    qargs = []
    if input_type:
        qargs.append(("input__input_type", input_type))
    if path:
        qargs.append(("input__path", path))
    qargs = dict(qargs)
    return list(i.input for i in i2js.filter(**qargs))


def per_asset_value(exd):
    """Return per-asset value for the given exposure data set.

    Calculate per asset value by considering the given exposure data (`exd`)
    as follows:

        case 1: cost type: aggregated:
            cost = economic value
        case 2: cost type: per asset:
            cost * number (of assets) = economic value
        case 3: cost type: per area and area type: aggregated:
            cost * area = economic value
        case 4: cost type: per area and area type: per asset:
            cost * area * number = economic value

    The same "formula" applies to contenst/retrofitting cost analogously.

    :param exd: a named tuple with the following properties:
        - cost
        - cost_type
        - area
        - area_type
        - number_of_units
    :returns: the per-asset value as a `float`
    :raises: `ValueError` in case of a malformed (risk exposure data) input
    """
    if exd.cost_type == "aggregated":
        return exd.cost
    elif exd.cost_type == "per_asset":
        return exd.cost * exd.number_of_units
    elif exd.cost_type == "per_area":
        if exd.area_type == "aggregated":
            return exd.cost * exd.area
        elif exd.area_type == "per_asset":
            return exd.cost * exd.area * exd.number_of_units
    raise ValueError("Invalid input: '%s'" % str(exd))


def model_equals(model_a, model_b, ignore=None):
    """Compare two Django model objects for equality. The two objects are
    considered equal if the values of the all of the fields of both models are
    equal.

    If you want to ignore some attributes (such as `id`) and compare the rest
    of the attributes, you can specify a list or tuple of attributes to ignore.

    :param model_a:
        A :class:`django.db.models.Model` instance.
    :param model_b:
        A :class:`django.db.models.Model` instance.
    :param ignore:
        Optional. A list or tuple of attribute names (as strings) to ignore in
        the comparison. For example::
            ('id', 'last_updated')

    :returns:
        `True` if the contents each model object are equal, taking into account
        any ignores.
    """
    if not model_a.__class__ == model_b.__class__:
        # Not the same class type; these are definitely not equal.
        return False

    # Now get each field name and compare the attributes in both objects.
    for field_name in model_a.__dict__.keys():
        # Ignore _state; this is an ever-present attribute of the model
        # __dict__ which we don't care about. It doesn't affect our equality
        # comparison.
        if field_name == '_state':
            continue

        # Make sure we ignore the attributes that were specified.
        if ignore is not None and field_name in ignore:
            continue

        a_val = getattr(model_a, field_name)
        b_val = getattr(model_b, field_name)

        # If the attribute is a geometry object,
        # use the GEOSGeometry.equals method to compare:
        if isinstance(a_val, GEOSGeometry):
            if not a_val.equals(b_val):
                return False
        else:
            if not a_val == b_val:
                return False

    return True


class FloatArrayField(models.Field):  # pylint: disable=R0904
    """This field models a postgres `float` array."""

    def db_type(self, connection):
        return 'float[]'

    def get_prep_value(self, value):
        if value is not None:
            return "{" + ', '.join(str(v) for v in value) + "}"
        else:
            return None


class CharArrayField(models.Field):  # pylint: disable=R0904
    """This field models a postgres `varchar` array."""

    def db_type(self, _connection):
        return 'varchar[]'

    def get_prep_value(self, value):
        """Return data in a format that has been prepared for use as a
        parameter in a query.

        :param value: sequence of string values to be saved in a varchar[]
            field
        :type value: list or tuple

        >>> caf = CharArrayField()
        >>> caf.get_prep_value(['foo', 'bar', 'baz123'])
        '{"foo", "bar", "baz123"}'
        """
        if value is not None:
            return '{' + ', '.join('"%s"' % str(v) for v in value) + '}'
        else:
            return None


## Tables in the 'admin' schema.


class Organization(models.Model):
    '''
    Organizations for grouping users
    '''
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
    job_pid = models.IntegerField(default=0)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"upload'


class Input(models.Model):
    '''
    A single OpenQuake input file uploaded by the user
    '''
    owner = models.ForeignKey('OqUser')
    path = models.TextField()
    INPUT_TYPE_CHOICES = (
        (u'unknown', u'Unknown'),
        (u'source', u'Source Model'),
        (u'lt_source', u'Source Model Logic Tree'),
        (u'lt_gmpe', u'GMPE Logic Tree'),
        (u'exposure', u'Exposure'),
        (u'vulnerability', u'Vulnerability'),
        (u'vulnerability_retrofitted', u'Vulnerability Retroffited'),
        (u'rupture', u'Rupture'),
    )
    input_type = models.TextField(choices=INPUT_TYPE_CHOICES)
    # Number of bytes in the file:
    size = models.IntegerField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"input'


class Input2job(models.Model):
    '''
    Associates input model files and jobs.
    '''
    input = models.ForeignKey('Input')
    oq_job = models.ForeignKey('OqJob')

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"input2job'


class Input2upload(models.Model):
    '''
    Associates input model files and uploads.
    '''
    input = models.ForeignKey('Input')
    upload = models.ForeignKey('Upload')

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"input2upload'


class OqJob(models.Model):
    '''
    An OpenQuake engine run started by the user
    '''
    owner = models.ForeignKey('OqUser')
    description = models.TextField(default='')
    path = models.TextField(null=True, unique=True)
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
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    def profile(self):
        """Return the associated job prfile."""
        return profile4job(self.id)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"oq_job'


class JobStats(models.Model):
    '''
    Capture various statistics about a job.
    '''
    oq_job = models.ForeignKey('OqJob')
    start_time = models.DateTimeField(editable=False)
    stop_time = models.DateTimeField(editable=False)
    # The number of total sites in job
    num_sites = models.IntegerField()
    # The number of logic tree samples
    # (for hazard jobs of all types except scenario)
    realizations = models.IntegerField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"job_stats'


class Job2profile(models.Model):
    '''
    Associates jobs with their profiles.
    '''
    oq_job = models.ForeignKey('OqJob')
    oq_job_profile = models.ForeignKey('OqJobProfile')

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"job2profile'


class OqJobProfile(models.Model):
    '''
    Parameters needed to run an OpenQuake job
    '''
    owner = models.ForeignKey('OqUser')
    description = models.TextField(default='')
    CALC_MODE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'event_based', u'Probabilistic Event-Based'),
        (u'scenario', u'Scenario'),
        (u'disaggregation', u'Disaggregation'),
        (u'uhs', u'UHS'),  # Uniform Hazard Spectra
        # Benefit-cost ratio calculator based on Classical PSHA risk calc
        (u'classical_bcr', u'Classical BCR'),
        # Benefit-cost ratio calculator based on Event Based risk calc
        (u'event_based_bcr', u'Probabilistic Event-Based BCR'),
    )
    calc_mode = models.TextField(choices=CALC_MODE_CHOICES)
    job_type = CharArrayField()
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
       (u'ia', u'Arias Intensity'),
       (u'rsd', u'Relative Significant Duration'),
       (u'mmi', u'Modified Mercalli Intensity'),
    )
    imt = models.TextField(choices=IMT_CHOICES)
    period = models.FloatField(null=True)
    damping = models.FloatField(null=True)
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
    reference_vs30_value = models.FloatField(
        "Average shear-wave velocity in the upper 30 meters of a site")
    imls = FloatArrayField(null=True)
    poes = FloatArrayField(null=True)
    realizations = models.IntegerField(null=True)
    histories = models.IntegerField(null=True)
    gm_correlated = models.NullBooleanField(null=True)
    gmf_calculation_number = models.IntegerField(null=True)
    rupture_surface_discretization = models.FloatField(null=True)
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    # We can specify a (region and region_grid_spacing) or sites, but not both.
    region = models.PolygonField(srid=4326, null=True)
    region_grid_spacing = models.FloatField(null=True)
    sites = models.MultiPointField(srid=4326, null=True)

    aggregate_loss_curve = models.NullBooleanField(null=True)  # 1/0 ?
    area_source_discretization = models.FloatField(null=True)
    area_source_magnitude_scaling_relationship = models.TextField(null=True)
    compute_mean_hazard_curve = models.NullBooleanField(null=True)
    conditional_loss_poe = FloatArrayField(null=True)
    fault_magnitude_scaling_relationship = models.TextField(null=True)
    fault_magnitude_scaling_sigma = models.FloatField(null=True)
    fault_rupture_offset = models.FloatField(null=True)
    fault_surface_discretization = models.FloatField(null=True)
    gmf_random_seed = models.IntegerField(null=True)
    gmpe_lt_random_seed = models.IntegerField(null=True)
    gmpe_model_name = models.TextField(null=True)
    grid_source_magnitude_scaling_relationship = models.TextField(null=True)
    include_area_sources = models.NullBooleanField(null=True)
    include_fault_source = models.NullBooleanField(null=True)
    include_grid_sources = models.NullBooleanField(null=True)
    include_subduction_fault_source = models.NullBooleanField(null=True)
    lrem_steps_per_interval = models.IntegerField(null=True)
    loss_curves_output_prefix = models.TextField(null=True)
    # Only used for Event-Based Risk calculations.
    loss_histogram_bins = models.IntegerField(null=True)
    maximum_distance = models.FloatField(null=True)
    quantile_levels = FloatArrayField(null=True)
    reference_depth_to_2pt5km_per_sec_param = models.FloatField(null=True)
    rupture_aspect_ratio = models.FloatField(null=True)
    RUPTURE_FLOATING_TYPE_CHOICES = (
        ('alongstrike', 'Only along strike ( rupture full DDW)'),
        ('downdip', 'Along strike and down dip'),
        ('centereddowndip', 'Along strike & centered down dip'),
    )
    rupture_floating_type = models.TextField(
        null=True, choices=RUPTURE_FLOATING_TYPE_CHOICES)
    SADIGH_SITE_TYPE_CHOICES = (
        ('rock', 'Rock'),
        ('deepsoil', 'Deep-Soil'),
    )
    sadigh_site_type = models.TextField(
        null=True, choices=SADIGH_SITE_TYPE_CHOICES)
    source_model_lt_random_seed = models.IntegerField(null=True)
    STANDARD_DEVIATION_TYPE_CHOICES = (
        ('total', 'Total'),
        ('interevent', 'Inter-Event'),
        ('intraevent', 'Intra-Event'),
        ('zero', 'None (zero)'),
        ('total_mag_dependent', 'Total (Mag Dependent)'),
        ('total_pga_dependent', 'Total (PGA Dependent)'),
        ('intraevent_mag_dependent', 'Intra-Event (Mag Dependent)'),
    )
    standard_deviation_type = models.TextField(
        null=True, choices=STANDARD_DEVIATION_TYPE_CHOICES)
    subduction_fault_magnitude_scaling_relationship = \
        models.TextField(null=True)
    subduction_fault_magnitude_scaling_sigma = models.FloatField(null=True)
    subduction_fault_rupture_offset = models.FloatField(null=True)
    subduction_fault_surface_discretization = models.FloatField(null=True)
    subduction_rupture_aspect_ratio = models.FloatField(null=True)
    subduction_rupture_floating_type = models.TextField(
        null=True, choices=RUPTURE_FLOATING_TYPE_CHOICES)
    SOURCE_AS_CHOICES = (
        ('pointsources', 'Point Sources'),
        ('linesources', 'Line Sources (random or given strike)'),
        ('crosshairsources', 'Cross Hair Line Sources'),
        ('16spokedsources', '16 Spoked Line Sources'),
    )
    treat_area_source_as = models.TextField(
        null=True, choices=SOURCE_AS_CHOICES)
    treat_grid_source_as = models.TextField(
        null=True, choices=SOURCE_AS_CHOICES)
    width_of_mfd_bin = models.FloatField(null=True)

    # The following bin limits fields are for the Disaggregation calculator
    # only:
    lat_bin_limits = FloatArrayField(null=True)
    lon_bin_limits = FloatArrayField(null=True)
    mag_bin_limits = FloatArrayField(null=True)
    epsilon_bin_limits = FloatArrayField(null=True)
    distance_bin_limits = FloatArrayField(null=True)
    # PMF (Probability Mass Function) result choices for the Disaggregation
    # calculator
    # TODO(LB), Sept. 23, 2011: We should consider implementing some custom
    # constraint checking for disagg_results. For now, I'm just going to let
    # the database check the constraints.
    # The following are the valid options for each element of this array field:
    #   MagPMF (Magnitude Probability Mass Function)
    #   DistPMF (Distance PMF)
    #   TRTPMF (Tectonic Region Type PMF)
    #   MagDistPMF (Magnitude-Distance PMF)
    #   MagDistEpsPMF (Magnitude-Distance-Epsilon PMF)
    #   LatLonPMF (Latitude-Longitude PMF)
    #   LatLonMagPMF (Latitude-Longitude-Magnitude PMF)
    #   LatLonMagEpsPMF (Latitude-Longitude-Magnitude-Epsilon PMF)
    #   MagTRTPMF (Magnitude-Tectonic Region Type PMF)
    #   LatLonTRTPMF (Latitude-Longitude-Tectonic Region Type PMF)
    #   FullDisaggMatrix (The full disaggregation matrix; includes
    #       Lat, Lon, Magnitude, Epsilon, and Tectonic Region Type)
    disagg_results = CharArrayField(null=True)
    uhs_periods = FloatArrayField(null=True)
    VS30_TYPE_CHOICES = (
       (u"measured", u"Value obtained from on-site measurements"),
       (u"inferred", u"Estimated value"),
    )
    vs30_type = models.TextField(choices=VS30_TYPE_CHOICES, default="measured")
    depth_to_1pt_0km_per_sec = models.FloatField(default=100.0)
    asset_life_expectancy = models.FloatField(null=True)
    interest_rate = models.FloatField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"oq_job_profile'


class Output(models.Model):
    '''
    A single artifact which is a result of an OpenQuake job.
    The data may reside in a file or in the database.
    '''
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
        (u'collapse_map', u'Collapse map'),
        (u'bcr_distribution', u'Benefit-cost ratio distribution'),
        (u'uh_spectra', u'Uniform Hazard Spectra'),
        (u'agg_loss_curve', u'Aggregate Loss Curve'),
        (u'dmg_dist_per_asset', u'Damage Distribution Per Asset'),
        (u'dmg_dist_per_taxonomy', u'Damage Distribution Per Taxonomy'),
        (u'dmg_dist_total', u'Total Damage Distribution'),
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
    hazard_map = models.ForeignKey('HazardMap')
    value = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"hazard_map_data'


class HazardCurve(models.Model):
    '''
    Hazard Curve header information
    '''
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
    hazard_curve = models.ForeignKey('HazardCurve')
    poes = FloatArrayField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"hazard_curve_data'


class GmfData(models.Model):
    '''
    Ground Motion Field data
    '''
    output = models.ForeignKey('Output')
    ground_motion = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"gmf_data'


class UhSpectra(models.Model):
    """Uniform Hazard Spectra

    A Collection of Uniform Hazard Spectrum which share a set of periods.
    A UH Spectrum has a PoE (Probability of Exceedence) and is conceptually
    composed of a set of 2D matrices, 1 matrix per site/point of interest.
    Each 2D matrix has a number of row equal to ``realizations`` and a number
    of columns equal to the number of ``periods``.
    """
    output = models.ForeignKey('Output')
    timespan = models.FloatField()
    realizations = models.IntegerField()
    periods = FloatArrayField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"uh_spectra'


class UhSpectrum(models.Model):
    """Uniform Hazard Spectrum

    * "Uniform" meaning "the same PoE"
    * "Spectrum" because it covers a range/band of periods/frequencies
    """
    uh_spectra = models.ForeignKey('UhSpectra')
    poe = models.FloatField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"uh_spectrum'


class UhSpectrumData(models.Model):
    """Uniform Hazard Spectrum Data

    A single "row" of data in a UHS matrix for a specific site/point of
    interest.
    """
    uh_spectrum = models.ForeignKey('UhSpectrum')
    realization = models.IntegerField()
    sa_values = FloatArrayField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'hzrdr\".\"uh_spectrum_data'


## Tables in the 'riskr' schema.


class LossMap(models.Model):
    '''
    Holds metadata for loss maps
    '''

    output = models.ForeignKey("Output")
    scenario = models.BooleanField()
    loss_map_ref = models.TextField(null=True)
    end_branch_label = models.TextField(null=True)
    category = models.TextField(null=True)
    unit = models.TextField(null=True)
    timespan = models.FloatField(null=True)
    poe = models.FloatField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"loss_map'


class LossMapData(models.Model):
    '''
    Holds an asset, its position and a value plus (for
    non-scenario maps) the standard deviation for its loss
    '''

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

    loss_curve = models.ForeignKey("LossCurve")
    losses = FloatArrayField()
    poes = FloatArrayField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"aggregate_loss_curve_data'


class CollapseMap(models.Model):
    '''
    Holds metadata for the collapse map
    '''

    output = models.ForeignKey("Output")
    exposure_model = models.ForeignKey("ExposureModel")

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"collapse_map'


class CollapseMapData(models.Model):
    '''
    Holds the actual data for the collapse map
    '''

    collapse_map = models.ForeignKey("CollapseMap")
    asset_ref = models.TextField()
    value = models.FloatField()
    std_dev = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"collapse_map_data'


class BCRDistribution(models.Model):
    '''
    Holds metadata for the benefit-cost ratio distribution
    '''

    output = models.ForeignKey("Output")
    exposure_model = models.ForeignKey("ExposureModel")

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"bcr_distribution'


class BCRDistributionData(models.Model):
    '''
    Holds the actual data for the benefit-cost ratio distribution
    '''

    bcr_distribution = models.ForeignKey("BCRDistribution")
    asset_ref = models.TextField()
    bcr = models.FloatField()
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"bcr_distribution_data'


class DmgDistPerAsset(models.Model):
    """Holds metadata for damage distributions per asset."""

    output = models.ForeignKey("Output")
    dmg_states = CharArrayField()
    end_branch_label = models.TextField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"dmg_dist_per_asset'


class DmgDistPerAssetData(models.Model):
    """Holds the actual data for damage distributions per asset."""

    dmg_dist_per_asset = models.ForeignKey("DmgDistPerAsset")
    exposure_data = models.ForeignKey("ExposureData")
    dmg_state = models.TextField()
    mean = models.FloatField()
    stddev = models.FloatField()
    # geometry for the computation cell which contains the referenced asset
    location = models.PointField(srid=4326)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"dmg_dist_per_asset_data'


class DmgDistPerTaxonomy(models.Model):
    """Hold metdata for damage distributions per taxonomy."""

    output = models.ForeignKey("Output")
    dmg_states = CharArrayField()
    end_branch_label = models.TextField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"dmg_dist_per_taxonomy'


class DmgDistPerTaxonomyData(models.Model):
    """Holds the actual data for damage distributions per taxonomy."""

    dmg_dist_per_taxonomy = models.ForeignKey("DmgDistPerTaxonomy")
    taxonomy = models.TextField()
    dmg_state = models.TextField()
    mean = models.FloatField()
    stddev = models.FloatField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"dmg_dist_per_taxonomy_data'


class DmgDistTotal(models.Model):
    """Holds metadata for 'total damage distribution' values for an entire
    calculation. This is the total over all assets and GMFs."""

    output = models.ForeignKey("Output")
    dmg_states = CharArrayField()
    end_branch_label = models.TextField(null=True)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"dmg_dist_total'


class DmgDistTotalData(models.Model):
    """Holds the actual 'total damage distribution' values for for an entire
    calculation. There should be  one record per calculation per damage state.
    """

    dmg_dist_total = models.ForeignKey("DmgDistTotal")
    dmg_state = models.TextField()
    mean = models.FloatField()
    stddev = models.FloatField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riskr\".\"dmg_dist_total_data'


## Tables in the 'oqmif' schema.


class ExposureModel(models.Model):
    '''
    A risk exposure model
    '''

    owner = models.ForeignKey("OqUser")
    input = models.ForeignKey("Input")
    name = models.TextField()
    description = models.TextField(null=True)
    category = models.TextField()
    taxonomy_source = models.TextField(
        null=True, help_text="the taxonomy system used to classify the assets")
    AREA_CHOICES = (
        (u'aggregated', u'Aggregated area value'),
        (u'per_asset', u'Per asset area value'),
    )
    area_type = models.TextField(null=True, choices=AREA_CHOICES)
    area_unit = models.TextField(null=True)
    COST_CHOICES = (
        (u'aggregated', u'Aggregated economic value'),
        (u'per_area', u'Per area economic value'),
        (u'per_asset', u'Per asset economic value'),
    )
    stco_type = models.TextField(null=True, choices=COST_CHOICES,
                                 help_text="structural cost type")
    stco_unit = models.TextField(null=True, help_text="structural cost unit")
    reco_type = models.TextField(null=True, choices=COST_CHOICES,
                                 help_text="retrofitting cost type")
    reco_unit = models.TextField(null=True, help_text="retrofitting cost unit")
    coco_type = models.TextField(null=True, choices=COST_CHOICES,
                                 help_text="contents cost type")
    coco_unit = models.TextField(null=True, help_text="contents cost unit")

    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'oqmif\".\"exposure_model'


class Occupancy(models.Model):
    '''
    Asset occupancy data
    '''

    exposure_data = models.ForeignKey("ExposureData")
    description = models.TextField()
    occupants = models.IntegerField()

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'oqmif\".\"occupancy'


class ExposureData(models.Model):
    '''
    Per-asset risk exposure data
    '''

    REXD = namedtuple(
        "REXD", "cost, cost_type, area, area_type, number_of_units")

    exposure_model = models.ForeignKey("ExposureModel")
    asset_ref = models.TextField()
    taxonomy = models.TextField()
    site = models.PointField(srid=4326)
    # Override the default manager with a GeoManager instance in order to
    # enable spatial queries.
    objects = models.GeoManager()

    stco = models.FloatField(null=True, help_text="structural cost")
    reco = models.FloatField(null=True, help_text="retrofitting cost")
    coco = models.FloatField(null=True, help_text="contents cost")

    number_of_units = models.FloatField(
        null=True, help_text="number of assets, people etc.")
    area = models.FloatField(null=True)

    ins_limit = models.FloatField(
        null=True, help_text="insurance coverage limit")
    deductible = models.FloatField(
        null=True, help_text="insurance deductible")

    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    @property
    def value(self):
        """The structural per-asset value."""
        exd = self.REXD(
            cost=self.stco, cost_type=self.exposure_model.stco_type,
            area=self.area, area_type=self.exposure_model.area_type,
            number_of_units=self.number_of_units)
        return per_asset_value(exd)

    @property
    def retrofitting_cost(self):
        """The retrofitting per-asset value."""
        exd = self.REXD(
            cost=self.reco, cost_type=self.exposure_model.reco_type,
            area=self.area, area_type=self.exposure_model.area_type,
            number_of_units=self.number_of_units)
        return per_asset_value(exd)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'oqmif\".\"exposure_data'


## Tables in the 'riski' schema.


class VulnerabilityModel(models.Model):
    '''
    A risk vulnerability model
    '''

    owner = models.ForeignKey("OqUser")
    input = models.ForeignKey("Input")
    name = models.TextField()
    description = models.TextField(null=True)
    imt = models.TextField(choices=OqJobProfile.IMT_CHOICES)
    imls = FloatArrayField()
    category = models.TextField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riski\".\"vulnerability_model'


class VulnerabilityFunction(models.Model):
    '''
    A risk vulnerability function
    '''

    vulnerability_model = models.ForeignKey("VulnerabilityModel")
    taxonomy = models.TextField()
    loss_ratios = FloatArrayField()
    covs = FloatArrayField()
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riski\".\"vulnerability_function'


class FragilityModel(models.Model):
    """A risk fragility model"""

    owner = models.ForeignKey("OqUser")
    input = models.ForeignKey("Input")
    description = models.TextField(null=True)
    FORMAT_CHOICES = (
        (u"continuous", u"Continuous fragility model"),
        (u"discrete", u"Discrete fragility model"),
    )
    format = models.TextField(choices=FORMAT_CHOICES)
    lss = CharArrayField(help_text="limit states")
    imls = FloatArrayField(null=True, help_text="Intensity measure levels")
    imt = models.TextField(null=True, choices=OqJobProfile.IMT_CHOICES,
                           help_text="Intensity measure type")
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riski\".\"fragility_model'


class Ffc(models.Model):
    """A continuous fragility function"""

    fragility_model = models.ForeignKey("FragilityModel")
    lsi = models.PositiveSmallIntegerField(
        help_text="limit state index, facilitates ordering of fragility "
                  "function in accordance with the limit states")
    ls = models.TextField(help_text="limit state")
    taxonomy = models.TextField()
    ftype = models.TextField(null=True, help_text="function/distribution type")
    mean = models.FloatField(help_text="Mean value")
    stddev = models.FloatField(help_text="Standard deviation")
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riski\".\"ffc'


class Ffd(models.Model):
    """A discrete fragility function"""

    fragility_model = models.ForeignKey("FragilityModel")
    lsi = models.PositiveSmallIntegerField(
        help_text="limit state index, facilitates ordering of fragility "
                  "function in accordance with the limit states")
    ls = models.TextField(help_text="limit state")
    taxonomy = models.TextField()
    poes = FloatArrayField(help_text="Probabilities of exceedance")
    last_update = models.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'riski\".\"ffd'
