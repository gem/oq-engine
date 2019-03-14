# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import getpass
import logging
from openquake.baselib import sap, config, datastore
from openquake.baselib.general import safeprint
from openquake.hazardlib import valid
from openquake.commonlib import logs, readinput
from openquake.engine import engine as eng
from openquake.engine.export import core
from openquake.engine.utils import confirm
from openquake.engine.tools.make_html_report import make_report
from openquake.server import dbserver
from openquake.commands.abort import abort


HAZARD_CALCULATION_ARG = "--hazard-calculation-id"
MISSING_HAZARD_MSG = "Please specify '%s=<id>'" % HAZARD_CALCULATION_ARG


def get_job_id(job_id, username=None):
    job = logs.dbcmd('get_job', job_id, username)
    if not job:
        sys.exit('Job %s not found' % job_id)
    return job.id


def run_job(job_ini, log_level='info', log_file=None, exports='',
            username=getpass.getuser(), **kw):
    """
    Run a job using the specified config file and other options.

    :param str job_ini:
        Path to calculation config (INI-style) files.
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param exports:
        A comma-separated string of export types requested by the user.
    :param username:
        Name of the user running the job
    :param kw:
        Extra parameters like hazard_calculation_id and calculation_mode
    """
    job_id = logs.init('job', getattr(logging, log_level.upper()))
    with logs.handle(job_id, log_level, log_file):
        job_ini = os.path.abspath(job_ini)
        oqparam = eng.job_from_file(job_ini, job_id, username, **kw)
        kw['username'] = username
        eng.run_calc(job_id, oqparam, exports, **kw)
        for line in logs.dbcmd('list_outputs', job_id, False):
            safeprint(line)
    return job_id


def run_tile(job_ini, sites_slice):
    """
    Used in tiling calculations
    """
    return run_job(job_ini, sites_slice=(sites_slice.start, sites_slice.stop))


def del_calculation(job_id, confirmed=False):
    """
    Delete a calculation and all associated outputs.
    """
    if logs.dbcmd('get_job', job_id) is None:
        print('There is no job %d' % job_id)
        return

    if confirmed or confirm(
            'Are you sure you want to (abort and) delete this calculation and '
            'all associated outputs?\nThis action cannot be undone. (y/n): '):
        try:
            abort(job_id)
            resp = logs.dbcmd('del_calc', job_id, getpass.getuser())
        except RuntimeError as err:
            safeprint(err)
        else:
            if 'success' in resp:
                print('Removed %d' % job_id)
            else:
                print(resp['error'])


def smart_run(job_ini, oqparam, log_level, log_file, exports, reuse_hazard):
    """
    Run calculations by storing their hazard checksum and reusing previous
    calculations if requested.
    """
    haz_checksum = readinput.get_checksum32(oqparam, hazard=True)
    # retrieve an old calculation with the right checksum, if any
    job = logs.dbcmd('get_job_from_checksum', haz_checksum)
    reuse = reuse_hazard and job and os.path.exists(job.ds_calc_dir + '.hdf5')
    # recompute the hazard and store the checksum
    ebr = (oqparam.calculation_mode == 'event_based_risk' and
           'gmfs' not in oqparam.inputs)
    if ebr:
        kw = dict(calculation_mode='event_based')
        if (oqparam.sites or 'sites' in oqparam.inputs or
                'site_model' in oqparam.inputs):
            # remove exposure from the hazard
            kw['exposure_file'] = ''
    else:
        kw = {}
    if not reuse:
        hc_id = run_job(job_ini, log_level, log_file, exports, **kw)
        if job is None:
            logs.dbcmd('add_checksum', hc_id, haz_checksum)
        elif not reuse_hazard or not os.path.exists(job.ds_calc_dir + '.hdf5'):
            logs.dbcmd('update_job_checksum', hc_id, haz_checksum)
        if ebr:
            run_job(job_ini, log_level, log_file,
                    exports, hazard_calculation_id=hc_id)
    else:
        hc_id = job.id
        logging.info('Reusing job #%d', job.id)
        run_job(job_ini, log_level, log_file,
                exports, hazard_calculation_id=hc_id)


