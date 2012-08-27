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

# Disable:
# - 'Maximum number of public methods for a class'
# - 'Missing docstring' (because of all of the model Meta)
# pylint: disable=R0904,C0111

'''
Model representations of the OpenQuake DB tables.
'''

import os

from collections import namedtuple
from datetime import datetime

import numpy

from django.contrib.gis.db import models as djm
from django.contrib.gis.geos.geometry import GEOSGeometry
from nhlib import geo as nhlib_geo
from shapely import wkt

from openquake.db import fields


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
        - category
        - cost
        - cost_type
        - area
        - area_type
        - number_of_units
    :returns: the per-asset value as a `float`
    :raises: `ValueError` in case of a malformed (risk exposure data) input
    """
    if exd.category is not None and exd.category == "population":
        return exd.number_of_units
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
    point = djm.PointField(srid=4326)

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
        srid=4326, dim=2,
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
    location = djm.PointField(srid=4326)

    def __repr__(self):
        return (
            'SiteModel(location="%s", vs30=%s, vs30_type=%s, z1pt0=%s, '
            'z2pt5=%s)'
            % (self.location.wkt, self.vs30, self.vs30_type, self.z1pt0,
               self.z2pt5))

    class Meta:
        db_table = 'hzrdi\".\"site_model'


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
    )
    input_type = djm.TextField(choices=INPUT_TYPE_CHOICES)
    # Number of bytes in the file:
    size = djm.IntegerField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    def model(self):
        """The model associated with this input or `None`.

        :returns: the appropriate model if one exists or `None`
        """
        assert self.input_type in ("exposure", "fragility"), (
            "unsupported model type (%s)" % self.input_type)
        attr = "%smodel_set" % self.input_type
        qm = getattr(self, attr)
        models = qm.all()
        if models:
            return models[0]

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
    num_sites = djm.IntegerField()
    # The number of logic tree samples
    # (for hazard jobs of all types except scenario)
    realizations = djm.IntegerField(null=True)

    class Meta:
        db_table = 'uiapi\".\"job_stats'


class JobPhaseStats(djm.Model):
    '''
    Capture when the various job phases started.
    '''
    oq_job = djm.ForeignKey('OqJob')
    job_status = djm.TextField()
    start_time = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'uiapi\".\"job_phase_stats'


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
    Parameters need to run a Hazard job.
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
    # TODO:
    #force_inputs = djm.BooleanField(
    #    default=False, help_text="whether the model inputs should be parsed "
    #    "and their content be written to the db no matter what")
    CALC_MODE_CHOICES = (
        (u'classical', u'Classical PSHA'),
        (u'event_based', u'Probabilistic Event-Based'),
    )
    calculation_mode = djm.TextField(choices=CALC_MODE_CHOICES)
    # For the calculation geometry, choose either `region` (with
    # `region_grid_spacing`) or `sites`.
    region = djm.PolygonField(srid=4326, null=True, blank=True)
    # Discretization parameter for a `region`. Units in degrees.
    region_grid_spacing = djm.FloatField(null=True, blank=True)
    # The points of interest for a calculation.
    sites = djm.MultiPointField(srid=4326, null=True, blank=True)

    ########################
    # Logic Tree parameters:
    ########################
    random_seed = djm.IntegerField()
    number_of_logic_tree_samples = djm.IntegerField()

    ###############################################
    # ERF (Earthquake Rupture Forecast) parameters:
    ###############################################
    rupture_mesh_spacing = djm.FloatField(
        help_text=('Rupture mesh spacing (in kilometers) for simple/complex '
                   'fault sources rupture discretization'),
    )
    width_of_mfd_bin = djm.FloatField(
        help_text=('Truncated Gutenberg-Richter MFD (Magnitude Frequency'
              'Distribution) bin width'),
    )
    area_source_discretization = djm.FloatField(
        help_text='Area Source Disretization, in kilometers',
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
    ground_motion_fields = fields.OqNullBooleanField(
        help_text=('If true, ground motion fields will be computed (in '
                   'addition to stochastic event sets)'),
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'uiapi\".\"hazard_calculation'

    def __init__(self, *args, **kwargs):
        # If geometries were specified as string lists of coords,
        # convert them to WKT before doing anything else.
        for field, wkt_fmt in (('sites', 'MULTIPOINT(%s)'),
                               ('region', 'POLYGON((%s))')):
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
                            if field == 'region':
                                points.append(points[0])
                            kwargs[field] = wkt_fmt % ', '.join(points)
        super(HazardCalculation, self).__init__(*args, **kwargs)

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


class Input2hcalc(djm.Model):
    '''
    `input` to `hazard_calculation` link table.
    '''

    input = djm.ForeignKey('Input')
    hazard_calculation = djm.ForeignKey('HazardCalculation')

    class Meta:
        db_table = 'uiapi\".\"input2hcalc'


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
    region = djm.PolygonField(srid=4326, null=True)
    region_grid_spacing = djm.FloatField(null=True)
    sites = djm.MultiPointField(srid=4326, null=True)

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


class Output(djm.Model):
    '''
    A single artifact which is a result of an OpenQuake job.
    The data may reside in a file or in the database.
    '''
    owner = djm.ForeignKey('OqUser')
    oq_job = djm.ForeignKey('OqJob')
    display_name = djm.TextField()
    OUTPUT_TYPE_CHOICES = (
        (u'unknown', u'Unknown'),
        (u'hazard_curve', u'Hazard Curve'),
        (u'hazard_map', u'Hazard Map'),
        (u'gmf', u'Ground Motion Field'),
        (u'ses', u'Stochastic Event Set'),
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
    output_type = djm.TextField(choices=OUTPUT_TYPE_CHOICES)
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    def __str__(self):
        return "%d||%s||%s" % (self.id, self.output_type, self.display_name)

    class Meta:
        db_table = 'uiapi\".\"output'


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
    poe = djm.FloatField()
    STAT_CHOICES = (
        (u'mean', u'Mean'),
        (u'quantile', u'Quantile'),
    )
    statistic_type = djm.TextField(choices=STAT_CHOICES)
    quantile = djm.FloatField(null=True)

    class Meta:
        db_table = 'hzrdr\".\"hazard_map'


class HazardMapData(djm.Model):
    '''
    Hazard Map data (data for a single point in the map)
    '''
    hazard_map = djm.ForeignKey('HazardMap')
    value = djm.FloatField()
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'hzrdr\".\"hazard_map_data'


class HazardCurve(djm.Model):
    '''
    Hazard Curve header information
    '''
    output = djm.ForeignKey('Output')
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

    class Meta:
        db_table = 'hzrdr\".\"hazard_curve'


class HazardCurveData(djm.Model):
    '''
    Hazard Curve data

    Contains an list of PoE (Probability of Exceedance)
    values and the geographical point associated with the curve
    '''
    hazard_curve = djm.ForeignKey('HazardCurve')
    poes = fields.FloatArrayField()
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'hzrdr\".\"hazard_curve_data'


class SESCollection(djm.Model):
    """
    Stochastic Event Set Collection: A container for 1 or more Stochastic Event
    Sets for a given logic tree realization.

    See also :class:`SES` and :class:`SESRupture`.
    """
    output = djm.ForeignKey('Output')
    lt_realization = djm.ForeignKey('LtRealization')

    class Meta:
        db_table = 'hzrdr\".\"ses_collection'


class SES(djm.Model):
    """
    Stochastic Event Set: A container for 1 or more ruptures associated with a
    specific investigation time span.

    See also :class:`SESRupture`.
    """
    ses_collection = djm.ForeignKey('SESCollection')
    investigation_time = djm.FloatField()

    class Meta:
        db_table = 'hzrdr\".\"ses'


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
    output = djm.ForeignKey('Output')
    lt_realization = djm.ForeignKey('LtRealization')

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

    def __iter__(self):
        """
        Iterator for walking through all child :class:`Gmf` objects.
        """
        return Gmf.objects.filter(gmf_set=self.id).iterator()


class Gmf(djm.Model):
    """
    Ground Motion Field: A collection of ground motion values and their
    respective geographical locations.
    """
    gmf_set = djm.ForeignKey('GmfSet')
    imt = djm.TextField(choices=IMT_CHOICES)
    sa_period = djm.FloatField(null=True)
    sa_damping = djm.FloatField(null=True)

    class Meta:
        db_table = 'hzrdr\".\"gmf'

    def __iter__(self):
        """
        Iterator for walking through all child :class:`Gmf` objects.
        """
        return GmfNode.objects.filter(gmf=self.id).iterator()


class GmfNode(djm.Model):
    """
    An indiviual node of a ground motion field, consisting of a ground motion
    value/intensity measure level and a point geometry.
    """
    gmf = djm.ForeignKey('Gmf')
    location = djm.PointField(srid=4326)
    iml = djm.FloatField()

    class Meta:
        db_table = 'hzrdr\".\"gmf_node'


class GmfData(djm.Model):
    '''
    Ground Motion Field data

    DEPRECATED. See instead :class:`GmfCollection`, :class:`GmfSet`,
    :class:`Gmf`, and :class:`GmfNode`.
    '''
    output = djm.ForeignKey('Output')
    ground_motion = djm.FloatField()
    location = djm.PointField(srid=4326)

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
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'hzrdr\".\"uh_spectrum_data'


class LtRealization(djm.Model):
    """
    Keep track of logic tree realization progress. When ``completed_sources``
    becomes equal to ``total_sources``, mark ``is_complete`` as `True`.

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
    total_sources = djm.IntegerField()
    completed_sources = djm.IntegerField(default=0)

    class Meta:
        db_table = 'hzrdr\".\"lt_realization'


