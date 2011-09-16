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
import subprocess
import urlparse
import logging

from ConfigParser import ConfigParser, RawConfigParser
from datetime import datetime
from django.db import transaction, close_connection
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry

from openquake import flags
from openquake import java
from openquake import kvs
from openquake import logs
from openquake import OPENQUAKE_ROOT
from openquake import shapes
from openquake.db.models import (
    OqJob, OqParams, OqUser, JobStats, FloatArrayField)
from openquake.supervising import supervisor
from openquake.job.handlers import resolve_handler
from openquake.job import config as conf
from openquake.job.mixins import Mixin
from openquake.job.params import PARAMS, CALCULATION_MODE, ENUM_MAP
from openquake.kvs import mark_job_as_current
from openquake.logs import LOG
from openquake.utils import config as oq_config

RE_INCLUDE = re.compile(r'^(.*)_INCLUDE')

FLAGS = flags.FLAGS

REVERSE_ENUM_MAP = dict((v, k) for k, v in ENUM_MAP.iteritems())


def run_job(job_file, output_type):
    """
    Given a job_file, run the job.

    :param job_file: the path of the configuration file for the job
    :type job_file: string
    :param output_type: the desired format for the results, one of 'db', 'xml'
    :type output_type: string
    """
    a_job = Job.from_file(job_file, output_type)
    a_job.set_status('running')

    # closing all db connections to make sure they're not shared between
    # supervisor and job executor processes. otherwise if one of them closes
    # the connection it immediately becomes unavailable for other
    close_connection()

    job_pid = os.fork()
    if not job_pid:
        # job executor process
        try:
            logs.init_logs_amqp_send(level=FLAGS.debug, job_id=a_job.job_id)
            a_job.launch()
        except Exception, ex:
            LOG.critical("Job failed with exception: '%s'" % str(ex))
            a_job.set_status('failed')
            raise
        else:
            a_job.set_status('succeeded')
        return

    supervisor_pid = os.fork()
    if not supervisor_pid:
        # supervisor process
        supervisor_pid = os.getpid()
        job = OqJob.objects.get(id=a_job.job_id)
        job.supervisor_pid = supervisor_pid
        job.job_pid = job_pid
        job.save()
        supervisor.supervise(job_pid, a_job.job_id)
        return

    # parent process

    # ignore Ctrl-C as well as supervisor process does. thus only
    # job executor terminates on SIGINT
    supervisor.ignore_sigint()
    # wait till both child processes are done
    os.waitpid(job_pid, 0)
    os.waitpid(supervisor_pid, 0)


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
                config_file = "%s/%s" % (os.path.dirname(config_file), value)
                new_params, new_sections = parse_config_file(config_file)
                sections.extend(new_sections)
                params.update(new_params)
            else:
                sections.append(section)
                params[key] = value

    params['BASE_PATH'] = base_path

    return params, list(set(sections))


def filter_configuration_parameters(params, sections):
    """
    Pre-process configuration parameters removing unknown ones.
    """

    job_type = CALCULATION_MODE[params['CALCULATION_MODE']]
    new_params = dict()

    for name, value in params.items():
        try:
            param = PARAMS[name]
        except KeyError:
            print 'Ignoring unknown parameter %r' % name
            continue

        if job_type not in param.modes:
            print 'Ignoring', name, 'in', job_type, \
                ', it\'s meaningful only in', ', '.join(param.modes)
            continue

        new_params[name] = value

    return new_params, sections


def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""

    url = urlparse.urlparse(file_spec)
    return resolve_handler(url, base_path).get()


