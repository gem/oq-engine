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
import getpass
import os
import sys

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

from openquake.engine.utils import config

config.abort_if_no_config_available()

# Please note: the /usr/bin/oq-engine script requires a celeryconfig.py
# file in the PYTHONPATH; when using binary packages, if a celeryconfig.py
# is not available the OpenQuake Engine default celeryconfig.py, located
# in /usr/share/openquake/engine, is used.
try:
    import celeryconfig
except ImportError:
    sys.path.append('/usr/share/openquake/engine')

import openquake.engine

from openquake.engine import __version__
from openquake.engine import engine, logs
from openquake.commonlib import datastore
from openquake.calculators import views
from openquake.server.db import models, upgrade_manager
from openquake.engine.export import core
from openquake.engine.tools.make_html_report import make_report

HAZARD_OUTPUT_ARG = "--hazard-output-id"
HAZARD_CALCULATION_ARG = "--hazard-calculation-id"
MISSING_HAZARD_MSG = ("Please specify the ID of the hazard output (or "
                      "job) to be used by using '%s (or %s) <id>'" %
                      (HAZARD_OUTPUT_ARG, HAZARD_CALCULATION_ARG))


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
        required=False, metavar='LOG_FILE', default='stderr')
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
        HAZARD_OUTPUT_ARG,
        '--ho',
        help='Use the desired hazard output as input for the risk job',
        metavar='HAZARD_OUTPUT_ID')
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


def list_calculations(job_type):
    """
    Print a summary of past calculations.

    :param job_type: 'hazard' or 'risk'
    """
    jobs = models.OqJob.objects.filter(
        user_name=getpass.getuser())
    if job_type == 'hazard':
        jobs = jobs.filter(hazard_calculation__isnull=True)
    else:  # risk
        jobs = jobs.filter(hazard_calculation__isnull=False)
    jobs = jobs.order_by('last_update')

    if len(jobs) == 0:
        print 'None'
    else:
        print ('job_id |     status |         last_update | '
               '        description')
        for job in jobs:
            descr = job.description
            latest_job = job
            if latest_job.is_running:
                status = 'pending'
            else:
                if latest_job.status == 'complete':
                    status = 'successful'
                else:
                    status = 'failed'
            last_update = latest_job.last_update.strftime(
                '%Y-%m-%d %H:%M:%S %Z'
            )
            print ('%6d | %10s | %s| %s' % (
                job.id, status, last_update, descr)).encode('utf-8')


def get_hc_id(hc_id):
    """
    If hc_id is negative, return the last calculation of the current user
    """
    hc_id = int(hc_id)
    if hc_id > 0:
        return hc_id
    return models.OqJob.objects.filter(
        user_name=getpass.getuser()).latest('id').id + hc_id + 1


def export_outputs(hc_id, target_dir, export_type):
    # make it possible commands like `oq-engine --eos -1 /tmp`
    outputs = models.Output.objects.filter(oq_job=hc_id)
    if not outputs:
        sys.exit('Found nothing to export for job %s' % hc_id)
    for output in outputs:
        print 'Exporting %s...' % output
        try:
            export(output.id, target_dir, export_type)
        except Exception as exc:
            print exc


def export(output_id, target_dir, export_type):
    """
    Simple UI wrapper around
    :func:`openquake.engine.export.core.export` which prints a summary
    of files exported, if any.
    """
    queryset = models.Output.objects.filter(pk=output_id)
    if not queryset.exists():
        print 'No output found for OUTPUT_ID %s' % output_id
        return

    if queryset.all()[0].oq_job.status != "complete":
        print ("Exporting output produced by a job which did not run "
               "successfully. Results might be uncomplete")

    the_file = core.export(output_id, target_dir, export_type)
    if the_file.endswith('.zip'):
        print 'Files Exported in', os.path.dirname(the_file)
    else:
        print 'File exported:', the_file


def _touch_log_file(log_file):
    """If a log file destination is specified, attempt to open the file in
    'append' mode ('a'). If the specified file is not writable, an
    :exc:`IOError` will be raised."""
    open(abspath(log_file), 'a').close()


def delete_uncompleted_calculations():
    for job in models.OqJob.objects.filter(
            oqjob__user_name=getpass.getuser()).exclude(
            oqjob__status="successful"):
        del_calc(job.id, True)


