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

import StringIO
import collections
import itertools
import operator
import os
import re
from datetime import datetime


def set_django_settings_module():
    if not os.getenv('DJANGO_SETTINGS_MODULE', False):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'openquake.engine.settings'

set_django_settings_module()


import numpy
from scipy import interpolate

from django.db import transaction, connections
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.gis.db import models as djm
from shapely import wkt

from openquake.hazardlib import geo as hazardlib_geo
from openquake.hazardlib import source as hazardlib_source
import openquake.hazardlib.site

from openquake.engine.db import fields
from openquake.engine import writer


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


#: Kind of supported type of loss outputs
LOSS_TYPES = ["structural", "nonstructural", "fatalities", "contents"]


#: relative tolerance to consider two risk outputs (almost) equal
RISK_RTOL = 0.05


#: absolute tolerance to consider two risk outputs (almost) equal
RISK_ATOL = 0.01


#: Hold both a Vulnerability function or a fragility function set and
#: the IMT associated to it
RiskModel = collections.namedtuple(
    'RiskModel',
    'imt vulnerability_function fragility_functions')


def required_imts(risk_models):
    """
    Get all the intensity measure types required by `risk_models`

    A nested dict taxonomy -> loss_type -> `RiskModel` instance

    :returns: a set with all the required imts
    """
    risk_models = sum([d.values() for d in risk_models.values()], [])
    return set([m.imt for m in risk_models])


def loss_types(risk_models):
    return set(sum([d.keys() for d in risk_models.values()], []))


def cost_type(loss_type):
    if loss_type == "fatalities":
        return "occupants"
    else:
        return loss_type


def risk_almost_equal(o1, o2, key=lambda x: x, rtol=RISK_RTOL, atol=RISK_ATOL):
    return numpy.testing.assert_allclose(
        numpy.array(key(o1)), numpy.array(key(o2)), rtol=rtol, atol=atol)


def loss_curve_almost_equal(curve, expected_curve):
    if curve.losses[curve.losses > 0].any():
        poes = interpolate.interp1d(
            curve.losses, curve.poes,
            bounds_error=False, fill_value=0)(expected_curve.losses)
    else:
        poes = numpy.zeros(len(expected_curve.poes))

    return risk_almost_equal(poes, expected_curve.poes)


def getcursor(route):
    """Return a cursor from a Django route"""
    return connections[route].cursor()


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


def get_site_model(hc_id):
    """Get the site model :class:`~openquake.engine.db.models.Input` record
    for the given job id.

    :param int hc_id:
        The id of a :class:`~openquake.engine.db.models.HazardCalculation`.

    :returns:
        The site model :class:`~openquake.engine.db.models.Input` record for
        this job.
    :raises:
        :exc:`RuntimeError` if the job has more than 1 site model.
    """
    site_model = inputs4hcalc(hc_id, input_type='site_model')

    if len(site_model) == 0:
        return None
    elif len(site_model) > 1:
        # Multiple site models for 1 job are not allowed.
        raise RuntimeError("Only 1 site model per job is allowed, found %s."
                           % len(site_model))

    # There's only one site model.
    return site_model[0]


## TODO: this could be implemented with a view, now that there is a site table
def get_closest_site_model_data(input_model, point):
    """Get the closest available site model data from the database for a given
    site model :class:`~openquake.engine.db.models.Input` and
    :class:`openquake.hazardlib.geo.point.Point`.

    :param input_model:
        :class:`openquake.engine.db.models.Input` with `input_type` of
        'site_model'.
    :param site:
        :class:`openquake.hazardlib.geo.point.Point` instance.

    :returns:
        The closest :class:`openquake.engine.db.models.SiteModel` for the given
        ``input_model`` and ``point`` of interest.

        This function uses the PostGIS `ST_Distance_Sphere
        <http://postgis.refractions.net/docs/ST_Distance_Sphere.html>`_
        function to calculate distance.

        If there is no site model data, return `None`.
    """
    query = """
    SELECT
        hzrdi.site_model.*,
        min(ST_Distance_Sphere(location, %s))
            AS min_distance
    FROM hzrdi.site_model
    WHERE input_id = %s
    GROUP BY id
    ORDER BY min_distance
    LIMIT 1;"""

    raw_query_set = SiteModel.objects.raw(
        query, ['SRID=4326; %s' % point.wkt2d, input_model.id]
    )

    site_model_data = list(raw_query_set)

    assert len(site_model_data) <= 1, (
        "This query should return at most 1 record.")

    if len(site_model_data) == 1:
        return site_model_data[0]


