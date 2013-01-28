# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2013, GEM Foundation.
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

# Disable:
# - 'Maximum number of public methods for a class'
# - 'Missing docstring' (because of all of the model Meta)
# pylint: disable=R0904,C0111

'''
Model representations of the OpenQuake DB tables.
'''

import itertools
import operator
import os
import re

from datetime import datetime

import numpy

from django.db import connection
from django.contrib.gis.db import models as djm
from nhlib import geo as nhlib_geo
from shapely import wkt

from openquake.db import fields

#: Default Spectral Acceleration damping. At the moment, this is not
#: configurable.
DEFAULT_SA_DAMPING = 5.0


#: System Reference ID used for geometry objects
DEFAULT_SRID = 4326


VS30_TYPE_CHOICES = (
    (u"measured", u"Value obtained from on-site measurements"),
    (u"inferred", u"Estimated value"),
)

IMT_CHOICES = (
    (u'PGA', u'Peak Ground Acceleration'),
    (u'PGV', u'Peak Ground Velocity'),
    (u'PGD', u'Peak Ground Displacement'),
    (u'SA', u'Spectral Acceleration'),
    (u'IA', u'Arias Intensity'),
    (u'RSD', u'Relative Significant Duration'),
    (u'MMI', u'Modified Mercalli Intensity'),
)

#: Default Loss Curve Resolution used for probabilistic risk calculators
DEFAULT_LOSS_CURVE_RESOLUTION = 50


def queryset_iter(queryset, chunk_size):
    """
    Given a QuerySet, split it into smaller queries and yield the result of
    each.

    :param queryset:
        A :class:`django.db.models.query.QuerySet` to iterate over, in chunks
        of ``chunk_size``.
    :param int chunksize:
        Chunk size for iteration over query results. For an unexecuted
        QuerySet, this will result in splitting a (potentially large) query
        into smaller queries.
    """
    offset = 0
    while True:
        chunk = list(queryset[offset:offset + chunk_size].iterator())
        if len(chunk) == 0:
            raise StopIteration
        else:
            yield chunk
            offset += chunk_size


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


def inputs4hcalc(calc_id, input_type=None):
    """
    Get all of the inputs for a given hazard calculation.

    :param int calc_id:
        ID of a :class:`HazardCalculation`.
    :param input_type:
        A valid input type (optional). Leave as `None` if you want all inputs
        for a given calculation.
    :returns:
        A list of :class:`Input` instances.
    """
    result = Input.objects.filter(input2hcalc__hazard_calculation=calc_id)
    if input_type is not None:
        result = result.filter(input_type=input_type)
    return result


def inputs4rcalc(calc_id, input_type=None):
    """
    Get all of the inputs for a given risk calculation.

    :param int calc_id:
        ID of a :class:`RiskCalculation`.
    :param input_type:
        A valid input type (optional). Leave as `None` if you want all inputs
        for a given calculation.
    :returns:
        A list of :class:`Input` instances.
    """
    result = Input.objects.filter(input2rcalc__risk_calculation=calc_id)
    if input_type is not None:
        result = result.filter(input_type=input_type)
    return result


## Tables in the 'admin' schema.


class Organization(djm.Model):
    '''
    Organizations for grouping users
    '''
    name = djm.TextField()
    address = djm.TextField(null=True)
    url = djm.TextField(null=True)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'admin\".\"organization'


class OqUser(djm.Model):
    '''
    OpenQuake users
    '''
    user_name = djm.TextField()
    full_name = djm.TextField()
    organization = djm.ForeignKey('Organization')
    data_is_open = djm.BooleanField(default=True)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    def __str__(self):
        return "%s||%s" % (self.user_name, self.organization.id)

    class Meta:
        db_table = 'admin\".\"oq_user'


class RevisionInfo(djm.Model):
    '''
    Revision information
    '''
    artefact = djm.TextField(unique=True)
    revision = djm.TextField()
    step = djm.IntegerField(default=0)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'admin\".\"revision_info'


## Tables in the 'eqcat' schema.


class Catalog(djm.Model):
    '''
    Earthquake catalog
    '''
    owner = djm.ForeignKey('OqUser')
    eventid = djm.IntegerField()
    agency = djm.TextField()
    identifier = djm.TextField()
    time = djm.DateTimeField()
    time_error = djm.FloatField()
    depth = djm.FloatField()
    depth_error = djm.FloatField()
    EVENT_CLASS_CHOICES = (
        (u'aftershock', u'Aftershock'),
        (u'foreshock', u'Foreshock'),
    )
    event_class = djm.TextField(null=True, choices=EVENT_CLASS_CHOICES)
    magnitude = djm.ForeignKey('Magnitude')
    surface = djm.ForeignKey('Surface')
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)
    point = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'eqcat\".\"catalog'


class Magnitude(djm.Model):
    '''
    Earthquake event magnitudes
    '''
    mb_val = djm.FloatField(null=True)
    mb_val_error = djm.FloatField(null=True)
    ml_val = djm.FloatField(null=True)
    ml_val_error = djm.FloatField(null=True)
    ms_val = djm.FloatField(null=True)
    ms_val_error = djm.FloatField(null=True)
    mw_val = djm.FloatField(null=True)
    mw_val_error = djm.FloatField(null=True)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'eqcat\".\"magnitude'


class Surface(djm.Model):
    '''
    Earthquake event surface (ellipse with an angle)
    '''
    semi_minor = djm.FloatField()
    semi_major = djm.FloatField()
    strike = djm.FloatField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'eqcat\".\"surface'


## Tables in the 'hzrdi' (Hazard Input) schema.


class ParsedSource(djm.Model):
    """Stores parsed hazard input model sources in serialized python object
       tree format."""
    input = djm.ForeignKey('Input')
    SRC_TYPE_CHOICES = (
        (u'area', u'Area'),
        (u'point', u'Point'),
        (u'complex', u'Complex'),
        (u'simple', u'Simple'),
    )
    source_type = djm.TextField(choices=SRC_TYPE_CHOICES)
    nrml = fields.PickleField(help_text="NRML object representing the source")
    polygon = djm.PolygonField(
        srid=DEFAULT_SRID, dim=2,
        help_text=('The surface projection (2D) of the "rupture enclosing" '
                   'polygon for each source. This is relevant to all source '
                   'types, including point sources. When considering a '
                   'parsed_source record given a minimum integration distance,'
                   ' use this polygon in distance calculations.')
    )

    class Meta:
        db_table = 'hzrdi\".\"parsed_source'


class SiteModel(djm.Model):
    '''
     A model for site-specific parameters.

    Used in Hazard calculations.
    '''

    input = djm.ForeignKey('Input')
    # Average shear wave velocity for top 30 m. Units m/s.
    vs30 = djm.FloatField()
    # 'measured' or 'inferred'. Identifies if vs30 value has been measured or
    # inferred.
    vs30_type = djm.TextField(choices=VS30_TYPE_CHOICES)
    # Depth to shear wave velocity of 1.0 km/s. Units m.
    z1pt0 = djm.FloatField()
    # Depth to shear wave velocity of 2.5 km/s. Units km.
    z2pt5 = djm.FloatField()
    location = djm.PointField(srid=DEFAULT_SRID)

    def __repr__(self):
        return (
            'SiteModel(location="%s", vs30=%s, vs30_type=%s, z1pt0=%s, '
            'z2pt5=%s)'
            % (self.location.wkt, self.vs30, self.vs30_type, self.z1pt0,
               self.z2pt5))

    class Meta:
        db_table = 'hzrdi\".\"site_model'


class ParsedRupture(djm.Model):
    """Stores parsed hazard rupture model in serialized python object
       tree format."""
    input = djm.ForeignKey('Input')
    RUPTURE_TYPE_CHOICES = (
        (u'complex_fault', u'Complex Fault'),
        (u'simple_fault', u'Simple Fault'),)
    rupture_type = djm.TextField(choices=RUPTURE_TYPE_CHOICES)
    nrml = fields.PickleField(help_text="NRML object representing the rupture"
                                        " model")

    class Meta:
        db_table = 'hzrdi\".\"parsed_rupture_model'


## Tables in the 'uiapi' schema.


class Upload(djm.Model):
    '''
    A batch of OpenQuake input files uploaded by the user
    '''
    owner = djm.ForeignKey('OqUser')
    description = djm.TextField(default='')
    path = djm.TextField(unique=True)
    STATUS_CHOICES = (
        (u'pending', u'Pending'),
        (u'running', u'Running'),
        (u'failed', u'Failed'),
        (u'succeeded', u'Succeeded'),
    )
    status = djm.TextField(choices=STATUS_CHOICES, default='pending')
    job_pid = djm.IntegerField(default=0)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"upload'


class Input(djm.Model):
    '''
    A single OpenQuake input file uploaded by the user.
    '''
    owner = djm.ForeignKey('OqUser')
    model_content = djm.ForeignKey('ModelContent')
    name = djm.TextField(null=True)
    digest = djm.TextField(help_text="32 byte md5sum digest, used to "
                                     "detect identical input model files")
    path = djm.TextField()
    INPUT_TYPE_CHOICES = (
        (u'unknown', u'Unknown'),
        (u'source', u'Source Model'),
        (u'lt_source', u'Source Model Logic Tree'),
        (u'lt_gsim', u'Ground Shaking Intensity Model Logic Tree'),
        (u'exposure', u'Exposure'),
        (u'fragility', u'Fragility'),
        (u'vulnerability', u'Vulnerability'),
        (u'vulnerability_retrofitted', u'Vulnerability Retroffited'),
        (u'site_model', u'Site Model'),
        (u'rupture_model', u'Rupture Model')
    )
    input_type = djm.TextField(choices=INPUT_TYPE_CHOICES)

    hazard_calculations = djm.ManyToManyField('HazardCalculation',
                                              through='Input2hcalc')
    risk_calculations = djm.ManyToManyField(
        'RiskCalculation', through='Input2rcalc', related_name="inputs")

    # Number of bytes in the file:
    size = djm.IntegerField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    def __str__(self):
        path_suffix = "/".join(self.path.rsplit(os.sep, 2)[1:])
        return "%s||%s||%s||%s" % (
            self.id, self.input_type, self.digest[:16], path_suffix)

    class Meta:
        db_table = 'uiapi\".\"input'


