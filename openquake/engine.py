# -*- coding: utf-8 -*-

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


"""The 'Engine' is responsible for instantiating calculators and running jobs.
"""


import md5
import os
import re

from datetime import datetime
from ConfigParser import ConfigParser
from lxml import etree

from django.db import close_connection
from django.db import transaction
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist
from nhlib import geo as nhlib_geo


from openquake.calculators.hazard import CALCULATORS as HAZ_CALCS
from openquake.calculators.risk import CALCULATORS as RISK_CALCS
from openquake.db.models import CharArrayField
from openquake.db.models import ExposureData
from openquake.db.models import FloatArrayField
from openquake.db.models import Input
from openquake.db.models import Input2job
from openquake.db.models import inputs4job
from openquake.db.models import Job2profile
from openquake.db.models import JobStats
from openquake.db.models import ModelContent
from openquake.db.models import OqJob
from openquake.db.models import OqJobProfile
from openquake.db.models import OqUser
from openquake.db.models import profile4job
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake import xml
from openquake.job import config as jobconf
from openquake.job.params import ARRAY_RE
from openquake.job.params import CALCULATION_MODE
from openquake.job.params import INPUT_FILE_TYPES
from openquake.job.params import PARAMS
from openquake.job.params import PATH_PARAMS
from openquake.kvs import mark_job_as_current
from openquake.supervising import supervisor
from openquake.utils import config as utils_config
from openquake.utils import stats

CALCS = dict(hazard=HAZ_CALCS, risk=RISK_CALCS)
RE_INCLUDE = re.compile(r'^(.*)_INCLUDE')