def del_calc(job_id, confirmed=False):
    """
    Delete a calculation and all associated outputs.
    """
    if confirmed or confirm(
            'Are you sure you want to delete this calculation and all '
            'associated outputs?\nThis action cannot be undone. (y/n): '):
        try:
            engine.del_calc(job_id)
        except RuntimeError as err:
            print err


def confirm(prompt):
    """
    Ask for confirmation, given a ``prompt`` and return a boolean value.
    """
    while True:
        try:
            answer = raw_input(prompt)
        except KeyboardInterrupt:
            # the user presses ctrl+c, just say 'no'
            return False

        answer = answer.strip().lower()

        if answer not in ('y', 'n'):
            print 'Please enter y or n'
            continue
        return answer == 'y'


def main():
    arg_parser = set_up_arg_parser()

    args = arg_parser.parse_args()

    exports = args.exports or 'xml,csv'

    if args.version:
        print __version__
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
        os.environ[openquake.engine.NO_DISTRIBUTE_VAR] = '1'

    if args.make_html_report:
        conn = models.getcursor('admin').connection
        print 'Written', make_report(conn, args.make_html_report)
        sys.exit(0)

    if args.upgrade_db:
        logs.set_level('info')
        conn = models.getcursor('admin').connection
        msg = upgrade_manager.what_if_I_upgrade(
            conn, extract_scripts='read_scripts')
        print msg
        if msg.startswith('Your database is already updated'):
            pass
        elif args.yes or confirm('Proceed? (y/n) '):
            upgrade_manager.upgrade_db(conn)
        sys.exit(0)

    if args.version_db:
        conn = models.getcursor('admin').connection
        print upgrade_manager.version_db(conn)
        sys.exit(0)

    if args.what_if_I_upgrade:
        conn = models.getcursor('admin').connection
        print upgrade_manager.what_if_I_upgrade(conn)
        sys.exit(0)

    run_job = engine.run_job

    if args.hazard_output_id:
        sys.exit('The --hazard-output-id option is not supported anymore')

    # hazard or hazard+risk
    hc_id = args.hazard_calculation_id
    if hc_id and int(hc_id) < 0:
        # make it possible commands like `oq-engine --run job_risk.ini --hc -1`
        hc_id = get_hc_id(int(hc_id))
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
            job = run_job(job_inis[0], args.log_level,
                          log_file, args.exports)
            # run risk
            run_job(job_inis[1], args.log_level, log_file,
                    args.exports, hazard_calculation_id=job.id)
        else:
            run_job(
                expanduser(args.run), args.log_level, log_file,
                args.exports, hazard_output_id=args.hazard_output_id,
                hazard_calculation_id=hc_id)
    # hazard
    elif args.list_hazard_calculations:
        list_calculations('hazard')
    elif args.run_hazard is not None:
        log_file = expanduser(args.log_file) \
            if args.log_file is not None else None
        run_job(expanduser(args.run_hazard), args.log_level,
                log_file, args.exports)
    elif args.delete_calculation is not None:
        del_calc(args.delete_calculation, args.yes)
    # risk
    elif args.list_risk_calculations:
        list_calculations('risk')
    elif args.run_risk is not None:
        if (args.hazard_output_id is None and
                args.hazard_calculation_id is None):
            sys.exit(MISSING_HAZARD_MSG)
        log_file = expanduser(args.log_file) \
            if args.log_file is not None else None
        run_job(
            expanduser(args.run_risk),
            args.log_level, log_file, args.exports,
            hazard_output_id=args.hazard_output_id,
            hazard_calculation_id=hc_id)

    # export
    elif args.list_outputs is not None:
        engine.list_outputs(get_hc_id(args.list_outputs))
    elif args.show_view is not None:
        job_id, view_name = args.show_view
        print views.view(view_name, datastore.read(int(job_id)))

    elif args.export_output is not None:
        output_id, target_dir = args.export_output
        export(int(output_id), expanduser(target_dir), exports)

    elif args.export_outputs is not None:
        job_id, target_dir = args.export_outputs
        export_outputs(get_hc_id(job_id), expanduser(target_dir), exports)

    elif args.delete_uncompleted_calculations:
        delete_uncompleted_calculations()
    else:
        arg_parser.print_usage()


if __name__ == '__main__':
    main()
