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

"""Engine: A collection of fundamental functions for initializing and running
calculations."""

import ConfigParser
import csv
import getpass
import md5
import os
import sys
import warnings

import openquake.engine

from django.core import exceptions
from django.db import close_connection

from openquake.engine import kvs
from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.job.validation import validate
from openquake.engine.supervising import supervisor
from openquake.engine.utils import monitor, get_calculator_class
from openquake.engine.writer import CacheInserter

from openquake import hazardlib
from openquake import risklib
from openquake import nrmllib


INPUT_TYPES = dict(models.Input.INPUT_TYPE_CHOICES)
UNABLE_TO_DEL_HC_FMT = 'Unable to delete hazard calculation: %s'
UNABLE_TO_DEL_RC_FMT = 'Unable to delete risk calculation: %s'


def prepare_job(user_name="openquake", log_level='progress'):
    """
    Create job for the given user, return it.

    :param str username:
        Username of the user who owns/started this job. If the username doesn't
        exist, a user record for this name will be created.
    :param str log_level:
        Defaults to 'progress'. Specify a logging level for this job. This
        level can be passed, for example, from the command line interface using
        the `--log-level` directive.
    :returns:
        :class:`openquake.engine.db.models.OqJob` instance.
    """
    # See if the current user exists
    # If not, create a record for them
    owner = prepare_user(user_name)
    job = models.OqJob(
        owner=owner,
        log_level=log_level,
        oq_version=openquake.engine.__version__,
        nrml_version=nrmllib.__version__,
        hazardlib_version=hazardlib.__version__,
        risklib_version=risklib.__version__,
    )
    job.save()
    return job


def prepare_user(user_name):
    """
    Make sure user with the given name exists, return it.
    """
    # See if the current user exists
    # If not, create a record for them
    try:
        user = models.OqUser.objects.get(user_name=user_name)
    except exceptions.ObjectDoesNotExist:
        # This user doesn't exist; let's fix that.
        # NOTE: The Organization is currently hardcoded to 1.
        # This org is added when the database is bootstrapped.
        user = models.OqUser(
            user_name=user_name, full_name=user_name, organization_id=1
        )
        user.save()
    return user


def get_current_user():
    """
    Utilty function for getting the :class:`openquake.engine.db.models.OqUser`
    for the the current user. If the user record doesn't exist, it will be
    created.
    """
    return prepare_user(getpass.getuser())


def parse_config(source):
    """Parse a dictionary of parameters from an INI-style config file.

    :param source:
        File-like object containing the config parameters.
    :returns:
        A `dict` of the parameter keys and values parsed from the config file
        and a `dict` of input model file paths keyed by input type.

        These dicts are return as a tuple/pair.
    """
    cp = ConfigParser.ConfigParser()
    cp.readfp(source)

    base_path = os.path.dirname(
        os.path.join(os.path.abspath('.'), source.name))
    params = dict(base_path=base_path)
    files = dict()

    # Directory containing the config file we're parsing.
    base_path = os.path.dirname(os.path.abspath(source.name))

    for sect in cp.sections():
        for key, value in cp.items(sect):
            if key == 'sites_csv':
                # Parse site coordinates from the csv file,
                # return as MULTIPOINT WKT:
                path = value
                if not os.path.isabs(path):
                    # It's a relative path
                    path = os.path.join(base_path, path)
                params['sites'] = _parse_sites_csv(open(path, 'r'))
            elif key.endswith('_file'):
                input_type = key[:-5]
                if not input_type in INPUT_TYPES:
                    raise ValueError(
                        'The parameter %s in the .ini file does '
                        'not correspond to a valid input type' % key)
                path = value
                # The `path` may be a path relative to the config file, or it
                # could be an absolute path.
                if not os.path.isabs(path):
                    # It's a relative path.
                    path = os.path.join(base_path, path)

                files[input_type] = path
            else:
                params[key] = value

    return params, files


def _parse_sites_csv(fh):
    """
    Get sites of interest from a csv file. The csv file (``fh``) is expected to
    have 2 columns: lon,lat.

    :param fh:
        File-like containing lon,lat coordinates in csv format.

    :returns:
        MULTIPOINT WKT representing all of the sites in the csv file.
    """
    reader = csv.reader(fh)
    coords = []
    for lon, lat in reader:
        coords.append('%s %s' % (lon, lat))

    return 'MULTIPOINT(%s)' % ', '.join(coords)