# Silencing 'Too many instance attributes'
# pylint: disable=R0902
class JobContext(object):
    """Contains everything a calculator needs to run a job. This
    includes: an :class:`OqJobProfile` object, an :class:`OqJob`, and a
    dictionary of all of the calculation config params (which is a basically a
    duplication of the :class:`OqJobProfile` member; in the future we would
    like to remove this duplication).

    This class also contains handful of utility methods for determining the
    sites of interest for a calculation, querying the calculation status, etc.
    """

    # Silencing 'Too many arguments'
    # pylint: disable=R0913
    def __init__(self, params, job_id, sections=list(), base_path=None,
                 serialize_results_to=list(), oq_job_profile=None,
                 oq_job=None, log_level='warn', force_inputs=False):
        """
        :param dict params: Dict of job config params.
        :param int job_id:
            ID of the corresponding oq_job db record.
        :param list sections: List of config file sections. Example::
            ['HAZARD', 'RISK']
        :param str base_path: base directory containing job input files
        :param oq_job_profile:
            :class:`openquake.db.models.OqJobProfile` instance; database
            representation of the job profile / calculation configuration.
        :param oq_job:
            :class:`openquake.db.models.OqJob` instance; database
            representation of the runtime thing we refer to as the
            'calculation'.
        :param str log_level:
            One of 'debug', 'info', 'warn', 'error', 'critical'.
            Defaults to 'warn'.
        :param bool force_inputs: If `True` the model input files will be
            parsed and the resulting content written to the database no matter
            what.
        """
        self._job_id = job_id
        mark_job_as_current(job_id)  # enables KVS gc

        self.sites = []
        self.blocks_keys = []
        self.params = params
        self.sections = list(set(sections))
        self.serialize_results_to = []
        self._base_path = base_path
        self.serialize_results_to = list(serialize_results_to)

        self.oq_job_profile = oq_job_profile
        self.oq_job = oq_job
        self.params['debug'] = log_level
        self._log_level = log_level
        self.force_inputs = force_inputs

    @property
    def log_level(self):
        """The log level for this job. (One of 'debug', 'info', 'warn',
        'error', 'critical'."""
        return self._log_level

    @property
    def base_path(self):
        """Directory containing the input files for this job.

        The base_path also acts as the base directory for calculation outputs.
        """
        if self._base_path is not None:
            return self._base_path
        else:
            return self.params.get('BASE_PATH')

    @staticmethod
    def from_kvs(job_id):
        """Return the job in the underlying kvs system with the given id."""
        params = kvs.get_value_json_decoded(
            kvs.tokens.generate_job_key(job_id))
        job_profile = profile4job(job_id)
        job = OqJob.objects.get(id=job_id)
        job = JobContext(params, job_id, oq_job_profile=job_profile,
                         oq_job=job, log_level=params['debug'])
        return job

    @staticmethod
    def get_status_from_db(job_id):
        """
        Get the status of the database record belonging to job ``job_id``.

        :returns: one of strings 'pending', 'running', 'succeeded', 'failed'.
        """
        return OqJob.objects.get(id=job_id).status

    @staticmethod
    def is_job_completed(job_id):
        """
        Return ``True`` if the :meth:`current status <get_status_from_db>`
        of the job ``job_id`` is either 'succeeded' or 'failed'. Returns
        ``False`` otherwise.
        """
        status = JobContext.get_status_from_db(job_id)
        return status == 'succeeded' or status == 'failed'

    def has(self, name):
        """Return false if this job doesn't have the given parameter defined,
        or parameter's string value otherwise."""
        return name in self.params and self.params[name]

    @property
    def job_id(self):
        """Return the id of this job."""
        return self._job_id

    @property
    def key(self):
        """Returns the kvs key for this job."""
        return kvs.tokens.generate_job_key(self.job_id)

    @property
    def region(self):
        """Compute valid region with appropriate cell size from config file."""
        if not self.has('REGION_VERTEX'):
            return None

        region = shapes.RegionConstraint.from_coordinates(
            self._extract_coords('REGION_VERTEX'))

        region.cell_size = float(self['REGION_GRID_SPACING'])
        return region

    def __getitem__(self, name):
        defined_param = PARAMS.get(name)
        if (hasattr(defined_param, 'to_job')
            and defined_param.to_job is not None
            and self.params.get(name) is not None):
            return defined_param.to_job(self.params.get(name))
        return self.params.get(name)

    def __eq__(self, other):
        return self.params == other.params

    def __str__(self):
        return str(self.params)

    def _slurp_files(self):
        """Read referenced files and write them into kvs, keyed on their
        sha1s."""
        kvs_client = kvs.get_client()
        if self.base_path is None:
            logs.LOG.debug("Can't slurp files without a base path, homie...")
            return
        for key, val in self.params.items():
            if key[-5:] == '_FILE':
                path = os.path.join(self.base_path, val)
                with open(path) as data_file:
                    logs.LOG.debug("Slurping %s" % path)
                    blob = data_file.read()
                    file_key = kvs.tokens.generate_blob_key(self.job_id, blob)
                    kvs_client.set(file_key, blob)
                    self.params[key] = file_key
                    self.params[key + "_PATH"] = path

    def to_kvs(self):
        """Store this job into kvs."""
        self._slurp_files()
        key = kvs.tokens.generate_job_key(self.job_id)
        data = self.params.copy()
        data['debug'] = self.log_level
        kvs.set_value_json_encoded(key, data)

    def sites_to_compute(self):
        """Return the sites used to trigger the computation on the
        hazard subsystem.

        If the SITES parameter is specified, the computation is triggered
        only on the sites specified in that parameter, otherwise
        the region is used.

        If the COMPUTE_HAZARD_AT_ASSETS_LOCATIONS parameter is specified,
        the hazard computation is triggered only on sites defined in the risk
        exposure file and located inside the region of interest.
        """

        if self.sites:
            return self.sites

        if jobconf.RISK_SECTION in self.sections \
                and self.has(jobconf.COMPUTE_HAZARD_AT_ASSETS):

            print "COMPUTE_HAZARD_AT_ASSETS_LOCATIONS selected, " \
                "computing hazard on exposure sites..."

            self.sites = read_sites_from_exposure(self)
        elif self.has(jobconf.SITES):

            coords = self._extract_coords(jobconf.SITES)
            sites = []

            for coord in coords:
                sites.append(nhlib_geo.Point(coord[0], coord[1]))
                # sites.append(shapes.Site(coord[0], coord[1]))

            self.sites = sites
        else:
            self.sites = self._sites_for_region()

        return self.sites

    def _extract_coords(self, config_param):
        """Extract from a configuration parameter the list of coordinates."""
        verts = self[config_param]
        return zip(verts[1::2], verts[::2])

    def _sites_for_region(self):
        """Return the list of sites for the region at hand."""
        region = shapes.Region.from_coordinates(
            self._extract_coords('REGION_VERTEX'))

        region.cell_size = self['REGION_GRID_SPACING']
        return [nhlib_geo.Point(x.longitude, x.latitude)
                for x in region.grid.centers()]

    def build_nrml_path(self, nrml_file):
        """Return the complete output path for the given nrml_file"""
        return os.path.join(self['BASE_PATH'], self['OUTPUT_DIR'], nrml_file)

    def extract_values_from_config(self, param_name, separator=' ',
                                   check_value=lambda _: True):
        """Extract the set of valid values from the configuration file."""

        def _acceptable(value):
            """Return true if the value taken from the configuration
            file is valid, false otherwise."""
            try:
                value = float(value)
            except ValueError:
                return False
            else:
                return check_value(value)

        values = []

        if param_name in self.params:
            raw_values = self.params[param_name].split(separator)
            values = [float(x) for x in raw_values if _acceptable(x)]

        return values

    @property
    def imls(self):
        "Return the intensity measure levels as specified in the config file"
        if self.has('INTENSITY_MEASURE_LEVELS'):
            return self['INTENSITY_MEASURE_LEVELS']
        return None

    def _record_initial_stats(self):
        '''
        Report initial job stats (such as start time) by adding a
        uiapi.job_stats record to the db.
        '''
        job_stats = JobStats(oq_job=self.oq_job)
        job_stats.start_time = datetime.utcnow()
        job_stats.num_sites = len(self.sites_to_compute())

        calc_mode = CALCULATION_MODE[self['CALCULATION_MODE']]
        if jobconf.HAZARD_SECTION in self.sections:
            if calc_mode != 'scenario':
                job_stats.realizations = self["NUMBER_OF_LOGIC_TREE_SAMPLES"]

        job_stats.save()