# FIXME (ms): this is needed until we fix SiteCollection in hazardlib;
# the issue is the reset of the depts; we need QA tests for that
class SiteCollection(openquake.hazardlib.site.SiteCollection):
    cache = {}  # hazard_calculation_id -> site_collection

    def __init__(self, sites):
        super(SiteCollection, self).__init__(sites)
        self.sites_dict = dict((s.id, s) for s in sites)

    def subcollection(self, indices):
        """
        :param indices:
            an array of integer identifying the ordinal of the sites
            to select. Sites are ordered by the value of their id field
        :returns:
            `self` is `indices` is None, otherwise, a `SiteCollection`
            holding sites at `indices`
        """
        if indices is None:
            return self
        sites = []
        for i, site in enumerate(self):
            if i in indices:
                sites.append(site)
        return self.__class__(sites)

    def __iter__(self):
        ids = sorted(self.sites_dict)
        for site_id in ids:
            yield self.sites_dict[site_id]

    def get_by_id(self, site_id):
        return self.sites_dict[site_id]

    def __contains__(self, site):
        return site.id in self.sites_dict

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
        (u'site_model', u'Site Model'),
        (u'rupture_model', u'Rupture Model'),

        # vulnerability models
        (u'structural_vulnerability', u'Structural Vulnerability'),
        (u'nonstructural_vulnerability', u'Non Structural Vulnerability'),
        (u'contents_vulnerability', u'Contents Vulnerability'),
        (u'business_interruption_vulnerability',
         u'Business Interruption Vulnerability'),
        (u'occupants_vulnerability', u'Occupants Vulnerability'),
        (u'structural_vulnerability_retrofitted',
         u'Structural Vulnerability Retrofitted'))

    VULNERABILITY_TYPE_CHOICES = [choice
                                  for choice in INPUT_TYPE_CHOICES
                                  if choice[0].endswith('vulnerability')]

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

    # contains the raw text of a gzipped UTF-8 input file
    raw_content = fields.GzippedField()
    # `content_type` should be used to indicate the file format
    # (xml, csv, etc.)
    content_type = djm.TextField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:  # pylint: disable=C0111,W0232
        db_table = 'uiapi\".\"model_content'

    @property
    def as_string_io(self):
        """
        Return a `StringIO` object containing the `raw_content` as utf-8 text.
        """
        return StringIO.StringIO(self.raw_content)


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
    hazard_calculation = djm.OneToOneField('HazardCalculation', null=True)
    risk_calculation = djm.OneToOneField('RiskCalculation', null=True)
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
    risklib_version = djm.TextField(null=True, blank=True)
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

    # The timeout is stored in seconds and is 100 hours by default.
    no_progress_timeout = djm.IntegerField(
        default=360000, help_text="what time period w/o any progress is "
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
    random_seed = djm.IntegerField(null=True, blank=True)
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

    def individual_curves_per_location(self):
        """
        Returns the number of individual curves per location, that are
        expected after a full computation of the hazard calculation
        has been performed
        """
        realizations_nr = self.ltrealization_set.count()
        return realizations_nr

    def points_to_compute(self, save_sites=True):
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
                lons, lats = zip(*sorted(set((asset.site.x, asset.site.y)
                                             for asset in assets)))
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
            # store the sites
            if save_sites and self._points_to_compute:
                self.save_sites([(pt.longitude, pt.latitude)
                                 for pt in self._points_to_compute])

        return self._points_to_compute

    @property
    def site_collection(self):
        """
        Create a SiteCollection from a HazardCalculation object.
        First, take all of the points/locations of interest defined by the
        calculation geometry. For each point, do distance queries on the site
        model and get the site parameters which are closest to the point of
        interest. This aggregation of points to the closest site parameters
        is what we store in the `site_collection` field.
        If the computation does not specify a site model the same 4 reference
        site parameters are used for all sites. The sites are ordered by id,
        to ensure reproducibility in tests.
        """
        if self.id in SiteCollection.cache:
            return SiteCollection.cache[self.id]

        site_model_inp = get_site_model(self.id)
        hsites = HazardSite.objects.filter(
            hazard_calculation=self).order_by('id')
        # NB: the sites MUST be ordered. The issue is that the disaggregation
        # calculator has a for loop of kind
        # for site in sites:
        #     bin_edge, disagg_matrix = disaggregation_poissonian(site, ...)
        # the generated ruptures are random if the order of the sites
        # is random, even if the seed is fixed; in particular for some
        # ordering no ruptures are generated and the test
        # qa_tests/hazard/disagg/case_1/test.py fails with a bad
        # error message
        sites = []
        for hsite in hsites:
            pt = openquake.hazardlib.geo.point.Point(
                hsite.location.x, hsite.location.y)
            if site_model_inp:
                smd = get_closest_site_model_data(site_model_inp, pt)
                measured = smd.vs30_type == 'measured'
                vs30 = smd.vs30
                z1pt0 = smd.z1pt0
                z2pt5 = smd.z2pt5
            else:
                vs30 = self.reference_vs30_value
                measured = self.reference_vs30_type == 'measured'
                z1pt0 = self.reference_depth_to_1pt0km_per_sec
                z2pt5 = self.reference_depth_to_2pt5km_per_sec

            sites.append(openquake.hazardlib.site.Site(
                         pt, vs30, measured, z1pt0, z2pt5, hsite.id))

        sitecoll = SiteCollection.cache[self.id] = \
            SiteCollection(sites) if sites else None
        return sitecoll

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

    def save_sites(self, coordinates):
        """
        Save all the gives sites on the hzrdi.hazard_site table.
        :param coordinates: a sequence of (lon, lat) pairs
        :returns: the ids of the inserted HazardSite instances
        """
        sites = [HazardSite(hazard_calculation=self,
                            location='POINT(%s %s)' % coord)
                 for coord in coordinates]
        return writer.CacheInserter.saveall(sites)

    def total_investigation_time(self):
        """
        Helper method to compute the total investigation time for a
        complete set of stochastic event sets for all realizations.
        """
        if self.number_of_logic_tree_samples > 0:
            # The calculation is set to do Monte-Carlo sampling of logic trees
            # The number of logic tree realizations is specified explicitly in
            # job configuration.
            n_lt_realizations = self.number_of_logic_tree_samples
        else:
            # The calculation is set do end-branch enumeration of all logic
            # tree paths
            # We can get the number of logic tree realizations by counting
            # initialized lt_realization records.
            n_lt_realizations = LtRealization.objects.filter(
                hazard_calculation=self).count()

        investigation_time = (self.investigation_time
                              * self.ses_per_logic_tree_path
                              * n_lt_realizations)

        return investigation_time


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

    # The timeout is stored in seconds and is 100 hours by default.
    no_progress_timeout = djm.IntegerField(
        default=360000, help_text="what time period w/o any progress is "
                                "acceptable for calculations?")

    CALC_MODE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'classical_bcr', u'Classical BCR'),
        (u'event_based', u'Probabilistic Event-Based'),
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
    # Gmf) used by the risk calculation
    hazard_output = djm.ForeignKey("Output", null=True, blank=True)

    # the HazardCalculation object used by the risk calculation when
    # each individual Output (i.e. each hazard logic tree realization)
    # is considered
    hazard_calculation = djm.ForeignKey("HazardCalculation",
                                        null=True, blank=True)

    risk_investigation_time = djm.FloatField(
        help_text=('Override the time span (in years) with which the '
                   'hazard has been computed.'),
        null=True,
        blank=True,
    )

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

    ######################################
    # Scenario parameters:
    ######################################
    time_event = fields.NullTextField()

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
        try:
            hcalc = (self.hazard_calculation or
                     self.hazard_output.oq_job.hazard_calculation)
        except ObjectDoesNotExist:
            raise RuntimeError("The provided hazard does not exist")
        return hcalc

    def hazard_outputs(self):
        """
        Returns the list of hazard outputs to be considered. Apply
        `filters` to the default queryset
        """

        if self.hazard_output:
            return [self.hazard_output]
        elif self.hazard_calculation:
            if self.calculation_mode in ["classical", "classical_bcr"]:
                filters = dict(output_type='hazard_curve_multi',
                               hazard_curve__lt_realization__isnull=False)
            elif self.calculation_mode in ["event_based", "event_based_bcr"]:
                if self.hazard_calculation.ground_motion_fields:
                    filters = dict(output_type='gmf',
                                   gmf__lt_realization__isnull=False)
                else:
                    filters = dict(
                        output_type='ses',
                        ses__lt_realization__isnull=False)
            elif self.calculation_mode in ['scenario', 'scenario_damage']:
                filters = dict(output_type='gmf_scenario')
            else:
                raise NotImplementedError

            return self.hazard_calculation.oqjob.output_set.filter(
                **filters).order_by('id')
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
        try:
            return self.get_exposure_input().exposuremodel
        except ObjectDoesNotExist:
            return None

    def get_exposure_input(self):
        try:
            return self.exposure_input or self.inputs.get(
                input_type="exposure")
        except ObjectDoesNotExist:
            raise RuntimeError("Calculation has no exposure associated with")

    def vulnerability_inputs(self, retrofitted):
        for loss_type in LOSS_TYPES:
            ctype = cost_type(loss_type)

            vulnerability_input = self.vulnerability_input(ctype, retrofitted)
            if vulnerability_input is not None:
                yield vulnerability_input, loss_type

    def vulnerability_input(self, ctype, retrofitted=False):
        if retrofitted:
            input_type = "%s_vulnerability_retrofitted" % ctype
        else:
            input_type = "%s_vulnerability" % ctype

        queryset = self.inputs.filter(input_type=input_type)
        if queryset.exists():
            return queryset[0]

    @property
    def investigation_time(self):
        return (self.risk_investigation_time or
                self.get_hazard_calculation().investigation_time)


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

    #: Hold the full paths in the model trees of ground shaking
    #: intensity models and of source models, respectively.
    LogicTreePath = collections.namedtuple(
        'logic_tree_path',
        'gsim_path sm_path')

    #: Hold the statistical params (statistics, quantile).
    StatisticalParams = collections.namedtuple(
        'statistical_params',
        'statistics quantile')

    owner = djm.ForeignKey('OqUser')
    oq_job = djm.ForeignKey('OqJob')  # nullable in the case of an output
    # coming from an external source, with no job associated
    display_name = djm.TextField()
    HAZARD_OUTPUT_TYPE_CHOICES = (
        (u'complete_lt_gmf', u'Complete Logic Tree GMF'),
        (u'complete_lt_ses', u'Complete Logic Tree SES'),
        (u'disagg_matrix', u'Disaggregation Matrix'),
        (u'gmf', u'Ground Motion Field'),
        (u'gmf_scenario', u'Ground Motion Field'),
        (u'hazard_curve', u'Hazard Curve'),
        (u'hazard_curve_multi', u'Hazard Curve (multiple imts)'),
        (u'hazard_map', u'Hazard Map'),
        (u'ses', u'Stochastic Event Set'),
        (u'uh_spectra', u'Uniform Hazard Spectra'),
    )

    RISK_OUTPUT_TYPE_CHOICES = (
        (u'agg_loss_curve', u'Aggregate Loss Curve'),
        (u'aggregate_loss', u'Aggregate Losses'),
        (u'bcr_distribution', u'Benefit-cost ratio distribution'),
        (u'collapse_map', u'Collapse Map Distribution'),
        (u'dmg_dist_per_asset', u'Damage Distribution Per Asset'),
        (u'dmg_dist_per_taxonomy', u'Damage Distribution Per Taxonomy'),
        (u'dmg_dist_total', u'Total Damage Distribution'),
        (u'event_loss', u'Event Loss Table'),
        (u'loss_curve', u'Loss Curve'),
        (u'event_loss_curve', u'Loss Curve'),
        (u'loss_fraction', u'Loss fractions'),
        (u'loss_map', u'Loss Map'),
    )

    output_type = djm.TextField(
        choices=HAZARD_OUTPUT_TYPE_CHOICES + RISK_OUTPUT_TYPE_CHOICES)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    objects = OutputManager()

    def __str__(self):
        return "%d||%s||%s" % (self.id, self.output_type, self.display_name)

    class Meta:
        db_table = 'uiapi\".\"output'

    def is_hazard_curve(self):
        return self.output_type in ['hazard_curve', 'hazard_curve_multi']

    @property
    def output_container(self):
        """
        :returns: the output container associated with this output
        """

        # FIXME(lp). Remove the following outstanding exceptions
        if self.output_type in ['agg_loss_curve', 'event_loss_curve']:
            return self.loss_curve
        elif self.output_type == 'hazard_curve_multi':
            return self.hazard_curve
        elif self.output_type == 'gmf_scenario':
            return self.gmf
        elif self.output_type == "complete_lt_gmf":
            return self.gmf
        elif self.output_type == "complete_lt_ses":
            return self.ses

        return getattr(self, self.output_type)

    @property
    def lt_realization_paths(self):
        """
        :returns: an instance of `LogicTreePath` the output is
        associated with. When the output is not associated with any
        logic tree branch then it returns a LogicTreePath namedtuple
        with a couple of None.
        """
        hazard_output_types = [el[0] for el in self.HAZARD_OUTPUT_TYPE_CHOICES]
        risk_output_types = [el[0] for el in self.RISK_OUTPUT_TYPE_CHOICES]
        container = self.output_container

        if self.output_type in hazard_output_types:
            if container.lt_realization_id is not None:
                return self.LogicTreePath(
                    tuple(container.lt_realization.gsim_lt_path),
                    tuple(container.lt_realization.sm_lt_path))
            else:
                return self.LogicTreePath(None, None)
        elif self.output_type in risk_output_types:
            if getattr(container, 'hazard_output_id', None):
                return container.hazard_output.lt_realization_paths
            else:
                return self.LogicTreePath(None, None)

        raise RuntimeError("unexpected output type %s" % self.output_type)

    @property
    def statistical_params(self):
        """
        :returns: an instance of `StatisticalParams` the output is
        associated with
        """
        if getattr(self.output_container, 'statistics', None) is not None:
            return self.StatisticalParams(self.output_container.statistics,
                                          self.output_container.quantile)
        elif getattr(
                self.output_container, 'hazard_output_id', None) is not None:
            return self.output_container.hazard_output.statistical_params
        else:
            return self.StatisticalParams(None, None)

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
        investigation_time = self.oq_job\
                                 .risk_calculation\
                                 .get_hazard_calculation()\
                                 .investigation_time

        statistics, quantile = self.statistical_params
        gsim_lt_path, sm_lt_path = self.lt_realization_paths

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
    output = djm.OneToOneField('Output', related_name="hazard_map")
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
    output = djm.OneToOneField(
        'Output', null=True, related_name="hazard_curve")
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
    output = djm.OneToOneField('Output', related_name="ses")
    # If `lt_realization` is None, this is a `complete logic tree`
    # Stochastic Event Set Collection, containing a single stochastic
    # event set containing all of the ruptures from the entire
    # calculation.
    lt_realization = djm.ForeignKey('LtRealization', null=True)

    class Meta:
        db_table = 'hzrdr\".\"ses_collection'
        ordering = ['lt_realization']

    def __iter__(self):
        """
        Iterator for walking through all child :class:`SES` objects.
        """
        return SES.objects.filter(ses_collection=self.id).order_by('ordinal') \
            .iterator()


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
        ordering = ['ordinal']

    def __iter__(self):
        """
        Iterator for walking through all child :class:`SESRupture` objects.
        """
        return SESRupture.objects.filter(ses=self.id).order_by('tag') \
            .iterator()