class ModelContent(djm.Model):
    '''
    Stores raw content for the various input model files.
    '''

    # contains the raw text of an input file
    raw_content = djm.TextField()
    # `content_type` should be used to indicate the file format
    # (xml, csv, etc.)
    content_type = djm.TextField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"model_content'

    @property
    def raw_content_ascii(self):
        """
        Returns raw_content in ASCII
        """
        return str(self.raw_content)


class Input2job(djm.Model):
    '''
    Associates input model files and jobs.
    '''
    input = djm.ForeignKey('Input')
    oq_job = djm.ForeignKey('OqJob')

    class Meta:
        db_table = 'uiapi\".\"input2job'


class Src2ltsrc(djm.Model):
    '''
    Associate an "lt_source" type input (a logic tree source) with "source"
    type inputs (hazard sources referenced by the logic tree source).
    This is needed for worker-side logic tree processing.
    '''
    hzrd_src = djm.ForeignKey("Input", related_name='+',
                              help_text="Hazard source input referenced "
                                        "by the logic tree source")
    lt_src = djm.ForeignKey("Input", related_name='+',
                            help_text="Logic tree source input")
    filename = djm.TextField(
        help_text="Name of the referenced hazard source file")

    class Meta:
        db_table = 'uiapi\".\"src2ltsrc'


class Input2upload(djm.Model):
    '''
    Associates input model files and uploads.
    '''
    input = djm.ForeignKey('Input')
    upload = djm.ForeignKey('Upload')

    class Meta:
        db_table = 'uiapi\".\"input2upload'


class OqJob(djm.Model):
    '''
    An OpenQuake engine run started by the user
    '''
    owner = djm.ForeignKey('OqUser')
    hazard_calculation = djm.ForeignKey('HazardCalculation', null=True)
    risk_calculation = djm.ForeignKey('RiskCalculation', null=True)
    LOG_LEVEL_CHOICES = (
        (u'debug', u'Debug'),
        (u'info', u'Info'),
        (u'progress', u'Progress'),
        (u'warn', u'Warn'),
        (u'error', u'Error'),
        (u'critical', u'Critical'),
    )
    log_level = djm.TextField(choices=LOG_LEVEL_CHOICES, default='progress')
    STATUS_CHOICES = (
        (u'pre_executing', u'Pre-Executing'),
        (u'executing', u'Executing'),
        (u'post_executing', u'Post-Executing'),
        (u'post_processing', u'Post-Processing'),
        (u'export', u'Exporting results'),
        (u'clean_up', u'Cleaning up'),
        (u'complete', u'Complete'),
    )
    status = djm.TextField(choices=STATUS_CHOICES, default='pre_executing')
    oq_version = djm.TextField(null=True, blank=True)
    nhlib_version = djm.TextField(null=True, blank=True)
    nrml_version = djm.TextField(null=True, blank=True)
    is_running = djm.BooleanField(default=False)
    duration = djm.IntegerField(default=0)
    job_pid = djm.IntegerField(default=0)
    supervisor_pid = djm.IntegerField(default=0)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"oq_job'


class JobStats(djm.Model):
    '''
    Capture various statistics about a job.
    '''
    oq_job = djm.ForeignKey('OqJob')
    start_time = djm.DateTimeField(editable=False, default=datetime.utcnow)
    stop_time = djm.DateTimeField(editable=False)
    # The number of total sites in job
    num_sites = djm.IntegerField(null=True)
    # The total number of tasks in a job
    num_tasks = djm.IntegerField(null=True)
    # The number of logic tree samples
    # (for hazard jobs of all types except scenario)
    num_realizations = djm.IntegerField(null=True)

    class Meta:
        db_table = 'uiapi\".\"job_stats'


class JobPhaseStats(djm.Model):
    '''
    Capture when the various job phases started.
    '''
    oq_job = djm.ForeignKey('OqJob')
    # calculation type (hazard|risk)
    ctype = djm.TextField()
    job_status = djm.TextField()
    start_time = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"job_phase_stats'


class CNodeStats(djm.Model):
    '''
    Captures the compute node status (changes).
    '''
    oq_job = djm.ForeignKey('OqJob')
    node = djm.TextField(help_text="Compute node name")
    STATUS_CHOICES = (
        (u"up", u"Compute node available"),
        (u"down", u"Compute node unavailable"),
    )
    current_status = djm.TextField(
        choices=STATUS_CHOICES, help_text="Current compute node status")

    # Please note: the time stamps are managed by triggers, no need to set
    # them manually
    current_ts = djm.DateTimeField(editable=False, default=datetime.utcnow)
    previous_ts = djm.DateTimeField(null=True)

    failures = djm.IntegerField(
        help_text="Number of up -> down status changes", default=0)

    class Meta:
        db_table = 'uiapi\".\"cnode_stats'


class Job2profile(djm.Model):
    '''
    Associates jobs with their profiles.
    '''
    oq_job = djm.ForeignKey('OqJob')
    oq_job_profile = djm.ForeignKey('OqJobProfile')

    class Meta:
        db_table = 'uiapi\".\"job2profile'