def _file_digest(path):
    """Return a 32 character digest for the file with the given pasth.

    :param str path:
        File path
    :returns:
        A 32 character string with the md5sum digest of the file.
    """
    checksum = md5.new()
    with open(path) as fh:
        checksum.update(fh.read())
        return checksum.hexdigest()


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


def get_or_create_input(path, input_type, owner, name=None,
                        haz_calc_id=None, risk_calc_id=None):
    """
    Get or create an :class:`~openquake.engine.db.models.Input` object for the
    given file (``path``) associated with a particular calculation. You must
    specify either ``haz_calc_id`` or ``risk_calc_id``.

    :param str path:
        Path to the input file.
    :param str input_type:
        The type of input. See :class:`openquake.engine.db.models.Input` for
        a list of valid types.
    :param owner:
        The :class:`~openquake.engine.db.models.OqUser` who will own the input
        that will be created.
    :param str name:
        Optional name to help idenfity this input.
    :param haz_calc_id:
        ID of a hazard calculation.
    :param risk_calc_id:
        ID of a risk calculation.
    :returns:
        :class:`openquake.engine.db.models.Input` object to represent the
        input. As a side effect, this function will also store a full raw copy
        of the input file
        (see :class:`openquake.engine.db.models.ModelContent`)
        and associate it to the `Input`.
    """
    assert not [haz_calc_id, risk_calc_id] == [None, None], (
        "Must specify one of either `haz_calc_id` or `risk_calc_id`."
    )

    try:
        # Try to get a preloaded model
        if haz_calc_id is not None:
            i2c = models.Input2hcalc.objects.get(
                hazard_calculation=haz_calc_id,
                input__path=path,
                input__input_type=input_type,
                input__owner=owner,
            )
            if name is not None:
                i2c = i2c.filter(input__name=name)
            inp = i2c.input
        elif risk_calc_id is not None:
            i2c = models.Input2rcalc.objects.get(
                risk_calculation=risk_calc_id,
                input__path=path,
                input__input_type=input_type,
                input__owner=owner,
            )
            if name is not None:
                i2c = i2c.filter(input__name=name)
            inp = i2c.input
    except exceptions.ObjectDoesNotExist:
        # It doesn't exist yet. Let's create it.
        inp = create_input(path, input_type, owner, name=name)

        # Now that the input is created, associate it with the specified
        # calculation:
        if haz_calc_id is not None:
            hc = models.HazardCalculation.objects.get(id=haz_calc_id)
            models.Input2hcalc.objects.create(
                input=inp, hazard_calculation=hc
            )
        elif risk_calc_id is not None:
            rc = models.RiskCalculation.objects.get(id=risk_calc_id)
            models.Input2rcalc.objects.create(
                input=inp, risk_calculation=rc
            )

    return inp


def create_input(path, input_type, owner, name=None):
    """
    Create a :class:`~openquake.engine.db.models.Input` object from the
    given file (``path``).

    :param str path:
        Path to the input file.
    :param str input_type:
        The type of input. See :class:`openquake.engine.db.models.Input` for
        a list of valid types.
    :param owner:
        The :class:`~openquake.engine.db.models.OqUser` who will own the input
        that will be created.
    :param str name:
        Optional name to help idenfity this input.
    :returns:
        :class:`openquake.engine.db.models.Input` object to represent the
        input. As a side effect, this function will also store a full raw copy
        of the input file
        (see :class:`openquake.engine.db.models.ModelContent`)
        and associate it to the `Input`.
    """
    digest = _file_digest(path)

    model_content = models.ModelContent()
    with open(path, 'rb') as fh:
        model_content.raw_content = fh.read()
    # Try to guess the content type:
    model_content.content_type = _get_content_type(path)
    model_content.save()

    inp = models.Input(
        path=path, input_type=input_type, owner=owner,
        size=os.path.getsize(path), digest=digest,
        model_content=model_content, name=name
    )
    inp.save()
    return inp


