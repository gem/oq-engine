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

import collections
import itertools
import operator
import os
import re

from datetime import datetime

import openquake.hazardlib
import numpy

from django.db import connections
from django.contrib.gis.db import models as djm
from openquake.hazardlib import geo as hazardlib_geo
from shapely import wkt

from openquake.engine.db import fields

#: Default Spectral Acceleration damping. At the moment, this is not
#: configurable.
DEFAULT_SA_DAMPING = 5.0


#: Kind of supported curve statistics
STAT_CHOICES = (
    (u'mean', u'Mean'),
    (u'quantile', u'Quantile'))


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


#: Minimum value for a seed number
MIN_SINT_32 = -(2 ** 31)
#: Maximum value for a seed number
MAX_SINT_32 = (2 ** 31) - 1


def order_by_location(queryset):
    """
    Utility function to order a queryset by location. This works even if
    the location is of Geography object (a simple order_by('location') only
    works for Geometry objects).
    """
    return queryset.extra(
        select={'x': 'ST_X(geometry(location))',
                'y': 'ST_Y(geometry(location))'},
        order_by=["x", "y"])


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
        (u'characteristic', u'Characteristic'),
    )
    source_type = djm.TextField(choices=SRC_TYPE_CHOICES)
    nrml = fields.PickleField(help_text="NRML object representing the source")

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


class Input(djm.Model):
    '''
    A single OpenQuake input file uploaded by the user.
    '''
    owner = djm.ForeignKey('OqUser')
    model_content = djm.ForeignKey('ModelContent', null=True)
    name = djm.TextField(null=True)
    digest = djm.TextField(help_text="32 byte md5sum digest, used to "
                                     "detect identical input model files")
    path = djm.TextField()
    INPUT_TYPE_CHOICES = (
        (u'unknown', u'Unknown'),
        (u'source', u'Source Model'),
        (u'source_model_logic_tree', u'Source Model Logic Tree'),
        (u'gsim_logic_tree', u'Ground Shaking Intensity Model Logic Tree'),
        (u'exposure', u'Exposure'),
        (u'fragility', u'Fragility'),
        (u'vulnerability', u'Vulnerability'),
        (u'vulnerability_retrofitted', u'Vulnerability Retrofitted'),
        (u'site_model', u'Site Model'),
        (u'rupture_model', u'Rupture Model')
    )
    input_type = djm.TextField(choices=INPUT_TYPE_CHOICES)

    hazard_calculations = djm.ManyToManyField('HazardCalculation',
                                              through='Input2hcalc',
                                              related_name="inputs")
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
    Associate an "source_model_logic_tree" type input (a logic tree source)
    with "source" type inputs (hazard sources referenced by the logic tree
    source). This is needed for worker-side logic tree processing.
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
    hazardlib_version = djm.TextField(null=True, blank=True)
    nrml_version = djm.TextField(null=True, blank=True)
    is_running = djm.BooleanField(default=False)
    duration = djm.IntegerField(default=0)
    job_pid = djm.IntegerField(default=0)
    supervisor_pid = djm.IntegerField(default=0)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"oq_job'

    @property
    def calculation(self):
        """
        :returns: a calculation object (hazard or risk) depending on
        the type of calculation. Useful in situations (e.g. core
        engine, stats, kvs, progress) where you do not have enough
        context about which kind of calculation is but still you want
        to access the common feature of a Calculation object.
        """
        return self.hazard_calculation or self.risk_calculation


class Performance(djm.Model):
    '''
    Contains performance information about the operations performed by a task
    launched by a job.
    '''
    oq_job = djm.ForeignKey('OqJob')
    task_id = djm.TextField(null=True)
    task = djm.TextField(null=True)
    operation = djm.TextField(null=False)
    start_time = djm.DateTimeField(editable=False)
    duration = djm.FloatField(null=True)
    pymemory = djm.IntegerField(null=True)
    pgmemory = djm.IntegerField(null=True)

    class Meta:
        db_table = 'uiapi\".\"performance'


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


