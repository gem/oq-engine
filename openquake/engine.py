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


"""The 'Engine' is responsible for instantiating calculators and running jobs.
"""


import re
import os

from ConfigParser import ConfigParser
from lxml import etree

from django.db import close_connection, transaction

from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry

from openquake import logs
from openquake import shapes
from openquake import xml

from openquake.flags import FLAGS
from openquake.job import config as jobconf
from openquake.job import Job
from openquake.supervising import supervisor
from openquake.utils import stats

from openquake.db.models import (CharArrayField, FloatArrayField, Input,
                                 InputSet, OqCalculation, OqJobProfile, OqUser)
from openquake.job.params import (ARRAY_RE, CALCULATION_MODE, INPUT_FILE_TYPES,
                                  PARAMS, PATH_PARAMS)
from openquake.hazard.calc import CALCULATORS as HAZ_CALCS
from openquake.risk.calc import CALCULATORS as RISK_CALCS


CALCS = dict(hazard=HAZ_CALCS, risk=RISK_CALCS)

RE_INCLUDE = re.compile(r'^(.*)_INCLUDE')


def run_job(job_file, output_type):
    """
    Given a job_file, run the job.

    :param job_file: the path of the configuration file for the job
    :type job_file: string
    :param output_type: the desired format for the results, one of 'db', 'xml'
    :type output_type: string
    """
    a_job = job_from_file(job_file, output_type)
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
            launch(a_job)
        except Exception, ex:
            logs.LOG.critical("Job failed with exception: '%s'" % str(ex))
            a_job.set_status('failed')
            raise
        else:
            a_job.set_status('succeeded')
        return

    supervisor_pid = os.fork()
    if not supervisor_pid:
        # supervisor process
        supervisor_pid = os.getpid()
        job = OqCalculation.objects.get(id=a_job.job_id)
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


def launch(a_job):
    """Based on the behavior specified in the configuration, mix in the correct
    behavior for job and execute it.

    :param a_job:
        :class:`openquake.job.Job` instance.
    """
    # TODO: This needs to be done as a pre-execution step of calculation.
    a_job._record_initial_stats()  # pylint: disable=W0212

    output_dir = os.path.join(a_job.base_path, a_job['OUTPUT_DIR'])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for job_type in ('hazard', 'risk'):
        if not job_type.upper() in a_job.sections:
            continue

        calc_mode = a_job['CALCULATION_MODE']
        calc_class = CALCS[job_type][calc_mode]

        calculator = calc_class(a_job)
        calculator.execute()


def job_from_file(config_file, output_type, owner_username='openquake'):
    """
    Create a job from external configuration files.

    :param config_file:
        The external configuration file path
    :param output_type:
        Where to store results:
        * 'db' database
        * 'xml' XML files *plus* database
    """

    # output_type can be set, in addition to 'db' and 'xml', also to
    # 'xml_without_db', which has the effect of serializing only to xml
    # without requiring a database at all.
    # This allows to run tests without requiring a database.
    # This is not documented in the public interface because it is
    # essentially a detail of our current tests and ci infrastructure.
    assert output_type in ('db', 'xml')

    params, sections = parse_config_file(config_file)
    params, sections = prepare_config_parameters(params, sections)
    job_profile = _prepare_job(params, sections)

    validator = jobconf.default_validators(sections, params)
    is_valid, errors = validator.is_valid()

    if not is_valid:
        raise jobconf.ValidationException(errors)

    owner = OqUser.objects.get(user_name=owner_username)
    # openquake-server creates the calculation record in advance and stores
    # the calculation id in the config file
    calculation_id = params.get('OPENQUAKE_JOB_ID')
    if not calculation_id:
        # create the database record for this calculation
        calculation = OqCalculation(owner=owner, path=None)
        calculation.oq_job_profile = job_profile
        calculation.save()
        calculation_id = calculation.id

    if output_type == 'db':
        serialize_results_to = ['db']
    else:
        serialize_results_to = ['db', 'xml']

    base_path = params['BASE_PATH']

    job = Job(params, calculation_id, sections=sections, base_path=base_path,
              serialize_results_to=serialize_results_to)
    job.to_kvs()

    return job


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

    return new_params, sections


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


@transaction.commit_on_success(using='job_init')
def _prepare_job(params, sections, owner_username='openquake'):
    """
    Create a new OqCalculation and fill in the related OqJobProfile entry.

    Returns the newly created job object.

    :param dict params:
        The job config params.
    :params sections:
        The job config file sections, as a list of strings.

    :returns:
        A new :class:`openquake.db.models.OqJobProfile` object.
    """

    @transaction.commit_on_success(using='job_init')
    def _get_job_profile(input_set, calc_mode, job_type, owner):
        """Create an OqJobProfile, save it to the db, commit, and return."""
        job_profile = OqJobProfile(input_set=input_set, calc_mode=calc_mode,
                                   job_type=job_type)

        _insert_input_files(params, input_set)
        _store_input_parameters(params, calc_mode, job_profile)

        job_profile.owner = owner
        job_profile.save()

        # Reset all progress indication counters for the job at hand.
        # TODO: Put this back in, in the correct place.
        # stats.delete_job_counters(job.id)

        return job_profile

    # TODO specify the owner as a command line parameter
    owner = OqUser.objects.get(user_name=owner_username)

    input_set = InputSet(upload=None, owner=owner)
    input_set.save()

    calc_mode = CALCULATION_MODE[params['CALCULATION_MODE']]
    job_type = [s.lower() for s in sections
        if s.upper() in [jobconf.HAZARD_SECTION, jobconf.RISK_SECTION]]

    job_profile = _get_job_profile(input_set, calc_mode, job_type, owner)
    job_profile.owner = owner

    # When querying this record from the db, Django changes the values
    # slightly (with respect to geometry, for example). Thus, we want a
    # "fresh" copy of the record from the db.
    return OqJobProfile.objects.get(id=job_profile.id)


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


def run_calc(job_profile):
    """Given an :class:`openquake.db.models.OqJobProfile` object, create a new
    :class:`openquake.db.models.OqCalculation` object and run the calculation.

    Returns the calculation object.

    :param job_profile:
        :class:`openquake.db.models.OqJobProfile` instance.
    :returns:
        :class:`openquake.db.models.OqCalculation` instance.
    """


def import_job_profile(path_to_cfg):
    """Given the path to a job config file, create a new
    :class:`openquake.db.models.OqJobProfile` and save it to the DB, and return
    it.

    :param str path_to_cfg:
        Path to a job config file.
    :returns:
        :class:`openquake.db.models.OqJobProfile` instance.
    """
    params, sections = parse_config_file(path_to_cfg)
    params, sections = prepare_config_parameters(params, sections)

    validator = jobconf.default_validators(sections, params)
    is_valid, errors = validator.is_valid()

    if not is_valid:
        raise jobconf.ValidationException(errors)

    job_profile = _prepare_job(params, sections)
    return job_profile
