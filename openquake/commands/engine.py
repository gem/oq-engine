# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
from __future__ import print_function
import os
import sys
import getpass
import logging
from openquake.baselib import sap
from openquake.baselib.general import safeprint
from openquake.commonlib import datastore, config, logs
from openquake.engine import engine as eng
from openquake.engine.export import core
from openquake.engine.utils import confirm
from openquake.engine.tools.make_html_report import make_report
from openquake.server import dbserver

HAZARD_CALCULATION_ARG = "--hazard-calculation-id"
MISSING_HAZARD_MSG = "Please specify '%s=<id>'" % HAZARD_CALCULATION_ARG


def get_job_id(job_id, username=None):
    username = username or getpass.getuser()
    job_id = logs.dbcmd('get_job_id', job_id, username)
    if not job_id:
        sys.exit('Job %s of %s not found' % (job_id, username))
    return job_id


def run_job(cfg_file, log_level='info', log_file=None, exports='',
            hazard_calculation_id=None, **kw):
    """
    Run a job using the specified config file and other options.

    :param str cfg_file:
        Path to calculation config (INI-style) files.
    :param str log_level:
        'debug', 'info', 'warn', 'error', or 'critical'
    :param str log_file:
        Path to log file.
    :param exports:
        A comma-separated string of export types requested by the user.
    :param hazard_calculation_id:
        ID of the previous calculation or None
    """
    # if the master dies, automatically kill the workers
    job_ini = os.path.abspath(cfg_file)
    job_id, oqparam = eng.job_from_file(
        job_ini, getpass.getuser(), hazard_calculation_id)
    calc = eng.run_calc(job_id, oqparam, log_level, log_file, exports,
                        hazard_calculation_id=hazard_calculation_id, **kw)
    calc._monitor.flush()
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
    if confirmed or confirm(
            'Are you sure you want to delete this calculation and all '
            'associated outputs?\nThis action cannot be undone. (y/n): '):
        try:
            logs.dbcmd('del_calc', job_id, getpass.getuser())
        except RuntimeError as err:
            safeprint(err)


@sap.Script
def engine(log_file, no_distribute, yes, config_file, make_html_report,
           upgrade_db, version_db, what_if_I_upgrade,
           run_hazard, run_risk, run,
           list_hazard_calculations, list_risk_calculations,
           delete_calculation, delete_uncompleted_calculations,
           hazard_calculation_id, list_outputs, show_log,
           export_output, export_outputs, exports='',
           log_level='info'):
    """
    Run a calculation using the traditional command line API
    """
    config.abort_if_no_config_available()

    if run or run_hazard or run_risk:
        # the logging will be configured in engine.py
        pass
    else:
        # configure a basic logging
        logging.basicConfig(level=logging.INFO)

    if config_file:
        os.environ[config.OQ_CONFIG_FILE_VAR] = os.path.abspath(
            os.path.expanduser(config_file))
        config.refresh()

    if no_distribute:
        os.environ['OQ_DISTRIBUTE'] = 'no'

    # check if the datadir exists
    if not os.path.exists(datastore.DATADIR):
        os.makedirs(datastore.DATADIR)

    dbserver.ensure_on()
    # check if we are talking to the right server
    err = dbserver.check_foreign()
    if err:
        sys.exit(err)

    if upgrade_db:
        logs.set_level('info')
        msg = logs.dbcmd('what_if_I_upgrade', 'read_scripts')
        if msg.startswith('Your database is already updated'):
            pass
        elif yes or confirm('Proceed? (y/n) '):
            logs.dbcmd('upgrade_db')
        sys.exit(0)

    if version_db:
        safeprint(logs.dbcmd('version_db'))
        sys.exit(0)

    if what_if_I_upgrade:
        safeprint(logs.dbcmd('what_if_I_upgrade', 'extract_upgrade_scripts'))
        sys.exit(0)

    # check if the db is outdated
    outdated = logs.dbcmd('check_outdated')
    if outdated:
        sys.exit(outdated)

    # hazard or hazard+risk
    if hazard_calculation_id:
        hc_id = get_job_id(hazard_calculation_id)
    else:
        hc_id = None
    if run:
        job_inis = [os.path.expanduser(ini) for ini in run.split(',')]
        if len(job_inis) not in (1, 2):
            sys.exit('%s should be a .ini filename or a pair of filenames '
                     'separated by a comma' % run)
        for job_ini in job_inis:
            open(job_ini).read()  # raise an IOError if the file does not exist
        log_file = os.path.expanduser(log_file) \
            if log_file is not None else None

        if len(job_inis) == 2:
            # run hazard
            job_id = run_job(job_inis[0], log_level,
                             log_file, exports)
            # run risk
            run_job(job_inis[1], log_level, log_file,
                    exports, hazard_calculation_id=job_id)
        else:
            run_job(
                os.path.expanduser(run), log_level, log_file,
                exports, hazard_calculation_id=hc_id)
    # hazard
    elif list_hazard_calculations:
        for line in logs.dbcmd(
                'list_calculations', 'hazard', getpass.getuser()):
            safeprint(line)
    elif run_hazard is not None:
        safeprint('WARN: --rh/--run-hazard are deprecated, use --run instead',
                  file=sys.stderr)
        log_file = os.path.expanduser(log_file) \
            if log_file is not None else None
        run_job(os.path.expanduser(run_hazard), log_level,
                log_file, exports)
    elif delete_calculation is not None:
        del_calculation(delete_calculation, yes)
    # risk
    elif list_risk_calculations:
        for line in logs.dbcmd('list_calculations', 'risk', getpass.getuser()):
            safeprint(line)
    elif run_risk is not None:
        safeprint('WARN: --rr/--run-risk are deprecated, use --run instead',
                  file=sys.stderr)
        if hazard_calculation_id is None:
            sys.exit(MISSING_HAZARD_MSG)
        log_file = os.path.expanduser(log_file) \
            if log_file is not None else None
        run_job(
            os.path.expanduser(run_risk),
            log_level, log_file, exports,
            hazard_calculation_id=hc_id)

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
engine._add('make_html_report', '--make-html-report', '-r',
            help='Build an HTML report of the computation at the given date',
            metavar='YYYY-MM-DD|today')
engine.flg('upgrade_db', 'Upgrade the openquake database')
engine.flg('version_db', 'Show the current version of the openquake database')
engine.flg('what_if_I_upgrade', 'Show what will happen to the openquake '
           'database if you upgrade')
engine._add('run_hazard', '--run-hazard', '--rh', help='Run a hazard job with '
            'the specified config file', metavar='CONFIG_FILE')
engine._add('run_risk', '--run-risk', '--rr', help='Run a risk job with the '
            'specified config file', metavar='CONFIG_FILE')
engine._add('run', '--run', help='Run a job with the specified config file',
            metavar='CONFIG_FILE')
engine._add('list_hazard_calculations', '--list-hazard-calculations', '--lhc',
            help='List risk calculation information', action='store_true')
engine._add('list_risk_calculations', '--list-risk-calculations', '--lrc',
            help='List hazard calculation information', action='store_true')
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