def old_field_property(prop):
    def wrapped_property(s):
        if getattr(s, "old_%s" % prop.__name__) is not None:
            return getattr(s, "old_%s" % prop.__name__)
        else:
            return prop(s)
    return property(wrapped_property)


class SESRupture(djm.Model):
    """
    A rupture as part of a Stochastic Event Set.
    """
    ses = djm.ForeignKey('SES')

    #: A pickled
    #: :class:`openquake.hazardlib.source.rupture.ProbabilisticRupture`
    #: instance
    rupture = fields.PickleField()

    # a tag with rlz, ses, src and ordinal info
    tag = djm.TextField()

    old_magnitude = djm.FloatField(null=True)
    old_strike = djm.FloatField(null=True)
    old_dip = djm.FloatField(null=True)
    old_rake = djm.FloatField(null=True)
    old_tectonic_region_type = djm.TextField(null=True)
    old_is_from_fault_source = djm.NullBooleanField(null=True)
    old_is_multi_surface = djm.NullBooleanField(null=True)
    old_lons = fields.PickleField(null=True)
    old_lats = fields.PickleField(null=True)
    old_depths = fields.PickleField(null=True)

    #: A pickled
    #: :class:`openquake.hazardlib.geo.surface.BaseSurface`
    #: instance
    old_surface = fields.PickleField(null=True)

    class Meta:
        db_table = 'hzrdr\".\"ses_rupture'
        ordering = ['tag']

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

    @old_field_property
    def is_from_fault_source(self):
        """
        If True, this rupture was generated from a simple/complex fault
        source. If False, this rupture was generated from a point/area source.
        """
        typology = self.rupture.source_typology
        is_char = typology is hazardlib_source.CharacteristicFaultSource
        is_complex_or_simple = typology in (
            hazardlib_source.ComplexFaultSource,
            hazardlib_source.SimpleFaultSource)
        is_complex_or_simple_surface = isinstance(
            self.rupture.surface, (hazardlib_geo.ComplexFaultSurface,
                                   hazardlib_geo.SimpleFaultSurface))
        return is_complex_or_simple or (
            is_char and is_complex_or_simple_surface)

    @old_field_property
    def is_multi_surface(self):
        typology = self.rupture.source_typology
        is_char = typology is hazardlib_source.CharacteristicFaultSource
        is_multi_sur = isinstance(
            self.rupture.surface, hazardlib_geo.MultiSurface)
        return is_char and is_multi_sur

    def get_geom(self):
        """
        The following fields can be interpreted different ways,
        depending on the value of `is_from_fault_source`. If
        `is_from_fault_source` is True, each of these fields should
        contain a 2D numpy array (all of the same shape). Each triple
        of (lon, lat, depth) for a given index represents the node of
        a rectangular mesh. If `is_from_fault_source` is False, each
        of these fields should contain a sequence (tuple, list, or
        numpy array, for example) of 4 values. In order, the triples
        of (lon, lat, depth) represent top left, top right, bottom
        left, and bottom right corners of the the rupture's planar
        surface. Update: There is now a third case. If the rupture
        originated from a characteristic fault source with a
        multi-planar-surface geometry, `lons`, `lats`, and `depths`
        will contain one or more sets of 4 points, similar to how
        planar surface geometry is stored (see above).
        """
        if self.is_from_fault_source:
            # for simple and complex fault sources,
            # rupture surface geometry is represented by a mesh
            surf_mesh = self.rupture.surface.get_mesh()
            lons = surf_mesh.lons
            lats = surf_mesh.lats
            depths = surf_mesh.depths
        else:
            if self.is_multi_surface:
                # `list` of
                # openquake.hazardlib.geo.surface.planar.PlanarSurface
                # objects:
                surfaces = self.rupture.surface.surfaces

                # lons, lats, and depths are arrays with len == 4*N,
                # where N is the number of surfaces in the
                # multisurface for each `corner_*`, the ordering is:
                #   - top left
                #   - top right
                #   - bottom left
                #   - bottom right
                lons = numpy.concatenate([x.corner_lons for x in surfaces])
                lats = numpy.concatenate([x.corner_lats for x in surfaces])
                depths = numpy.concatenate([x.corner_depths for x in surfaces])
            else:
                # For area or point source,
                # rupture geometry is represented by a planar surface,
                # defined by 3D corner points
                surface = self.rupture.surface
                lons = numpy.zeros((4))
                lats = numpy.zeros((4))
                depths = numpy.zeros((4))

                # NOTE: It is important to maintain the order of these
                # corner points. TODO: check the ordering
                for i, corner in enumerate((surface.top_left,
                                            surface.top_right,
                                            surface.bottom_left,
                                            surface.bottom_right)):
                    lons[i] = corner.longitude
                    lats[i] = corner.latitude
                    depths[i] = corner.depth
        return lons, lats, depths

    @old_field_property
    def lons(self):
        return self.get_geom()[0]

    @old_field_property
    def lats(self):
        return self.get_geom()[1]

    @old_field_property
    def depths(self):
        return self.get_geom()[2]

    @old_field_property
    def surface(self):
        return self.rupture.surface

    @old_field_property
    def magnitude(self):
        return self.rupture.mag

    @old_field_property
    def strike(self):
        return self.rupture.surface.get_strike()

    @old_field_property
    def dip(self):
        return self.rupture.surface.get_dip()

    @old_field_property
    def rake(self):
        return self.rupture.rake

    @old_field_property
    def tectonic_region_type(self):
        return self.rupture.tectonic_region_type