def read_sites_from_exposure(job_ctxt):
    """Given a :class:`JobContext` object, get all of the sites in the exposure
    model which are contained by the region of interest (defined in the
    `JobContext`).

    It is assumed that exposure model is already loaded into the database.

    :param job_ctxt:
        :class:`JobContext` instance.
    :returns:
        `list` of :class:`openquake.shapes.Site` objects, with no duplicates
    """
    em_inputs = inputs4job(job_ctxt.job_id, input_type="exposure")
    exp_points = ExposureData.objects.filter(
        exposure_model__input__id__in=[em.id for em in em_inputs],
        site__contained=job_ctxt.oq_job_profile.region).values(
            'site').distinct()

    sites = [shapes.Site(p['site'].x, p['site'].y) for p in exp_points]
    return sites


# Too many local variables
# pylint: disable=R0914
def _job_from_file(config_file, output_type, owner_username='openquake',
                   force_inputs=False):
    """
    Create a job from external configuration files.

    NOTE: This function is deprecated. Please use
    :function:`openquake.engine.import_job_profile`.

    :param config_file:
        The external configuration file path
    :param output_type:
        Where to store results:
        * 'db' database
        * 'xml' XML files *plus* database
    :param owner_username:
        oq_user.user_name which defines the owner of all DB artifacts created
        by this function.
    :param bool force_inputs: If `True` the model input files will be parsed
        and the resulting content written to the database no matter what.
    """

    # output_type can be set, in addition to 'db' and 'xml', also to
    # 'xml_without_db', which has the effect of serializing only to xml
    # without requiring a database at all.
    # This allows to run tests without requiring a database.
    # This is not documented in the public interface because it is
    # essentially a detail of our current tests and ci infrastructure.
    assert output_type in ('db', 'xml')

    params, sections = _parse_config_file(config_file)
    params, sections = _prepare_config_parameters(params, sections)

    validator = jobconf.default_validators(sections, params)
    is_valid, errors = validator.is_valid()

    if not is_valid:
        raise jobconf.ValidationException(errors)

    owner = OqUser.objects.get(user_name=owner_username)
    # openquake-server creates the job record in advance and stores
    # the calculation id in the config file
    job_id = params.get('OPENQUAKE_JOB_ID')
    if not job_id:
        # create the database record for this job
        job = OqJob(owner=owner, path=None)
        job.save()
        job_id = job.id
    else:
        job = OqJob.objects.get(job_id)

    job_profile = _prepare_job(params, sections, owner_username, job,
                               force_inputs)

    if output_type == 'db':
        serialize_results_to = ['db']
    else:
        serialize_results_to = ['db', 'xml']

    base_path = params['BASE_PATH']

    job_ctxt = JobContext(
        params, job_id, sections=sections, base_path=base_path,
        serialize_results_to=serialize_results_to, oq_job=job,
        oq_job_profile=job_profile)
    job_ctxt.to_kvs()

    return job_ctxt


