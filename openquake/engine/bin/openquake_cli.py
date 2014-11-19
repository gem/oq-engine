#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

try:
    import celeryconfig
except ImportError:
    sys.path.append('/usr/openquake/engine')

import openquake.engine

from openquake.engine import __version__
from openquake.engine import engine, logs
from openquake.engine.db import models, upgrade_manager
from openquake.engine.export.core import export as core_export
from openquake.engine.tools.import_gmf_scenario import import_gmf_scenario
from openquake.engine.tools.import_hazard_curves import import_hazard_curves
from openquake.engine.tools import save_hazards, load_hazards
from openquake.engine.tools.make_html_report import make_report

HAZARD_OUTPUT_ARG = "--hazard-output-id"
HAZARD_CALCULATION_ARG = "--hazard-calculation-id"
MISSING_HAZARD_MSG = ("Please specify the ID of the hazard output (or "
                      "job) to be used by using '%s (or %s) <id>'" %
                      (HAZARD_OUTPUT_ARG, HAZARD_CALCULATION_ARG))


def deprecate(option, newoption):
    """
    Print a deprecation warning for obsolete options.
    """
    print('The option %s is deprecated and will be removed in the next '
          'version of the engine.\nUse %s instead.' % (option, newoption))


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
        '--list-inputs', '--li',
        help='List inputs of a specific input type',
        metavar="INPUT_TYPE")

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
        '--delete-hazard-calculation',
        '--dhc',
        help='Delete a hazard calculation and all associated outputs',
        metavar='HAZARD_CALCULATION_ID')

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
        metavar='HAZARD_OUTPUT')
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
    risk_grp.add_argument(
        '--delete-risk-calculation',
        '--drc',
        help='Delete a risk calculation and all associated outputs',
        metavar='RISK_CALCULATION_ID')

    export_grp = parser.add_argument_group('Export')
    export_grp.add_argument(
        '--list-outputs',
        '--lo',
        help='List outputs for the specified calculation',
        metavar='CALCULATION_ID')

    # deprecated options
    export_grp.add_argument(
        '--list-hazard-outputs',
        '--lho',
        help='List outputs for the specified calculation [deprecated]',
        metavar='CALCULATION_ID')
    export_grp.add_argument(
        '--list-risk-outputs',
        '--lro',
        help='List outputs for the specified calculation [deprecated]',
        metavar='CALCULATION_ID')

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
        '--export-hazard-output',
        '--eh',
        help='Export the output to the specified directory [deprecated]',
        nargs=2, metavar=('OUTPUT_ID', 'TARGET_DIR'))
    export_grp.add_argument(
        '--export-risk-output',
        '--er',
        help='Export the output to the specified directory [deprecated]',
        nargs=2, metavar=('OUTPUT_ID', 'TARGET_DIR'))
    export_grp.add_argument(
        '--export-outputs',
        '--eos',
        help='Export all the calculation outputs to the specified directory',
        nargs=2, metavar=('HAZARD_CALCULATION_ID', 'TARGET_DIR'))
    export_grp.add_argument(
        '--export-hazard-outputs',
        '--eho',
        help='Export all the outputs to the specified directory [deprecated]',
        nargs=2, metavar=('HAZARD_CALCULATION_ID', 'TARGET_DIR'))
    export_grp.add_argument(
        '--export-risk-outputs',
        '--ero',
        help='Export all the outputs to the specified directory [deprecated]',
        nargs=2, metavar=('HAZARD_CALCULATION_ID', 'TARGET_DIR'))
    save_load_grp = parser.add_argument_group('Save/Load')
    save_load_grp.add_argument(
        '--save-hazard-calculation', '--shc',
        help=('Save a hazard calculation to a new created directory.'),
        nargs=2, metavar=('HAZARD_CALCULATION_ID', 'DUMP_DIR'))
    save_load_grp.add_argument(
        '--load-hazard-calculation',
        help=("Load a hazard calculation from a saved import. "
              "Only SES outputs currently supported"),
        metavar=('DUMP_DIR'))

    import_grp = parser.add_argument_group('Import')
    import_grp.add_argument(
        '--load-gmf',
        help=('Load gmf from a file. Only single-source gmf are supported '
              'currently. The file can be xml or tab-separated.'),
        metavar='GMF_FILE',
    )
    import_grp.add_argument(
        '--load-curve',
        help=('Load hazard curves from an XML file.'),
        metavar='CURVE_FILE',
    )
    import_grp.add_argument(
        '--list-imported-outputs', action='store_true',
        help=('List outputs which were imported from a file, not calculated '
              'from a job'))

    return parser


def list_inputs(input_type):
    """
    Print a list of available input models
    """

    if input_type == "exposure":
        model = models.ExposureModel
    else:
        sys.exit("Wrong input type. Available input types: exposure")

    inputs = model.objects.all()

    if not inputs.count():
        print "No inputs found of type %s" % input_type
        return
    print ('model id | name')

    for inp in inputs:
        print "%9d|%s" % (inp.id, inp.name)


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
            descr = job.get_param('description', None)
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
            print '%6d | %10s | %s| %s' % (
                job.id, status, last_update, descr)