class _GmfsPerSES(object):
    """
    An iterator object storing all the GMFs generated by the
    ruptures in a given SES.
    """
    def __init__(self, gmfs, investigation_time, stochastic_event_set_id):
        self._gmfs = iter(gmfs)
        self.investigation_time = investigation_time
        self.stochastic_event_set_id = stochastic_event_set_id

    def __iter__(self):
        return self

    def next(self):
        return self._gmfs.next()

    def __str__(self):
        return ('GMFsPerSES(investigation_time=%f, '
                'stochastic_event_set_id=%s,\n%s)' % (
                self.investigation_time,
                self.stochastic_event_set_id,
                '\n'.join(sorted(map(str, self._gmfs)))))


class _Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Gmf(djm.Model):
    """
    A collection of ground motion field (GMF) sets for a given logic tree
    realization.
    """
    output = djm.OneToOneField('Output', related_name="gmf")
    # If `lt_realization` is None, this is a `complete logic tree`
    # GMF Collection, containing a single GMF set containing all of the ground
    # motion fields in the calculation.
    lt_realization = djm.ForeignKey('LtRealization', null=True)

    class Meta:
        db_table = 'hzrdr\".\"gmf'

    # NB: uses the helper view gmf_family
    def get_children(self):
        """
        Get the children of a given gmf, if any.
        :returns:
          A list of :class:`openquake.engine.db.models.Gmf` instances
        """
        curs = getcursor('job_init')
        curs.execute('select child_id from hzrdr.gmf_family '
                     'where parent_id=%s', (self.id,))
        return [self.__class__.objects.get(pk=r[0]) for r in curs]

    # this part is tested in models_test:GmfsPerSesTestCase
    def __iter__(self):
        """
        Get the ground motion fields per SES ("GMF set" objects) for
        the XML export. Each "GMF set" should:

            * have an `investigation_time` attribute
            * have an `stochastic_event_set_id` attribute
            * be iterable, yielding a sequence of "GMF" objects

            Each "GMF" object should:

            * have an `imt` attribute
            * have an `sa_period` attribute (only if `imt` is 'SA')
            * have an `sa_damping` attribute (only if `imt` is 'SA')
            * have a `rupture_id` attribute (to indicate which rupture
              contributed to this gmf)
            * be iterable, yielding a sequence of "GMF node" objects

            Each "GMF node" object should have:

            * a `gmv` attribute (to indicate the ground motion value
            * `lon` and `lat` attributes (to indicate the geographical location
              of the ground motion field)
        """
        children = self.get_children()
        if children:  # complete logic tree
            all_gmfs = []
            tot_time = 0.0
            fake_ses_ordinal = 1
            for coll in children:
                for g in coll:
                    all_gmfs.append(g)
                    tot_time += g.investigation_time
            if all_gmfs:
                yield _GmfsPerSES(
                    itertools.chain(*all_gmfs), tot_time, fake_ses_ordinal)
            return
        # leaf of the tree
        ses_coll = SESCollection.objects.get(
            lt_realization=self.lt_realization)

        hc = ses_coll.output.oq_job.hazard_calculation

        for ses in SES.objects.filter(ses_collection=ses_coll
                                      ).order_by('ordinal'):
            query = """
        SELECT imt, sa_period, sa_damping, tag,
               array_agg(gmv) AS gmvs,
               array_agg(ST_X(location::geometry)) AS xs,
               array_agg(ST_Y(location::geometry)) AS ys
        FROM (SELECT imt, sa_period, sa_damping, ses_id,
             unnest(rupture_ids) as rupture_id, location, unnest(gmvs) AS gmv
           FROM hzrdr.gmf_data, hzrdi.hazard_site
           WHERE site_id = hzrdi.hazard_site.id AND hazard_calculation_id=%s
             AND gmf_id=%d AND ses_id=%d) AS x, hzrdr.ses_rupture AS y
        WHERE x.rupture_id = y.id
        GROUP BY imt, sa_period, sa_damping, tag
        ORDER BY imt, sa_period, sa_damping, tag;
        """ % (hc.id, self.id, ses.id)
            with transaction.commit_on_success(using='job_init'):
                curs = getcursor('job_init')
                curs.execute(query)

            def gengmfs(data):
                for imt, sa_period, sa_damping, rupture_tag, gmvs, xs, ys \
                        in data:
                    nodes = [_GroundMotionFieldNode(gmv, _Point(x, y))
                             for gmv, x, y in zip(gmvs, xs, ys)]
                    yield _GroundMotionField(
                        imt, sa_period, sa_damping, rupture_tag, nodes)
            yield _GmfsPerSES(gengmfs(curs), ses.investigation_time,
                              ses.ordinal)


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
                 'sa_damping=%(sa_damping)s rupture_id=%(rupture_id)s' %
                 vars(self))
        nodes = sorted(map(str, self.gmf_nodes))
        return 'GMF(%s\n%s)' % (mdata, '\n'.join(nodes))