## Tables in the 'riskr' schema.


class LossMap(djm.Model):
    '''
    Holds metadata for loss maps
    '''

    output = djm.ForeignKey("Output")
    scenario = djm.BooleanField()
    loss_map_ref = djm.TextField(null=True)
    end_branch_label = djm.TextField(null=True)
    category = djm.TextField(null=True)
    unit = djm.TextField(null=True)
    timespan = djm.FloatField(null=True)
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
    std_dev = djm.FloatField(default=0.0)
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'riskr\".\"loss_map_data'


class LossCurve(djm.Model):
    '''
    Holds the parameters common to a set of loss curves
    '''

    output = djm.ForeignKey("Output")
    aggregate = djm.BooleanField(default=False)
    end_branch_label = djm.TextField(null=True)
    category = djm.TextField(null=True)
    unit = djm.TextField(null=True)

    class Meta:
        db_table = 'riskr\".\"loss_curve'


class LossCurveData(djm.Model):
    '''
    Holds the probabilities of exceedance for a given loss curve
    '''

    loss_curve = djm.ForeignKey("LossCurve")
    asset_ref = djm.TextField()
    losses = fields.FloatArrayField()
    poes = fields.FloatArrayField()
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'riskr\".\"loss_curve_data'


class AggregateLossCurveData(djm.Model):
    '''
    Holds the probabilities of exceedance for the whole exposure model
    '''

    loss_curve = djm.ForeignKey("LossCurve")
    losses = fields.FloatArrayField()
    poes = fields.FloatArrayField()

    class Meta:
        db_table = 'riskr\".\"aggregate_loss_curve_data'


