#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

"""
OpenQuake: software for seismic hazard and risk assessment
"""
import logging
import argparse
import os
import sys
import socket
import getpass
import subprocess

from os.path import abspath
from os.path import dirname
from os.path import expanduser
from os.path import join

# just in the case that are you using oq-engine from sources
# with the rest of oq libraries installed into the system (or a
# virtual environment) you must set this environment variable
if os.environ.get("OQ_ENGINE_USE_SRCDIR") is not None:
    sys.modules['openquake'].__dict__["__path__"].insert(
        0, join(dirname(dirname(__file__)), "openquake")
    )

from openquake.engine import utils, config

# Please note: the /usr/bin/oq-engine script requires a celeryconfig.py
# file in the PYTHONPATH; when using binary packages, if a celeryconfig.py
# is not available the OpenQuake Engine default celeryconfig.py, located
# in /usr/share/openquake/engine, is used.
if utils.USE_CELERY:
    try:
        import celeryconfig
    except ImportError:
        sys.path.append('/usr/share/openquake/engine')

from openquake.engine.utils import confirm, config
import openquake.engine
from openquake.engine import engine, logs
from openquake.engine.tools.make_html_report import make_report
from openquake.engine.export import core
from openquake.commonlib import datastore, valid
from openquake.calculators import views

from openquake.commonlib.concurrent_futures_process_mpatch import (
    concurrent_futures_process_monkeypatch)

HAZARD_OUTPUT_ARG = "--hazard-output-id"
HAZARD_CALCULATION_ARG = "--hazard-calculation-id"
MISSING_HAZARD_MSG = "Please specify '%s=<id>'" % HAZARD_CALCULATION_ARG


def get_job_id(job_id, username=None):
    username = username or getpass.getuser()
    job_id = logs.dbcmd('get_job_id', job_id, username)
    if not job_id:
        sys.exit('Job %s of %s not found' % (job_id, username))
    return job_id