class HazardCalculation(djm.Model):
    '''
    Parameters needed to run a Hazard job.
    '''
    owner = djm.ForeignKey('OqUser')
    # Contains the absolute path to the directory containing the job config
    # file.
    base_path = djm.TextField()
    export_dir = djm.TextField(null=True, blank=True)
    force_inputs = djm.BooleanField()

    #####################
    # General parameters:
    #####################

    # A description for this config profile which is meaningful to a user.
    description = djm.TextField(default='', blank=True)

    # The timeout is stored in seconds and is 1 hour by default.
    no_progress_timeout = djm.IntegerField(
        default=3600, help_text="what time period w/o any progress is "
                                "acceptable for calculations?")
    CALC_MODE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'event_based', u'Probabilistic Event-Based'),
        (u'disaggregation', u'Disaggregation'),
        (u'scenario', u'Scenario'),
    )
    calculation_mode = djm.TextField(choices=CALC_MODE_CHOICES)
    # For the calculation geometry, choose either `region` (with
    # `region_grid_spacing`) or `sites`.
    region = djm.PolygonField(srid=DEFAULT_SRID, null=True, blank=True)
    # Discretization parameter for a `region`. Units in degrees.
    region_grid_spacing = djm.FloatField(null=True, blank=True)
    # The points of interest for a calculation.
    sites = djm.MultiPointField(srid=DEFAULT_SRID, null=True, blank=True)

    ########################
    # Logic Tree parameters:
    ########################
    random_seed = djm.IntegerField()
    number_of_logic_tree_samples = djm.IntegerField(null=True, blank=True)

    ###############################################
    # ERF (Earthquake Rupture Forecast) parameters:
    ###############################################
    rupture_mesh_spacing = djm.FloatField(
        help_text=('Rupture mesh spacing (in kilometers) for simple/complex '
                   'fault sources rupture discretization'),
        null=True,
        blank=True,

    )
    width_of_mfd_bin = djm.FloatField(
        help_text=('Truncated Gutenberg-Richter MFD (Magnitude Frequency'
                   'Distribution) bin width'),
        null=True,
        blank=True,
    )
    area_source_discretization = djm.FloatField(
        help_text='Area Source Disretization, in kilometers',
        null=True,
        blank=True,
    )

    ##################
    # Site parameters:
    ##################
    # If there is no `site_model`, these 4 parameters must be specified:
    reference_vs30_value = djm.FloatField(
        help_text='Shear wave velocity in the uppermost 30 m. In m/s.',
        null=True,
        blank=True,
    )
    VS30_TYPE_CHOICES = (
        (u'measured', u'Measured'),
        (u'inferred', u'Inferred'),
    )
    reference_vs30_type = djm.TextField(
        choices=VS30_TYPE_CHOICES,
        null=True,
        blank=True,
    )
    reference_depth_to_2pt5km_per_sec = djm.FloatField(
        help_text='Depth to where shear-wave velocity = 2.5 km/sec. In km.',
        null=True,
        blank=True,
    )
    reference_depth_to_1pt0km_per_sec = djm.FloatField(
        help_text='Depth to where shear-wave velocity = 1.0 km/sec. In m.',
        null=True,
        blank=True,
    )

    #########################
    # Calculation parameters:
    #########################
    investigation_time = djm.FloatField(
        help_text=('Time span (in years) for probability of exceedance '
                   'calculation'),
        null=True,
        blank=True,
    )
    intensity_measure_types_and_levels = fields.DictField(
        help_text=(
            'Dictionary containing for each intensity measure type ("PGA", '
            '"PGV", "PGD", "SA", "IA", "RSD", "MMI"), the list of intensity '
            'measure levels for calculating probability of exceedence'),
        null=True,
        blank=True,
    )
    truncation_level = djm.FloatField(
        help_text='Level for ground motion distribution truncation',
        null=True,
        blank=True
    )
    maximum_distance = djm.FloatField(
        help_text=('Maximum distance (in km) of sources to be considered in '
                   'the probability of exceedance calculation. Sources more '
                   'than this distance away (from the sites of interest) are '
                   'ignored.'),
    )

    ################################
    # Event-Based Calculator params:
    ################################
    intensity_measure_types = fields.CharArrayField(
        help_text=(
            'List of intensity measure types (input for GMF calculation)'),
        null=True,
        blank=True,
    )
    ses_per_logic_tree_path = djm.IntegerField(
        help_text=('Number of Stochastic Event Sets to compute per logic tree'
                   ' branch (enumerated or randomly sampled'),
        null=True,
        blank=True,
    )
    GROUND_MOTION_CORRELATION_MODELS = (
        (u'JB2009', u'Jayaram-Baker 2009'),
    )
    ground_motion_correlation_model = djm.TextField(
        help_text=('Name of the ground correlation model to use in the'
                   ' calculation'),
        null=True,
        blank=True,
        choices=GROUND_MOTION_CORRELATION_MODELS,
    )
    ground_motion_correlation_params = fields.DictField(
        help_text=('Parameters specific to the chosen ground motion'
                   ' correlation model'),
        null=True,
        blank=True,
    )

    ###################################
    # Disaggregation Calculator params:
    ###################################
    mag_bin_width = djm.FloatField(
        help_text=('Width of magnitude bins, which ultimately defines the size'
                   ' of the magnitude dimension of a disaggregation matrix'),
        null=True,
        blank=True,
    )
    distance_bin_width = djm.FloatField(
        help_text=('Width of distance bins, which ultimately defines the size'
                   ' of the distance dimension of a disaggregation matrix'),
        null=True,
        blank=True,
    )
    coordinate_bin_width = djm.FloatField(
        help_text=('Width of coordinate bins, which ultimately defines the'
                   ' size of the longitude and latitude dimensions of a'
                   ' disaggregation matrix'),
        null=True,
        blank=True,
    )
    num_epsilon_bins = djm.IntegerField(
        help_text=('Number of epsilon bins, which defines the size of the'
                   ' epsilon dimension of a disaggregation matrix'),
        null=True,
        blank=True,
    )
    ################################
    # Scenario Calculator params:
    ################################
    gsim = djm.TextField(
        help_text=('Name of the ground shaking intensity model to use in the '
                   'calculation'),
        null=True,
        blank=True,
    )
    number_of_ground_motion_fields = djm.IntegerField(
        null=True,
        blank=True,
    )
    poes_disagg = fields.FloatArrayField(
        help_text=('The probabilities of exceedance for which we interpolate'
                   ' grond motion values from hazard curves. This GMV is used'
                   ' as input for computing disaggregation histograms'),
        null=True,
        blank=True,
    )

    ################################
    # Output/post-processing params:
    ################################
    # Classical params:
    ###################
    mean_hazard_curves = fields.OqNullBooleanField(
        help_text='Compute mean hazard curves',
        null=True,
        blank=True,
    )
    quantile_hazard_curves = fields.FloatArrayField(
        help_text='Compute quantile hazard curves',
        null=True,
        blank=True,
    )
    poes_hazard_maps = fields.FloatArrayField(
        help_text=('PoEs (probabilities of exceedence) to be used for '
                   'computing hazard maps (from individual curves, mean and '
                   'quantile curves if calculated)'),
        null=True,
        blank=True,
    )
    # Event-Based params:
    #####################
    complete_logic_tree_ses = fields.OqNullBooleanField(
        help_text=('If true, generate a collection of all of the stochastic '
                   'event sets for all logic tree samples with an adjusted '
                   'investgation time'),
        null=True,
        blank=True,
    )
    complete_logic_tree_gmf = fields.OqNullBooleanField(
        help_text=(
            'If true, generate a collection of all of the GMFs for all'
            ' logic tree branches with an adjusted investigation time.'),
        null=True,
        blank=True,
    )
    ground_motion_fields = fields.OqNullBooleanField(
        help_text=('If true, ground motion fields will be computed (in '
                   'addition to stochastic event sets)'),
        null=True,
        blank=True,
    )
    hazard_curves_from_gmfs = fields.OqNullBooleanField(
        help_text=('If true, ground motion fields will be post-processed into '
                   'hazard curves.'),
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'uiapi\".\"hazard_calculation'

    def __init__(self, *args, **kwargs):
        kwargs = _prep_geometry(kwargs)
        super(HazardCalculation, self).__init__(*args, **kwargs)

    def individual_curves_per_location(self):
        """
        Returns the number of individual curves per location, that are
        expected after a full computation of the hazard calculation
        has been performed
        """
        realizations_nr = self.ltrealization_set.count()
        return realizations_nr

    def should_compute_mean_curves(self):
        """
        Return True if mean curve calculation has been requested
        """
        return self.mean_hazard_curves is True

    def should_compute_quantile_curves(self):
        """
        Return True if quantile curve calculation has been requested
        """
        return (self.quantile_hazard_curves is not None
                and len(self.quantile_hazard_curves) > 0)

    def should_consider_weights_in_aggregates(self):
        """
        Return True if the calculation of aggregate result should
        consider the weight of the individual curves
        """
        return not (
            self.number_of_logic_tree_samples > 0)

    def points_to_compute(self):
        """
        Generate a :class:`~nhlib.geo.mesh.Mesh` of points. These points
        indicate the locations of interest in a hazard calculation.

        The mesh can be calculated given a `region` polygon and
        `region_grid_spacing` (the discretization parameter), or from a list of
        `sites`.
        """
        if self.region is not None and self.region_grid_spacing is not None:
            # assume that the polygon is a single linear ring
            coords = self.region.coords[0]
            points = [nhlib_geo.Point(*x) for x in coords]
            poly = nhlib_geo.Polygon(points)
            return poly.discretize(self.region_grid_spacing)
        elif self.sites is not None:
            lons, lats = zip(*self.sites.coords)
            return nhlib_geo.Mesh(
                numpy.array(lons), numpy.array(lats), depths=None)
        else:
            # there's no geometry defined
            return None


class RiskCalculation(djm.Model):
    '''
    Parameters needed to run a Risk job.
    '''
    owner = djm.ForeignKey('OqUser')
    # Contains the absolute path to the directory containing the job config
    # file.
    base_path = djm.TextField()
    export_dir = djm.TextField(null=True, blank=True)
    force_inputs = djm.BooleanField()

    #####################
    # General parameters:
    #####################

    # A description for this config profile which is meaningful to a user.
    description = djm.TextField(default='', blank=True)

    # The timeout is stored in seconds and is 1 hour by default.
    no_progress_timeout = djm.IntegerField(
        default=3600, help_text="what time period w/o any progress is "
                                "acceptable for calculations?")

    CALC_MODE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'classical_bcr', u'Classical BCR'),
        (u'event_based', u'Probabilistic Event-Based'),
        # TODO(LB): Enable these once calculators are supported and
        # implemented.
        # (u'scenario', u'Scenario'),
        # (u'scenario_damage', u'Scenario Damage'),
        (u'event_based_bcr', u'Probabilistic Event-Based BCR'),
    )
    calculation_mode = djm.TextField(choices=CALC_MODE_CHOICES)
    region_constraint = djm.PolygonField(
        srid=DEFAULT_SRID, null=True, blank=True)

    # the hazard output (it can point to an HazardCurve or to a
    # GmfSet) used by the risk calculation
    hazard_output = djm.ForeignKey("Output", null=False, blank=False)

    # A seed used to generate random values to be applied to
    # vulnerability functions
    master_seed = djm.IntegerField(null=True, blank=True)

    ##################################
    # Probabilistic shared parameters
    ##################################
    ASSET_CORRELATION_CHOICES = (
        (u'perfect', u'Perfect'),
        (u'uncorrelated', u'Uncorrelated'),
    )
    asset_correlation = djm.TextField(null=True, blank=True,
                                      choices=ASSET_CORRELATION_CHOICES)

    #######################
    # Classical parameters:
    #######################
    lrem_steps_per_interval = djm.IntegerField(null=True, blank=True)
    conditional_loss_poes = fields.FloatArrayField(null=True, blank=True)

    #########################
    # Event-Based parameters:
    #########################
    loss_curve_resolution = djm.IntegerField(
        null=False, blank=True, default=DEFAULT_LOSS_CURVE_RESOLUTION)
    insured_losses = djm.NullBooleanField(null=True, blank=True, default=False)

    ######################################
    # BCR (Benefit-Cost Ratio) parameters:
    ######################################
    interest_rate = djm.FloatField(null=True, blank=True)
    asset_life_expectancy = djm.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'uiapi\".\"risk_calculation'

    def __init__(self, *args, **kwargs):
        kwargs = _prep_geometry(kwargs)
        super(RiskCalculation, self).__init__(*args, **kwargs)

    @property
    def hazard_calculation(self):
        """
        :returns: the hazard calculation associated with the hazard
        output used as input in risk calculation
        """
        return self.hazard_output.oq_job.hazard_calculation

    @property
    def hazard_statistics(self):
        """
        The hazard statistics value (mean/quantile and quantile value
        if applicable) associated with the hazard output used by this
        risk calculation
        """
        if self.hazard_output.is_hazard_curve():
            return (self.hazard_output.hazardcurve.statistics,
                    self.hazard_output.hazardcurve.quantile)
        else:
            return None, None  # no mean/quantile for gmf

    @property
    def hazard_logic_tree_paths(self):
        """
        The logic tree paths associated with the hazard output used by
        this risk calculation
        """
        if self.hazard_output.is_hazard_curve():
            lt = self.hazard_output.hazardcurve.lt_realization
        else:
            lt = self.hazard_output.gmfcollection.lt_realization
        return lt.sm_lt_path, lt.gsim_lt_path

    @property
    def is_bcr(self):
        return self.calculation_mode in ['classical_bcr', 'event_based_bcr']

    @property
    def exposure_model(self):
        return self.inputs.get(input_type="exposure").exposuremodel