class CollapseMap(djm.Model):
    '''
    Holds metadata for the collapse map
    '''

    output = djm.ForeignKey("Output")
    exposure_model = djm.ForeignKey("ExposureModel")

    class Meta:
        db_table = 'riskr\".\"collapse_map'


class CollapseMapData(djm.Model):
    '''
    Holds the actual data for the collapse map
    '''

    collapse_map = djm.ForeignKey("CollapseMap")
    asset_ref = djm.TextField()
    value = djm.FloatField()
    std_dev = djm.FloatField()
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'riskr\".\"collapse_map_data'


class BCRDistribution(djm.Model):
    '''
    Holds metadata for the benefit-cost ratio distribution
    '''

    output = djm.ForeignKey("Output")
    exposure_model = djm.ForeignKey("ExposureModel")

    class Meta:
        db_table = 'riskr\".\"bcr_distribution'


class BCRDistributionData(djm.Model):
    '''
    Holds the actual data for the benefit-cost ratio distribution
    '''

    bcr_distribution = djm.ForeignKey("BCRDistribution")
    asset_ref = djm.TextField()
    bcr = djm.FloatField()
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'riskr\".\"bcr_distribution_data'


class DmgDistPerAsset(djm.Model):
    """Holds metadata for damage distributions per asset."""

    output = djm.ForeignKey("Output")
    dmg_states = fields.CharArrayField()
    end_branch_label = djm.TextField(null=True)

    class Meta:
        db_table = 'riskr\".\"dmg_dist_per_asset'