class HazardCalculation(djm.Model):
    '''
    Parameters needed to run a Hazard job.
    '''
    owner = djm.ForeignKey('OqUser')
    # Contains the absolute path to the directory containing the job config
    # file.
    base_path = djm.TextField()
    export_dir = djm.TextField(null=True, blank=True)

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

    # We we create a `openquake.hazardlib.site.SiteCollection` for the
    # calculation, we can cache it here to avoid recomputing every time
    # we need to use it in a task context. For large regions, this can be
    # quite expensive.
    _site_collection = fields.PickleField(
        null=True, blank=True, db_column='site_collection'
    )

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
    truncation_level = fields.NullFloatField(
        help_text='Level for ground motion distribution truncation',
        null=True,
        blank=True,
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
    poes = fields.FloatArrayField(
        help_text=('PoEs (probabilities of exceedence) to be used for '
                   'computing hazard maps and uniform hazard spectra'),
        null=True,
        blank=True,
    )
    hazard_maps = fields.OqNullBooleanField(
        help_text='Compute hazard maps',
        null=True,
        blank=True,
    )
    uniform_hazard_spectra = fields.OqNullBooleanField(
        help_text=('Compute uniform hazard spectra; if true, hazard maps will'
                   ' be computed as well'),
        null=True,
        blank=True,
    )
    export_multi_curves = fields.OqNullBooleanField(
        help_text=('If true hazard curve outputs that groups multiple curves '
                   'in multiple imt will be exported when asked in export '
                   'phase.'))
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
        # A place to cache computation geometry. Recomputing this many times
        # for large regions is wasteful.
        self._points_to_compute = None
        super(HazardCalculation, self).__init__(*args, **kwargs)

    @property
    def site_collection(self):
        """
        Get the :class:`openquake.hazardlib.site.SiteCollection` for this
        calculation.

        Because this data is costly to compute, we try to only compute it once
        and cache it in the DB. See :meth:`init_site_collection`.
        """
        if self._site_collection is None:
            self.init_site_collection()
        return self._site_collection

    def init_site_collection(self):
        """
        Compute, cache, and save (to the DB) the
        :class:`openquake.hazardlib.site.SiteCollection` which represents
        the calculation sites of interest with associated soil parameters.

        A `SiteCollection` is a combination of the geometry of interest for the
        calculation, which is basically just a collection of geographical
        points, and the soil associated soil parameters for each point.

        .. note::
            For computational efficiency, the `site_collection` should only be
            computed once and cached in the database. If the computation
            geometry or site parameters change during runtime, which highly
            unlikely to occur in typical calculation scenarios, you will need
            to recompute the site collection by calling this method again.

            In this case, it obvious that such a thing should be done carefully
            and with much discretion.

            Ideally, this method should only be called once at the very
            beginning a calculation.
        """
        self._site_collection = get_site_collection(self)
        self.save()

    def individual_curves_per_location(self):
        """
        Returns the number of individual curves per location, that are
        expected after a full computation of the hazard calculation
        has been performed
        """
        realizations_nr = self.ltrealization_set.count()
        return realizations_nr

    def points_to_compute(self):
        """
        Generate a :class:`~openquake.hazardlib.geo.mesh.Mesh` of points.
        These points indicate the locations of interest in a hazard
        calculation.

        The mesh can be calculated given a `region` polygon and
        `region_grid_spacing` (the discretization parameter), or from a list of
        `sites`.

        .. note::
            This mesh is cached for efficiency when dealing with large numbers
            of calculation points. If you need to clear the cache and
            recompute, set `_points_to_compute` to `None` and call this method
            again.
        """
        if self._points_to_compute is None:
            if self.pk and self.inputs.filter(input_type='exposure').exists():
                assets = self.exposure_model.exposuredata_set.all().order_by(
                    'asset_ref')

                # the points here must be sorted
                lons, lats = zip(
                    *sorted(set([(asset.site.x, asset.site.y)
                                 for asset in assets])))
                # Cache the mesh:
                self._points_to_compute = hazardlib_geo.Mesh(
                    numpy.array(lons), numpy.array(lats), depths=None
                )
            elif self.region and self.region_grid_spacing:
                # assume that the polygon is a single linear ring
                coords = self.region.coords[0]
                points = [hazardlib_geo.Point(*x) for x in coords]
                poly = hazardlib_geo.Polygon(points)
                # Cache the mesh:
                self._points_to_compute = poly.discretize(
                    self.region_grid_spacing
                )
            elif self.sites is not None:
                lons, lats = zip(*self.sites.coords)
                # Cache the mesh:
                self._points_to_compute = hazardlib_geo.Mesh(
                    numpy.array(lons), numpy.array(lats), depths=None
                )
        return self._points_to_compute

    @property
    def exposure_model(self):
        if self.inputs.filter(input_type='exposure').exists():
            return self.inputs.get(input_type='exposure').exposuremodel

    def get_imts(self):
        """
        Returns intensity mesure types or
        intensity mesure types with levels.
        """

        return (self.intensity_measure_types or
                self.intensity_measure_types_and_levels.keys())


def get_site_collection(hc):
    """
    Create a `SiteCollection`, which is needed by hazardlib to perform various
    calculation tasks (such computing hazard curves and GMFs).

    :param hc:
        Instance of a :class:`HazardCalculation`. We need this in order to get
        the points of interest for a calculation as well as load pre-computed
        site data or access reference site parameters.

    :returns:
        :class:`openquake.hazardlib.site.SiteCollection` instance.
    """
    site_data = SiteData.objects.filter(hazard_calculation=hc.id)
    if len(site_data) > 0:
        site_data = site_data[0]
        sites = zip(site_data.lons, site_data.lats, site_data.vs30s,
                    site_data.vs30_measured, site_data.z1pt0s,
                    site_data.z2pt5s)
        sites = [openquake.hazardlib.site.Site(
            openquake.hazardlib.geo.Point(lon, lat), vs30, vs30m, z1pt0, z2pt5)
            for lon, lat, vs30, vs30m, z1pt0, z2pt5 in sites]
    else:
        # Use the calculation reference parameters to make a site collection.
        points = hc.points_to_compute()
        measured = hc.reference_vs30_type == 'measured'
        sites = [
            openquake.hazardlib.site.Site(pt, hc.reference_vs30_value,
                                          measured,
                                          hc.reference_depth_to_2pt5km_per_sec,
                                          hc.reference_depth_to_1pt0km_per_sec)
            for pt in points]

    return openquake.hazardlib.site.SiteCollection(sites)


class RiskCalculation(djm.Model):
    '''
    Parameters needed to run a Risk job.
    '''

    #: Default maximum asset-hazard distance in km
    DEFAULT_MAXIMUM_DISTANCE = 5

    owner = djm.ForeignKey('OqUser')
    # Contains the absolute path to the directory containing the job config
    # file.
    base_path = djm.TextField()
    export_dir = djm.TextField(null=True, blank=True)

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
        (u'scenario', u'Scenario'),
        (u'scenario_damage', u'Scenario Damage'),
        (u'event_based_bcr', u'Probabilistic Event-Based BCR'),
    )
    calculation_mode = djm.TextField(choices=CALC_MODE_CHOICES)
    region_constraint = djm.PolygonField(
        srid=DEFAULT_SRID, null=True, blank=True)

    exposure_input = djm.ForeignKey('Input', null=True, blank=True)

    # the maximum distance for an hazard value with the corresponding
    # asset. Expressed in kilometers
    maximum_distance = djm.FloatField(
        null=True, blank=True, default=DEFAULT_MAXIMUM_DISTANCE)
    # the hazard output (it can point to an HazardCurve or to a
    # GmfCollection) used by the risk calculation
    hazard_output = djm.ForeignKey("Output", null=True, blank=True)

    # the HazardCalculation object used by the risk calculation when
    # each individual Output (i.e. each hazard logic tree realization)
    # is considered
    hazard_calculation = djm.ForeignKey("HazardCalculation",
                                        null=True, blank=True)

    # A seed used to generate random values to be applied to
    # vulnerability functions
    master_seed = djm.IntegerField(null=True, blank=True)

    ####################################################
    # For calculators that output (conditional) loss map
    ####################################################
    conditional_loss_poes = fields.FloatArrayField(null=True, blank=True)

    ####################################################
    # For calculators that output statistical results
    ####################################################
    mean_loss_curves = fields.OqNullBooleanField(
        help_text='Compute mean loss curves, maps, etc.',
        null=True,
        blank=True)
    quantile_loss_curves = fields.FloatArrayField(
        help_text='List of quantiles for computing quantile outputs',
        null=True,
        blank=True)

    taxonomies_from_model = fields.OqNullBooleanField(
        help_text='if true calculation only consider the taxonomies in '
        'the fragility model', null=True, blank=True)

    ##################################
    # Probabilistic shared parameters
    ##################################
    # 0 == uncorrelated, 1 == perfect correlation by taxonomy
    asset_correlation = djm.FloatField(null=True, blank=True, default=0)

    #######################
    # Classical parameters:
    #######################
    lrem_steps_per_interval = djm.IntegerField(null=True, blank=True)

    poes_disagg = fields.FloatArrayField(
        null=True, blank=True,
        help_text='The probability of exceedance used to interpolate '
                  'loss curves for disaggregation purposes')

    #########################
    # Event-Based parameters:
    #########################
    loss_curve_resolution = djm.IntegerField(
        null=False, blank=True, default=DEFAULT_LOSS_CURVE_RESOLUTION)
    insured_losses = djm.NullBooleanField(null=True, blank=True, default=False)

    # The points of interest for disaggregation
    sites_disagg = djm.MultiPointField(
        srid=DEFAULT_SRID, null=True, blank=True)

    mag_bin_width = djm.FloatField(
        help_text=('Width of magnitude bins'),
        null=True,
        blank=True,
    )
    distance_bin_width = djm.FloatField(
        help_text=('Width of distance bins'),
        null=True,
        blank=True,
    )
    coordinate_bin_width = djm.FloatField(
        help_text=('Width of coordinate bins'),
        null=True,
        blank=True,
    )

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

    def get_hazard_calculation(self):
        """
        Get the hazard calculation associated with the hazard output used as an
        input to this risk calculation.

        :returns:
            :class:`HazardCalculation` instance.
        """
        hcalc = (self.hazard_calculation or
                 self.hazard_output.oq_job.hazard_calculation)
        return hcalc

    def hazard_outputs(self):
        """
        Returns the list of hazard outputs to be considered. Apply
        `filters` to the default queryset
        """

        if self.calculation_mode in ["classical", "classical_bcr"]:
            filters = dict(output_type='hazard_curve_multi',
                           hazardcurve__lt_realization__isnull=False)
        elif self.calculation_mode in ["event_based", "event_based_bcr"]:
            filters = dict(output_type='gmf',
                           gmfcollection__lt_realization__isnull=False)
        elif self.calculation_mode in ['scenario', 'scenario_damage']:
            filters = dict(output_type='gmf_scenario')
        else:
            raise NotImplementedError

        if self.hazard_output:
            return [self.hazard_output]
        elif self.hazard_calculation:
            return self.hazard_calculation.oqjob_set.filter(
                status="complete").latest(
                    'last_update').output_set.filter(**filters).order_by('id')
        else:
            raise RuntimeError("Neither hazard calculation "
                               "neither a hazard output has been provided")

    @property
    def best_maximum_distance(self):
        """
        Get the asset-hazard maximum distance (in km) to be used in
        hazard getters.

        :returns:
            The minimum between the maximum distance provided by the user (if
            not given, `DEFAULT_MAXIMUM_DISTANCE` is used as default) and the
            step (if exists) used by the hazard calculation.
        """
        dist = self.maximum_distance

        if dist is None:
            dist = self.DEFAULT_MAXIMUM_DISTANCE

        hc = self.get_hazard_calculation()
        if hc.sites is None and hc.region_grid_spacing is not None:
            dist = min(dist, hc.region_grid_spacing * numpy.sqrt(2) / 2)

        # if we are computing hazard at exact location we set the
        # maximum_distance to a very small number in order to help the
        # query to find the results.
        if hc.inputs.filter(input_type='exposure').exists():
            dist = 0.001
        return dist

    @property
    def is_bcr(self):
        return self.calculation_mode in ['classical_bcr', 'event_based_bcr']

    @property
    def exposure_model(self):
        exposure_input = self.exposure_input or self.inputs.get(
            input_type="exposure")
        return exposure_input.exposuremodel

    def will_compute_loss_curve_statistics(self):
        """
        Return true if this risk calculation will compute mean and/or
        quantile loss curves
        """
        return ((self.mean_loss_curves or self.quantile_loss_curves) and
                self.calculation_mode in ['classical', 'event_based'])


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
                           ('sites_disagg', 'MULTIPOINT(%s)'),
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

    #: Metadata of hazard outputs used by risk calculation. See
    #: `hazard_metadata` property for more details
    HazardMetadata = collections.namedtuple(
        'hazard_metadata',
        'investigation_time statistics quantile sm_path gsim_path')

    owner = djm.ForeignKey('OqUser')
    oq_job = djm.ForeignKey('OqJob')  # nullable in the case of an output
    # coming from an external source, with no job associated
    display_name = djm.TextField()
    OUTPUT_TYPE_CHOICES = (
        (u'agg_loss_curve', u'Aggregate Loss Curve'),
        (u'aggregate_losses', u'Aggregate Losses'),
        (u'bcr_distribution', u'Benefit-cost ratio distribution'),
        (u'collapse_map', u'Collapse Map Distribution'),
        (u'complete_lt_gmf', u'Complete Logic Tree GMF'),
        (u'complete_lt_ses', u'Complete Logic Tree SES'),
        (u'disagg_matrix', u'Disaggregation Matrix'),
        (u'dmg_dist_per_asset', u'Damage Distribution Per Asset'),
        (u'dmg_dist_per_taxonomy', u'Damage Distribution Per Taxonomy'),
        (u'dmg_dist_total', u'Total Damage Distribution'),
        (u'event_loss', u'Event Loss Table'),
        (u'gmf', u'Ground Motion Field'),
        (u'gmf_scenario', u'Ground Motion Field by Scenario Calculator'),
        (u'hazard_curve', u'Hazard Curve'),
        (u'hazard_curve_multi', u'Hazard Curve (multiple imts)'),
        (u'hazard_map', u'Hazard Map'),
        (u'loss_curve', u'Loss Curve'),
        # FIXME(lp). We should distinguish between conditional losses
        # and loss map
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

    def is_hazard_curve(self):
        return self.output_type in ['hazard_curve', 'hazard_curve_multi']

    def is_gmf_scenario(self):
        return self.output_type == 'gmf_scenario'

    @property
    def hazard_metadata(self):
        """
        Given an Output produced by a risk calculation it returns the
        corresponding hazard metadata.

        :returns:
            A `namedtuple` with the following attributes::

                * investigation_time: the hazard investigation time (float)
                * statistics: the kind of hazard statistics (None, "mean" or
                  "quantile")
                * quantile: quantile value (when `statistics` is "quantile")
                * sm_path: a list representing the source model path
                * gsim_path: a list representing the gsim logic tree path

        """

        rc = self.oq_job.risk_calculation
        hc = rc.get_hazard_calculation()

        investigation_time = hc.investigation_time

        # in scenario calculation we do not have neither statistics
        # neither logic tree realizations

        # if ``hazard_output`` is None, then the risk output is
        # computed over multiple hazard outputs (related to different
        # logic tree realizations). Then, We do not have to collect
        # metadata regarding statistics or logic tree
        statistics = None
        quantile = None
        sm_lt_path = None
        gsim_lt_path = None

        if rc.calculation_mode != 'scenario':
            # Two cases:
            # - hazard_output
            # - hazard_calculation
            if rc.hazard_output is not None:
                ho = rc.hazard_output

                if ho.is_hazard_curve():
                    lt = rc.hazard_output.hazardcurve.lt_realization
                    if lt is None:
                        # statistical result:
                        statistics = ho.hazardcurve.statistics
                        quantile = ho.hazardcurve.quantile
                    else:
                        sm_lt_path = lt.sm_lt_path
                        gsim_lt_path = lt.gsim_lt_path
                else:
                    lt = ho.gmfcollection.lt_realization
                    sm_lt_path = lt.sm_lt_path
                    gsim_lt_path = lt.gsim_lt_path
            elif rc.hazard_calculation is not None:
                # we're consuming multiple outputs from a single hazard
                # calculation
                if self.output_type in ['loss_curve', 'agg_loss_curve']:
                    the_output = self.loss_curve
                elif self.output_type == 'loss_map':
                    the_output = self.loss_map
                elif self.output_type == 'loss_fraction':
                    the_output = self.loss_fraction
                else:
                    raise RuntimeError(
                        'Error getting hazard metadata: Unexpected output_type'
                        ' "%s"' % self.output_type
                    )

                if the_output.hazard_output_id is not None:
                    haz_output = the_output.hazard_output

                    if haz_output.is_hazard_curve():
                        haz = haz_output.hazardcurve
                    else:
                        haz = haz_output.gmfcollection

                    if haz.lt_realization is not None:
                        sm_lt_path = haz.lt_realization.sm_lt_path
                        gsim_lt_path = haz.lt_realization.gsim_lt_path
                else:
                    if self.output_type == 'loss_curve':
                        # FIXME(lp). This is clearly not correct

                        # it's a mean/quantile loss curve
                        statistics = self.loss_curve.statistics
                        quantile = self.loss_curve.quantile

        return self.HazardMetadata(investigation_time,
                                   statistics, quantile,
                                   sm_lt_path, gsim_lt_path)


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
    output = djm.OneToOneField('Output')
    # FK only required for non-statistical results (i.e., mean or quantile
    # curves).
    lt_realization = djm.ForeignKey('LtRealization', null=True)
    investigation_time = djm.FloatField()
    imt = djm.TextField(choices=IMT_CHOICES)
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

    def __str__(self):
        return (
            'HazardMap(poe=%(poe)s, imt=%(imt)s, sa_period=%(sa_period)s, '
            'statistics=%(statistics)s, quantile=%(quantile)s)'
        ) % self.__dict__

    def __repr__(self):
        return self.__str__()


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


class HazardCurve(djm.Model):
    '''
    Hazard Curve header information
    '''
    output = djm.OneToOneField('Output', null=True)
    # FK only required for non-statistical results (i.e., mean or quantile
    # curves).
    lt_realization = djm.ForeignKey('LtRealization', null=True)
    investigation_time = djm.FloatField()
    imt = djm.TextField(choices=IMT_CHOICES, default=None, blank=True)
    imls = fields.FloatArrayField()
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'quantile', u'Quantile'),
    )
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)

    class Meta:
        db_table = 'hzrdr\".\"hazard_curve'

    @property
    def imt_long(self):
        """
        :returns: a string representing the imt associated with the
        curve (if any) in the long form, e.g. SA(0.01)
        """
        if self.imt:
            if self.imt == "SA":
                return "%s(%s)" % (self.imt, self.sa_damping)
            else:
                return self.imt

    def __iter__(self):
        assert self.output.output_type == 'hazard_curve_multi'

        siblings = self.__class__.objects.filter(
            output__oq_job=self.output.oq_job,
            output__output_type='hazard_curve')

        if not self.statistics:
            return iter(siblings.filter(lt_realization__isnull=False))
        elif self.quantile:
            return iter(
                siblings.filter(statistics="quantile", quantile=self.quantile))
        else:
            return iter(siblings.filter(statistics="mean"))