def _prep_geometry(kwargs):
    """
    Helper function to convert geometry specified in a job config file to WKT,
    so that it can save to the database in a geometry field.

    :param dict kwargs:
        `dict` representing some keyword arguments, which may contain geometry
        definitions in some sort of string or list form

    :returns:
        The modified ``kwargs``, with WKT to replace the input geometry
        definitions.
    """
    # If geometries were specified as string lists of coords,
    # convert them to WKT before doing anything else.
    for field, wkt_fmt in (('sites', 'MULTIPOINT(%s)'),
                           ('region', 'POLYGON((%s))'),
                           ('region_constraint', 'POLYGON((%s))')):
        if field in kwargs:
            geom = kwargs[field]
            try:
                wkt.loads(geom)
                # if this succeeds, we know the wkt is at least valid
                # we don't know the geometry type though; we'll leave that
                # to subsequent validation
            except wkt.ReadingError:
                try:
                    coords = [
                        float(x) for x in fields.ARRAY_RE.split(geom)
                    ]
                except ValueError:
                    raise ValueError(
                        'Could not coerce `str` to a list of `float`s'
                    )
                else:
                    if not len(coords) % 2 == 0:
                        raise ValueError(
                            'Got an odd number of coordinate values'
                        )
                    else:
                        # Construct WKT from the coords
                        # NOTE: ordering is expected to be lon,lat
                        points = ['%s %s' % (coords[i], coords[i + 1])
                                  for i in xrange(0, len(coords), 2)]
                        # if this is the region, close the linear polygon
                        # ring by appending the first coord to the end
                        if field in ('region', 'region_constraint'):
                            points.append(points[0])
                        # update the field
                        kwargs[field] = wkt_fmt % ', '.join(points)

    # return the (possbily) modified kwargs
    return kwargs


class Input2hcalc(djm.Model):
    '''
    `input` to `hazard_calculation` link table.
    '''

    input = djm.ForeignKey('Input')
    hazard_calculation = djm.ForeignKey('HazardCalculation')

    class Meta:
        db_table = 'uiapi\".\"input2hcalc'


class Input2rcalc(djm.Model):
    '''
    `input` to `risk_calculation` link table.
    '''

    input = djm.ForeignKey('Input')
    risk_calculation = djm.ForeignKey('RiskCalculation')

    class Meta:
        db_table = 'uiapi\".\"input2rcalc'


class OqJobProfile(djm.Model):
    '''
    Parameters needed to run an OpenQuake job
    '''
    owner = djm.ForeignKey('OqUser')
    description = djm.TextField(default='')
    force_inputs = djm.BooleanField(
        default=False, help_text="whether the model inputs should be parsed "
        "and their content be written to the db no matter what")
    CALC_MODE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'event_based', u'Probabilistic Event-Based'),
        (u'scenario', u'Scenario'),
        (u'scenario_damage', u'Scenario Damage'),
        (u'disaggregation', u'Disaggregation'),
        (u'uhs', u'UHS'),  # Uniform Hazard Spectra
        # Benefit-cost ratio calculator based on Classical PSHA risk calc
        (u'classical_bcr', u'Classical BCR'),
        # Benefit-cost ratio calculator based on Event Based risk calc
        (u'event_based_bcr', u'Probabilistic Event-Based BCR'),
    )
    calc_mode = djm.TextField(choices=CALC_MODE_CHOICES)
    job_type = fields.CharArrayField()
    min_magnitude = djm.FloatField(null=True)
    investigation_time = djm.FloatField(null=True)
    COMPONENT_CHOICES = (
        (u'average', u'Average horizontal'),
        (u'gmroti50', u'Average horizontal (GMRotI50)'),
    )
    component = djm.TextField(choices=COMPONENT_CHOICES)
    IMT_CHOICES = (
        (u'pga', u'Peak Ground Acceleration'),
        (u'sa', u'Spectral Acceleration'),
        (u'pgv', u'Peak Ground Velocity'),
        (u'pgd', u'Peak Ground Displacement'),
        (u'ia', u'Arias Intensity'),
        (u'rsd', u'Relative Significant Duration'),
        (u'mmi', u'Modified Mercalli Intensity'),
    )
    imt = djm.TextField(choices=IMT_CHOICES)
    period = djm.FloatField(null=True)
    damping = djm.FloatField(null=True)
    TRUNC_TYPE_CHOICES = (
        (u'none', u'None'),
        (u'onesided', u'One-sided'),
        (u'twosided', u'Two-sided'),
    )
    truncation_type = djm.TextField(choices=TRUNC_TYPE_CHOICES)
    # TODO(LB): We should probably find out why (from a science perspective)
    # the default is 3.0 and document it. I definitely don't remember why it's
    # 3.0.
    truncation_level = djm.FloatField(default=3.0)
    reference_vs30_value = djm.FloatField(
        "Average shear-wave velocity in the upper 30 meters of a site")
    imls = fields.FloatArrayField(null=True)
    poes = fields.FloatArrayField(null=True)
    realizations = djm.IntegerField(null=True)
    histories = djm.IntegerField(null=True)
    gm_correlated = djm.NullBooleanField(null=True)
    gmf_calculation_number = djm.IntegerField(null=True)
    rupture_surface_discretization = djm.FloatField(null=True)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    # We can specify a (region and region_grid_spacing) or sites, but not both.
    region = djm.PolygonField(srid=DEFAULT_SRID, null=True)
    region_grid_spacing = djm.FloatField(null=True)
    sites = djm.MultiPointField(srid=DEFAULT_SRID, null=True)

    area_source_discretization = djm.FloatField(null=True)
    area_source_magnitude_scaling_relationship = djm.TextField(null=True)

    ASSET_CORRELATION_CHOICES = (
        (u'perfect', u'Perfect'),
        (u'uncorrelated', u'Uncorrelated'),
    )
    asset_correlation = djm.TextField(null=True,
                                      choices=ASSET_CORRELATION_CHOICES)
    compute_mean_hazard_curve = djm.NullBooleanField(null=True)
    conditional_loss_poe = fields.FloatArrayField(null=True)
    fault_magnitude_scaling_relationship = djm.TextField(null=True)
    fault_magnitude_scaling_sigma = djm.FloatField(null=True)
    fault_rupture_offset = djm.FloatField(null=True)
    fault_surface_discretization = djm.FloatField(null=True)
    gmf_random_seed = djm.IntegerField(null=True)
    gmpe_lt_random_seed = djm.IntegerField(null=True)
    gmpe_model_name = djm.TextField(null=True)
    grid_source_magnitude_scaling_relationship = djm.TextField(null=True)
    include_area_sources = djm.NullBooleanField(null=True)
    include_fault_source = djm.NullBooleanField(null=True)
    include_grid_sources = djm.NullBooleanField(null=True)
    include_subduction_fault_source = djm.NullBooleanField(null=True)
    lrem_steps_per_interval = djm.IntegerField(null=True)
    loss_curves_output_prefix = djm.TextField(null=True)
    # Only used for Event-Based Risk calculations.
    loss_histogram_bins = djm.IntegerField(null=True)
    maximum_distance = djm.FloatField(null=True)
    quantile_levels = fields.FloatArrayField(null=True)
    reference_depth_to_2pt5km_per_sec_param = djm.FloatField(null=True)
    rupture_aspect_ratio = djm.FloatField(null=True)
    RUPTURE_FLOATING_TYPE_CHOICES = (
        ('alongstrike', 'Only along strike ( rupture full DDW)'),
        ('downdip', 'Along strike and down dip'),
        ('centereddowndip', 'Along strike & centered down dip'),
    )
    rupture_floating_type = djm.TextField(
        null=True, choices=RUPTURE_FLOATING_TYPE_CHOICES)
    SADIGH_SITE_TYPE_CHOICES = (
        ('rock', 'Rock'),
        ('deepsoil', 'Deep-Soil'),
    )
    sadigh_site_type = djm.TextField(
        null=True, choices=SADIGH_SITE_TYPE_CHOICES)
    source_model_lt_random_seed = djm.IntegerField(null=True)
    STANDARD_DEVIATION_TYPE_CHOICES = (
        ('total', 'Total'),
        ('interevent', 'Inter-Event'),
        ('intraevent', 'Intra-Event'),
        ('zero', 'None (zero)'),
        ('total_mag_dependent', 'Total (Mag Dependent)'),
        ('total_pga_dependent', 'Total (PGA Dependent)'),
        ('intraevent_mag_dependent', 'Intra-Event (Mag Dependent)'),
    )
    standard_deviation_type = djm.TextField(
        null=True, choices=STANDARD_DEVIATION_TYPE_CHOICES)
    subduction_fault_magnitude_scaling_relationship = \
        djm.TextField(null=True)
    subduction_fault_magnitude_scaling_sigma = djm.FloatField(null=True)
    subduction_fault_rupture_offset = djm.FloatField(null=True)
    subduction_fault_surface_discretization = djm.FloatField(null=True)
    subduction_rupture_aspect_ratio = djm.FloatField(null=True)
    subduction_rupture_floating_type = djm.TextField(
        null=True, choices=RUPTURE_FLOATING_TYPE_CHOICES)
    SOURCE_AS_CHOICES = (
        ('pointsources', 'Point Sources'),
        ('linesources', 'Line Sources (random or given strike)'),
        ('crosshairsources', 'Cross Hair Line Sources'),
        ('16spokedsources', '16 Spoked Line Sources'),
    )
    treat_area_source_as = djm.TextField(
        null=True, choices=SOURCE_AS_CHOICES)
    treat_grid_source_as = djm.TextField(
        null=True, choices=SOURCE_AS_CHOICES)
    width_of_mfd_bin = djm.FloatField(null=True)

    # The following bin limits fields are for the Disaggregation calculator
    # only:
    lat_bin_limits = fields.FloatArrayField(null=True)
    lon_bin_limits = fields.FloatArrayField(null=True)
    mag_bin_limits = fields.FloatArrayField(null=True)
    epsilon_bin_limits = fields.FloatArrayField(null=True)
    distance_bin_limits = fields.FloatArrayField(null=True)
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
    disagg_results = fields.CharArrayField(null=True)
    uhs_periods = fields.FloatArrayField(null=True)
    vs30_type = djm.TextField(choices=VS30_TYPE_CHOICES, default="measured",
                              null=True)
    depth_to_1pt_0km_per_sec = djm.FloatField(default=100.0)
    asset_life_expectancy = djm.FloatField(null=True)
    interest_rate = djm.FloatField(null=True)

    class Meta:
        db_table = 'uiapi\".\"oq_job_profile'