def create_hazard_calculation(username, params, files):
    """
    Given a params `dict` parsed from the config file, create a
    :class:`~openquake.engine.db.models.HazardCalculation`.

    :param username:
        Username of the user who will own this calculation profile.
    :param dict params:
        Dictionary of parameter names and values. Parameter names should match
        exactly the field names of
        :class:`openquake.engine.db.model.HazardCalculation`.
    :param list files:
        List of :class:`~openquake.engine.db.models.Input` objects to be
        linked to the calculation.
    :returns:
        :class:`openquake.engine.db.model.HazardCalculation` object.
        A corresponding record will obviously be saved to the database.
    """
    owner = prepare_user(username)
    if "export_dir" in params:
        params["export_dir"] = os.path.abspath(params["export_dir"])

    haz_calc_fields = models.HazardCalculation._meta.get_all_field_names()
    for param in set(params) - set(haz_calc_fields):
        msg = "Unknown parameter '%s'. Ignoring."
        msg %= param
        warnings.warn(msg, RuntimeWarning)
        params.pop(param)

    hc = models.HazardCalculation(**params)
    hc.owner = owner
    hc.full_clean()
    hc.save()

    # Load the other input files into the database.
    # This also links the inputs to the calculation via the `input2hcalc` table.
    for input_type, input_path in files.iteritems():
        get_or_create_input(input_path, input_type, owner, haz_calc_id=hc.id)

    return hc


def create_risk_calculation(owner, params, files):
    """Given a params `dict` parsed from the config file, create a
    :class:`~openquake.engine.db.models.RiskCalculation`.

    :param owner:
        The :class:`~openquake.engine.db.models.OqUser` who will own this
        profile.
    :param dict params:
        Dictionary of parameter names and values. Parameter names should match
        exactly the field names of
        :class:`openquake.engine.db.model.RiskCalculation`.
    :param list files:
        List of :class:`~openquake.engine.db.models.Input` objects to be
        linked to the calculation.
    :returns:
        :class:`openquake.engine.db.model.RiskCalculation` object.
        A corresponding record will obviously be saved to the database.
    """
    if "export_dir" in params:
        params["export_dir"] = os.path.abspath(params["export_dir"])

    rc = models.RiskCalculation(**params)
    rc.owner = owner
    rc.full_clean()
    rc.save()

    for input_type, input_path in files.iteritems():
        get_or_create_input(input_path, input_type, owner, risk_calc_id=rc.id)

    return rc


# used by bin/openquake
def run_calc(job, log_level, log_file, exports, job_type):
    """
    Run a calculation.

    :param job:
        :class:`openquake.engine.db.model.OqJob` instance which references a
        valid :class:`openquake.engine.db.models.RiskCalculation` or
        :class:`openquake.engine.db.models.HazardCalculation`.
    :param str log_level:
        The desired logging level. Valid choices are 'debug', 'info',
        'progress', 'warn', 'error', and 'critical'.
    :param str log_file:
        Complete path (including file name) to file where logs will be written.
        If `None`, logging will just be printed to standard output.
    :param list exports:
        A (potentially empty) list of export targets. Currently only "xml" is
        supported.
    :param calc:
        Calculator object, which must implement the interface of
        :class:`openquake.engine.calculators.base.Calculator`.
    :param str job_type:
        'hazard' or 'risk'
    """
    calc_mode = getattr(job, '%s_calculation' % job_type).calculation_mode
    calc = get_calculator_class(job_type, calc_mode)(job)

    # Create job stats, which implicitly records the start time for the job
    models.JobStats.objects.create(oq_job=job)

    # Closing all db connections to make sure they're not shared between
    # supervisor and job executor processes.
    # Otherwise, if one of them closes the connection it immediately becomes
    # unavailable for others.
    close_connection()

    job_pid = os.fork()

    if not job_pid:
        # calculation executor process
        try:
            logs.init_logs_amqp_send(level=log_level, calc_domain=job_type,
                                     calc_id=job.calculation.id)
            # run the job
            job.is_running = True
            job.save()
            kvs.mark_job_as_current(job.id)
            _do_run_calc(job, exports, calc, job_type)
        except Exception, ex:
            logs.LOG.critical("Calculation failed with exception: '%s'"
                              % str(ex))
            raise
        finally:
            job.is_running = False
            job.save()
        return

    supervisor_pid = os.fork()
    if not supervisor_pid:
        # supervisor process
        logs.set_logger_level(logs.logging.root, log_level)
        # TODO: deal with KVS garbage collection
        supervisor.supervise(job_pid, job.id, log_file=log_file)
        return

    # parent process

    # ignore Ctrl-C as well as supervisor process does. thus only
    # job executor terminates on SIGINT
    supervisor.ignore_sigint()
    # wait till both child processes are done
    os.waitpid(job_pid, 0)
    os.waitpid(supervisor_pid, 0)

    # Refresh the job record, since the forked processes are going to modify
    # job state.
    return models.OqJob.objects.get(id=job.id)