@sap.Script  # do not use sap.script, other oq engine will break
def engine(log_file, no_distribute, yes, config_file, make_html_report,
           upgrade_db, db_version, what_if_I_upgrade, run,
           list_hazard_calculations, list_risk_calculations,
           delete_calculation, delete_uncompleted_calculations,
           hazard_calculation_id, list_outputs, show_log,
           export_output, export_outputs, exports='',
           log_level='info', reuse_hazard=False):
    """
    Run a calculation using the traditional command line API
    """
    if not run:
        # configure a basic logging
        logs.init()

    if config_file:
        config.read(os.path.abspath(os.path.expanduser(config_file)),
                    soft_mem_limit=int, hard_mem_limit=int, port=int,
                    multi_user=valid.boolean, multi_node=valid.boolean)

    if no_distribute:
        os.environ['OQ_DISTRIBUTE'] = 'no'

    # check if the datadir exists
    datadir = datastore.get_datadir()
    if not os.path.exists(datadir):
        os.makedirs(datadir)

    dbserver.ensure_on()
    # check if we are talking to the right server
    err = dbserver.check_foreign()
    if err:
        sys.exit(err)

    if upgrade_db:
        msg = logs.dbcmd('what_if_I_upgrade', 'read_scripts')
        if msg.startswith('Your database is already updated'):
            pass
        elif yes or confirm('Proceed? (y/n) '):
            logs.dbcmd('upgrade_db')
        sys.exit(0)

    if db_version:
        safeprint(logs.dbcmd('db_version'))
        sys.exit(0)

    if what_if_I_upgrade:
        safeprint(logs.dbcmd('what_if_I_upgrade', 'extract_upgrade_scripts'))
        sys.exit(0)

    # check if the db is outdated
    outdated = logs.dbcmd('check_outdated')
    if outdated:
        sys.exit(outdated)

    # hazard or hazard+risk
    if hazard_calculation_id == -1:
        # get the latest calculation of the current user
        hc_id = get_job_id(hazard_calculation_id, getpass.getuser())
    elif hazard_calculation_id:
        # make it possible to use calculations made by another user
        hc_id = get_job_id(hazard_calculation_id)
    else:
        hc_id = None
    if run:
        log_file = os.path.expanduser(log_file) \
            if log_file is not None else None
        job_inis = [os.path.expanduser(f) for f in run]
        if len(job_inis) == 1 and not hc_id:
            # init logs before calling get_oqparam
            logs.init('nojob', getattr(logging, log_level.upper()))
            # not using logs.handle that logs on the db
            oq = readinput.get_oqparam(job_inis[0])
            smart_run(job_inis[0], oq, log_level, log_file,
                      exports, reuse_hazard)
            return
        for i, job_ini in enumerate(job_inis):
            open(job_ini, 'rb').read()  # IOError if the file does not exist
            job_id = run_job(job_ini, log_level, log_file,
                             exports, hazard_calculation_id=hc_id)
            if not hc_id:  # use the first calculation as base for the others
                hc_id = job_id
    # hazard
    elif list_hazard_calculations:
        for line in logs.dbcmd(
                'list_calculations', 'hazard', getpass.getuser()):
            safeprint(line)
    elif delete_calculation is not None:
        del_calculation(delete_calculation, yes)
    # risk
    elif list_risk_calculations:
        for line in logs.dbcmd('list_calculations', 'risk', getpass.getuser()):
            safeprint(line)

    # export
    elif make_html_report:
        safeprint('Written %s' % make_report(make_html_report))
        sys.exit(0)

    elif list_outputs is not None:
        hc_id = get_job_id(list_outputs)
        for line in logs.dbcmd('list_outputs', hc_id):
            safeprint(line)
    elif show_log is not None:
        hc_id = get_job_id(show_log)
        for line in logs.dbcmd('get_log', hc_id):
            safeprint(line)

    elif export_output is not None:
        output_id, target_dir = export_output
        dskey, calc_id, datadir = logs.dbcmd('get_output', int(output_id))
        for line in core.export_output(
                dskey, calc_id, datadir, os.path.expanduser(target_dir),
                exports or 'csv,xml'):
            safeprint(line)

    elif export_outputs is not None:
        job_id, target_dir = export_outputs
        hc_id = get_job_id(job_id)
        for line in core.export_outputs(
                hc_id, os.path.expanduser(target_dir), exports or 'csv,xml'):
            safeprint(line)

    elif delete_uncompleted_calculations:
        logs.dbcmd('delete_uncompleted_calculations', getpass.getuser())

    else:
        engine.parentparser.prog = 'oq engine'
        engine.parentparser.print_usage()


engine._add('log_file', '--log-file', '-L', help='''\
Location where to store log messages; if not specified, log messages
will be printed to the console (to stderr)''')
engine._add('no_distribute', '--no-distribute', '--nd', help='''\
Disable calculation task distribution and run the
computation in a single process. This is intended for
use in debugging and profiling.''', action='store_true')
engine.flg('yes', 'Automatically answer "yes" when asked to confirm an action')
engine.opt('config_file', 'Custom openquake.cfg file, to override default '
           'configurations')
engine._add('make_html_report', '--make-html-report', '--r',
            help='Build an HTML report of the computation at the given date',
            metavar='YYYY-MM-DD|today')
engine.flg('upgrade_db', 'Upgrade the openquake database')
engine.flg('db_version', 'Show the current version of the openquake database')
engine.flg('what_if_I_upgrade', 'Show what will happen to the openquake '
           'database if you upgrade')
engine._add('run', '--run', help='Run a job with the specified config file',
            metavar='JOB_INI', nargs='+')
engine._add('list_hazard_calculations', '--list-hazard-calculations', '--lhc',
            help='List hazard calculation information', action='store_true')
engine._add('list_risk_calculations', '--list-risk-calculations', '--lrc',
            help='List risk calculation information', action='store_true')
engine._add('delete_calculation', '--delete-calculation', '--dc',
            help='Delete a calculation and all associated outputs',
            metavar='CALCULATION_ID', type=int)
engine._add('delete_uncompleted_calculations',
            '--delete-uncompleted-calculations', '--duc',
            help='Delete all the uncompleted calculations',
            action='store_true')
engine._add('hazard_calculation_id', '--hazard-calculation-id', '--hc',
            help='Use the given job as input for the next job')
engine._add('list_outputs', '--list-outputs', '--lo',
            help='List outputs for the specified calculation',
            metavar='CALCULATION_ID')
engine._add('show_log', '--show-log', '--sl',
            help='Show the log of the specified calculation',
            metavar='CALCULATION_ID')
engine._add('export_output', '--export-output', '--eo',
            nargs=2, metavar=('OUTPUT_ID', 'TARGET_DIR'),
            help='Export the desired output to the specified directory')
engine._add('export_outputs', '--export-outputs', '--eos',
            nargs=2, metavar=('CALCULATION_ID', 'TARGET_DIR'),
            help='Export all of the calculation outputs to the '
            'specified directory')
engine.opt('exports', 'Comma-separated string specifing the export formats, '
           'in order of priority')
engine.opt('log_level', 'Defaults to "info"',
           choices=['debug', 'info', 'warn', 'error', 'critical'])
engine.flg('reuse_hazard', 'Reuse the event based hazard if available')