class OutputManager(djm.Manager):
    """
    Manager class to filter and create Output objects
    """
    def create_output(self, job, display_name, output_type):
        """
        Create an output for the given `job`, `display_name` and
        `output_type` (default to hazard_curve)
        """
        return self.create(oq_job=job,
                           owner=job.owner,
                           display_name=display_name,
                           output_type=output_type)


class Output(djm.Model):
    '''
    A single artifact which is a result of an OpenQuake job.
    The data may reside in a file or in the database.
    '''
    owner = djm.ForeignKey('OqUser')
    oq_job = djm.ForeignKey('OqJob')
    display_name = djm.TextField()
    OUTPUT_TYPE_CHOICES = (
        (u'agg_loss_curve', u'Aggregate Loss Curve'),
        (u'bcr_distribution', u'Benefit-cost ratio distribution'),
        (u'collapse_map', u'Collapse map'),
        (u'complete_lt_gmf', u'Complete Logic Tree GMF'),
        (u'complete_lt_ses', u'Complete Logic Tree SES'),
        (u'disagg_matrix', u'Disaggregation Matrix'),
        (u'dmg_dist_per_asset', u'Damage Distribution Per Asset'),
        (u'dmg_dist_per_taxonomy', u'Damage Distribution Per Taxonomy'),
        (u'dmg_dist_total', u'Total Damage Distribution'),
        (u'gmf', u'Ground Motion Field'),
        (u'gmf_scenario', u'Ground Motion Field by Scenario Calculator'),
        (u'hazard_curve', u'Hazard Curve'),
        (u'hazard_map', u'Hazard Map'),
        (u'ins_loss_curve', u'Insured Loss Curve'),
        (u'loss_curve', u'Loss Curve'),
        (u'loss_map', u'Loss Map'),
        (u'ses', u'Stochastic Event Set'),
        (u'uh_spectra', u'Uniform Hazard Spectra'),
        (u'unknown', u'Unknown'),
    )
    output_type = djm.TextField(choices=OUTPUT_TYPE_CHOICES)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    objects = OutputManager()

    def __str__(self):
        return "%d||%s||%s" % (self.id, self.output_type, self.display_name)

    class Meta:
        db_table = 'uiapi\".\"output'

    def is_ground_motion_field(self):
        return self.output_type in ['gmf', 'complete_lt_gmf']

    def is_hazard_curve(self):
        return self.output_type == 'hazard_curve'


class ErrorMsg(djm.Model):
    '''
    Error information associated with a job failure
    '''
    oq_job = djm.ForeignKey('OqJob')
    brief = djm.TextField()
    detailed = djm.TextField()

    class Meta:
        db_table = 'uiapi\".\"error_msg'


## Tables in the 'hzrdr' schema.


class HazardMap(djm.Model):
    '''
    Hazard Map header (information which pertains to entire map)
    '''
    output = djm.ForeignKey('Output')
    # FK only required for non-statistical results (i.e., mean or quantile
    # curves).
    lt_realization = djm.ForeignKey('LtRealization', null=True)
    investigation_time = djm.FloatField()
    imt = djm.TextField(choices=IMT_CHOICES)
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'quantile', u'Quantile'),
    )
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)
    poe = djm.FloatField()
    # lons, lats, and imls are stored as numpy arrays with a uniform size and
    # shape
    lons = fields.PickleField()
    lats = fields.PickleField()
    imls = fields.PickleField()

    class Meta:
        db_table = 'hzrdr\".\"hazard_map'


def parse_imt(imt):
    """
    Given an intensity measure type in long form (with attributes),
    return the intensity measure type, the sa_period and sa_damping
    """
    sa_period = None
    sa_damping = None
    if 'SA' in imt:
        match = re.match(r'^SA\(([^)]+?)\)$', imt)
        sa_period = float(match.group(1))
        sa_damping = DEFAULT_SA_DAMPING
        hc_im_type = 'SA'  # don't include the period
    else:
        hc_im_type = imt
    return hc_im_type, sa_period, sa_damping


class HazardCurveManager(djm.Manager):
    """
    Manager class to filter and create HazardCurve objects
    """

    def create_aggregate_curve(self, output, imt, statistics, quantile=None):
        """
        Create an aggregate curve with intensity measure type `imt`
        for the given `statistics` (default to mean) and `quantile`.
        Here imt is given in long form. e.g. SA(10)
        """
        if quantile and not statistics == "quantile":
            raise ValueError(
                "A quantile level can be specified only for quantile curves")

        hc = output.oq_job.hazard_calculation
        hc_im_type, sa_period, sa_damping = parse_imt(imt)
        levels = hc.intensity_measure_types_and_levels[imt]
        curve = self.create(output=output,
                            lt_realization=None,
                            investigation_time=hc.investigation_time,
                            imt=hc_im_type,
                            imls=levels,
                            statistics=statistics,
                            quantile=quantile,
                            sa_period=sa_period,
                            sa_damping=sa_damping)
        return curve


class HazardCurve(djm.Model):
    '''
    Hazard Curve header information
    '''
    output = djm.OneToOneField('Output', null=True)
    # FK only required for non-statistical results (i.e., mean or quantile
    # curves).
    lt_realization = djm.ForeignKey('LtRealization', null=True)
    investigation_time = djm.FloatField()
    imt = djm.TextField(choices=IMT_CHOICES)
    imls = fields.FloatArrayField()
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'quantile', u'Quantile'),
    )
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)

    objects = HazardCurveManager()

    class Meta:
        db_table = 'hzrdr\".\"hazard_curve'


class HazardCurveDataManager(djm.GeoManager):
    """
    Manager class to filter and create HazardCurveData objects
    """

    def individual_curves(self, job, imt):
        """
        Returns all the individual hazard curve data objects. If `imt`
        is given the results are filtered by intensity measure type.
        Here imt is given in the long format.
        """
        hc_im_type, sa_period, sa_damping = parse_imt(imt)

        query_args = {'hazard_curve__statistics__isnull': True,
                      'hazard_curve__output__oq_job': job,
                      'hazard_curve__output__output_type': "hazard_curve",
                      'hazard_curve__imt': hc_im_type,
                      'hazard_curve__sa_period': sa_period,
                      'hazard_curve__sa_damping': sa_damping}

        queryset = self.filter(**query_args)
        return queryset

    def individual_curves_ordered(self, job, imt):
        """
        Same as #individual_curves but the results are ordered by location
        """
        return self.individual_curves(job, imt).order_by('location')

    def individual_curves_nr(self, job, imt):
        """
        Returns the number of individual curves. If `imt` is given, it
        returns the number of individual curves with intensity measure
        type `imt`
        """
        return self.individual_curves(job, imt).count()

    def individual_curves_chunk(self, job, imt, offset, block_size):
        """
        Get a chunk of individual curves related to `job` with `imt`
        at offset `offset`. The size of the returned chunk is
        `block_size`. The results are augmented with the wkb
        representation of the location and the weight of the
        individual curve
        """
        base_queryset = self.individual_curves_ordered(job, imt)
        base_queryset = base_queryset.extra({
            'wkb': 'asBinary(location)',
        })
        values = base_queryset.values(
            'poes', 'wkb', 'hazard_curve__lt_realization__weight')

        return values[offset: block_size + offset]

    def individual_curves_chunks(self, job, imt, location_block_size=1):
        """
        Return a list of chunk of individual curves. A chunk is a
        tuple with all the ingredients needed to get a chunk of
        individual curves, i.e. a curve finder, the current job, the
        imt of the curves, a block size and an offset
        """
        curve_nr = self.individual_curves_nr(job, imt)
        calc = job.hazard_calculation
        curves_per_location = calc.individual_curves_per_location()
        block_size = location_block_size * curves_per_location
        ranges = xrange(0, curve_nr, block_size)

        return [IndividualHazardCurveChunk(
                job, imt, curves_per_location, offset, block_size)
                for offset in ranges]

    def all_curves_for_imt(self, job, imt, sa_period, sa_damping):
        """
        Helper function for creating a :class:`django.db.models.query.QuerySet`
        for selecting all curves from all realizations for a given ``job_id``
        and ``imt``.

        :param job:
            An :class:`openquake.db.models.OqJob` instance.
        :param str imt:
            Intensity measure type.
        :param sa_period:
            Spectral Acceleration period value. Only relevant if the ``imt`` is
            "SA".
        :param sa_damping:
            Spectrail Acceleration damping value. Only relevant if the ``imt``
            is "SA".
        """
        return self.filter(hazard_curve__output__oq_job=job,
                           hazard_curve__imt=imt,
                           hazard_curve__sa_period=sa_period,
                           hazard_curve__sa_damping=sa_damping,
                           # We only want curves associated with a logic tree
                           # realization (and not statistical aggregates):
                           hazard_curve__lt_realization__isnull=False)

    def all_curves_simple(self, filter_args=None, order_by='id'):
        """
        Get all :class:`HazardCurveData` records matching `filter_args` and
        return the results in a simple, lean format: a sequence of (x, y, poes)
        triples, where x and y are longitude and latitude of the `location`.

        For querying large sets of hazard curve data, this is a rather lean
        and efficient method for getting the results.

        :param dict filter_args:
            Optional. Dictionary of filter arguments to apply to the query.
        :param str order_by:
            Defaults to the primary key ('id'). Field by which to order
            results. Currently, only one `ORDER BY` field is supported.
        """
        if filter_args is None:
            filter_args = dict()

        return self\
            .filter(**filter_args)\
            .order_by(order_by)\
            .extra(select={'x': 'ST_X(location)', 'y': 'ST_Y(location)'})\
            .values_list('x', 'y', 'poes')\
            .iterator()