def _parse_config_file(config_file):
    """
    We have a single configuration file which may contain a risk section and
    a hazard section. This input file must be in the ConfigParser format
    defined at: http://docs.python.org/library/configparser.html.

    There may be a general section which may define configuration includes in
    the format of "sectionname_include = someconfigname.gem". These too must be
    in the ConfigParser format.
    """

    config_file = os.path.abspath(config_file)
    base_path = os.path.abspath(os.path.dirname(config_file))

    if not os.path.exists(config_file):
        raise jobconf.ValidationException(
            ["File '%s' not found" % config_file])

    parser = ConfigParser()
    parser.read(config_file)

    params = {}
    sections = []

    for section in parser.sections():
        for key, value in parser.items(section):
            key = key.upper()
            # Handle includes.
            if RE_INCLUDE.match(key):
                config_file = os.path.join(os.path.dirname(config_file), value)
                new_params, new_sections = _parse_config_file(config_file)
                sections.extend(new_sections)
                params.update(new_params)
            else:
                sections.append(section)
                params[key] = value

    params['BASE_PATH'] = base_path

    return params, list(set(sections))


def _prepare_config_parameters(params, sections):
    """
    Pre-process configuration parameters removing unknown ones.
    """

    calc_mode = CALCULATION_MODE[params['CALCULATION_MODE']]
    new_params = dict()

    for name, value in params.items():
        try:
            param = PARAMS[name]
        except KeyError:
            print 'Ignoring unknown parameter %r' % name
            continue

        if calc_mode not in param.modes:
            msg = "Ignoring %s in %s, it's meaningful only in "
            msg %= (name, calc_mode)
            print msg, ', '.join(param.modes)
            continue

        new_params[name] = value

    # make file paths absolute
    for name in PATH_PARAMS:
        if name not in new_params:
            continue

        new_params[name] = os.path.join(params['BASE_PATH'], new_params[name])

    # Set default parameters (if applicable).
    # TODO(LB): This probably isn't the best place for this code (since we may
    # want to implement similar default param logic elsewhere). For now,
    # though, it will have to do.

    # If job is classical and hazard+risk:
    if calc_mode == 'classical' and set(['HAZARD', 'RISK']).issubset(sections):
        if params.get('COMPUTE_MEAN_HAZARD_CURVE'):
            # If this param is already defined, display a message to the user
            # that this config param is being ignored and set to the default:
            print "Ignoring COMPUTE_MEAN_HAZARD_CURVE; defaulting to 'true'."
        # The value is set to a string because validators still expected job
        # config params to be strings at this point:
        new_params['COMPUTE_MEAN_HAZARD_CURVE'] = 'true'

    # Fri, 11 May 2012 11:03:03 +0200, al-maisan
    # According to dmonelli and larsbutler the intensity measure type for UHS
    # jobs is *always* SA irrespective of the value specified in the config
    # file.
    if calc_mode == "uhs":
        new_params["INTENSITY_MEASURE_TYPE"] = "SA"

    return new_params, sections


def _file_digest(path):
    """Return a 32 character digest for the file with the given path.

    :param str path: file path
    :returns: a string of length 32 with the md5sum digest
    """
    checksum = md5.new()
    with open(path) as fh:
        checksum.update(fh.read())
        return checksum.hexdigest()


def _identical_input(input_type, digest, owner_id):
    """Get an identical input with the same type or `None`.

    Identical inputs are found by comparing md5sum digests. In order to avoid
    reusing corrupted/broken input models we ignore all the inputs that are
    associated with a first job that failed.
    Also, we only want inputs owned by the user who is running the current job
    and if there is more than one input we want the most recent one.

    :param str input_type: input model type
    :param str digest: md5sum digest
    :param int owner_id: the database key of the owner
    :returns: an `:class:openquake.db.models.Input` instance or `None`
    """
    q = """
    SELECT * from uiapi.input WHERE id = (
        SELECT MAX(input_id) AS max_input_id FROM
            uiapi.oq_job, (
                SELECT DISTINCT MIN(j.id) AS min_job_id, i.id AS input_id
                FROM uiapi.oq_job AS j, uiapi.input2job AS i2j,
                     uiapi.input AS i, admin.oq_user u
                WHERE i2j.oq_job_id = j.id AND i2j.input_id = i.id
                    AND i.digest = %s AND i.input_type = %s
                    AND j.owner_id = u.id AND u.id = %s
                GROUP BY i.id ORDER BY i.id DESC) AS mjq
            WHERE id = mjq.min_job_id AND status = 'succeeded')"""
    ios = list(Input.objects.raw(q, [digest, input_type, owner_id]))
    return ios[0] if ios else None


