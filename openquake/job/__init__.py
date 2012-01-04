# -*- coding: utf-8 -*-

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

"""A single hazard/risk job."""

import os
import re
import urlparse

from ConfigParser import ConfigParser
from datetime import datetime
from django.db import transaction
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from lxml import etree

from openquake import flags
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake import xml
from openquake.parser import exposure
from openquake.db.models import (
    OqCalculation, OqJobProfile, OqUser, CalcStats, FloatArrayField,
    CharArrayField, InputSet, Input)
from openquake.job import config as conf
from openquake.job import params as job_params
from openquake.job.mixins import Mixin
from openquake.job.params import (
    PARAMS, CALCULATION_MODE, ENUM_MAP, PATH_PARAMS, INPUT_FILE_TYPES,
    ARRAY_RE)
from openquake.kvs import mark_job_as_current
from openquake.logs import LOG
from openquake.utils import stats

RE_INCLUDE = re.compile(r'^(.*)_INCLUDE')

FLAGS = flags.FLAGS

REVERSE_ENUM_MAP = dict((v, k) for k, v in ENUM_MAP.iteritems())


def parse_config_file(config_file):
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
        raise conf.ValidationException(
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
                new_params, new_sections = parse_config_file(config_file)
                sections.extend(new_sections)
                params.update(new_params)
            else:
                sections.append(section)
                params[key] = value

    params['BASE_PATH'] = base_path

    return params, list(set(sections))


def prepare_config_parameters(params, sections):
    """
    Pre-process configuration parameters to:
        - remove unknown parameters
        - expand file paths to make them absolute
        - set default parameter values
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

    return new_params, sections


def get_source_models(logic_tree):
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


def _insert_input_files(params, input_set):
    """Create uiapi.input records for all input files"""

    # insert input files in input table
    for param_key, file_type in INPUT_FILE_TYPES.items():
        if param_key not in params:
            continue
        path = params[param_key]
        in_model = Input(input_set=input_set, path=path,
                         input_type=file_type, size=os.path.getsize(path))
        in_model.save()

    # insert soft-linked source models in input table
    if 'SOURCE_MODEL_LOGIC_TREE_FILE' in params:
        for path in get_source_models(params['SOURCE_MODEL_LOGIC_TREE_FILE']):
            in_model = Input(input_set=input_set, path=path,
                             input_type='source', size=os.path.getsize(path))
            in_model.save()


def _store_input_parameters(params, calc_mode, oqp):
    """Store parameters in uiapi.oq_job_profile columns"""

    for name, param in PARAMS.items():
        if calc_mode in param.modes and param.default is not None:
            setattr(oqp, param.column, param.default)

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

        setattr(oqp, param.column, value)

    if oqp.imt != 'sa':
        oqp.period = None
        oqp.damping = None


@transaction.commit_on_success(using='job_init')
def prepare_job(params, sections):
    """
    Create a new OqCalculation and fill in the related OpParams entry.

    Returns the newly created job object.

    :param dict params:
        The job config params.
    :params sections:
        The job config file sections, as a list of strings.
    """
    # TODO specify the owner as a command line parameter
    owner = OqUser.objects.get(user_name='openquake')

    input_set = InputSet(upload=None, owner=owner)
    input_set.save()

    calc_mode = CALCULATION_MODE[params['CALCULATION_MODE']]
    job_type = [s.lower() for s in sections
        if s.upper() in [conf.HAZARD_SECTION, conf.RISK_SECTION]]

    job = OqCalculation(owner=owner, path=None)

    oqp = OqJobProfile(input_set=input_set, calc_mode=calc_mode,
                       job_type=job_type)

    _insert_input_files(params, input_set)
    _store_input_parameters(params, calc_mode, oqp)

    oqp.save()

    job.oq_job_profile = oqp
    job.save()

    # Reset all progress indication counters for the job at hand.
    stats.delete_job_counters(job.id)

    return job


class Job(object):
    """A job is a collection of parameters identified by a unique id."""

    @staticmethod
    def from_kvs(job_id):
        """Return the job in the underlying kvs system with the given id."""
        params = kvs.get_value_json_decoded(
            kvs.tokens.generate_job_key(job_id))
        job = Job(params, job_id)
        return job

    @staticmethod
    def from_file(config_file, output_type):
        """
        Create a job from external configuration files.

        :param config_file: the external configuration file path
        :param output_type: where to store results:
            * 'db' database
            * 'xml' XML files *plus* database
        :param params: optional dictionary of default parameters, overridden by
            the ones read from the config file
        :type params: :py:class:`dict`
        """

        # output_type can be set, in addition to 'db' and 'xml', also to
        # 'xml_without_db', which has the effect of serializing only to xml
        # without requiring a database at all.
        # This allows to run tests without requiring a database.
        # This is not documented in the public interface because it is
        # essentially a detail of our current tests and ci infrastructure.
        assert output_type in ('db', 'xml', 'xml_without_db')

        params, sections = parse_config_file(config_file)
        params, sections = prepare_config_parameters(params, sections)

        validator = conf.default_validators(sections, params)
        is_valid, errors = validator.is_valid()

        if not is_valid:
            raise conf.ValidationException(errors)

        if output_type == 'xml_without_db':
            # we are running a test
            job_id = 0
            serialize_results_to = ['xml']
        else:
            # openquake-server creates the job record in advance and stores the
            # job id in the config file
            job_id = params.get('OPENQUAKE_JOB_ID')
            if not job_id:
                # create the database record for this job
                job_id = prepare_job(params, sections).id

            if output_type == 'db':
                serialize_results_to = ['db']
            else:
                serialize_results_to = ['db', 'xml']

        base_path = params['BASE_PATH']

        job = Job(params, job_id, sections=sections, base_path=base_path,
                  serialize_results_to=serialize_results_to)
        job.to_kvs()

        return job

    @staticmethod
    def get_status_from_db(job_id):
        """
        Get the status of the database record belonging to job ``job_id``.

        :returns: one of strings 'pending', 'running', 'succeeded', 'failed'.
        """
        return OqCalculation.objects.get(id=job_id).status

    @staticmethod
    def is_job_completed(job_id):
        """
        Return ``True`` if the :meth:`current status <get_status_from_db>`
        of the job ``job_id`` is either 'succeeded' or 'failed'. Returns
        ``False`` otherwise.
        """
        status = Job.get_status_from_db(job_id)
        return status == 'succeeded' or status == 'failed'

    def __init__(self, params, job_id, sections=list(), base_path=None,
                 serialize_results_to=list()):
        """
        :param dict params: Dict of job config params.
        :param int job_id: ID of the corresponding oq_calculation db record.
        :param list sections: List of config file sections. Example::
            ['HAZARD', 'RISK']
        :param str base_path: base directory containing job input files
        """
        self._job_id = job_id
        mark_job_as_current(job_id)  # enables KVS gc

        self.sites = []
        self.blocks_keys = []
        self.params = params
        self.sections = list(set(sections))
        self.serialize_results_to = []
        self.base_path = base_path
        self.serialize_results_to = list(serialize_results_to)

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

    def set_status(self, status):
        """
        Set the status of the database record belonging to this job.

        :param status: one of 'pending', 'running', 'succeeded', 'failed'
        :type status: string
        """
        job = OqCalculation.objects.get(id=self.job_id)
        job.status = status
        job.save()

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
        defined_param = job_params.PARAMS.get(name)
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
            LOG.debug("Can't slurp files without a base path, homie...")
            return
        for key, val in self.params.items():
            if key[-5:] == '_FILE':
                path = os.path.join(self.base_path, val)
                with open(path) as data_file:
                    LOG.debug("Slurping %s" % path)
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
        data['debug'] = FLAGS.debug
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

        if conf.RISK_SECTION in self.sections \
                and self.has(conf.COMPUTE_HAZARD_AT_ASSETS):

            print "COMPUTE_HAZARD_AT_ASSETS_LOCATIONS selected, " \
                "computing hazard on exposure sites..."

            self.sites = read_sites_from_exposure(self)
        elif self.has(conf.SITES):

            coords = self._extract_coords(conf.SITES)
            sites = []

            for coord in coords:
                sites.append(shapes.Site(coord[0], coord[1]))

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
        return [site for site in region]

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
        uiapi.calc_stats record to the db.
        '''
        oq_calculation = OqCalculation.objects.get(id=self.job_id)

        calc_stats = CalcStats(oq_calculation=oq_calculation)
        calc_stats.start_time = datetime.utcnow()
        calc_stats.num_sites = len(self.sites_to_compute())

        calc_mode = CALCULATION_MODE[self['CALCULATION_MODE']]
        if conf.HAZARD_SECTION in self.sections:
            if calc_mode != 'scenario':
                calc_stats.realizations = self["NUMBER_OF_LOGIC_TREE_SAMPLES"]

        calc_stats.save()


def read_sites_from_exposure(a_job):
    """
    Given the exposure model specified in the job config, read all sites which
    are located within the region of interest.

    :param a_job: a Job object with an EXPOSURE parameter defined
    :type a_job: :py:class:`openquake.job.Job`

    :returns: a list of :py:class:`openquake.shapes.Site` objects
    """

    sites = []
    path = os.path.join(a_job.base_path, a_job.params[conf.EXPOSURE])

    reader = exposure.ExposurePortfolioFile(path)
    constraint = a_job.region

    LOG.debug(
        "Constraining exposure parsing to %s" % constraint)

    for site, _asset_data in reader.filter(constraint):

        # we don't want duplicates (bug 812395):
        if not site in sites:
            sites.append(site)

    return sites