class IndividualHazardCurveChunk(object):
    """
    A class that model a chunk of individual curves that might cover
    different locations
    """

    def __init__(self, job, imt, curves_per_location, offset, block_size):
        self.job = job
        self.imt = imt
        self.offset = offset
        self.curves_per_location = curves_per_location
        self.block_size = block_size
        self._raw_data = None

    @property
    def raw_data(self):
        return HazardCurveData.objects.individual_curves_chunk(
            self.job, self.imt, self.offset, self.block_size)

    @property
    def poes(self):
        return [r['poes'] for r in self.raw_data]

    @property
    def weights(self):
        weights = [r['hazard_curve__lt_realization__weight']
                   for r in self.raw_data]
        return weights[0:self.curves_per_location]

    @property
    def locations(self):
        locations = [r['wkb'] for r in self.raw_data]
        return locations[0::self.curves_per_location]


class HazardCurveData(djm.Model):
    '''
    Hazard Curve data

    Contains an list of PoE (Probability of Exceedance)
    values and the geographical point associated with the curve
    '''
    hazard_curve = djm.ForeignKey('HazardCurve')
    poes = fields.FloatArrayField()
    location = djm.PointField(srid=DEFAULT_SRID)
    # weight can be null/None if the weight is implicit:
    weight = djm.DecimalField(decimal_places=100, max_digits=101, null=True)

    objects = HazardCurveDataManager()

    class Meta:
        db_table = 'hzrdr\".\"hazard_curve_data'


class SESCollection(djm.Model):
    """
    Stochastic Event Set Collection: A container for 1 or more Stochastic Event
    Sets for a given logic tree realization.

    See also :class:`SES` and :class:`SESRupture`.
    """
    output = djm.ForeignKey('Output')
    # If `lt_realization` is None, this is a `complete logic tree`
    # Stochastic Event Set Collection, containing a single stochastic
    # event set containing all of the ruptures from the entire
    # calculation.
    lt_realization = djm.ForeignKey('LtRealization', null=True)
    # A flag to indicate that this is a `complete logic
    # tree` SES collection.
    complete_logic_tree_ses = djm.BooleanField(default=False)

    class Meta:
        db_table = 'hzrdr\".\"ses_collection'

    def __iter__(self):
        """
        Iterator for walking through all child :class:`SES` objects.
        """
        return SES.objects.filter(ses_collection=self.id).iterator()


class SES(djm.Model):
    """
    Stochastic Event Set: A container for 1 or more ruptures associated with a
    specific investigation time span.

    See also :class:`SESRupture`.
    """
    ses_collection = djm.ForeignKey('SESCollection')
    investigation_time = djm.FloatField()
    # Order number of this Stochastic Event Set in a series of SESs
    # (for a given logic tree realization).
    # For `complete logic tree` SESs, this should be None/NULL.
    ordinal = djm.IntegerField(null=True)
    # A flag to indicate that this is a `complete logic
    # tree` SES.
    complete_logic_tree_ses = djm.BooleanField(default=False)

    class Meta:
        db_table = 'hzrdr\".\"ses'

    def __iter__(self):
        """
        Iterator for walking through all child :class:`SESRupture` objects.
        """
        return SESRupture.objects.filter(ses=self.id).iterator()


class SESRupture(djm.Model):
    """
    A rupture as part of a Stochastic Event Set.

    Ruptures will have different geometrical definitions, depending on whether
    the event was generated from a point/area source or a simple/complex fault
    source.
    """
    ses = djm.ForeignKey('SES')
    magnitude = djm.FloatField()
    strike = djm.FloatField()
    dip = djm.FloatField()
    rake = djm.FloatField()
    tectonic_region_type = djm.TextField()
    # If True, this rupture was generated from a simple/complex fault
    # source. If False, this rupture was generated from a point/area source.
    is_from_fault_source = djm.BooleanField()
    # The following fields can be interpreted different ways, depending on the
    # value of `is_from_fault_source`.
    # If `is_from_fault_source` is True, each of these fields should contain a
    # 2D numpy array (all of the same shape). Each triple of (lon, lat, depth)
    # for a given index represents the node of a rectangular mesh.
    # If `is_from_fault_source` is False, each of these fields should contain
    # a sequence (tuple, list, or numpy array, for example) of 4 values. In
    # order, the triples of (lon, lat, depth) represent top left, top right,
    # bottom right, and bottom left corners of the the rupture's planar
    # surface.
    lons = fields.PickleField()
    lats = fields.PickleField()
    depths = fields.PickleField()
    result_grp_ordinal = djm.IntegerField()
    # NOTE(LB): The ordinal of a rupture within a given result group (indicated
    # by ``result_grp_ordinal``). This rupture correspond indices of the
    # ``gmvs`` field in Gmf. Thus, if you join SESRupture and Gmf records on
    # the ``result_grp_ordinal``, you can extract ground motion values for a
    # specific rupture.
    # At the moment this functionality is not directly used, but in the future
    # we will need to provide some way of tracing ground motion to the original
    # rupture.
    rupture_ordinal = djm.IntegerField()

    class Meta:
        db_table = 'hzrdr\".\"ses_rupture'

    def _validate_planar_surface(self):
        """
        A rupture's planar surface (existing only in the case of ruptures from
        area/point sources) may only consist of 4 points (top left, top right,
        bottom right, and bottom left corners, in that order).

        If the surface is not valid, a :exc:`ValueError` is raised.

        This should only be used if `is_from_fault_source` is `False`.
        """
        if not (4 == len(self.lons) == len(self.lats) == len(self.depths)):
            raise ValueError(
                "Incorrect number of points; there should be exactly 4")

    @property
    def top_left_corner(self):
        if not self.is_from_fault_source:
            self._validate_planar_surface()
            return self.lons[0], self.lats[0], self.depths[0]
        return None

    @property
    def top_right_corner(self):
        if not self.is_from_fault_source:
            self._validate_planar_surface()
            return self.lons[1], self.lats[1], self.depths[1]
        return None

    @property
    def bottom_right_corner(self):
        if not self.is_from_fault_source:
            self._validate_planar_surface()
            return self.lons[2], self.lats[2], self.depths[2]
        return None

    @property
    def bottom_left_corner(self):
        if not self.is_from_fault_source:
            self._validate_planar_surface()
            return self.lons[3], self.lats[3], self.depths[3]
        return None


class GmfCollection(djm.Model):
    """
    A collection of ground motion field (GMF) sets for a given logic tree
    realization.
    """
    output = djm.OneToOneField('Output')
    # If `lt_realization` is None, this is a `complete logic tree`
    # GMF Collection, containing a single GMF set containing all of the ground
    # motion fields in the calculation.
    lt_realization = djm.ForeignKey('LtRealization', null=True)
    # A flag to indicate that this is a `complete logic
    # tree` GMF collection.
    complete_logic_tree_gmf = djm.BooleanField(default=False)

    class Meta:
        db_table = 'hzrdr\".\"gmf_collection'

    def __iter__(self):
        """
        Iterator for walking through all child :class:`GmfSet` objects.
        """
        return GmfSet.objects.filter(gmf_collection=self.id).iterator()


class GmfSet(djm.Model):
    """
    A set of ground motion fields for a given investigation time (in years).
    """
    gmf_collection = djm.ForeignKey('GmfCollection')
    investigation_time = djm.FloatField()
    # Keep track of the stochastic event set which this GMF set is associated
    # with.
    ses_ordinal = djm.IntegerField()
    complete_logic_tree_gmf = djm.BooleanField(default=False)

    class Meta:
        db_table = 'hzrdr\".\"gmf_set'

    # Disabling pylint for 'Too many local variables'
    # pylint: disable=R0914
    def __iter__(self):
        """
        Iterator for walking through all child :class:`Gmf` objects.
        """
        job = self.gmf_collection.output.oq_job
        hc = job.hazard_calculation
        if self.complete_logic_tree_gmf:
            # Get all of the GmfSets associated with a logic tree realization,
            # for this calculation.
            lt_gmf_sets = GmfSet.objects\
                .filter(
                    gmf_collection__output__oq_job=job,
                    gmf_collection__lt_realization__isnull=False)\
                .order_by('id')
            for gmf in itertools.chain(*lt_gmf_sets):
                yield gmf
        else:
            num_tasks = JobStats.objects.get(oq_job=job.id).num_tasks

            imts = [parse_imt(x) for x in hc.intensity_measure_types]

            for imt, sa_period, sa_damping in imts:

                for result_grp_ordinal in xrange(1, num_tasks + 1):
                    gmfs = Gmf.objects\
                        .filter(
                            gmf_set=self.id,
                            imt=imt,
                            sa_period=sa_period,
                            sa_damping=sa_damping,
                            result_grp_ordinal=result_grp_ordinal)\
                        .order_by('location')
                    if len(gmfs) == 0:
                        # This task did not contribute to this GmfSet
                        continue

                    # len of each gmfs == number of sites
                    # need to walk through each columns of gmvs, slicing
                    # vertically to extract individual ground motion fields
                    first = gmfs[0]
                    num_ruptures = len(first.gmvs)

                    for i in xrange(num_ruptures):
                        gmf_nodes = []
                        for gmf in gmfs:
                            assert len(gmf.gmvs) == num_ruptures
                            # TODO: Rename `iml` to `gmv`,
                            # in NRML serializer as well
                            gmf_nodes.append(_GroundMotionFieldNode(
                                iml=gmf.gmvs[i], location=gmf.location))
                        yield _GroundMotionField(
                            imt=first.imt, sa_period=first.sa_period,
                            sa_damping=first.sa_damping, gmf_nodes=gmf_nodes)
                        del gmf_nodes


