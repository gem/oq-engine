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
from openquake.job import CalculationProxy
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


def _job_from_file(config_file, output_type, owner_username='openquake'):
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
    """

    # output_type can be set, in addition to 'db' and 'xml', also to
    # 'xml_without_db', which has the effect of serializing only to xml
    # without requiring a database at all.
    # This allows to run tests without requiring a database.
    # This is not documented in the public interface because it is
    # essentially a detail of our current tests and ci infrastructure.
    assert output_type in ('db', 'xml')

    params, sections = _parse_config_file(config_file)
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

    job = CalculationProxy(params, calculation_id, sections=sections,
                           base_path=base_path,
                           serialize_results_to=serialize_results_to)
    job.to_kvs()

    return job


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
        for path in _get_source_models(params['SOURCE_MODEL_LOGIC_TREE_FILE']):
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


def run_calculation(job_profile, params, sections, output_type='db'):
    """Given an :class:`openquake.db.models.OqJobProfile` object, create a new
    :class:`openquake.db.models.OqCalculation` object and run the calculation.

    NOTE: The params and sections parameters are temporary but will be required
    until we can run calculations purely using Django model objects as
    calculator input.

    Returns the calculation object when the calculation concludes.

    :param job_profile:
        :class:`openquake.db.models.OqJobProfile` instance.
    :param params:
        A dictionary of config parameters parsed from the calculation
        config file.
    :param sections:
        A list of sections parsed from the calculation config file.
    :param output_type:
        'db' or 'xml' (defaults to 'db')

    :returns:
        :class:`openquake.db.models.OqCalculation` instance.
    """
    if not output_type in ('db', 'xml'):
        raise RuntimeError("output_type must be 'db' or 'xml'")

    calculation = OqCalculation(owner=job_profile.owner)
    calculation.oq_job_profile = job_profile
    calculation.status = 'running'
    calculation.save()

    # Clear any counters for this calculation_id, prior to running the
    # calculation.
    # We do this just to make sure all of the counters behave properly and can
    # provide accurate data about a calculation in-progress.
    stats.delete_job_counters(calculation.id)

    serialize_results_to = ['db']
    if output_type == 'xml':
        serialize_results_to.append('xml')

    calc_proxy = CalculationProxy(params, calculation.id, sections=sections,
                                  serialize_results_to=serialize_results_to,
                                  oq_job_profile=job_profile,
                                  oq_calculation=calculation)

    # closing all db connections to make sure they're not shared between
    # supervisor and job executor processes. otherwise if one of them closes
    # the connection it immediately becomes unavailable for other
    close_connection()

    calc_pid = os.fork()
    if not calc_pid:
        # calculation executor process
        try:
            logs.init_logs_amqp_send(level=FLAGS.debug, job_id=calculation.id)
            _launch_calculation(calc_proxy, sections)
        except Exception, ex:
            logs.LOG.critical("Calculation failed with exception: '%s'"
                              % str(ex))
            calculation.status = 'failed'
            calculation.save()
            raise
        else:
            calculation.status = 'succeeded'
            calculation.save()
        return

    supervisor_pid = os.fork()
    if not supervisor_pid:
        # supervisor process
        supervisor_pid = os.getpid()
        calculation.supervisor_pid = supervisor_pid
        calculation.job_pid = calc_pid
        calculation.save()
        supervisor.supervise(calc_pid, calculation.id)
        return

    # parent process

    # ignore Ctrl-C as well as supervisor process does. thus only
    # job executor terminates on SIGINT
    supervisor.ignore_sigint()
    # wait till both child processes are done
    os.waitpid(calc_pid, 0)
    os.waitpid(supervisor_pid, 0)

    return calculation


def _launch_calculation(calc_proxy, sections):
    """Instantiate calculator(s) and actually run the calculation.

    :param calc_proxy:
        :class:`openquake.job.CalculationProxy` instance.
    :param sections:
        List of config file sections. Example::
            ['general', 'HAZARD', 'RISK']
    """
    # This should be moved to the analyze() method of the base Calculator
    # class, or something like that.
    # Ignoring 'Access to a protected member'
    # pylint: disable=W0212
    calc_proxy._record_initial_stats()
    calc_proxy.to_kvs()

    output_dir = os.path.join(calc_proxy.base_path, calc_proxy['OUTPUT_DIR'])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    calc_mode = calc_proxy.oq_job_profile.calc_mode


    for job_type in ('hazard', 'risk'):
        if not job_type.upper() in sections:
            continue

        calc_class = CALCS[job_type][calc_mode]

        calculator = calc_class(calc_proxy)
        logs.LOG.debug("Launching calculation with id=%s and type='%s'"
                       % (calc_proxy.job_id, job_type))
        calculator.execute()


def import_job_profile(path_to_cfg):
    """Given the path to a job config file, create a new
    :class:`openquake.db.models.OqJobProfile` and save it to the DB, and return
    it.

    :param str path_to_cfg:
        Path to a job config file.

    :returns:
        A tuple of :class:`openquake.db.models.OqJobProfile` instance,
        params dict, and sections list.
        NOTE: The params and sections are temporary. These should be removed
        from the return value the future whenever possible to keep the API
        clean.
    """
    params, sections = _parse_config_file(path_to_cfg)
    params, sections = prepare_config_parameters(params, sections)

    validator = jobconf.default_validators(sections, params)
    is_valid, errors = validator.is_valid()

    if not is_valid:
        raise jobconf.ValidationException(errors)

    job_profile = _prepare_job(params, sections)
    return job_profile, params, sections
