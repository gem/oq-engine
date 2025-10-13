# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
from openquake.baselib import config
from openquake.baselib.general import safeprint
from openquake.commonlib import logs, datastore
from openquake.engine.engine import create_jobs, run_jobs
from openquake.engine.export import core
from openquake.engine.utils import confirm
from openquake.engine.tools.make_html_report import make_report
from openquake.server import dbserver
from openquake.commands.abort import main as abort


DEFAULT_EXPORTS = 'csv,xml,rst'
HAZARD_CALCULATION_ARG = "--hazard-calculation-id"
MISSING_HAZARD_MSG = "Please specify '%s=<id>'" % HAZARD_CALCULATION_ARG


def get_job_id(job_id, username):
    # limit to the current user only if -1 is passed
    job = logs.dbcmd('get_job', job_id, username if job_id == -1 else None)
    if not job:
        if job_id == -1:
            sys.exit('No jobs for user %s!' % username)
        else:
            sys.exit('Job %s not found' % job_id)
    return job.id


def del_calculation(job_id, confirmed=False):
    """
    Delete a calculation and all associated outputs.
    """
    job = logs.dbcmd('get_job', job_id)
    if not job:
        print('There is no job %d' % job_id)
        return

    if confirmed or confirm(
            'Are you sure you want to (abort and) delete this calculation and '
            'all associated outputs?\nThis action cannot be undone. (y/n): '):
        try:
            abort([job.id])
            resp = logs.dbcmd('del_calc', job.id, getpass.getuser(), False)
        except RuntimeError as err:
            safeprint(err)
        else:
            if 'success' in resp:
                for hdf5path in resp['hdf5paths']:
                    if os.path.exists(hdf5path):
                        os.remove(hdf5path)
                print('Removed %d' % job.id)
            else:
                print(resp['error'])


def main(
        no_distribute=False,
        yes=False,
        upgrade_db=False,
        db_version=False,
        what_if_I_upgrade=False,
        list_hazard_calculations=False,
        list_risk_calculations=False,
        delete_uncompleted_calculations=False,
        multi=False,
        *,
        log_file=None,
        make_html_report=None,
        run=None,
        delete_calculation: int = None,
        hazard_calculation_id: int = None,
        list_outputs: int = None,
        show_log=None,
        export_output=None,
        export_outputs=None,
        param='',
        exports='',
        log_level='info',
        sample_sources=False,
        nodes: int = 1):
    """
    Run a calculation using the traditional command line API
    """
    user_name = getpass.getuser()

    if not run:
        # configure a basic logging
        logging.basicConfig(level=logging.INFO)

    if no_distribute:
        os.environ['OQ_DISTRIBUTE'] = 'no'

    if sample_sources:
        assert 0 < float(sample_sources) < 1
        os.environ['OQ_SAMPLE_SOURCES'] = sample_sources

    # check if the datadir exists
    datadir = datastore.get_datadir()
    if not os.path.exists(datadir):
        os.makedirs(datadir)

    fname = os.path.expanduser(config.dbserver.file)
    host = os.environ.get('OQ_DATABASE', config.dbserver.host)
    if host == '127.0.0.1' and getpass.getuser() != 'openquake':  # no DbServer
        if not os.path.exists(fname):
            upgrade_db = True  # automatically creates the db
            yes = True
    else:  # DbServer yes
        print(f'Using the DbServer on {host}')
        dbserver.ensure_on()
        # check that we are talking to the right server
        err = dbserver.check_foreign()
        if err:
            sys.exit(err)

    if upgrade_db:
        msg = logs.dbcmd('what_if_I_upgrade', 'read_scripts')
        if msg.startswith('Your database is already updated'):
            pass
        elif yes or confirm('Proceed? (y/n) '):
            logs.dbcmd('upgrade_db')
        if not run:
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
    if hazard_calculation_id:
        hc_id = get_job_id(hazard_calculation_id, user_name)
    else:
        hc_id = None
    if run:
        pars = dict(p.split('=', 1) for p in param.split(',')) if param else {}
        log_file = os.path.expanduser(log_file) \
            if log_file is not None else None
        job_inis = [os.path.expanduser(f) for f in run]
        jobs = create_jobs(job_inis, log_level, log_file, user_name, hc_id)
        for job in jobs:
            job.params.update(pars)
            job.params['exports'] = exports
        run_jobs(jobs, nodes=nodes, sbatch=True, precalc=not multi)

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
        hc_id = get_job_id(list_outputs, user_name)
        for line in logs.dbcmd('list_outputs', hc_id):
            safeprint(line)
    elif show_log is not None:
        hc_id = get_job_id(show_log, user_name)
        for line in logs.dbcmd('get_log', hc_id):
            safeprint(line)

    elif export_output is not None:
        output_id, target_dir = export_output
        dskey, calc_id, datadir = logs.dbcmd('get_output', int(output_id))
        for line in core.export_output(
                dskey, calc_id, datadir, os.path.expanduser(target_dir),
                exports or DEFAULT_EXPORTS):
            safeprint(line)

    elif export_outputs is not None:
        job_id, target_dir = export_outputs
        hc_id = get_job_id(job_id, user_name)
        for line in core.export_outputs(
                hc_id, os.path.expanduser(target_dir),
                exports or DEFAULT_EXPORTS):
            safeprint(line)

    elif delete_uncompleted_calculations:
        logs.dbcmd('delete_uncompleted_calculations', getpass.getuser())
    else:
        print("Please pass some option, see oq engine --help")