class _GroundMotionField(object):

    def __init__(self, imt, sa_period, sa_damping, gmf_nodes):
        self.imt = imt
        self.sa_period = sa_period
        self.sa_damping = sa_damping
        self.gmf_nodes = gmf_nodes

    def __iter__(self):
        return iter(self.gmf_nodes)

    def __getitem__(self, key):
        return self.gmf_nodes[key]


class _GroundMotionFieldNode(object):

    def __init__(self, iml, location):
        self.iml = iml
        self.location = location  # must have x and y attributes


class Gmf(djm.Model):
    """
    Ground Motion Field: A collection of ground motion values and their
    respective geographical locations.
    """
    gmf_set = djm.ForeignKey('GmfSet')
    imt = djm.TextField(choices=IMT_CHOICES)
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)
    location = djm.PointField(srid=DEFAULT_SRID)
    gmvs = fields.FloatArrayField()
    result_grp_ordinal = djm.IntegerField()

    objects = djm.GeoManager()

    class Meta:
        db_table = 'hzrdr\".\"gmf'


class GmfScenario(djm.Model):
    """
    Ground Motion Field: A collection of ground motion values and their
    respective geographical locations.
    """
    output = djm.ForeignKey('Output')
    imt = djm.TextField(choices=IMT_CHOICES)
    # Spectral acceleration
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)
    location = djm.PointField(srid=DEFAULT_SRID)
    gmvs = fields.FloatArrayField()
    result_grp_ordinal = djm.IntegerField()

    objects = djm.GeoManager()

    class Meta:
        db_table = 'hzrdr\".\"gmf_scenario'


def get_gmfs_scenario(output, imt=None):
    """
    Iterator for walking through all :class:`Gmf` objects associated
    to a given output. Notice that values for the same site are
    displayed together and then ordered according to the iml, so that
    it is possible to get reproducible outputs in the test cases.

    :param output: instance of :class:`openquake.db.models.Output`

    :param string imt: a string with the IMT to extract; the default
                       is None, all the IMT in the job.ini file are extracted

    :returns: an iterator over
              :class:`openquake.db.models._GroundMotionField` instances
    """
    job = output.oq_job
    hc = job.hazard_calculation
    if imt is None:
        imts = [parse_imt(x) for x in hc.intensity_measure_types]
    else:
        imts = [parse_imt(imt)]
    for imt, sa_period, sa_damping in imts:
        gmfs = GmfScenario.objects.filter(
            output__id=output.id,
            imt=imt,
            sa_period=sa_period,
            sa_damping=sa_damping,
        ).order_by('location')
        # yield all the nodes associated to a given location
        for loc, rows in itertools.groupby(
                gmfs, operator.attrgetter('location')):
            gmf_nodes = []
            for gmf in rows:
                for gmv in gmf.gmvs:
                    gmf_nodes.append(
                        _GroundMotionFieldNode(iml=gmv, location=loc))
            yield _GroundMotionField(
                imt=imt,
                sa_period=sa_period,
                sa_damping=sa_damping,
                gmf_nodes=sorted(gmf_nodes, key=operator.attrgetter('iml')))


class DisaggResult(djm.Model):
    """
    Storage for disaggregation historgrams. Each histogram is stored in
    `matrix` as a 6-dimensional numpy array (pickled). The dimensions of the
    matrix are as follows, in order:

    * magnitude
    * distance
    * longitude
    * latitude
    * epsilon
    * tectonic region type

    Bin edges are defined for all of these dimensions (except tectonic region
    type) as:

    * `mag_bin_edges`
    * `dist_bin_edges`
    * `lat_bin_edges`
    * `lon_bin_edges`
    * `eps_bin_edges`

    The size of the tectonic region type (TRT) dimension is simply determined
    by the length of `trts`.

    Additional metadata for the disaggregation histogram is stored, including
    location (POINT geometry), disaggregation PoE (Probability of Exceedance)
    and the corresponding IML (Intensity Measure Level) extracted from the
    hazard curve, logic tree path information, and investigation time.
    """

    output = djm.ForeignKey('Output')
    lt_realization = djm.ForeignKey('LtRealization')
    investigation_time = djm.FloatField()
    imt = djm.TextField(choices=IMT_CHOICES)
    iml = djm.FloatField()
    poe = djm.FloatField()
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)
    mag_bin_edges = fields.FloatArrayField()
    dist_bin_edges = fields.FloatArrayField()
    lon_bin_edges = fields.FloatArrayField()
    lat_bin_edges = fields.FloatArrayField()
    eps_bin_edges = fields.FloatArrayField()
    trts = fields.CharArrayField()
    location = djm.PointField(srid=DEFAULT_SRID)
    matrix = fields.PickleField()

    class Meta:
        db_table = 'hzrdr\".\"disagg_result'


class GmfData(djm.Model):
    '''
    Ground Motion Field data

    DEPRECATED. See instead :class:`GmfCollection`, :class:`GmfSet`,
    :class:`Gmf`, and :class:`GmfNode`.
    '''
    output = djm.ForeignKey('Output')
    ground_motion = djm.FloatField()
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'hzrdr\".\"gmf_data'


class UhSpectra(djm.Model):
    """Uniform Hazard Spectra

    A Collection of Uniform Hazard Spectrum which share a set of periods.
    A UH Spectrum has a PoE (Probability of Exceedence) and is conceptually
    composed of a set of 2D matrices, 1 matrix per site/point of interest.
    Each 2D matrix has a number of row equal to ``realizations`` and a number
    of columns equal to the number of ``periods``.
    """
    output = djm.ForeignKey('Output')
    timespan = djm.FloatField()
    realizations = djm.IntegerField()
    periods = fields.FloatArrayField()

    class Meta:
        db_table = 'hzrdr\".\"uh_spectra'


class UhSpectrum(djm.Model):
    """Uniform Hazard Spectrum

    * "Uniform" meaning "the same PoE"
    * "Spectrum" because it covers a range/band of periods/frequencies
    """
    uh_spectra = djm.ForeignKey('UhSpectra')
    poe = djm.FloatField()

    class Meta:
        db_table = 'hzrdr\".\"uh_spectrum'


class UhSpectrumData(djm.Model):
    """Uniform Hazard Spectrum Data

    A single "row" of data in a UHS matrix for a specific site/point of
    interest.
    """
    uh_spectrum = djm.ForeignKey('UhSpectrum')
    realization = djm.IntegerField()
    sa_values = fields.FloatArrayField()
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'hzrdr\".\"uh_spectrum_data'


class LtRealization(djm.Model):
    """
    Keep track of logic tree realization progress. When ``completed_items``
    becomes equal to ``total_items``, mark ``is_complete`` as `True`.

    Marking progress as we go gives us the ability to resume partially-
    completed calculations.
    """

    hazard_calculation = djm.ForeignKey('HazardCalculation')
    ordinal = djm.IntegerField()
    seed = djm.IntegerField()
    weight = djm.DecimalField(decimal_places=100, max_digits=101)
    sm_lt_path = fields.CharArrayField()
    gsim_lt_path = fields.CharArrayField()
    is_complete = djm.BooleanField(default=False)
    total_items = djm.IntegerField()
    completed_items = djm.IntegerField(default=0)

    class Meta:
        db_table = 'hzrdr\".\"lt_realization'


## Tables in the 'riskr' schema.


class LossMap(djm.Model):
    '''
    Holds metadata for loss maps
    '''

    output = djm.OneToOneField("Output")
    poe = djm.FloatField(null=True)

    class Meta:
        db_table = 'riskr\".\"loss_map'


class LossMapData(djm.Model):
    '''
    Holds an asset, its position and a value plus (for
    non-scenario maps) the standard deviation for its loss
    '''

    loss_map = djm.ForeignKey("LossMap")
    asset_ref = djm.TextField()
    value = djm.FloatField()
    std_dev = djm.FloatField(default=0.0, null=True)
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'riskr\".\"loss_map_data'


class LossCurve(djm.Model):
    '''
    Holds the parameters common to a set of loss curves
    '''

    output = djm.OneToOneField("Output")
    aggregate = djm.BooleanField(default=False)
    insured = djm.BooleanField(default=False)

    class Meta:
        db_table = 'riskr\".\"loss_curve'


class LossCurveData(djm.Model):
    '''
    Holds the probabilities of exceedance for a given loss curve
    '''

    loss_curve = djm.ForeignKey("LossCurve")
    asset_ref = djm.TextField()
    losses = fields.FloatArrayField()
    loss_ratios = fields.FloatArrayField()
    poes = fields.FloatArrayField()
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'riskr\".\"loss_curve_data'


class AggregateLossCurveData(djm.Model):
    '''
    Holds the probabilities of exceedance for the whole exposure model
    '''

    loss_curve = djm.OneToOneField("LossCurve")
    losses = fields.FloatArrayField()
    poes = fields.FloatArrayField()

    class Meta:
        db_table = 'riskr\".\"aggregate_loss_curve_data'


class BCRDistribution(djm.Model):
    '''
    Holds metadata for the benefit-cost ratio distribution
    '''

    output = djm.OneToOneField("Output")

    class Meta:
        db_table = 'riskr\".\"bcr_distribution'


class BCRDistributionData(djm.Model):
    '''
    Holds the actual data for the benefit-cost ratio distribution
    '''

    bcr_distribution = djm.ForeignKey("BCRDistribution")
    asset_ref = djm.TextField()
    average_annual_loss_original = djm.FloatField()
    average_annual_loss_retrofitted = djm.FloatField()
    bcr = djm.FloatField()
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'riskr\".\"bcr_distribution_data'