class _GroundMotionFieldNode(object):

    # the signature is not (gmv, x, y) because the XML writer expect a location
    # object
    def __init__(self, gmv, loc):
        self.gmv = gmv
        self.location = loc

    def __str__(self):
        "Return lon, lat and gmv of the node in a compact string form"
        return '<X=%9.5f, Y=%9.5f, GMV=%9.7f>' % (
            self.location.x, self.location.y, self.gmv)


class GmfData(djm.Model):
    """
    Ground Motion Field: A collection of ground motion values and their
    respective geographical locations.
    """
    gmf = djm.ForeignKey('Gmf')
    ses = djm.ForeignKey('SES', null=True)
    imt = djm.TextField(choices=IMT_CHOICES)
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)
    gmvs = fields.FloatArrayField()
    rupture_ids = fields.IntArrayField(null=True)
    site = djm.ForeignKey('HazardSite')
    objects = djm.GeoManager()

    class Meta:
        db_table = 'hzrdr\".\"gmf_data'


def get_gmvs_per_site(output, imt=None, sort=sorted):
    """
    Iterator for walking through all :class:`GmfData` objects associated
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
    coll = output.gmf
    if imt is None:
        imts = [parse_imt(x) for x in hc.intensity_measure_types]
    else:
        imts = [parse_imt(imt)]
    for imt, sa_period, sa_damping in imts:
        for gmf in GmfData.objects.filter(
                gmf=coll, imt=imt,
                sa_period=sa_period, sa_damping=sa_damping).\
                order_by('site'):
            yield sort(gmf.gmvs)


def get_gmfs_scenario(output, imt=None):
    """
    Iterator for walking through all :class:`GmfData` objects associated
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
    coll = output.gmf
    if imt is None:
        imts = [parse_imt(x) for x in hc.intensity_measure_types]
    else:
        imts = [parse_imt(imt)]
    for imt, sa_period, sa_damping in imts:
        nodes = collections.defaultdict(list)  # realization -> gmf_nodes
        for gmf in GmfData.objects.filter(
                gmf=coll, imt=imt,
                sa_period=sa_period, sa_damping=sa_damping):
            for i, gmv in enumerate(gmf.gmvs):  # i is the realization index
                nodes[i].append(_GroundMotionFieldNode(gmv, gmf.site.location))
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

    output = djm.OneToOneField('Output', related_name="disagg_matrix")
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