def run_job(cfg_file, log_level, log_file, exports='',
            hazard_calculation_id=None):
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
        Currently only 'xml' is supported.
    :param hazard_calculation_id:
        ID of the previous calculation or None
    """
    # if the master dies, automatically kill the workers
    concurrent_futures_process_monkeypatch()
    job_ini = os.path.abspath(cfg_file)
    job_id, oqparam = engine.job_from_file(
        job_ini, getpass.getuser(), hazard_calculation_id)
    calc = engine.run_calc(job_id, oqparam, log_level, log_file, exports,
                           hazard_calculation_id=hazard_calculation_id)
    calc.monitor.flush()
    for line in logs.dbcmd('list_outputs', job_id, False):
        print line
    return job_id


def delete_calculation(job_id, confirmed=False):
    """
    Delete a calculation and all associated outputs.
    """
    if confirmed or confirm(
            'Are you sure you want to delete this calculation and all '
            'associated outputs?\nThis action cannot be undone. (y/n): '):
        try:
            logs.dbcmd('del_calc', job_id, getpass.getuser())
        except RuntimeError as err:
            print(err)


def set_up_arg_parser():
    """Set up and return an :class:`argparse.ArgumentParser` with all of the
    OpenQuake command line options."""
    parser = argparse.ArgumentParser(
        description='OpenQuake Seismic Hazard and Risk Analysis Engine')

    general_grp = parser.add_argument_group('General')
    general_grp.add_argument(
        '--version', action='store_true', help='Display version information')
    general_grp.add_argument(
        '--log-file', '-L',
        help=('Location to store log messages; if not specified, log messages'
              ' will be printed to the console (to stderr)'),
        required=False, metavar='LOG_FILE')
    general_grp.add_argument(
        '--log-level', '-l',
        help='Defaults to "info"', required=False,
        choices=['debug', 'info', 'progress', 'warn', 'error', 'critical'],
        default='info')
    general_grp.add_argument(
        '--no-distribute', '--nd', action='store_true',
        help=('Disable calculation task distribution and run the computation'
              ' in a single process. This is intended for use in debugging '
              ' and profiling.')
    )
    general_grp.add_argument(
        '--run',
        help='Run a job with the specified configuration file; you can also '
        'pass a comma-separated pair of files for hazard and risk',
        metavar='CONFIG_FILE')

    general_grp.add_argument(
        '--yes', '-y', action='store_true',
        help='Automatically answer "yes" when asked to confirm an action'
    )
    general_grp.add_argument(
        '--config-file',
        help='Custom openquake.cfg file, to override default configurations',
        metavar='CONFIG_FILE'
    )
    general_grp.add_argument(
        '--make-html-report', '-r',
        help='Build an HTML report of the computation at the given date',
        metavar='YYYY-MM-DD|today')

    db_grp = parser.add_argument_group('Database')
    db_grp.add_argument(
        '--upgrade-db', action='store_true',
        help='Upgrade the openquake database',
    )
    db_grp.add_argument(
        '--version-db', action='store_true',
        help='Show the current version of the openquake database',
    )
    db_grp.add_argument(
        '--what-if-I-upgrade', action='store_true',
        help='Show what will happen to the openquake database if you upgrade',
    )

    hazard_grp = parser.add_argument_group('Hazard')
    hazard_grp.add_argument(
        '--run-hazard',
        '--rh',
        help='Run a hazard job with the specified config file',
        metavar='CONFIG_FILE')
    hazard_grp.add_argument(
        '--list-hazard-calculations',
        '--lhc',
        help='List hazard calculation information',
        action='store_true')
    hazard_grp.add_argument(
        '--delete-calculation',
        '--dc',
        help='Delete a calculation and all associated outputs',
        metavar='CALCULATION_ID')

    hazard_grp.add_argument(
        '--delete-uncompleted-calculations',
        '--duc',
        action='store_true',
        help='Delete all the uncompleted calculations')

    risk_grp = parser.add_argument_group('Risk')
    risk_grp.add_argument(
        '--run-risk',
        '--rr',
        help='Run a risk job with the specified config file',
        metavar='CONFIG_FILE')
    risk_grp.add_argument(
        HAZARD_CALCULATION_ARG,
        '--hc',
        help='Use the desired hazard job as input for the risk job',
        metavar='HAZARD_CALCULATION_ID')
    risk_grp.add_argument(
        '--list-risk-calculations',
        '--lrc',
        help='List risk calculation information',
        action='store_true')

    export_grp = parser.add_argument_group('Export')
    export_grp.add_argument(
        '--list-outputs',
        '--lo',
        help='List outputs for the specified calculation',
        metavar='CALCULATION_ID')

    export_grp.add_argument(
        '--show-view',
        '--sv',
        help='Show a view of the specified calculation',
        nargs=2, metavar=('CALCULATION_ID', 'VIEW_NAME'))

    export_grp.add_argument(
        '--show-log',
        '--sl',
        help='Show the log of the specified calculation',
        nargs=1, metavar='CALCULATION_ID')

    export_grp.add_argument(
        '--exports', action="store",
        default='',
        help=(
            'Comma-separated string specifing the export formats, in order '
            'of priority'), metavar='EXPORT_FORMATS')
    export_grp.add_argument(
        '--export-output',
        '--eo',
        help='Export the desired output to the specified directory',
        nargs=2, metavar=('OUTPUT_ID', 'TARGET_DIR'))
    export_grp.add_argument(
        '--export-outputs',
        '--eos',
        help='Export all the calculation outputs to the specified directory',
        nargs=2, metavar=('CALCULATION_ID', 'TARGET_DIR'))

    return parser


def main():
    arg_parser = set_up_arg_parser()

    args = arg_parser.parse_args()

    exports = args.exports or 'xml,csv'

    if args.version:
        print openquake.engine.__version__
        sys.exit(0)

    if args.run or args.run_hazard or args.run_risk:
        # the logging will be configured in engine.py
        pass
    else:
        # configure a basic logging
        logging.basicConfig(level=logging.INFO)

    if args.config_file:
        os.environ[config.OQ_CONFIG_FILE_VAR] = \
            abspath(expanduser(args.config_file))
        config.refresh()

    if args.no_distribute:
        os.environ['OQ_DISTRIBUTE'] = 'no'

    # check if the DbServer is up
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        err = sock.connect_ex(config.DBS_ADDRESS)
    finally:
        sock.close()
    if err:
        multi_user = valid.boolean(config.get('dbserver', 'multi_user'))
        if multi_user:
            sys.exit('Please start the DbServer: '
                     'see the documentation for details')
        # otherwise start the DbServer automatically
        dblog = os.path.expanduser('~/oq-dbserver.log')
        subprocess.Popen([sys.executable, '-m', 'openquake.server.dbserver',
                          '-l', 'INFO'], stderr=open(dblog, 'w'))
    if args.upgrade_db:
        logs.set_level('info')
        msg = logs.dbcmd('what_if_I_upgrade', 'read_scripts')
        if msg.startswith('Your database is already updated'):
            pass
        elif args.yes or confirm('Proceed? (y/n) '):
            logs.dbcmd('upgrade_db')
        sys.exit(0)

    if args.version_db:
        print logs.dbcmd('version_db')
        sys.exit(0)

    if args.what_if_I_upgrade:
        print logs.dbcmd('what_if_I_upgrade', 'extract_upgrade_scripts')
        sys.exit(0)

    # check if the db is outdated
    outdated = logs.dbcmd('check_outdated')
    if outdated:
        sys.exit(outdated)

    # hazard or hazard+risk
    if args.hazard_calculation_id:
        hc_id = get_job_id(args.hazard_calculation_id)
    else:
        hc_id = None
    if args.run:
        job_inis = map(expanduser, args.run.split(','))
        if len(job_inis) not in (1, 2):
            sys.exit('%s should be a .ini filename or a pair of filenames '
                     'separated by a comma' % args.run)
        for job_ini in job_inis:
            open(job_ini).read()  # raise an IOError if the file does not exist
        log_file = expanduser(args.log_file) \
            if args.log_file is not None else None

        if len(job_inis) == 2:
            # run hazard
            job_id = run_job(job_inis[0], args.log_level,
                             log_file, args.exports)
            # run risk
            run_job(job_inis[1], args.log_level, log_file,
                    args.exports, hazard_calculation_id=job_id)
        else:
            run_job(
                expanduser(args.run), args.log_level, log_file,
                args.exports, hazard_calculation_id=hc_id)
    # hazard
    elif args.list_hazard_calculations:
        for line in logs.dbcmd(
                'list_calculations', 'hazard', getpass.getuser()):
            print line
    elif args.run_hazard is not None:
        log_file = expanduser(args.log_file) \
            if args.log_file is not None else None
        run_job(expanduser(args.run_hazard), args.log_level,
                log_file, args.exports)
    elif args.delete_calculation is not None:
        delete_calculation(args.delete_calculation, args.yes)
    # risk
    elif args.list_risk_calculations:
        for line in logs.dbcmd('list_calculations', 'risk', getpass.getuser()):
            print line
    elif args.run_risk is not None:
        if args.hazard_calculation_id is None:
            sys.exit(MISSING_HAZARD_MSG)
        log_file = expanduser(args.log_file) \
            if args.log_file is not None else None
        run_job(
            expanduser(args.run_risk),
            args.log_level, log_file, args.exports,
            hazard_calculation_id=hc_id)

    # export
    elif args.make_html_report:
        print 'Written', make_report(args.make_html_report)
        sys.exit(0)

    elif args.list_outputs is not None:
        hc_id = get_job_id(args.list_outputs)
        for line in logs.dbcmd('list_outputs', hc_id):
            print line
    elif args.show_view is not None:
        job_id, view_name = args.show_view
        print views.view(view_name, datastore.read(int(job_id)))
    elif args.show_log is not None:
        hc_id = get_job_id(args.show_log[0])
        for line in logs.dbcmd('get_log', hc_id):
            print line

    elif args.export_output is not None:
        output_id, target_dir = args.export_output
        dskey, calc_id, datadir = logs.dbcmd('get_output', int(output_id))
        for line in core.export_output(
                dskey, calc_id, datadir, expanduser(target_dir), exports):
            print line

    elif args.export_outputs is not None:
        job_id, target_dir = args.export_outputs
        hc_id = get_job_id(job_id)
        for line in core.export_outputs(
                hc_id, expanduser(target_dir), exports):
            print line

    elif args.delete_uncompleted_calculations:
        logs.dbcmd('delete_uncompleted_calculations', getpass.getuser())
    else:
        arg_parser.print_usage()


if __name__ == '__main__':
    config.abort_if_no_config_available()
    main()