def _switch_to_job_phase(job, ctype, status):
    """Switch to a particular phase of execution.

    This involves creating a `job_phase_stats` record and logging the new
    status.

    :param job:
        An :class:`~openquake.engine.db.models.OqJob` instance.
    :param str ctype: calculation type (hazard|risk)
    :param str status: one of the following: pre_executing, executing,
        post_executing, post_processing, export, clean_up, complete
    """
    job.status = status
    job.save()
    models.JobPhaseStats.objects.create(oq_job=job, job_status=status,
                                        ctype=ctype)
    logs.LOG.progress("%s (%s)" % (status, ctype))
    if status == "executing" and not openquake.engine.no_distribute():
        # Record the compute nodes that were available at the beginning of the
        # execute phase so we can detect failed nodes later.
        failed_nodes = monitor.count_failed_nodes(job)
        if failed_nodes == -1:
            logs.LOG.critical("No live compute nodes, aborting calculation")
            sys.exit(1)


def _do_run_calc(job, exports, calc, job_type):
    """
    Step through all of the phases of a calculation, updating the job
    status at each phase.

    :param job:
        An :class:`~openquake.engine.db.models.OqJob` instance.
    :param list exports:
        a (potentially empty) list of export targets, currently only "xml" is
        supported
    :returns:
        The input job object when the calculation completes.
    """
    # - Run the calculation
    _switch_to_job_phase(job, job_type, "pre_executing")

    calc.pre_execute()

    _switch_to_job_phase(job, job_type, "executing")
    calc.execute()

    _switch_to_job_phase(job, job_type, "post_executing")
    calc.post_execute()

    _switch_to_job_phase(job, job_type, "post_processing")
    calc.post_process()

    _switch_to_job_phase(job, job_type, "export")
    calc.export(exports=exports)

    _switch_to_job_phase(job, job_type, "clean_up")
    calc.clean_up()

    CacheInserter.flushall()  # flush caches into the db

    _switch_to_job_phase(job, job_type, "complete")
    logs.LOG.debug("*> complete")

    return job


def del_haz_calc(hc_id):
    """
    Delete a hazard calculation and all associated outputs.

    :param hc_id:
        ID of a :class:`~openquake.engine.db.models.HazardCalculation`.
    """
    try:
        hc = models.HazardCalculation.objects.get(id=hc_id)
    except exceptions.ObjectDoesNotExist:
        raise RuntimeError('Unable to delete hazard calculation: '
                           'ID=%s does not exist' % hc_id)

    user = get_current_user()
    if hc.owner == user:
        # we are allowed to delete this

        # but first, check if any risk calculations are referencing any of our
        # outputs, or the hazard calculation itself
        msg = UNABLE_TO_DEL_HC_FMT % (
            'The following risk calculations are referencing this hazard'
            ' calculation: %s'
        )

        # check for a reference to hazard outputs
        assoc_outputs = models.RiskCalculation.objects.filter(
            hazard_output__oq_job__hazard_calculation=hc_id
        )
        if assoc_outputs.count() > 0:
            raise RuntimeError(msg % ', '.join([str(x.id)
                                                for x in assoc_outputs]))

        # check for a reference to the hazard calculation itself
        assoc_calcs = models.RiskCalculation.objects.filter(
            hazard_calculation=hc_id
        )
        if assoc_calcs.count() > 0:
            raise RuntimeError(msg % ', '.join([str(x.id)
                                                for x in assoc_calcs]))

        # No risk calculation are referencing what we want to delete.
        # Carry on with the deletion.
        hc.delete(using='admin')
    else:
        # this doesn't belong to the current user
        raise RuntimeError(UNABLE_TO_DEL_HC_FMT % 'Access denied')