class UHS(djm.Model):
    """
    UHS/Uniform Hazard Spectra:
    * "Uniform" meaning "the same PoE"
    * "Spectrum" because it covers a range/band of periods/frequencies

    Records in this table contain metadata for a collection of UHS data.
    """
    output = djm.OneToOneField('Output', null=True, related_name="uh_spectra")
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
    loss_type = djm.TextField(choices=zip(LOSS_TYPES, LOSS_TYPES))

    class Meta:
        db_table = 'riskr\".\"loss_fraction'

    def __iter__(self):
        return iter(self.lossfractiondata_set.all())

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type,
                self.output.hazard_metadata,
                self.statistics, self.quantile,
                self.variable, self.poe, self.loss_type)

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

        loss_fraction = collections.namedtuple('loss_fraction', 'bin loss')

        return collections.OrderedDict(
            sorted(
                [loss_fraction(
                    self.display_value(value, rc),
                    (loss, loss / total))
                 for value, loss in cursor],
                key=operator.attrgetter('loss'),
                reverse=True))

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
                       key=lambda kv: kv[0]))
            yield node

    def to_array(self):
        """
        :returns: the loss fractions as numpy array

        :NOTE:  (not memory efficient)
        """
        def to_tuple():
            for (lon, lat), data in self.iteritems():
                for taxonomy, (absolute_loss, fraction) in data.items():
                    yield lon, lat, taxonomy, absolute_loss, fraction

        return numpy.array(list(to_tuple()), dtype='f4, f4, S3, f4, f4')


class LossFractionData(djm.Model):
    loss_fraction = djm.ForeignKey(LossFraction)
    location = djm.PointField(srid=DEFAULT_SRID)
    value = djm.TextField()
    absolute_loss = djm.TextField()

    class Meta:
        db_table = 'riskr\".\"loss_fraction_data'

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return (self.loss_fraction.output_hash +
                ("%.5f" % self.location.x, "%.5f" % self.location.y,
                 self.value))

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data, operator.attrgetter('absolute_loss'))


class LossMap(djm.Model):
    '''
    Holds metadata for loss maps
    '''

    output = djm.OneToOneField("Output", related_name="loss_map")
    hazard_output = djm.ForeignKey("Output", related_name="risk_loss_maps")
    insured = djm.BooleanField(default=False)
    poe = djm.FloatField(null=True)
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)
    loss_type = djm.TextField(choices=zip(LOSS_TYPES, LOSS_TYPES))

    class Meta:
        db_table = 'riskr\".\"loss_map'

    def __iter__(self):
        return iter(self.lossmapdata_set.all())

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type,
                self.output.hazard_metadata,
                self.statistics, self.quantile,
                self.insured, self.poe, self.loss_type)


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

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.loss_map.output_hash + (self.asset_ref,)

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data, operator.attrgetter('value', 'stddev'))


class AggregateLoss(djm.Model):
    output = djm.OneToOneField("Output", related_name="aggregate_loss")
    insured = djm.BooleanField(default=False)
    mean = djm.FloatField()
    std_dev = djm.FloatField()
    loss_type = djm.TextField(choices=zip(LOSS_TYPES, LOSS_TYPES))

    class Meta:
        db_table = 'riskr\".\"aggregate_loss'

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type,
                self.output.hazard_metadata,
                self.insured,
                self.mean, self.std_dev,
                self.loss_type)

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.output_hash

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data, lambda x: operator.attrgetter('mean', 'std_dev'))


class LossCurve(djm.Model):
    '''
    Holds the parameters common to a set of loss curves
    '''

    output = djm.OneToOneField("Output", related_name="loss_curve")
    hazard_output = djm.ForeignKey("Output", related_name="risk_loss_curves")
    aggregate = djm.BooleanField(default=False)
    insured = djm.BooleanField(default=False)

    # If the curve is a result of an aggregation over different
    # hazard_output the following fields must be set
    statistics = djm.TextField(null=True, choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)
    loss_type = djm.TextField(choices=zip(LOSS_TYPES, LOSS_TYPES))

    class Meta:
        db_table = 'riskr\".\"loss_curve'

    def __iter__(self):
        if self.aggregate:
            return iter([self.aggregatelosscurvedata])
        else:
            return iter(self.losscurvedata_set.all())

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type,
                self.output.hazard_metadata,
                self.statistics, self.quantile,
                self.aggregate, self.insured, self.loss_type)


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
    stddev_loss_ratio = djm.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'riskr\".\"loss_curve_data'

    @property
    def losses(self):
        return numpy.array(self.loss_ratios) * self.asset_value

    @property
    def average_loss(self):
        return self.average_loss_ratio * self.asset_value

    @property
    def stddev_loss(self):
        if self.stddev_loss_ratio is not None:
            return self.stddev_loss_ratio * self.asset_value

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.loss_curve.output_hash + (self.asset_ref,)

    def assertAlmostEqual(self, data):
        return loss_curve_almost_equal(self, data)


class AggregateLossCurveData(djm.Model):
    '''
    Holds the probabilities of exceedance for the whole exposure model
    '''

    loss_curve = djm.OneToOneField("LossCurve")
    losses = fields.FloatArrayField()
    poes = fields.FloatArrayField()
    average_loss = djm.FloatField()
    stddev_loss = djm.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'riskr\".\"aggregate_loss_curve_data'

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.loss_curve.output_hash

    def assertAlmostEqual(self, data):
        return loss_curve_almost_equal(self, data)