# TODO: the command-line switches are not tested, included this one
def list_imported_outputs():
    """
    List outputs which were imported from a file, not calculated from a job
    """
    jobs = [jp.job.id for jp in models.JobParam.objects.filter(
            value__contains=' importer, file ', name='description',
            job__user_name=getpass.getuser())]
    outputs = models.Output.objects.filter(oq_job__in=jobs)
    engine.print_outputs_summary(outputs)


def export_outputs(hc_id, target_dir, export_type):
    for output in models.Output.objects.filter(oq_job=hc_id):
        print 'Exporting %s...' % output
        export(output.id, target_dir, export_type)


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

    try:
        the_file = core_export(output_id, target_dir, export_type)
        print 'File Exported:'
        print the_file
    except NotImplementedError, err:
        print err.message
        print 'This feature is probably not implemented yet'


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
        except RuntimeError, err:
            print err.message


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

    exports = args.exports or 'xml'

    if args.version:
        print __version__
        sys.exit(0)

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
        logging.basicConfig(level=logging.INFO)
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

    if args.list_inputs:
        list_inputs(args.list_inputs)

    # hazard
    elif args.list_hazard_calculations:
        logging.basicConfig(level=logging.INFO)
        list_calculations('hazard')
    elif args.run_hazard is not None:
        log_file = expanduser(args.log_file) \
            if args.log_file is not None else None
        engine.run_job(expanduser(args.run_hazard), args.log_level,
                       log_file, args.exports)
    elif args.delete_hazard_calculation is not None:
        del_calc(args.delete_hazard_calculation, args.yes)
    # risk
    elif args.list_risk_calculations:
        list_calculations('risk')
    elif args.run_risk is not None:
        if (args.hazard_output_id is None
                and args.hazard_calculation_id is None):
            sys.exit(MISSING_HAZARD_MSG)
        log_file = expanduser(args.log_file) \
            if args.log_file is not None else None
        engine.run_job(
            expanduser(args.run_risk), args.log_level, log_file,
            args.exports,
            hazard_output_id=args.hazard_output_id,
            hazard_calculation_id=args.hazard_calculation_id)
    elif args.delete_risk_calculation is not None:
        del_calc(args.delete_risk_calculation, args.yes)

    # export
    elif args.list_outputs is not None:
        engine.list_outputs(args.list_outputs)
    elif args.list_hazard_outputs is not None:
        deprecate('--list-hazard-outputs', '--list-outputs')
        engine.list_outputs(args.list_hazard_outputs)
    elif args.list_risk_outputs is not None:
        deprecate('--list-risk-outputs', '--list-outputs')
        engine.list_outputs(args.list_risk_outputs)

    elif args.export_output is not None:
        output_id, target_dir = args.export_output
        export(int(output_id), expanduser(target_dir), exports)

    elif args.export_hazard_output is not None:
        deprecate('--export-hazard-output', '--export-output')
        output_id, target_dir = args.export_hazard_output
        export(int(output_id), expanduser(target_dir), exports)

    elif args.export_risk_output is not None:
        deprecate('--export-hazard-output', '--export-output')
        output_id, target_dir = args.export_risk_output
        export(int(output_id), expanduser(target_dir), exports)

    elif args.export_outputs is not None:
        job_id, target_dir = args.export_outputs
        export_outputs(int(job_id), expanduser(target_dir), exports)
    # deprecated
    elif args.export_hazard_outputs is not None:
        deprecate('--export-hazard-outputs', '--export-outputs')
        job_id, target_dir = args.export_hazard_outputs
        export_outputs(int(job_id), expanduser(target_dir), exports)
    elif args.export_risk_outputs is not None:
        deprecate('--export-risk-outputs', '--export-outputs')
        job_id, target_dir = args.export_risk_outputs
        export_outputs(int(job_id), expanduser(target_dir), exports)
    # import
    elif args.load_gmf is not None:
        with open(args.load_gmf) as f:
            out = import_gmf_scenario(f)
            print 'Added output id=%d of type %s; hazard_calculation_id=%d'\
                % (out.id, out.output_type, out.oq_job.id)
    elif args.load_curve is not None:
        with open(args.load_curve) as f:
            out = import_hazard_curves(f)
            print 'Added output id=%d of type %s; hazard_calculation_id=%d'\
                % (out.id, out.output_type, out.oq_job.id)
    elif args.list_imported_outputs:
        list_imported_outputs()
    elif args.delete_uncompleted_calculations:
        delete_uncompleted_calculations()
    elif args.save_hazard_calculation:
        save_hazards.main(*args.save_hazard_calculation)
    elif args.load_hazard_calculation:
        job_ids = load_hazards.hazard_load(
            models.getcursor('admin').connection, args.load_hazard_calculation)
        print "Load hazard calculation with IDs: %s" % job_ids
    else:
        arg_parser.print_usage()


if __name__ == '__main__':
    main()