class DmgDistPerAssetData(djm.Model):
    """Holds the actual data for damage distributions per asset."""

    dmg_dist_per_asset = djm.ForeignKey("DmgDistPerAsset")
    exposure_data = djm.ForeignKey("ExposureData")
    dmg_state = djm.TextField()
    mean = djm.FloatField()
    stddev = djm.FloatField()
    # geometry for the computation cell which contains the referenced asset
    location = djm.PointField(srid=4326)

    class Meta:
        db_table = 'riskr\".\"dmg_dist_per_asset_data'


class DmgDistPerTaxonomy(djm.Model):
    """Hold metdata for damage distributions per taxonomy."""

    output = djm.ForeignKey("Output")
    dmg_states = fields.CharArrayField()
    end_branch_label = djm.TextField(null=True)

    class Meta:
        db_table = 'riskr\".\"dmg_dist_per_taxonomy'


class DmgDistPerTaxonomyData(djm.Model):
    """Holds the actual data for damage distributions per taxonomy."""

    dmg_dist_per_taxonomy = djm.ForeignKey("DmgDistPerTaxonomy")
    taxonomy = djm.TextField()
    dmg_state = djm.TextField()
    mean = djm.FloatField()
    stddev = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"dmg_dist_per_taxonomy_data'


class DmgDistTotal(djm.Model):
    """Holds metadata for 'total damage distribution' values for an entire
    calculation. This is the total over all assets and GMFs."""

    output = djm.ForeignKey("Output")
    dmg_states = fields.CharArrayField()
    end_branch_label = djm.TextField(null=True)

    class Meta:
        db_table = 'riskr\".\"dmg_dist_total'


class DmgDistTotalData(djm.Model):
    """Holds the actual 'total damage distribution' values for for an entire
    calculation. There should be  one record per calculation per damage state.
    """

    dmg_dist_total = djm.ForeignKey("DmgDistTotal")
    dmg_state = djm.TextField()
    mean = djm.FloatField()
    stddev = djm.FloatField()

    class Meta:
        db_table = 'riskr\".\"dmg_dist_total_data'


## Tables in the 'oqmif' schema.


class ExposureModel(djm.Model):
    '''
    A risk exposure model
    '''

    owner = djm.ForeignKey("OqUser")
    input = djm.ForeignKey("Input")
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


class Occupancy(djm.Model):
    '''
    Asset occupancy data
    '''

    exposure_data = djm.ForeignKey("ExposureData")
    description = djm.TextField()
    occupants = djm.IntegerField()

    class Meta:
        db_table = 'oqmif\".\"occupancy'


