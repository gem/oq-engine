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
import subprocess
import sys


def psql(config, script=None, cmd=None):
    """Runs the `psql` tool either with a command or SQL script.

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
        return (-1, "", "")
    else:
        p = subprocess.Popen(
            cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            # An error occurred.
            print "psql terminated with exit code: %s" % p.returncode
            print err
            sys.exit(1)
        return (p.returncode, out, err)


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
        sys.exit(1)

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
    rev_data = out.split('\n')[2:-3]

    rev_info = dict()
    columns = ("id", "revision", "step")
    for info in rev_data:
        info = [d.strip() for d in info.split('|')]
        rev_info[info[0]] = dict(zip(columns, info[1:]))
    print rev_info


if __name__ == '__main__':
    main(sys.argv)