class HazardCurveDataManager(djm.GeoManager):
    """
    Manager class to filter and create HazardCurveData objects
    """

    def all_curves_for_imt(self, job, imt, sa_period, sa_damping):
        """
        Helper function for creating a :class:`django.db.models.query.QuerySet`
        for selecting all curves from all realizations for a given ``job_id``
        and ``imt``.

        :param job:
            An :class:`openquake.engine.db.models.OqJob` instance.
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
    output = djm.OneToOneField('Output')
    # If `lt_realization` is None, this is a `complete logic tree`
    # Stochastic Event Set Collection, containing a single stochastic
    # event set containing all of the ruptures from the entire
    # calculation.
    lt_realization = djm.ForeignKey('LtRealization', null=True)

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
    is_multi_surface = djm.BooleanField()
    # The following fields can be interpreted different ways, depending on the
    # value of `is_from_fault_source`.
    # If `is_from_fault_source` is True, each of these fields should contain a
    # 2D numpy array (all of the same shape). Each triple of (lon, lat, depth)
    # for a given index represents the node of a rectangular mesh.
    # If `is_from_fault_source` is False, each of these fields should contain
    # a sequence (tuple, list, or numpy array, for example) of 4 values. In
    # order, the triples of (lon, lat, depth) represent top left, top right,
    # bottom left, and bottom right corners of the the rupture's planar
    # surface.
    # Update:
    # There is now a third case. If the rupture originated from a
    # characteristic fault source with a multi-planar-surface geometry,
    # `lons`, `lats`, and `depths` will contain one or more sets of 4 points,
    # similar to how planar surface geometry is stored (see above).
    lons = fields.PickleField()
    lats = fields.PickleField()
    depths = fields.PickleField()

    # HazardLib Surface object. Stored as it is needed by risk disaggregation
    surface = fields.PickleField()

    result_grp_ordinal = djm.IntegerField()
    # NOTE(LB): The ordinal of a rupture within a given result group (indicated
    # by ``result_grp_ordinal``). This rupture correspond to the indices of the
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
        if not (self.is_from_fault_source or self.is_multi_surface):
            self._validate_planar_surface()
            return self.lons[0], self.lats[0], self.depths[0]
        return None

    @property
    def top_right_corner(self):
        if not (self.is_from_fault_source or self.is_multi_surface):
            self._validate_planar_surface()
            return self.lons[1], self.lats[1], self.depths[1]
        return None

    @property
    def bottom_left_corner(self):
        if not (self.is_from_fault_source or self.is_multi_surface):
            self._validate_planar_surface()
            return self.lons[2], self.lats[2], self.depths[2]
        return None

    @property
    def bottom_right_corner(self):
        if not (self.is_from_fault_source or self.is_multi_surface):
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

    class Meta:
        db_table = 'hzrdr\".\"gmf_set'

    @property
    def stochastic_event_set_id(self):
        """

        :returns:
            The ID of the stochastic event set which this ground motion field
            set has been generated from.
        """
        if self.ses_ordinal is None:  # complete logic tree
            job = self.gmf_collection.output.oq_job
            return SES.objects.get(
                ordinal=None,
                ses_collection__output__oq_job=job).id
        else:
            rlz = self.gmf_collection.lt_realization
            return SES.objects.get(
                ses_collection__lt_realization=rlz,
                ordinal=self.ses_ordinal).id

    # Disabling pylint for 'Too many local variables'
    # pylint: disable=R0914
    def __iter__(self):
        """
        Iterator for walking through all child :class:`Gmf` objects.
        """
        return self.iter_gmfs()

    def iter_gmfs(self, location=None, num_tasks=None, imts=None):
        """
        Queries for and iterates over child :class:`Gmf` records, with the
        option of specifying a ``location``.

        :param location:
            An (optional) parameter for filtering :class:`GMFs <Gmf>`.
            ``location`` is expected to be a point represented as WKT.

            Example: `POINT(21.1 45.8)`

       :param num_tasks:
            If given, only the result_grp_ordinal <= num_tasks are returned,
            otherwise there is no filtering; this is used only in a test and
            will disappear in the future

        :param imts:
            A list of IMT triples; if not given, all the calculated IMTs
            are taken in consideration (no filtering)
        """
        job = self.gmf_collection.output.oq_job
        if self.ses_ordinal is None:  # complete logic tree
            # Get all of the GmfSets associated with a logic tree realization,
            # for this calculation.
            lt_gmf_sets = GmfSet.objects\
                .filter(
                    gmf_collection__output__oq_job=job,
                    gmf_collection__lt_realization__isnull=False)\
                .order_by('id')
            for gmf in itertools.chain(
                    *(each_set.iter_gmfs(location=location)
                      for each_set in lt_gmf_sets)):
                yield gmf
        else:
            num_tasks = num_tasks or \
                JobStats.objects.get(oq_job=job.id).num_tasks
            imts = imts or \
                map(parse_imt, job.hazard_calculation.intensity_measure_types)

            for imt, sa_period, sa_damping in imts:
                for result_grp_ordinal in xrange(1, num_tasks + 1):
                    gmfs = order_by_location(
                        Gmf.objects.filter(
                            gmf_set=self.id,
                            imt=imt,
                            sa_period=sa_period,
                            sa_damping=sa_damping,
                            result_grp_ordinal=result_grp_ordinal))
                    if location is not None:
                        gmfs = gmfs.extra(
                            # The `location` field is a GEOGRAPHY type, so an
                            # explicit cast is needed to compare geometry:
                            where=["location::geometry ~= "
                                   "'SRID=4326;%s'::geometry" % location]
                        )

                    if len(gmfs) == 0:
                        # There are no GMFs in this result group for the given
                        # search parameters.
                        continue

                    # collect gmf nodes for each event
                    gmf_nodes = collections.OrderedDict()
                    for gmf in gmfs:
                        for gmv, rupture_id in zip(gmf.gmvs, gmf.rupture_ids):
                            if not rupture_id in gmf_nodes:
                                gmf_nodes[rupture_id] = []
                            gmf_nodes[rupture_id].append(
                                _GroundMotionFieldNode(
                                    gmv=gmv, location=gmf.location))

                    # then yield ground motion fields for each rupture
                    first = gmfs[0]
                    for rupture_id in gmf_nodes:
                        yield _GroundMotionField(
                            imt=first.imt, sa_period=first.sa_period,
                            sa_damping=first.sa_damping,
                            rupture_id=rupture_id,
                            gmf_nodes=gmf_nodes[rupture_id])


class _GroundMotionField(object):

    def __init__(self, imt, sa_period, sa_damping, rupture_id, gmf_nodes):
        self.imt = imt
        self.sa_period = sa_period
        self.sa_damping = sa_damping
        self.rupture_id = rupture_id
        self.gmf_nodes = gmf_nodes

    def __iter__(self):
        return iter(self.gmf_nodes)

    def __getitem__(self, key):
        return self.gmf_nodes[key]

    def __str__(self):
        """
        String representation of a _GroundMotionField object showing the
        content of the nodes (lon, lat an gmv). This is useful for debugging
        and testing.
        """
        mdata = ('imt=%(imt)s sa_period=%(sa_period)s '
                 'sa_damping=%(sa_damping)s rupture_id=%(rupture_id)d' %
                 vars(self))
        return 'GMF(%s\n%s)' % (mdata, '\n'.join(map(str, self.gmf_nodes)))


class _GroundMotionFieldNode(object):

    def __init__(self, gmv, location):
        self.gmv = gmv
        self.location = location  # must have x and y attributes

    def __str__(self):
        "Return lon, lat and gmv of the node in a compact string form"
        return '<X=%9.5f, Y=%9.5f, GMV=%9.7f>' % (
            self.location.x, self.location.y, self.gmv)


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
    rupture_ids = fields.IntArrayField()
    result_grp_ordinal = djm.IntegerField()

    objects = djm.GeoManager()

    class Meta:
        db_table = 'hzrdr\".\"gmf'


class GmfAgg(djm.Model):
    """
    Ground Motion Field: A collection of ground motion values and their
    respective geographical locations.
    """
    gmf_collection = djm.ForeignKey('GmfCollection')
    imt = djm.TextField(choices=IMT_CHOICES)
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)
    location = djm.PointField(srid=DEFAULT_SRID)
    gmvs = fields.FloatArrayField()
    rupture_ids = fields.IntArrayField()

    objects = djm.GeoManager()

    class Meta:
        db_table = 'hzrdr\".\"gmf_agg'


class GmfScenario(djm.Model):
    """
    Ground Motion Field: A collection of ground motion values and their
    respective geographical locations.
    """
    output = djm.ForeignKey('Output')
    imt = djm.TextField()
    location = djm.PointField(srid=DEFAULT_SRID)
    gmvs = fields.FloatArrayField()

    objects = djm.GeoManager()

    class Meta:
        db_table = 'hzrdr\".\"gmf_scenario'


def get_gmvs_per_site(output, imt=None, sort=sorted):
    """
    Iterator for walking through all :class:`GmfScenario` objects associated
    to a given output. Notice that values for the same site are
    displayed together and then ordered according to the iml, so that
    it is possible to get reproducible outputs in the test cases.

    :param output: instance of :class:`openquake.engine.db.models.Output`

    :param string imt: a string with the IMT to extract; the default
                       is None, all the IMT in the job.ini file are extracted

    :param sort: callable used for sorting the list of ground motion values.

    :returns: a list of ground motion values per each site
    """
    job = output.oq_job
    hc = job.hazard_calculation
    if imt is None:
        imts = [parse_imt(x) for x in hc.intensity_measure_types]
    else:
        imts = [parse_imt(imt)]
    for imt, sa_period, _ in imts:
        if imt == 'SA':
            imt = 'SA(%s)' % sa_period
        for gmf in order_by_location(
                GmfScenario.objects.filter(output__id=output.id, imt=imt)):
            yield sort(gmf.gmvs)


def get_gmfs_scenario(output, imt=None):
    """
    Iterator for walking through all :class:`GmfScenario` objects associated
    to a given output. Notice that the fields are ordered according to the
    location, so it is possible to get reproducible outputs in the test cases.

    :param output: instance of :class:`openquake.engine.db.models.Output`

    :param string imt: a string with the IMT to extract; the default
                       is None, all the IMT in the job.ini file are extracted

    :returns: an iterator over
              :class:`openquake.engine.db.models._GroundMotionField` instances
    """
    job = output.oq_job
    hc = job.hazard_calculation
    if imt is None:
        imts = [parse_imt(x) for x in hc.intensity_measure_types]
    else:
        imts = [parse_imt(imt)]
    for imt, sa_period, sa_damping in imts:
        imt_long = 'SA(%s)' % sa_period if imt == 'SA' else imt
        nodes = collections.defaultdict(list)  # realization -> gmf_nodes
        for gmf in GmfScenario.objects.filter(
                output__id=output.id, imt=imt_long):
            for i, gmv in enumerate(gmf.gmvs):  # i is the realization index
                nodes[i].append(
                    _GroundMotionFieldNode(gmv=gmv, location=gmf.location))
        for gmf_nodes in nodes.itervalues():
            yield _GroundMotionField(
                imt=imt,
                sa_period=sa_period,
                sa_damping=sa_damping,
                rupture_id=None,
                gmf_nodes=sorted(gmf_nodes, key=operator.attrgetter('gmv')))


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

    output = djm.OneToOneField('Output')
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


class UHS(djm.Model):
    """
    UHS/Uniform Hazard Spectra:
    * "Uniform" meaning "the same PoE"
    * "Spectrum" because it covers a range/band of periods/frequencies

    Records in this table contain metadata for a collection of UHS data.
    """
    output = djm.OneToOneField('Output', null=True)
    # FK only required for non-statistical results (i.e., mean or quantile
    # curves).
    lt_realization = djm.ForeignKey('LtRealization', null=True)
    investigation_time = djm.FloatField()
    poe = djm.FloatField()
    periods = fields.FloatArrayField()
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'quantile', u'Quantile'),
    )
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)

    class Meta:
        db_table = 'hzrdr\".\"uhs'

    def __iter__(self):
        """
        Iterate over the :class:`UHSData` which belong this object.
        """
        return self.uhsdata_set.iterator()


class UHSData(djm.Model):
    """
    UHS curve for a given location.
    """
    uhs = djm.ForeignKey('UHS')
    imls = fields.FloatArrayField()
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'hzrdr\".\"uhs_data'


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


class LossFraction(djm.Model):
    """
    Holds metadata for loss fraction data
    """
    output = djm.OneToOneField("Output", related_name="loss_fraction")
    variable = djm.TextField(choices=(("taxonomy", "taxonomy"),
                                      ("magnitude_distance",
                                       "Magnitude Distance"),
                                      ("coordinate", "Coordinate")))
    hazard_output = djm.ForeignKey(
        "Output", related_name="risk_loss_fractions")
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)
    poe = djm.FloatField(null=True)

    class Meta:
        db_table = 'riskr\".\"loss_fraction'

    def display_value(self, value, rc):
        """
        Converts `value` in a form that is best suited to be
        displayed.

        :param rc:
           A `RiskCalculation` object used to get the bin width

        :returns: `value` if the attribute `variable` is equal to
           taxonomy. if the attribute `variable` is equal to
           `magnitude-distance`, then it extracts two integers (comma
           separated) from `value` and convert them into ranges
           encoded back as csv.
        """

        if self.variable == "taxonomy":
            return value
        elif self.variable == "magnitude_distance":
            magnitude, distance = map(float, value.split(","))
            return "%.4f,%.4f|%.4f,%.4f" % (
                magnitude * rc.mag_bin_width,
                (magnitude + 1) * rc.mag_bin_width,
                distance * rc.distance_bin_width,
                (distance + 1) * rc.distance_bin_width)
        elif self.variable == "coordinate":
            lon, lat = map(float, value.split(","))
            return "%.4f,%.4f|%.4f,%.4f" % (
                lon * rc.coordinate_bin_width,
                (lon + 1) * rc.coordinate_bin_width,
                lat * rc.coordinate_bin_width,
                (lat + 1) * rc.coordinate_bin_width)
        else:
            raise RuntimeError(
                "disaggregation of type %s not supported" % self.variable)

    def total_fractions(self):
        """
        :returns: a dictionary mapping values of `variable` (e.g. a
        taxonomy) to tuples yielding the associated absolute losses
        (e.g. the absolute losses for assets of a taxonomy) and the
        percentage (expressed in decimal format) over the total losses
        """
        cursor = connections['job_init'].cursor()

        total = self.lossfractiondata_set.aggregate(
            djm.Sum('absolute_loss')).values()[0]

        if not total:
            return {}

        query = """
        SELECT value, sum(absolute_loss)
        FROM riskr.loss_fraction_data
        WHERE loss_fraction_id = %s
        GROUP BY value
        """
        cursor.execute(query, (self.id,))

        rc = self.output.oq_job.risk_calculation

        return collections.OrderedDict(
            sorted(
                [(self.display_value(value, rc), (loss, loss / total))
                 for value, loss in cursor],
                key=lambda kv: kv[1][0]))

    def iteritems(self):
        """
        Yields tuples with two elements. The first one is a location
        (described by a lon/lat tuple), the second one is a dictionary
        modeling the disaggregation of the losses on such location. In
        this dictionary, each key is a value of `variable`, and each
        corresponding value is a tuple holding the absolute losses and
        the fraction of losses occurring in that location.
        """
        rc = self.output.oq_job.risk_calculation
        cursor = connections['job_init'].cursor()

        # Partition by lon,lat because partitioning on geometry types
        # seems not supported in postgis 1.5
        query = """
        SELECT lon, lat, value,
               fraction_loss,
               SUM(fraction_loss) OVER w,
               COUNT(*) OVER w
        FROM (SELECT ST_X(location) as lon,
                     ST_Y(location) as lat,
              value, sum(absolute_loss) as fraction_loss
              FROM riskr.loss_fraction_data
              WHERE loss_fraction_id = %s
              GROUP BY location, value) g
        WINDOW w AS (PARTITION BY lon, lat)
        """

        cursor.execute(query, (self.id, ))

        def display_value_and_fractions(value, absolute_loss, total_loss):
            display_value = self.display_value(value, rc)

            if total_loss > 0:
                fraction = absolute_loss / total_loss
            else:
                # When a rupture is associated with a positive ground
                # shaking (gmv > 0) but with a loss = 0, we still
                # store this information. In that case, total_loss =
                # absolute_loss = 0
                fraction = 0
            return display_value, fraction

        # We iterate on loss fraction data by location in two steps.
        # First we fetch a loss fraction for a single location and a
        # single value. In the same query we get the number `count` of
        # bins stored for such location. Then, we fetch `count` - 1
        # fractions to finalize the fractions on the current location.

        while 1:
            data = cursor.fetchone()
            if data is None:
                raise StopIteration
            lon, lat, value, absolute_loss, total_loss, count = data

            display_value, fraction = display_value_and_fractions(
                value, absolute_loss, total_loss)
            node = [(lon, lat),
                    {display_value: (absolute_loss, fraction)}]

            data = cursor.fetchmany(count - 1)

            for lon, lat, value, absolute_loss, total_loss, count in data:
                display_value, fraction = display_value_and_fractions(
                    value, absolute_loss, total_loss)
                node[1][display_value] = (absolute_loss, fraction)

            node[1] = collections.OrderedDict(
                sorted([(k, v) for k, v in node[1].items()],
                       key=lambda kv: kv[1][0]))
            yield node


class LossFractionData(djm.Model):
    loss_fraction = djm.ForeignKey(LossFraction)
    location = djm.PointField(srid=DEFAULT_SRID)
    value = djm.TextField()
    absolute_loss = djm.TextField()

    class Meta:
        db_table = 'riskr\".\"loss_fraction_data'


class LossMap(djm.Model):
    '''
    Holds metadata for loss maps
    '''

    output = djm.OneToOneField("Output", related_name="loss_map")
    hazard_output = djm.OneToOneField("Output", related_name="risk_loss_map")
    insured = djm.BooleanField(default=False)
    poe = djm.FloatField(null=True)
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)

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


class AggregateLoss(djm.Model):
    output = djm.OneToOneField("Output")
    insured = djm.BooleanField(default=False)
    mean = djm.FloatField()
    std_dev = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"aggregate_loss'


class LossCurve(djm.Model):
    '''
    Holds the parameters common to a set of loss curves
    '''

    output = djm.OneToOneField("Output", related_name="loss_curve")
    hazard_output = djm.OneToOneField("Output", related_name="risk_loss_curve")
    aggregate = djm.BooleanField(default=False)
    insured = djm.BooleanField(default=False)

    # If the curve is a result of an aggregation over different
    # hazard_output the following fields must be set
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)

    class Meta:
        db_table = 'riskr\".\"loss_curve'


class LossCurveData(djm.Model):
    '''
    Holds the probabilities of exceedance for a given loss curve
    '''

    loss_curve = djm.ForeignKey("LossCurve")
    asset_ref = djm.TextField()
    asset_value = djm.FloatField()
    loss_ratios = fields.FloatArrayField()
    poes = fields.FloatArrayField()
    location = djm.PointField(srid=DEFAULT_SRID)
    average_loss_ratio = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"loss_curve_data'

    @property
    def losses(self):
        return numpy.array(self.loss_ratios) * self.asset_value

    @property
    def average_loss(self):
        return self.average_loss_ratio * self.asset_value


class AggregateLossCurveData(djm.Model):
    '''
    Holds the probabilities of exceedance for the whole exposure model
    '''

    loss_curve = djm.OneToOneField("LossCurve")
    losses = fields.FloatArrayField()
    poes = fields.FloatArrayField()
    average_loss = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"aggregate_loss_curve_data'


class EventLoss(djm.Model):
    """
    Holds the aggregate loss we have for each rupture
    """

    #: Foreign key to an :class:`openquake.engine.db.models.Output`
    #: object with output_type == event_loss
    output = djm.OneToOneField('Output')
    rupture = djm.ForeignKey('SESRupture')
    aggregate_loss = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"event_loss'


class BCRDistribution(djm.Model):
    '''
    Holds metadata for the benefit-cost ratio distribution
    '''

    output = djm.OneToOneField("Output", related_name="bcr_distribution")
    hazard_output = djm.OneToOneField(
        "Output", related_name="risk_bcr_distribution")

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
    risk_calculation = djm.ForeignKey("RiskCalculation")
    dmg_state = djm.TextField(
        help_text="The name of the damage state")
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

## Tables in the 'riski' schema.


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
        db_table = 'riski\".\"exposure_model'

    def taxonomies_in(self, region_constraint):
        """
        :param str region_constraint:
            polygon in wkt format the assets must be contained into
        :returns:
            A dictionary mapping each taxonomy with the number of assets
            contained in `region_constraint`
        """

        return ExposureData.objects.taxonomies_contained_in(
            self.id, region_constraint)

    def get_asset_chunk(self, taxonomy, region_constraint, offset, count):
        """

        :param str taxonomy:
            The taxonomy of the returned objects.
        :param Polygon region_constraint:
            A Polygon object with a wkt property used to filter the exposure.
        :param int offset:
            An offset used to paginate the returned set.
        :param int count:
            An offset used to paginate the returned set.

        :returns:
            A list of `openquake.engine.db.models.ExposureData` objects of a
            given taxonomy contained in a region and paginated.
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
        db_table = 'riski\".\"occupancy'


