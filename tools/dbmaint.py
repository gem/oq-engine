#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""
OpenQuake database maintenance tool, performs schema upgrades and/or data
migration.

  -h | --help     : prints this help string
       --host H   : database host machine name [default: localhost]
  -d | --db D     : database to use [default: openquake]
  -n | --dryrun   : don't do anything just show what needs done
  -p | --path P   : path to schema upgrade files [default: db/schema/upgrades]
  -U | --user U   : database user to use [default: postgres]
"""

from distutils import version
import getopt
import logging
import subprocess
import re
import sys
import os


logging.basicConfig(level=logging.INFO)


def run_cmd(cmds, ignore_exit_code=False):
    """Run the given command and return the exit code, stdout and stderr.

    :param list cmds: the strings that comprise the command to run
    :param bool ignore_exit_code: if `True` no `Exception` will be raised for
        non-zero command exit code.
    :returns: an `(exit code, stdout, stderr)` triple
    :raises Exception: when the command terminates with a non-zero command
        exit code.
    """
    p = subprocess.Popen(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0 and not ignore_exit_code:
        error = ("%s terminated with exit code: %s\n%s"
                 % (cmds[0], p.returncode, err))
        logging.error(error)
        raise Exception(error)
    return (p.returncode, out, err)


def psql(config, script=None, cmd=None, ignore_dryrun=False, runner=run_cmd):
    """Runs the `psql` tool either with a command or SQL script.

    If the `dryrun` configuration flag is set the command will not be run but
    merely printed.
    Please note that `file` and `cmd` are mutually exclusive.

    :param dict config: the configuration to use: database, host, user, path.
    :param string script: the script to run, relative to the path in `config`.
    :param string cmd: the command to run.
    :param bool ignore_dryrun: if `True` the `dryrun` flag in the
        configuration will be disregarded.
    :param runner: function to use for running the `psql` tool.
    :returns: a triple (exit code, stdout, stderr) with psql execution outcome
    """
    if script and cmd:
        raise Exception("Please specify either an SQL script or a command.")

    if not script and not cmd:
        raise Exception("Neither SQL script nor command specified.")

    if config['host'] in ["localhost", "127.0.0.1"]:
        psql_cmd = "psql --set ON_ERROR_STOP=1 -d %(db)s -U %(user)s" % config
    else:
        psql_cmd =\
        "psql --set ON_ERROR_STOP=1 -d %(db)s -U %(user)s -h %(host)s" % config

    cmds = psql_cmd.split()

    if cmd:
        cmds.extend(['-c', "%s" % cmd])
    else:
        cmds.extend(["-f", "%s/%s" % (config['path'], script)])

    if config['dryrun'] and not ignore_dryrun:
        if cmd:
            cmds[-1] = '"%s"' % cmds[-1]
        print " ".join(cmds)
        return (-1, "", "")
    else:
        return runner(cmds)


def find_scripts(path):
    """Find all SQL scripts at level 2 of the given `path`."""
    result = []
    cmd = "find %s -mindepth 2 -maxdepth 2 -type f" \
          "     ( -name *.sql -o -name *.py )" % path

    code, out, err = run_cmd(cmd.split(), ignore_exit_code=True)

    if code == 0:
        prefix_length = len(path) + 1
        for file in out.split('\n'):
            result.append(file[prefix_length:])
    return [r for r in result if r]


def version_key(string):
    """Returns a version representation useful for version comparison"""

    # remove the trailing '-<release>' number if any
    string = string.split('-', 1)[0]

    return version.StrictVersion(string)


def script_sort_key(script):
    """
    Return a sort key to order upgrade scripts first by revision, then
    by step, then by file name
    """

    revision, step, name = script.rsplit('/', 3)

    return version_key(revision), int(step), name


def scripts_to_run(artefact, rev_info, config):
    """The SQL scripts that need to run given the `artefact` and `rev_info`.

    :param string artefact: name of the revision controlled database artefact
    :param dict rev_info: current revision info: revision and step
    :param dict config: the configuration to use: database, host, user, path.

    :return: a sorted list of SQL script paths (relative to the path in
        `config`)
    """
    result = []
    revision = rev_info['revision']

    # find upgrade scripts for this revision
    path = "%s/%s/%s" % (config['path'], artefact, revision)
    files = find_scripts(path)
    step = int(rev_info['step'])
    for script in files:
        spath, sfile = script.split('/')
        if (int(spath) > step):
            result.append(os.path.join(revision, script))

    # find upgrade scripts for revisions newer than the current one
    path = "%s/%s" % (config['path'], artefact)
    current_revision_key = version_key(revision)
    if os.path.isdir(path):
        dirs = [os.path.join(path, d)
                    for d in os.listdir(path)
                    if os.path.isdir(os.path.join(path, d))]

        for dir_name in dirs:
            path_revision = os.path.basename(dir_name)

            if version_key(path_revision) > current_revision_key:
                result.extend(os.path.join(path_revision, s)
                                  for s in find_scripts(dir_name))

    return sorted(result, key=script_sort_key)


def error_occurred(output):
    """Detect psql errors in `output`."""
    regex = re.compile('sql:\d+:\s+ERROR:\s+')
    return regex.search(output) is not None


def run_scripts(artefact, rev_info, scripts, config):
    """Run the SQL `scripts` for the given `artefact`.

    Once all scripts complete the step of the `artefact` at hand will be
    updated to the highest step encountered.

    :param string artefact: name of the revision controlled database artefact
    :param dict rev_info: current revision info: revision and step
    :param list scripts: a sorted list of SQL script paths (relative to the
        path in `config`)
    :param dict config: the configuration to use: database, host, user, path.
    :returns: True for success, False for failure
    """
    max_step = 0
    max_revision = '0.0.0'

    for script in scripts:
        # Keep track of the max. step/revision applied.
        revision, step, _ = script.split('/')
        step = int(step)
        if ((version_key(revision), step) >
            (version_key(max_revision), max_step)):
            max_step = step
            max_revision = revision

        # Run the SQL script.
        results = psql(config, script="%s/%s" % (artefact, script))
        if script_failed(results, script, config):
            # A step of '-1' indicates a broken upgrade.
            max_step = -1
            break

    if max_step != 0:
        cmd = ("UPDATE admin.revision_info SET step=%s, revision='%s', "
               "last_update=timezone('UTC'::text, now()) "
               "WHERE artefact='%s' AND revision = '%s'")
        cmd %= (max_step, max_revision, artefact, rev_info['revision'])
        code, out, err = psql(config, cmd=cmd)

    return max_step != -1


def script_failed((code, out, err), script, config):
    """Log SQL script output and return `True` in case of errors."""
    if not config['dryrun']:
        logging.info("%s (%s)" % (script, code))
        out = out.strip()
        if out:
            logging.info(out)
        err = err.strip()
        if err:
            logging.info(err)
            if error_occurred(err):
                return True
    return False


def perform_upgrade(config):
    """Perform the upgrades for all artefacts in the database.

    :param dict config: the configuration to use: database, host, user, path.
    :returns: True for success, False for failure
    """
    # Get the revision information from the database.
    cmd = "SELECT artefact, id, revision, step FROM admin.revision_info"
    code, out, err = psql(config, cmd=cmd, ignore_dryrun=True)
    # Throw away the psql header and footer.
    db_rev_data = out.split('\n')[2:-3]

    rev_data = dict()
    columns = ("id", "revision", "step")

    # Extract the revision info from the psql input.
    #     artefact     | id | revision | step
    # -----------------+----+----------+------
    #  openquake/admin |  1 | 0.3.9-1  |    0
    #  openquake/eqcat |  2 | 0.3.9-1  |    0
    #  openquake/uiapi |  4 | 0.3.9-1  |    0
    #  openquake/hzrdi |  3 | 0.3.9-1  |    0
    # (4 rows)
    for info in db_rev_data:
        info = [d.strip() for d in info.split('|')]
        rev_data[info[0]] = dict(zip(columns, info[1:]))
    logging.debug(rev_data)

    # one-time only upgrade step (can't be a normal upgrade step)
    if not 'openquake' in rev_data:
        # this code works because we don't support upgrades from 0.3.9; the
        # +1 is for the missing upgrade step for the big schema rename
        cmd = "INSERT INTO admin.revision_info (artefact, revision, step)" \
              "    VALUES ('openquake', '0.4.2', " \
              "            (SELECT SUM(step) FROM admin.revision_info" \
              "                 WHERE revision = '0.4.2') + 1)"
        code, out, err = psql(config, cmd=cmd)
        step = sum(int(r['step']) for r in rev_data.values()
                       if r['revision'] == '0.4.2')
        cmd = "DELETE FROM INTO admin.revision_info" \
              "    WHERE artefact <> 'openquake'"
        rev_data = dict(openquake=dict(revision='0.4.2', step=step))

    # Run upgrade scripts (if any) for all artefacts.
    for artefact, rev_info in rev_data.iteritems():
        scripts = scripts_to_run(artefact, rev_info, config)
        if scripts:
            logging.debug("%s: %s" % (artefact, scripts))
            if not run_scripts(artefact, rev_info, scripts, config):
                return False

    return True


def main(cargs):
    """Run SQL scripts that upgrade the database and/or migrate data."""
    def strip_dashes(arg):
        return arg.split('-')[-1]

    config = dict(
        db="openquake", user="postgres", path="openquake/db/schema/upgrades",
        host="localhost", dryrun=False)
    longopts = ["%s" % k if isinstance(v, bool) else "%s=" % k
                for k, v in config.iteritems()] + ["help"]
    s2l = dict(d="db", p="path", n="dryrun", U="user")

    try:
        opts, args = getopt.getopt(cargs[1:], "hd:np:U:", longopts)
    except getopt.GetoptError, e:
        print e
        print __doc__
        sys.exit(101)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        opt = strip_dashes(opt)
        if opt not in config:
            opt = s2l[opt]
        config[opt] = arg if arg else not config[opt]

    success = perform_upgrade(config)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main(sys.argv)