# flags
main.no_distribute = dict(abbrev='--nd', help='''\
Disable calculation task distribution and run the
computation in a single process. This is intended for
use in debugging and profiling.''')
main.yes = 'Automatically answer "yes" when asked to confirm an action'
main.upgrade_db = 'Upgrade the openquake database'
main.db_version = 'Show the current version of the openquake database'
main.what_if_I_upgrade = (
    'Show what will happen to the openquake database if you upgrade')
main.list_hazard_calculations = dict(
    abbrev='--lhc', help='List hazard calculation information')
main.list_risk_calculations = dict(
    abbrev='--lrc', help='List risk calculation information')
main.delete_uncompleted_calculations = dict(
    abbrev='--duc', help='Delete all the uncompleted calculations')
main.multi = 'Run multiple job.inis in parallel'

# options
main.log_file = dict(
    abbrev='-L', help='''\
Location where to store log messages; if not specified, log messages
will be printed to the console (to stderr)''')
main.make_html_report = dict(
    abbrev='--r', metavar='YYYY-MM-DD|today',
    help='Build an HTML report of the computation at the given date')
main.run = dict(abbrev='--run',
                help='Run a job with the specified config file',
                metavar='JOB_INI', nargs='+')
main.delete_calculation = dict(
    abbrev='--dc',
    help='Delete a calculation and all associated outputs',
    metavar='CALCULATION_ID')
main.hazard_calculation_id = dict(
    abbrev='--hc', help='Use the given job as input for the next job')
main.list_outputs = dict(
    abbrev='--lo', help='List outputs for the specified calculation',
    metavar='CALCULATION_ID')
main.show_log = dict(
    abbrev='--sl', help='Show the log of the specified calculation',
    metavar='CALCULATION_ID')
main.export_output = dict(
    abbrev='--eo', nargs=2, metavar=('OUTPUT_ID', 'TARGET_DIR'),
    help='Export the desired output to the specified directory')
main.export_outputs = dict(
    abbrev='--eos', nargs=2, metavar=('CALCULATION_ID', 'TARGET_DIR'),
    help='Export all of the calculation outputs to the specified directory')
main.param = dict(
    abbrev='-p', help='Override parameters specified with the syntax '
    'NAME1=VALUE1,NAME2=VALUE2,...')
main.exports = ('Comma-separated string specifing the export formats, '
                'in order of priority')
main.log_level = dict(help='Defaults to "info"',
                      choices=['debug', 'info', 'warn', 'error', 'critical'])
main.sample_sources = dict(abbrev='--ss',
                           help="Sample fraction in the range 0..1")
main.nodes = 'Number of SLURM nodes (if applicable)'