def del_risk_calc(rc_id):
    """
    Delete a risk calculation and all associated outputs.

    :param hc_id:
        ID of a :class:`~openquake.engine.db.models.RiskCalculation`.
    """
    try:
        rc = models.RiskCalculation.objects.get(id=rc_id)
    except exceptions.ObjectDoesNotExist:
        raise RuntimeError('Unable to delete risk calculation: '
                           'ID=%s does not exist' % rc_id)

    user = get_current_user()
    if rc.owner == user:
        # we are allowed to delete this
        rc.delete(using='admin')
    else:
        # this doesn't belong to the current user
        raise RuntimeError('Unable to delete risk calculation: '
                           'Access denied')


def run_hazard(cfg_file, log_level, log_file, exports):
    """
    Run a hazard calculation using the specified config file and other options.

    :param str cfg_file:
        Path to calculation config (INI-style) file.
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param list exports:
        A list of export types requested by the user. Currently only 'xml'
        is supported.
    """
    try:
        if log_file is not None:
            touch_log_file(log_file)

        job = haz_job_from_file(
            cfg_file, getpass.getuser(), log_level, exports
        )

        # Initialize the supervisor, instantiate the calculator,
        # and run the calculation.
        completed_job = run_calc(
            job, log_level, log_file, exports, 'hazard'
        )
        if completed_job is not None:
            # We check for `None` here because the supervisor and executor
            # process forks return to here as well. We want to ignore them.
            if completed_job.status == 'complete':
                print 'Calculation %d results:' % (
                    completed_job.hazard_calculation.id)
                list_hazard_outputs(completed_job.hazard_calculation.id)
            else:
                complain_and_exit('Calculation %d failed'
                                  % completed_job.hazard_calculation.id,
                                  exit_code=1)
    except IOError as e:
        print str(e)
    except Exception as e:
        raise


def haz_job_from_file(cfg_file_path, username, log_level, exports):
    """
    Create a full hazard job profile from a job config file.

    :param str cfg_file_path:
        Path to the job.ini.
    :param str username:
        The user who will own this job profile and all results.
    :param str log_level:
        Desired log level.
    :param exports:
        List of desired export types.

    :returns:
        :class:`openquake.engine.db.models.OqJob` object
    :raises:
        `RuntimeError` if the input job configuration is not valid
    """
    # create the job
    job = prepare_job(user_name=username, log_level=log_level)

    # read calculation params and create the calculation profile
    params, files = parse_config(open(cfg_file_path, 'r'))
    calculation = create_hazard_calculation(
        username, params, files
    )
    job.hazard_calculation = calculation
    job.save()

    # validate and raise if there are any problems
    error_message = validate(job, 'hazard', params, files, exports)
    if error_message:
        raise RuntimeError(error_message)

    return job


def list_hazard_outputs(hc_id):
    """
    List the outputs for a given
    :class:`~openquake.engine.db.models.HazardCalculation`.

    :param hc_id:
        ID of a hazard calculation.
    """
    print_outputs_summary(get_hazard_outputs(hc_id))


def get_hazard_outputs(hc_id):
    """
    :param hc_id:
        ID of a hazard calculation.
    :returns:
        A sequence of :class:`openquake.engine.db.models.Output` objects
    """
    return models.Output.objects.filter(oq_job__hazard_calculation=hc_id)


def touch_log_file(log_file):
    """
    If a log file destination is specified, attempt to open the file in
    'append' mode ('a'). If the specified file is not writable, an
    :exc:`IOError` will be raised.
    """
    try:
        open(os.path.abspath(log_file), 'a').close()
    except IOError as e:
        raise IOError('Error writing to log file %s: %s'
                      % (log_file, e.strerror))


def complain_and_exit(msg, exit_code=0):
    """
    Print a ``msg`` and exit the current process with the given ``exit_code``.
    """
    print msg
    sys.exit(exit_code)


def print_outputs_summary(outputs):
    """
    List of :class:`openquake.engine.db.models.Output` objects.
    """
    if len(outputs) > 0:
        print 'id | output_type | name'
        for o in outputs.order_by('output_type'):
            print '%s | %s | %s' % (o.id, o.output_type, o.display_name)