def _get_content_type(path):
    """Given the path to a file, guess the content type by looking at the file
    extension. If there is none, simply return 'unknown'.
    """
    _, ext = os.path.splitext(path)
    if ext == '':
        return 'unknown'
    else:
        # This gives us the . and extension (such as '.xml').
        # Don't include the period.
        return ext[1:]


def _insert_input_files(params, job, force_inputs):
    """Create uiapi.input records for all input files

    :param dict params: The job config params.
    :param job: The :class:`openquake.db.models.OqJob` instance to use
    :param bool force_inputs: If `True` the model input files will be parsed
        and the resulting content written to the database no matter what.
    """

    inputs_seen = []

    def ln_input2job(job, path, input_type):
        """Link identical or newly created input to the given job."""
        digest = _file_digest(path)
        linked_inputs = inputs4job(job.id)
        if any(li.digest == digest and li.input_type == input_type
               for li in linked_inputs):
            return

        in_model = (_identical_input(input_type, digest, job.owner.id)
                    if not force_inputs else None)
        if in_model is None:
            # Save the raw input file contents to the DB:
            model_content = ModelContent()
            with open(path, 'rb') as fh:
                model_content.raw_content = fh.read()
            # Try to guess the content type:
            model_content.content_type = _get_content_type(path)
            model_content.save()

            in_model = Input(path=path, input_type=input_type, owner=job.owner,
                             size=os.path.getsize(path), digest=digest,
                             model_content=model_content)
            in_model.save()

        # Make sure we don't link to the same input more than once.
        if in_model.id in inputs_seen:
            return
        else:
            inputs_seen.append(in_model.id)

        i2j = Input2job(input=in_model, oq_job=job)
        i2j.save()

    # insert input files in input table
    for param_key, file_type in INPUT_FILE_TYPES.items():
        if param_key not in params:
            continue
        path = params[param_key]
        ln_input2job(job, path, file_type)

    # insert source models referenced in the logic tree
    if 'SOURCE_MODEL_LOGIC_TREE_FILE' in params:
        for path in _get_source_models(params['SOURCE_MODEL_LOGIC_TREE_FILE']):
            ln_input2job(job, path, "source")


def prepare_job(user_name="openquake"):
    """Create job for the given user, return it."""
    # See if the current user exists
    # If not, create a record for them
    owner = prepare_user(user_name)
    job = OqJob(owner=owner)
    job.save()
    return job


def prepare_user(user_name):
    """Make sure user with the given name exists, return it."""
    # See if the current user exists
    # If not, create a record for them
    try:
        user = OqUser.objects.get(user_name=user_name)
    except ObjectDoesNotExist:
        # This user doesn't exist; let's fix that.
        # NOTE: The Organization is currently hardcoded to 1.
        # This org is added when the database is bootstrapped.
        user = OqUser(user_name=user_name, full_name=user_name,
                       organization_id=1)
        user.save()
    return user