class EventLoss(djm.Model):
    """
    Holds the aggregate loss we have for each rupture
    """

    #: Foreign key to an :class:`openquake.engine.db.models.Output`
    #: object with output_type == event_loss
    output = djm.OneToOneField('Output', related_name="event_loss")
    hazard_output = djm.ForeignKey(
        "Output", related_name="risk_event_loss_tables")
    loss_type = djm.TextField(choices=zip(LOSS_TYPES, LOSS_TYPES))

    class Meta:
        db_table = 'riskr\".\"event_loss'

    def __iter__(self):
        return iter(self.eventlossdata_set.all().order_by('-aggregate_loss'))

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        # FIXME(lp) this is not db-sequence independent
        return (self.output.output_type, self.output.hazard_metadata,
                self.loss_type)


class EventLossData(djm.Model):
    event_loss = djm.ForeignKey(EventLoss)
    rupture = djm.ForeignKey('SESRupture')
    aggregate_loss = djm.FloatField()

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.event_loss.output_hash + (self.rupture_id,)

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data, operator.attrgetter('aggregate_loss'))

    class Meta:
        db_table = 'riskr\".\"event_loss_data'


class BCRDistribution(djm.Model):
    '''
    Holds metadata for the benefit-cost ratio distribution
    '''

    output = djm.OneToOneField("Output", related_name="bcr_distribution")
    hazard_output = djm.ForeignKey(
        "Output", related_name="risk_bcr_distribution")
    loss_type = djm.TextField(choices=zip(LOSS_TYPES, LOSS_TYPES))

    class Meta:
        db_table = 'riskr\".\"bcr_distribution'

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type,
                self.output.hazard_metadata,
                self.loss_type)


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

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.bcr_distribution.output_hash + (self.asset_ref,)

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data,
            operator.attrgetter('average_annual_loss_original',
                                'average_loss_retrofitted',
                                'bcr'))


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

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type,
                self.dmg_state.dmg_state, self.exposure_data.asset_ref)

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.output_hash

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data, operator.attrgetter('mean', 'stddev'))

    @property
    def output(self):
        return self.dmg_state.rc_calculation.oqjob.output_set.get(
            output_type="dmg_dist_per_asset")


class DmgDistPerTaxonomy(djm.Model):
    """Holds the actual data for damage distributions per taxonomy."""

    dmg_state = djm.ForeignKey("DmgState")
    taxonomy = djm.TextField()
    mean = djm.FloatField()
    stddev = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"dmg_dist_per_taxonomy'

    @property
    def output(self):
        return self.dmg_state.rc_calculation.oqjob.output_set.get(
            output_type="dmg_dist_per_taxonomy")

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type,
                self.dmg_state.dmg_state, self.taxonomy)

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.output_hash

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data, operator.attrgetter('mean', 'stddev'))


class DmgDistTotal(djm.Model):
    """Holds the actual 'total damage distribution' values for for an entire
    calculation. There should be  one record per calculation per damage state.
    """

    dmg_state = djm.ForeignKey("DmgState")
    mean = djm.FloatField()
    stddev = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"dmg_dist_total'

    @property
    def output(self):
        return self.dmg_state.rc_calculation.oqjob.output_set.get(
            output_type="dmg_dist_total")

    @property
    def output_hash(self):
        """
        :returns:
            a (db-sequence independent) tuple that identifies this output among
            which the ones created in the same calculation
        """
        return (self.output.output_type, self.dmg_state.dmg_state, )

    @property
    def data_hash(self):
        """
        A db-sequence independent tuple that identifies this output
        """
        return self.output_hash

    def assertAlmostEqual(self, data):
        return risk_almost_equal(
            self, data, operator.attrgetter('mean', 'stddev'))


## Tables in the 'riski' schema.


class ExposureModel(djm.Model):
    '''
    A risk exposure model
    '''

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
    deductible_absolute = djm.BooleanField(default=True)
    insurance_limit_absolute = djm.BooleanField(default=True)

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

    def unit(self, loss_type):
        if loss_type == "fatalities":
            return "people"
        else:
            return self.costtype_set.get(name=loss_type).unit

    def has_insurance_bounds(self):
        return not self.exposuredata_set.filter(
            (djm.Q(cost__deductible_absolute__isnull=True) |
             djm.Q(cost__insurance_limit_absolute__isnull=True))).exists()

    def has_retrofitted_costs(self):
        return not (
            self.exposuredata_set.filter(
                cost__converted_retrofitted_cost__isnull=True)).exists()

    def has_time_event(self, time_event):
        return (
            self.exposuredata_set.filter(occupancy__period=time_event).count()
            ==
            self.exposuredata_set.count())

    def supports_loss_type(self, loss_type):
        """
        :returns:
            True if the exposure contains the asset data needed
            for computing losses for `loss_type`
        """
        if loss_type != "fatalities":
            ct = cost_type(loss_type)
            return self.exposuredata_set.filter(
                cost__cost_type__name=ct).exists()
        else:
            if self.category == "population":
                return not self.exposuredata_set.filter(
                    number_of_units__isnull=True).exists()
            else:
                return not self.exposuredata_set.filter(
                    occupancy__isnull=True).exists()


class CostType(djm.Model):
    COST_TYPE_CHOICES = (
        ("structuralCost", "structuralCost"),
        ("retrofittedStructuralCost", "retrofittedStructuralCost"),
        ("nonStructuralCost", "nonStructuralCost"),
        ("contentsCost", "contentsCost"),
        ("businessInterruptionCost", "businessInterruptionCost"))
    CONVERSION_CHOICES = (
        (u'aggregated', u'Aggregated economic value'),
        (u'per_area', u'Per area economic value'),
        (u'per_asset', u'Per asset economic value'),
    )

    exposure_model = djm.ForeignKey(ExposureModel)
    name = djm.TextField(choices=COST_TYPE_CHOICES)
    conversion = djm.TextField(choices=CONVERSION_CHOICES)
    unit = djm.TextField(null=True)
    retrofitted_conversion = djm.TextField(
        null=True, choices=CONVERSION_CHOICES)
    retrofitted_unit = djm.TextField(null=True)

    class Meta:
        db_table = 'riski\".\"cost_type'


class Occupancy(djm.Model):
    '''
    Asset occupancy data
    '''

    exposure_data = djm.ForeignKey("ExposureData")
    period = djm.TextField()
    occupants = djm.FloatField()

    class Meta:
        db_table = 'riski\".\"occupancy'