class DmgState(djm.Model):
    """Holds the damage_states associated to a given output"""
    # they actually come from the fragility model xml input
    output = djm.ForeignKey("Output")
    dmg_state = djm.TextField()
    lsi = djm.PositiveSmallIntegerField(
        help_text="limit state index, to order the limit states")

    class Meta:
        db_table = 'riskr\".\"dmg_state'


class DmgDistPerAsset(djm.Model):
    """Holds the actual data for damage distributions per asset."""

    dmg_state = djm.ForeignKey("DmgState")
    exposure_data = djm.ForeignKey("ExposureData")
    mean = djm.FloatField()
    stddev = djm.FloatField()
    # geometry for the computation cell which contains the referenced asset
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'riskr\".\"dmg_dist_per_asset'


class DmgDistPerTaxonomy(djm.Model):
    """Holds the actual data for damage distributions per taxonomy."""

    dmg_state = djm.ForeignKey("DmgState")
    taxonomy = djm.TextField()
    mean = djm.FloatField()
    stddev = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"dmg_dist_per_taxonomy'


class DmgDistTotal(djm.Model):
    """Holds the actual 'total damage distribution' values for for an entire
    calculation. There should be  one record per calculation per damage state.
    """

    dmg_state = djm.ForeignKey("DmgState")
    mean = djm.FloatField()
    stddev = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"dmg_dist_total'

## Tables in the 'oqmif' schema.


class ExposureModel(djm.Model):
    '''
    A risk exposure model
    '''

    owner = djm.ForeignKey("OqUser")
    input = djm.OneToOneField("Input")
    name = djm.TextField()
    description = djm.TextField(null=True)
    category = djm.TextField()
    taxonomy_source = djm.TextField(
        null=True, help_text="the taxonomy system used to classify the assets")
    AREA_CHOICES = (
        (u'aggregated', u'Aggregated area value'),
        (u'per_asset', u'Per asset area value'),
    )
    area_type = djm.TextField(null=True, choices=AREA_CHOICES)
    area_unit = djm.TextField(null=True)
    COST_CHOICES = (
        (u'aggregated', u'Aggregated economic value'),
        (u'per_area', u'Per area economic value'),
        (u'per_asset', u'Per asset economic value'),
    )
    stco_type = djm.TextField(null=True, choices=COST_CHOICES,
                              help_text="structural cost type")
    stco_unit = djm.TextField(null=True, help_text="structural cost unit")
    reco_type = djm.TextField(null=True, choices=COST_CHOICES,
                              help_text="retrofitting cost type")
    reco_unit = djm.TextField(null=True, help_text="retrofitting cost unit")
    coco_type = djm.TextField(null=True, choices=COST_CHOICES,
                              help_text="contents cost type")
    coco_unit = djm.TextField(null=True, help_text="contents cost unit")

    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'oqmif\".\"exposure_model'

    def taxonomies_in(self, region_constraint):
        """
        :param str region_constraint: polygon in wkt format the assets
        must be contained into
        :returns: a dictionary mapping each taxonomy with the number
        of assets contained in `region_constraint`
        """

        return ExposureData.objects.taxonomies_contained_in(
            self.id, region_constraint)

    def get_asset_chunk(self, taxonomy, region_constraint, offset, count):
        """
        :returns: a list of `openquake.db.models.ExposureData` objects
        of a given taxonomy contained in a region and paginated

        :param str taxonomy: the taxonomy of the returned objects

        :param Polygon region_constraint: a Polygon object with a wkt
        property used to filter the exposure

        :param int offset: An offset used to paginate the returned set
        :param int count: An offset used to paginate the returned set
        """
        return ExposureData.objects.contained_in(
            self.id, taxonomy, region_constraint, offset, count)


class Occupancy(djm.Model):
    '''
    Asset occupancy data
    '''

    exposure_data = djm.ForeignKey("ExposureData")
    description = djm.TextField()
    occupants = djm.IntegerField()

    class Meta:
        db_table = 'oqmif\".\"occupancy'


class AssetManager(djm.GeoManager):
    """
    Asset manager
    """
    def contained_in(self, exposure_model_id, taxonomy,
                     region_constraint, offset, size):
        """
        :returns the asset ids (ordered by id) contained in
        `region_constraint` of `taxonomy` associated with an
        `openquake.db.models.ExposureModel` with ID equal to
        `exposure_model_id`
        """
        return list(
            self.raw("""
            SELECT * FROM oqmif.exposure_data
            WHERE exposure_model_id = %s AND taxonomy = %s AND
            ST_COVERS(ST_GeographyFromText(%s), site)
            ORDER BY taxonomy, id LIMIT %s OFFSET %s
            """, [exposure_model_id, taxonomy,
                  "SRID=4326; %s" % region_constraint.wkt,
                  size, offset]))

    def taxonomies_contained_in(self, exposure_model_id, region_constraint):
        """
        :returns: a dictionary which map each taxonomy associated with
        `exposure_model` and contained in `region_constraint` with the
        number of assets.
        """
        cursor = connection.cursor()

        cursor.execute("""
        SELECT oqmif.exposure_data.taxonomy, COUNT(*)
        FROM oqmif.exposure_data WHERE
        exposure_model_id = %s AND ST_COVERS(ST_GeographyFromText(%s), site)
        group by oqmif.exposure_data.taxonomy
        """, [exposure_model_id, "SRID=4326; %s" % region_constraint.wkt])

        return dict(cursor)


class ExposureData(djm.Model):
    '''
    Per-asset risk exposure data
    '''

    NO_RETROFITTING_COST = "no retrofitting cost"

    exposure_model = djm.ForeignKey("ExposureModel")
    asset_ref = djm.TextField()
    taxonomy = djm.TextField()
    site = djm.PointField(geography=True)
    # Override the default manager with a GeoManager instance in order to
    # enable spatial queries.
    objects = djm.GeoManager()

    stco = djm.FloatField(null=True, help_text="structural cost")
    reco = djm.FloatField(null=True, help_text="retrofitting cost")
    coco = djm.FloatField(null=True, help_text="contents cost")

    number_of_units = djm.FloatField(
        null=True, help_text="number of assets, people etc.")
    area = djm.FloatField(null=True)

    ins_limit = djm.FloatField(
        null=True, help_text="insurance coverage limit")
    deductible = djm.FloatField(
        null=True, help_text="insurance deductible")

    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    objects = AssetManager()

    class Meta:
        db_table = 'oqmif\".\"exposure_data'

    @staticmethod
    def per_asset_value(
            cost, cost_type, area, area_type, number_of_units, category):
        """Return per-asset value for the given exposure data set.

        Calculate per asset value by considering the given exposure
        data as follows:
            case 1: cost type: aggregated:
                cost = economic value
            case 2: cost type: per asset:
                cost * number (of assets) = economic value
            case 3: cost type: per area and area type: aggregated:
                cost * area = economic value
            case 4: cost type: per area and area type: per asset:
                cost * area * number = economic value
        The same "formula" applies to contenst/retrofitting cost analogously.
        :returns: the per-asset value as a `float`
        :raises: `ValueError` in case of a malformed (risk exposure data) input
        """
        if category is not None and category == "population":
            return number_of_units
        if cost_type == "aggregated":
            return cost
        elif cost_type == "per_asset":
            return cost * number_of_units
        elif cost_type == "per_area":
            if area_type == "aggregated":
                return cost * area
            elif area_type == "per_asset":
                return cost * area * number_of_units
        raise ValueError("Invalid input")

    @property
    def value(self):
        """The structural per-asset value."""
        return self.per_asset_value(
            cost=self.stco, cost_type=self.exposure_model.stco_type,
            area=self.area, area_type=self.exposure_model.area_type,
            number_of_units=self.number_of_units,
            category=self.exposure_model.category)

    @property
    def retrofitting_cost(self):
        """The retrofitting per-asset value."""
        return self.per_asset_value(
            cost=self.reco, cost_type=self.exposure_model.reco_type,
            area=self.area, area_type=self.exposure_model.area_type,
            number_of_units=self.number_of_units,
            category=self.exposure_model.category)


## Tables in the 'htemp' schema.


class SourceProgress(djm.Model):
    """
    Keep track of which sources have been considered for a given logic tree
    realization.

    Marking progress as we go gives us the ability to resume partially-
    completed logic tree realizations.
    """

    lt_realization = djm.ForeignKey('LtRealization')
    parsed_source = djm.ForeignKey('ParsedSource')
    is_complete = djm.BooleanField(default=False)

    class Meta:
        db_table = 'htemp\".\"source_progress'


class HazardCurveProgress(djm.Model):
    """
    Store intermediate results of hazard curve calculations (as a pickled numpy
    array) for a single logic tree realization.
    """

    lt_realization = djm.ForeignKey('LtRealization')
    imt = djm.TextField()
    # stores a pickled numpy array for intermediate results
    # array is 2d: sites x IMLs
    # each row indicates a site,
    # each column holds the PoE vaue for the IML at that index
    result_matrix = fields.PickleField()

    class Meta:
        db_table = 'htemp\".\"hazard_curve_progress'


class SiteData(djm.Model):
    """
    Contains pre-computed site parameter matrices. ``lons`` and ``lats``
    represent the calculation sites of interest. The associated site parameters
    are from the closest point in a site model in relation to each calculation
    point of interest.

    Used only if a calculation defines a site model (otherwise, reference
    parameters are use for all points of interest).
    """

    hazard_calculation = djm.ForeignKey('HazardCalculation')
    lons = fields.PickleField()
    lats = fields.PickleField()
    vs30s = fields.PickleField()
    # `vs30_measured` stores a numpy array of booleans.
    # If a value is `False`, this means that the vs30 value is 'inferred'.
    vs30_measured = fields.PickleField()
    z1pt0s = fields.PickleField()
    z2pt5s = fields.PickleField()

    class Meta:
        db_table = 'htemp\".\"site_data'