@transaction.commit_on_success(using='job_init')
def _prepare_job(params, sections, owner_username, job, force_inputs):
    """
    Create a new OqJob and fill in the related OqJobProfile entry.

    Returns the newly created job object.

    :param dict params:
        The job config params.
    :param sections:
        The job config file sections, as a list of strings.
    :param owner_username:
        The username of the user who will own the returned job profile.
    :param job:
        The :class:`openquake.db.models.OqJob` instance to use
    :param bool force_inputs: If `True` the model input files will be parsed
        and the resulting content written to the database no matter what.

    :returns:
        A new :class:`openquake.db.models.OqJobProfile` object.
    """

    @transaction.commit_on_success(using='job_init')
    def _get_job_profile(calc_mode, job_type, owner):
        """Create an OqJobProfile, save it to the db, commit, and return."""
        job_profile = OqJobProfile(calc_mode=calc_mode, job_type=job_type)

        _insert_input_files(params, job, force_inputs)
        _store_input_parameters(params, calc_mode, job_profile)

        job_profile.owner = owner
        job_profile.force_inputs = force_inputs
        job_profile.save()
        Job2profile(oq_job=job, oq_job_profile=job_profile).save()

        return job_profile

    # TODO specify the owner as a command line parameter
    owner = prepare_user(owner_username)

    calc_mode = CALCULATION_MODE[params['CALCULATION_MODE']]
    job_type = [s.lower() for s in sections
        if s.upper() in [jobconf.HAZARD_SECTION, jobconf.RISK_SECTION]]

    job_profile = _get_job_profile(calc_mode, job_type, owner)

    # When querying this record from the db, Django changes the values
    # slightly (with respect to geometry, for example). Thus, we want a
    # "fresh" copy of the record from the db.
    return OqJobProfile.objects.get(id=job_profile.id)


def _get_source_models(logic_tree):
    """Returns the source models soft-linked by the given logic tree.

    :param str logic_tree: path to a source model logic tree file
    :returns: list of source model file paths
    """

    # can be removed if we don't support .inp files
    if not logic_tree.endswith('.xml'):
        return []

    base_path = os.path.dirname(os.path.abspath(logic_tree))
    model_files = []

    uncert_mdl_tag = xml.NRML + 'uncertaintyModel'

    for _event, elem in etree.iterparse(logic_tree):
        if elem.tag == uncert_mdl_tag:
            e_text = elem.text.strip()
            if e_text.endswith('.xml'):
                model_files.append(os.path.join(base_path, e_text))

    return model_files


def _store_input_parameters(params, calc_mode, job_profile):
    """Store parameters in uiapi.oq_job_profile columns"""

    for name, param in PARAMS.items():
        if calc_mode in param.modes and param.default is not None:
            setattr(job_profile, param.column, param.default)

    for name, value in params.items():
        param = PARAMS[name]
        value = value.strip()

        if param.type in (models.BooleanField, models.NullBooleanField):
            value = value.lower() not in ('0', 'false')
        elif param.type == models.PolygonField:
            ewkt = shapes.polygon_ewkt_from_coords(value)
            value = GEOSGeometry(ewkt)
        elif param.type == models.MultiPointField:
            ewkt = shapes.multipoint_ewkt_from_coords(value)
            value = GEOSGeometry(ewkt)
        elif param.type == FloatArrayField:
            value = [float(v) for v in ARRAY_RE.split(value) if len(v)]
        elif param.type == CharArrayField:
            if param.to_db is not None:
                value = param.to_db(value)
            value = [str(v) for v in ARRAY_RE.split(value) if len(v)]
        elif param.to_db is not None:
            value = param.to_db(value)
        elif param.type == None:
            continue

        setattr(job_profile, param.column, value)

    if job_profile.imt != 'sa':
        job_profile.period = None
        job_profile.damping = None