class AssetManager(djm.GeoManager):
    """
    Asset manager
    """

    def get_asset_chunk(self, rc, taxonomy, offset, size):
        """
        :returns:

           a list of instances of
           :class:`openquake.engine.db.models.ExposureData` (ordered
           by location) contained in `region_constraint`(embedded in
           the risk calculation `rc`) of `taxonomy` associated with
           the `openquake.engine.db.models.ExposureModel` associated
           with `rc`.

           It also add an annotation to each ExposureData object to provide the
           occupants value for the risk calculation given in input and the cost
           for each cost type considered in `rc`
        """

        query, args = self._get_asset_chunk_query_args(
            rc, taxonomy, offset, size)
        return list(self.raw(query, args))

    def _get_asset_chunk_query_args(self, rc, taxonomy, offset, size):
        """
        Build a parametric query string and the corresponding args for
        #get_asset_chunk
        """
        args = (rc.exposure_model.id, taxonomy,
                "SRID=4326; %s" % rc.region_constraint.wkt)

        people_field, occupants_cond, occupancy_join, occupants_args = (
            self._get_people_query_helper(
                rc.exposure_model.category, rc.time_event))

        args += occupants_args + (size, offset)

        cost_type_fields, cost_type_joins = self._get_cost_types_query_helper(
            rc.exposure_model.costtype_set.all())

        query = """
            SELECT riski.exposure_data.*,
                   {people_field} AS people,
                   {costs}
            FROM riski.exposure_data
            {occupancy_join}
            ON riski.exposure_data.id = riski.occupancy.exposure_data_id
            {costs_join}
            WHERE exposure_model_id = %s AND
                  taxonomy = %s AND
                  ST_COVERS(ST_GeographyFromText(%s), site) AND
                  {occupants_cond}
            GROUP BY riski.exposure_data.id
            ORDER BY ST_X(geometry(site)), ST_Y(geometry(site))
            LIMIT %s OFFSET %s
            """.format(people_field=people_field,
                       occupants_cond=occupants_cond,
                       costs=cost_type_fields,
                       costs_join=cost_type_joins,
                       occupancy_join=occupancy_join)

        return query, args

    def _get_people_query_helper(self, category, time_event):
        """
        Support function for _get_asset_chunk_query_args
        """
        args = ()
        # if the exposure model is of type "population" we extract the
        # data from the `number_of_units` field
        if category == "population":
            occupants_field = "number_of_units"
            occupants_cond = "1 = 1"
            occupancy_join = ""
        else:
            # otherwise we will "left join" the occupancy table
            occupancy_join = "LEFT JOIN riski.occupancy"
            occupants_field = "AVG(riski.occupancy.occupants)"

            # and the time_event is not specified we compute the
            # number of occupants by averaging the occupancy data for
            # each asset, otherwise we get the unique proper occupants
            # value.
            if time_event is None:
                occupants_cond = "1 = 1"
            else:
                args += (time_event,)
                occupants_cond = "riski.occupancy.period = %s"
        return occupants_field, occupants_cond, occupancy_join, args

    def _get_cost_types_query_helper(self, cost_types):
        """
        Support function for _get_asset_chunk_query_args
        """
        # For each cost type associated with the exposure model we
        # join the `cost` table to the current queryset in order to
        # lookup for a cost value for each asset.

        # Actually we extract 4 values: the cost, the retrofitted
        # cost, the deductible and the insurance limit

        costs = []
        costs_join = ""

        for cost_type in cost_types:
            # here the max value is irrelevant as we are sureto join
            # against one row
            costs.append("max(%s.converted_cost) AS %s" % (cost_type.name,
                                                           cost_type.name))
            costs.append(
                "max(%s.converted_retrofitted_cost) AS retrofitted_%s" % (
                    cost_type.name, cost_type.name))
            costs.append(
                "max(%s.deductible_absolute) AS deductible_%s" % (
                    cost_type.name, cost_type.name))
            costs.append(
                "max(%s.insurance_limit_absolute) AS insurance_limit_%s" % (
                    cost_type.name, cost_type.name))

            costs_join += """
            LEFT JOIN riski.cost AS %(name)s
            ON %(name)s.cost_type_id = '%(id)s' AND
            %(name)s.exposure_data_id = riski.exposure_data.id""" % dict(
                name=cost_type.name, id=cost_type.id)

        return ", ".join(costs), costs_join

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

    number_of_units = djm.FloatField(
        null=True, help_text="number of assets, people, etc.")
    area = djm.FloatField(null=True)

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

    # we expect several annotations depending on "loss_type" to be
    # present. See `get_asset_chunk` for details.

    def value(self, loss_type):
        """
        Extract the value of the asset for the given `loss_type`.
        Although the Django Model definition does not have a value for
        each loss type, we rely on the fact that an annotation on the
        asset named `loss_type` is present.
        """
        if loss_type == "fatalities":
            return getattr(self, "people")

        return getattr(self, loss_type)

    def retrofitted(self, loss_type):
        """
        Extract the retrofitted cost of the asset for the given
        `loss_type`. See the method `value` for details.
        """
        return getattr(self, "retrofitted_%s" % loss_type)

    def deductible(self, loss_type):
        """
        Extract the deductible limit of the asset for the given
        `loss_type`. See the method `value` for details.
        """
        return (getattr(self, "deductible_%s" % loss_type) /
                getattr(self, loss_type))

    def insurance_limit(self, loss_type):
        """
        Extract the insurance limit of the asset for the given
        `loss_type`. See the method `value` for details.
        """
        return (getattr(self, "insurance_limit_%s" % loss_type) /
                getattr(self, loss_type))


def make_absolute(limit, value, is_absolute=None):
    """
    :returns:
        `limit` if `is_absolute` is True or `limit` is None,
        else `limit` * `value`
    """
    if limit is not None:
        if not is_absolute:
            return value * limit
        else:
            return limit


class Cost(djm.Model):
    exposure_data = djm.ForeignKey(ExposureData)
    cost_type = djm.ForeignKey(CostType)
    converted_cost = djm.FloatField()
    converted_retrofitted_cost = djm.FloatField(null=True)
    deductible_absolute = djm.FloatField(null=True, blank=True)
    insurance_limit_absolute = djm.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'riski\".\"cost'

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


class HazardSite(djm.Model):
    """
    Contains pre-computed site parameter matrices. ``lons`` and ``lats``
    represent the calculation sites of interest. The associated site parameters
    are from the closest point in a site model in relation to each calculation
    point of interest.

    Used only if a calculation defines a site model (otherwise, reference
    parameters are use for all points of interest).
    """

    hazard_calculation = djm.ForeignKey('HazardCalculation')
    location = djm.PointField(srid=DEFAULT_SRID)

    class Meta:
        db_table = 'hzrdi\".\"hazard_site'