class ExposureData(djm.Model):
    '''
    Per-asset risk exposure data
    '''

    REXD = namedtuple(
        "REXD", "category, cost, cost_type, area, area_type, number_of_units")

    exposure_model = djm.ForeignKey("ExposureModel")
    asset_ref = djm.TextField()
    taxonomy = djm.TextField()
    site = djm.PointField(srid=4326)
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

    @property
    def value(self):
        """The structural per-asset value."""
        exd = self.REXD(
            cost=self.stco, cost_type=self.exposure_model.stco_type,
            area=self.area, area_type=self.exposure_model.area_type,
            number_of_units=self.number_of_units,
            category=self.exposure_model.category)
        return per_asset_value(exd)

    @property
    def retrofitting_cost(self):
        """The retrofitting per-asset value."""
        exd = self.REXD(
            cost=self.reco, cost_type=self.exposure_model.reco_type,
            area=self.area, area_type=self.exposure_model.area_type,
            number_of_units=self.number_of_units,
            category=self.exposure_model.category)
        return per_asset_value(exd)

    class Meta:
        db_table = 'oqmif\".\"exposure_data'


## Tables in the 'riski' schema.


class VulnerabilityModel(djm.Model):
    '''
    A risk vulnerability model
    '''

    owner = djm.ForeignKey("OqUser")
    input = djm.ForeignKey("Input")
    name = djm.TextField()
    description = djm.TextField(null=True)
    imt = djm.TextField(choices=OqJobProfile.IMT_CHOICES)
    imls = fields.FloatArrayField()
    category = djm.TextField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'riski\".\"vulnerability_model'


class VulnerabilityFunction(djm.Model):
    '''
    A risk vulnerability function
    '''

    vulnerability_model = djm.ForeignKey("VulnerabilityModel")
    taxonomy = djm.TextField()
    loss_ratios = fields.FloatArrayField()
    covs = fields.FloatArrayField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'riski\".\"vulnerability_function'


class FragilityModel(djm.Model):
    """A risk fragility model"""

    owner = djm.ForeignKey("OqUser")
    input = djm.ForeignKey("Input")
    description = djm.TextField(null=True)
    FORMAT_CHOICES = (
        (u"continuous", u"Continuous fragility model"),
        (u"discrete", u"Discrete fragility model"),
    )
    format = djm.TextField(choices=FORMAT_CHOICES)
    lss = fields.CharArrayField(help_text="limit states")
    imls = fields.FloatArrayField(null=True,
                                  help_text="Intensity measure levels")
    imt = djm.TextField(null=True, choices=OqJobProfile.IMT_CHOICES,
                           help_text="Intensity measure type")
    iml_unit = djm.TextField(null=True, help_text="IML unit of measurement")
    min_iml = djm.FloatField(
        null=True, help_text="Minimum IML value, for continuous models only")
    max_iml = djm.FloatField(
        null=True, help_text="Maximum IML value, for continuous models only")
    no_damage_limit = djm.FloatField(
        null=True, help_text="No Damage Limit value, for discrete models only")
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'riski\".\"fragility_model'


class Ffc(djm.Model):
    """A continuous fragility function"""

    fragility_model = djm.ForeignKey("FragilityModel")
    lsi = djm.PositiveSmallIntegerField(
        help_text="limit state index, facilitates ordering of fragility "
                  "function in accordance with the limit states")
    ls = djm.TextField(help_text="limit state")
    taxonomy = djm.TextField()
    ftype = djm.TextField(null=True, help_text="function/distribution type")
    mean = djm.FloatField(help_text="Mean value")
    stddev = djm.FloatField(help_text="Standard deviation")
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'riski\".\"ffc'


class Ffd(djm.Model):
    """A discrete fragility function"""

    fragility_model = djm.ForeignKey("FragilityModel")
    lsi = djm.PositiveSmallIntegerField(
        help_text="limit state index, facilitates ordering of fragility "
                  "function in accordance with the limit states")
    ls = djm.TextField(help_text="limit state")
    taxonomy = djm.TextField()
    poes = fields.FloatArrayField(help_text="Probabilities of exceedance")
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)

    class Meta:
        db_table = 'riski\".\"ffd'


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