class AssetManager(djm.GeoManager):
    """
    Asset manager
    """
    def contained_in(self, exposure_model_id, taxonomy,
                     region_constraint, offset, size):
        """
        :returns the asset ids (ordered by location) contained in
        `region_constraint` of `taxonomy` associated with an
        `openquake.engine.db.models.ExposureModel` with ID equal to
        `exposure_model_id`
        """

        return list(
            self.raw("""
            SELECT * FROM riski.exposure_data
            WHERE exposure_model_id = %s AND taxonomy = %s AND
            ST_COVERS(ST_GeographyFromText(%s), site)
            ORDER BY ST_X(geometry(site)), ST_Y(geometry(site))
            LIMIT %s OFFSET %s
            """, [exposure_model_id, taxonomy,
                  "SRID=4326; %s" % region_constraint.wkt,
                  size, offset]))

    def taxonomies_contained_in(self, exposure_model_id, region_constraint):
        """

        :returns:
            A dictionary which map each taxonomy associated with
            `exposure_model` and contained in `region_constraint` with the
            number of assets.
        """
        cursor = connections['job_init'].cursor()

        cursor.execute("""
        SELECT riski.exposure_data.taxonomy, COUNT(*)
        FROM riski.exposure_data WHERE
        exposure_model_id = %s AND ST_COVERS(ST_GeographyFromText(%s), site)
        group by riski.exposure_data.taxonomy
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
        db_table = 'riski\".\"exposure_data'

    def __str__(self):
        return "%s (%s-%s @ %s)" % (
            self.id, self.exposure_model_id, self.asset_ref, self.site)

    @staticmethod
    def per_asset_value(
            cost, cost_type, area, area_type, number_of_units, category):
        """
        Return per-asset value for the given exposure data set.

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

        :returns:
            The per-asset value as a `float`.
        :raises:
            `ValueError` in case of a malformed (risk exposure data) input.
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
        """
        The structural per-asset value.
        """
        return self.per_asset_value(
            cost=self.stco, cost_type=self.exposure_model.stco_type,
            area=self.area, area_type=self.exposure_model.area_type,
            number_of_units=self.number_of_units,
            category=self.exposure_model.category)

    @property
    def retrofitting_cost(self):
        """
        The retrofitting per-asset value.
        """
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
    result_matrix = fields.NumpyListField(default=None)

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