def run_job(job, params, sections, output_type='db', log_level='warn',
            force_inputs=False, log_file=None):
    """Given an :class:`openquake.db.models.OqJobProfile` object, create a new
    :class:`openquake.db.models.OqJob` object and run the job.

    NOTE: The params and sections parameters are temporary but will be required
    until we can run calculations purely using Django model objects as
    calculator input.

    Returns the calculation object when the calculation concludes.

    :param job:
        :class:`openquake.db.models.OqJob` instance
    :param params:
        A dictionary of config parameters parsed from the calculation
        config file.
    :param sections:
        A list of sections parsed from the calculation config file.
    :param output_type:
        'db' or 'xml' (defaults to 'db')
    :param str log_level:
        One of 'debug', 'info', 'warn', 'error', or 'critical'.
        Defaults to 'warn'.
    :param bool force_inputs: If `True` the model input files will be parsed
        and the resulting content written to the database no matter what.
    :param str log_file:
        Optional log file location.

    :returns:
        :class:`openquake.db.models.OqJob` instance.
    """
    if not output_type in ('db', 'xml'):
        raise RuntimeError("output_type must be 'db' or 'xml'")

    job.description = job.profile().description
    job.status = 'running'
    job.save()

    # Clear any counters for this job_id, prior to running the
    # job.
    # We do this just to make sure all of the counters behave properly and can
    # provide accurate data about a calculation in-progress.
    stats.delete_job_counters(job.id)

    # Make the job/calculation ID generally available.
    utils_config.Config().job_id = job.id

    serialize_results_to = ['db']
    if output_type == 'xml':
        serialize_results_to.append('xml')

    job_ctxt = JobContext(params, job.id, sections=sections,
                          serialize_results_to=serialize_results_to,
                          oq_job_profile=job.profile(), oq_job=job,
                          log_level=log_level, force_inputs=force_inputs)

    # closing all db connections to make sure they're not shared between
    # supervisor and job executor processes. otherwise if one of them closes
    # the connection it immediately becomes unavailable for other
    close_connection()

    job_pid = os.fork()
    if not job_pid:
        # calculation executor process
        try:
            logs.init_logs_amqp_send(level=log_level, job_id=job.id)
            _launch_job(job_ctxt, sections)
        except Exception, ex:
            logs.LOG.critical("Calculation failed with exception: '%s'"
                              % str(ex))
            job.status = 'failed'
            job.save()
            raise
        else:
            job.status = 'succeeded'
            job.save()
        return

    supervisor_pid = os.fork()
    if not supervisor_pid:
        # supervisor process
        logs.set_logger_level(logs.logging.root, log_level)
        supervisor_pid = os.getpid()
        job.supervisor_pid = supervisor_pid
        job.job_pid = job_pid
        job.save()
        supervisor.supervise(job_pid, job.id, log_file=log_file)
        return

    # parent process

    # ignore Ctrl-C as well as supervisor process does. thus only
    # job executor terminates on SIGINT
    supervisor.ignore_sigint()
    # wait till both child processes are done
    os.waitpid(job_pid, 0)
    os.waitpid(supervisor_pid, 0)

    return job


def _launch_job(job_ctxt, sections):
    """Instantiate calculator(s) and actually run the job.

    :param job_ctxt:
        :class:`openquake.engine.JobContext` instance.
    :param sections:
        List of config file sections. Example::
            ['general', 'HAZARD', 'RISK']
    """
    # TODO(LB):
    # In the future, this should be moved to the initialize() method of the
    # base Calculator class, or something like that. For now, we don't want it
    # there because it would get called twice in a Hazard+Risk job.
    # This is going to need some thought.
    # Ignoring 'Access to a protected member'
    # pylint: disable=W0212
    job_ctxt._record_initial_stats()

    job_ctxt.to_kvs()

    output_dir = os.path.join(job_ctxt.base_path, job_ctxt['OUTPUT_DIR'])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    calc_mode = job_ctxt.oq_job_profile.calc_mode

    for job_type in ('hazard', 'risk'):
        if not job_type.upper() in sections:
            continue

        calc_class = CALCS[job_type][calc_mode]

        calculator = calc_class(job_ctxt)
        logs.LOG.debug("Launching calculation with id=%s and type='%s'"
                       % (job_ctxt.job_id, job_type))

        calculator.initialize()
        calculator.pre_execute()
        calculator.execute()
        calculator.post_execute()


def import_job_profile(path_to_cfg, job, user_name='openquake',
                       force_inputs=False):
    """Given the path to a job config file, create a new
    :class:`openquake.db.models.OqJobProfile`, save it to the DB, and return
    it.

    :param str path_to_cfg:
        Path to a job config file.
    :param job:
        The :class:`openquake.db.models.OqJob` instance to use
    :param user_name:
        The user performing this action.
    :param bool force_inputs: If `True` the model input files will be parsed
        and the resulting content written to the database no matter what.

    :returns:
        A tuple of :class:`openquake.db.models.OqJobProfile` instance,
        params dict, and sections list.
        NOTE: The params and sections are temporary. These should be removed
        from the return value the future whenever possible to keep the API
        clean.
    """
    params, sections = _parse_config_file(path_to_cfg)
    params, sections = _prepare_config_parameters(params, sections)

    validator = jobconf.default_validators(sections, params)
    is_valid, errors = validator.is_valid()

    if not is_valid:
        raise jobconf.ValidationException(errors)

    job_profile = _prepare_job(params, sections, user_name, job, force_inputs)
    return job_profile, params, sections
