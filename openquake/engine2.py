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

"""Engine: A collection of fundamental functions for initializing and running
calculations."""

import ConfigParser
import getpass
import md5
import os

from django.core import exceptions
from django.db import close_connection

from openquake import kvs
from openquake import logs
from openquake.db import models
from openquake.supervising import supervisor


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
        :class:`openquake.db.models.OqJob` instance.
    """
    # See if the current user exists
    # If not, create a record for them
    owner = prepare_user(user_name)
    job = models.OqJob(owner=owner, log_level=log_level)
    job.save()
    return job


def prepare_user(user_name):
    """Make sure user with the given name exists, return it."""
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


_FILE_PARAMS_TO_INPUT_TYPE = {
    'source_model_logic_tree_file': 'lt_source',
    'gsim_logic_tree_file': 'lt_gsim',
    'site_model_file': 'site_model',
}


def parse_config(source, force_inputs=False):
    """Parse a dictionary of parameters from an INI-style config file.

    :param source:
        File-like object containing the config parameters.
    :returns:
        A `dict` of the parameter keys and values parsed from the config file
        and a `dict` of :class:`~openquake.db.models.Input` objects, keyed by
        the config file parameter.

        These dicts are return as a tuple/pair.
    """
    cp = ConfigParser.ConfigParser()
    cp.readfp(source)

    base_path = os.path.dirname(
        os.path.join(os.path.abspath('.'), source.name))
    params = dict(base_path=base_path, force_inputs=force_inputs)
    files = dict()

    for sect in cp.sections():
        for key, value in cp.items(sect):
            if key in _FILE_PARAMS_TO_INPUT_TYPE:
                # If this is a file, create (or reuse) an Input for the file.
                input_type = _FILE_PARAMS_TO_INPUT_TYPE[key]
                path = value
                # The `path` may be a path relative to the config file, or it
                # could be an absolute path.
                if not os.path.isabs(path):
                    # It's a relative path.
                    if hasattr(source, 'name'):
                        base_path = os.path.dirname(
                            os.path.abspath(source.name)
                        )
                        path = os.path.join(base_path, path)

                files[key] = get_input(
                    path, input_type, prepare_user(getpass.getuser()),
                    force_inputs
                )
            else:
                params[key] = value

    return params, files


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


def get_input(path, input_type, owner, force_input, name=None):
    """Get an :class:`~openquake.db.models.Input` object for the given file
    (``path``).

    If ``force_input`` is `False` or there are no existing copies of the input
    available to ``owner``, create a fresh `Input` record.

    :param str path:
        Path to the input file.
    :param str input_type:
        The type of input. See :class:`openquake.db.models.Input` for a list of
        valid types.
    :param owner:
        The :class:`~openquake.db.models.OqUser` who will own the input, if a
        fresh input record is being created. If the record is being reused, we
        will only reuse records which belong to this user (if any exist).
    :param bool force_input:
        If `True` do not reuse existing inputs that match the file at ``path``
        and always create a new input.
    :param str name:
        Optional name to help idenfity this input.
    :returns:
        :class:`openquake.db.models.Input` object to represent the input. As a
        side effect, this function will also store a full raw copy of the input
        file (see :class:`openquake.db.models.ModelContent`) and associate it
        to the `Input`.
    """
    inp = None

    digest = _file_digest(path)
    existing_input = _identical_input(input_type, digest, owner.id)

    if force_input or existing_input is None:
        # If we chose to force inputs, or there are simply none to reuse,
        # create the new input.
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
    else:
        # Reuse the existing copy.
        inp = existing_input

    return inp


def _identical_input(input_type, digest, owner_id):
    """Get an identical input with the same type or `None`.

    Identical inputs are found by comparing md5sum digests. In order to avoid
    reusing corrupted/broken input models we ignore all the inputs that are
    associated with a first job that failed.
    Also, we only want inputs owned by the user who is running the current job
    and if there is more than one input we want the most recent one.

    :param str input_type:
        input model type
    :param str digest:
        md5sum digest
    :param int owner_id:
        the database key of the owner
    :returns:
        an `:class:openquake.db.models.Input` instance or `None`
    """
    query = """
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
            WHERE
                id = mjq.min_job_id
                AND status = 'complete'
                AND is_running = false)"""
    ios = list(models.Input.objects.raw(query, [digest, input_type, owner_id]))
    return ios[0] if ios else None


def create_hazard_calculation(owner, params, files):
    """Given a params `dict` parsed from the config file, create a
    :class:`~openquake.db.models.HazardCalculation`.

    :param owner:
        The :class:`~openquake.db.models.OqUser` who will own this profile.
    :param dict params:
        Dictionary of parameter names and values. Parameter names should match
        exactly the field names of
        :class:`openquake.db.model.HazardCalculation`.
    :param list files:
        List of :class:`~openquake.db.models.Input` objects to be linked to the
        calculation.
    :returns:
        :class:`openquake.db.model.HazardCalculation` object. A corresponding
        record will obviously be saved to the database.
    """
    if "export_dir" in params:
        params["export_dir"] = os.path.abspath(params["export_dir"])

    hc = models.HazardCalculation(**params)
    hc.owner = owner
    hc.full_clean()
    hc.save()

    for f in files:
        models.Input2hcalc(input=f, hazard_calculation=hc).save()

    return hc


def run_hazard(job, log_level, log_file, exports):
    """Run a hazard job.

    :param job:
        :class:`openquake.db.models.OqJob` instance which references a valid
        :class:`openquake.db.models.HazardCalculation`.
    :param list exports:
        a (potentially empty) list of export targets, currently only "xml" is
        supported
    """
    # Closing all db connections to make sure they're not shared between
    # supervisor and job executor processes.
    # Otherwise, if one of them closes the connection it immediately becomes
    # unavailable for others.
    close_connection()

    job_pid = os.fork()
    if not job_pid:
        # calculation executor process
        try:
            logs.init_logs_amqp_send(level=log_level, job_id=job.id)
            # run the job
            job.is_running = True
            job.save()
            kvs.mark_job_as_current(job.id)
            _do_run_hazard(job, exports)
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


def _switch_to_job_phase(job, status):
    """Switch to a particular phase of execution.

    This involves setting the job's status as well as creating a
    `job_phase_stats` record.

    :param job:
        An :class:`~openquake.db.models.OqJob` instance.
    :param str status: one of the following: pre_executing, executing,
        post_executing, post_processing, export, clean_up, complete
    """
    job.status = status
    job.save()
    models.JobPhaseStats.objects.create(oq_job=job, job_status=status)
    logs.log_progress("%s" % status, 1)


def _do_run_hazard(job, exports):
    """
    Step through all of the phases of a hazard calculation, updating the job
    status at each phase.

    :param job:
        An :class:`~openquake.db.models.OqJob` instance.
    :param list exports:
        a (potentially empty) list of export targets, currently only "xml" is
        supported
    :returns:
        The input job object when the calculation completes.
    """
    from openquake.calculators.hazard import CALCULATORS_NEXT

    calc_mode = job.hazard_calculation.calculation_mode

    # - Instantiate the calculator class
    calc = CALCULATORS_NEXT[calc_mode](job)

    # - Run the calculation
    _switch_to_job_phase(job, "pre_executing")
    calc.pre_execute()

    _switch_to_job_phase(job, "executing")
    calc.execute()

    _switch_to_job_phase(job, "post_executing")
    calc.post_execute()

    _switch_to_job_phase(job, "post_processing")
    calc.post_process()

    _switch_to_job_phase(job, "export")
    calc.export(exports=exports)

    _switch_to_job_phase(job, "clean_up")
    calc.clean_up()

    _switch_to_job_phase(job, "complete")
    logs.LOG.debug("*> complete")

    return job
