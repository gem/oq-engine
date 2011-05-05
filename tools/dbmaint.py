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

import getopt
import logging
import subprocess
import sys


logging.basicConfig(level=logging.DEBUG)


def psql(config, script=None, cmd=None):
    """Runs the `psql` tool either with a command or SQL script.

    If the `dryrun` configuration flag is set the command will not be run but
    merely printed.
    Please note that `file` and `cmd` are mutually exclusive.

    :param dict config: the configuration to use: database, host, user, path.
    :param string script: the script to run, relative to the path in `config`.
    :param string cmd: the command to run.

    :returns: a triple (exit code, stdout, stderr) with psql execution outcome
    """
    if script and cmd:
        raise Exception("Please specify either an SQL script or command.")

    psql_cmd = "psql -d %(db)s -U %(user)s -h %(host)s" % config
    cmds = psql_cmd.split()
    if cmd:
        cmds.extend(['-c', "%s" % cmd])
    else:
        cmds.extend(["-f", "%s/%s" % (config['path'], script)])

    if config['dryrun']:
        cmds[-1] = '"%s"' % cmds[-1]
        logging.info(" ".join(cmds))
        return (-1, "", "")
    else:
        p = subprocess.Popen(
            cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            # An error occurred. Abort maintenance run.
            error = (
                "psql terminated with exit code: %s\n%s" % (p.returncode, err))
            logging.error(error)
            raise Exception(error)
        return (p.returncode, out, err)


def find_scripts(path):
    """Find all SQL scripts at level 2 of the given `path`."""
    result = []
    cmd = "find %s -maxdepth 2 -type f -name *.sql" % path
    p = subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        logging.warn(err)
    else:
        prefix_length = len(path) + 1
        for file in out.split('\n'):
            result.append(file[prefix_length:])
    return [r for r in result if r]


def scripts_to_run(artefact, rev_info, config):
    """The SQL scripts that need to run given the `artefact` and `rev_info`.

    :param string artefact: name of the revision controlled database artefact
    :param dict rev_info: current revision info: revision and step
    :param dict config: the configuration to use: database, host, user, path.
    """
    result = []
    path = "%s/%s/%s" % (config['path'], artefact, rev_info['revision'])
    files = find_scripts(path)
    step = int(rev_info['step'])
    for script in files:
        spath, sfile = script.split('/')
        if (int(spath) > step):
            result.append(script)
    return list(sorted(result))


def main(cargs):
    """Perform database maintenance.

    This includes running SQL scripts that upgrade the database and/or migrate
    data.
    """
    def strip_dashes(arg):
        return arg.split('-')[-1]

    config=dict(db="openquake", user="postgres", path="db/schema/upgrades",
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

    # Get the revision information from the database.
    cmd = "SELECT artefact, id, revision, step FROM admin.revision_info"
    code, out, err = psql(config, cmd=cmd)
    # Throw away the psql header and footer.
    db_rev_data = out.split('\n')[2:-3]

    rev_data = dict()
    columns = ("id", "revision", "step")
    for info in db_rev_data:
        info = [d.strip() for d in info.split('|')]
        rev_data[info[0]] = dict(zip(columns, info[1:]))
    logging.debug(rev_data)
    for artefact, rev_info in rev_data.iteritems():
        scripts = scripts_to_run(artefact, rev_info, config)
        logging.debug("%s: %s" % (artefact, scripts))


if __name__ == '__main__':
    main(sys.argv)