@transaction.commit_on_success(using='job_init')
def prepare_job(params):
    """
    Create a new OqJob and fill in the related OpParams entry.

    Returns the newly created job object.
    """
    oqp = OqParams(upload=None)

    # TODO specify the owner as a command line parameter
    owner = OqUser.objects.get(user_name='openquake')

    job = OqJob(
        owner=owner, path=None,
        job_type=CALCULATION_MODE[params['CALCULATION_MODE']])

    oqp.job_type = job.job_type

    for name, param in PARAMS.items():
        if job.job_type in param.modes and param.default is not None:
            setattr(oqp, param.column, param.default)

    number_re = re.compile('[^0-9.]+')

    for name, value in params.items():
        param = PARAMS[name]
        value = value.strip()

        if param.to_db is not None:
            value = param.to_db(value)
        elif param.type in (models.BooleanField, models.NullBooleanField):
            value = value.lower() not in ('0', 'false')
        elif param.type == models.PolygonField:
            ewkt = shapes.polygon_ewkt_from_coords(value)
            value = GEOSGeometry(ewkt)
        elif param.type == models.MultiPointField:
            ewkt = shapes.multipoint_ewkt_from_coords(value)
            value = GEOSGeometry(ewkt)
        elif param.type == FloatArrayField:
            value = [float(v) for v in number_re.split(value) if len(v)]
        elif param.type == None:
            continue

        setattr(oqp, param.column, value)

    if oqp.imt != 'sa':
        oqp.period = None
        oqp.damping = None

    oqp.save()
    job.oq_params = oqp
    job.save()

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
        params, sections = filter_configuration_parameters(params, sections)

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
                job_id = prepare_job(params).id

            if output_type == 'db':
                serialize_results_to = ['db']
            else:
                serialize_results_to = ['db', 'xml']

        base_path = params['BASE_PATH']

        job = Job(params, job_id, sections=sections, base_path=base_path)
        job.serialize_results_to = serialize_results_to

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
        status = Job.get_status_from_db(job_id)
        return status == 'succeeded' or status == 'failed'

    def __init__(self, params, job_id, sections=list(), base_path=None,
            validator=None):
        """
        :param dict params: Dict of job config params.
        :param int job_id: ID of the corresponding oq_job db record.
        :param list sections: List of config file sections. Example::
            ['HAZARD', 'RISK']
        :param str base_path: base directory containing job input files
        :param validator: validator(s) used to check the configuration file
        """
        self._job_id = job_id
        mark_job_as_current(job_id)  # enables KVS gc

        self.blocks_keys = []
        self.params = params
        self.sections = list(set(sections))
        self.serialize_results_to = []
        self.base_path = base_path
        self.validator = validator

        if base_path:
            self.to_kvs()

    def has(self, name):
        """Return true if this job has the given parameter defined
        and specified, false otherwise."""
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
        job = OqJob.objects.get(id=self.job_id)
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

    @property
    def super_config_path(self):
        """ Return the path of the super config """
        filename = "%s-super.gem" % self.job_id
        return os.path.join(self.base_path or '', "./", filename)

    def launch(self):
        """ Based on the behaviour specified in the configuration, mix in the
        correct behaviour for the tasks and then execute them.
        """
        self._record_initial_stats()

        output_dir = os.path.join(self.base_path, self['OUTPUT_DIR'])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for (key, mixin) in Mixin.ordered_mixins():
            if key.upper() not in self.sections:
                continue

            with Mixin(self, mixin):
                # The mixin defines a preload decorator to handle the needed
                # data for the tasks and decorates _execute(). the mixin's
                # _execute() method calls the expected tasks.
                LOG.debug(
                    "Job %s Launching %s for %s" % (self.job_id, mixin, key))
                self.execute()

    def __getitem__(self, name):
        return self.params[name]

    def __eq__(self, other):
        return self.params == other.params

    def __str__(self):
        return str(self.params)

    def _write_super_config(self):
        """
            Take our params and write them out as a 'super' config file.
            Its name is equal to the job_id, which should be the sha1 of
            the file in production or a random job in dev.
        """

        kvs_client = kvs.get_client()
        config = RawConfigParser()

        section = 'openquake'
        config.add_section(section)

        for key, val in self.params.items():
            v = kvs_client.get(val)
            if v:
                val = v
            config.set(section, key, val)

        with open(self.super_config_path, "wb") as configfile:
            config.write(configfile)

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

    def to_kvs(self, write_cfg=True):
        """Store this job into kvs."""
        self._slurp_files()
        if write_cfg:
            self._write_super_config()
        key = kvs.tokens.generate_job_key(self.job_id)
        data = self.params.copy()
        data['debug'] = FLAGS.debug
        kvs.set_value_json_encoded(key, data)

    def sites_to_compute(self):
        """Return the sites used to trigger the computation on the
        hazard subsystem.

        If the SITES parameter is specified, the computation is triggered
        only on the sites specified in that parameter, otherwise
        the region is used."""

        if self.has(conf.SITES):
            sites = []
            coords = self._extract_coords(conf.SITES)

            for coord in coords:
                sites.append(shapes.Site(coord[0], coord[1]))

            return sites
        else:
            return self._sites_for_region()

    def _extract_coords(self, config_param):
        """Extract from a configuration parameter the list of coordinates."""
        verts = [float(x) for x in self.params[config_param].split(",")]
        return zip(verts[1::2], verts[::2])

    def _sites_for_region(self):
        """Return the list of sites for the region at hand."""
        region = shapes.Region.from_coordinates(
            self._extract_coords('REGION_VERTEX'))

        region.cell_size = float(self.params['REGION_GRID_SPACING'])
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
        return self.extract_values_from_config('INTENSITY_MEASURE_LEVELS',
                                               separator=',')

    def _record_initial_stats(self):
        '''
        Report initial job stats (such as start time) by adding a
        uiapi.job_stats record to the db.
        '''
        oq_job = OqJob.objects.get(id=self.job_id)

        stats = JobStats(oq_job=oq_job)
        stats.start_time = datetime.utcnow()
        stats.num_sites = len(self.sites_to_compute())

        stats.save()