def run_risk(cfg_file, log_level, log_file, exports, hazard_output_id=None,
             hazard_calculation_id=None):
    """
    Run a risk calculation using the specified config file and other options.
    One of hazard_output_id or hazard_calculation_id must be specified.

    :param str cfg_file:
        Path to calculation config (INI-style) file.
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param list exports:
        A list of export types requested by the user. Currently only 'xml'
        is supported.
    :param str hazard_ouput_id:
        The Hazard Output ID used by the risk calculation (can be None)
    :param str hazard_calculation_id:
        The Hazard Calculation ID used by the risk calculation (can be None)
    """
    try:
        if log_file is not None:
            touch_log_file(log_file)

        job = risk_job_from_file(
            cfg_file, getpass.getuser(), log_level, exports, hazard_output_id,
            hazard_calculation_id
        )

        # Initialize the supervisor, instantiate the calculator,
        # and run the calculation.
        completed_job = run_calc(
            job, log_level, log_file, exports, 'risk'
        )
        if completed_job is not None:
            # We check for `None` here because the supervisor and executor
            # process forks return to here as well. We want to ignore them.
            if completed_job.status == 'complete':
                print 'Calculation %d results:' % (
                    completed_job.risk_calculation.id)
                list_risk_outputs(completed_job.risk_calculation.id)
            else:
                complain_and_exit('Calculation %s failed'
                                  % completed_job.risk_calculation.id,
                                  exit_code=1)
    except IOError as e:
        print str(e)
    except Exception as e:
        raise


def risk_job_from_file(cfg_file_path, username, log_level, exports,
                       hazard_output_id=None, hazard_calculation_id=None):
    """
    Create a full risk job profile from a job config file.

    :param str cfg_file_path:
        Path to the job.ini.
    :param str username:
        The user who will own this job profile and all results.
    :param str log_level:
        Desired log level.
    :param exports:
        List of desired export types.
    :param int hazard_output_id:
        ID of a hazard output to use as input to this calculation. Specify
        this xor ``hazard_calculation_id``.
    :param int hazard_calculation_id:
        ID of a complete hazard calculation to use as input to this
        calculation. Specify this xor ``hazard_output_id``.

    :returns:
        :class:`openquake.engine.db.models.OqJob` object
    :raises:
        `RuntimeError` if the input job configuration is not valid
    """
    assert not(hazard_output_id is None and hazard_calculation_id is None), (
        "Must specify either `hazard_output_id` or `hazard_calculation_id`, "
        "and not both"
    )
    # create the job
    job = prepare_job(user_name=username, log_level=log_level)

    # read calculation params and create the calculation profile
    params, files = parse_config(open(cfg_file_path, 'r'))
    # Add the hazard output id to the risk calculation constructor args
    params.update(dict(hazard_output_id=hazard_output_id,
                       hazard_calculation_id=hazard_calculation_id))

    calculation = create_risk_calculation(
        job.owner, params, files
    )
    job.risk_calculation = calculation
    job.save()

    error_message = validate(job, 'risk', params, files,  exports)
    if error_message:
        raise RuntimeError(error_message)

    return job


def list_risk_outputs(rc_id):
    """
    List the outputs for a given
    :class:`~openquake.engine.db.models.RiskCalculation`.

    :param rc_id:
        ID of a risk calculation.
    """
    print_outputs_summary(get_risk_outputs(rc_id))


def get_risk_outputs(rc_id):
    """
    :param rc_id:
        ID of a risk calculation.
    :returns:
        A sequence of :class:`openquake.engine.db.models.Output` objects
    """
    return models.Output.objects.filter(oq_job__risk_calculation=rc_id)


def get_hazard_calculations(username):
    """
    Get all hazard calculations belonging to the given ``username``.
    """
    return models.HazardCalculation.objects\
        .filter(owner__user_name=username)\
        .order_by('oqjob__last_update')


def get_risk_calculations(username):
    """
    Get all risk calculations belonging to the given ``username``.
    """
    return models.RiskCalculation.objects\
        .filter(owner__user_name=username)\
        .order_by('oqjob__last_update')
