# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2025 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import ast
import sys
import inspect
import getpass
from decorator import getfullargspec
from openquake.baselib import config
from openquake.calculators.views import text_table
from openquake.commonlib import logs
from openquake.server.db import actions

commands = {}
for func in vars(actions).values():
    if inspect.isfunction(func):  # is really a function
        argspec = getfullargspec(func)
        if argspec.args[0] == 'db':  # is a db action
            commands[func.__name__] = argspec.args[1:]


def convert(strings):
    """
    Convert strings into literal Python objects
    """
    for s in strings:
        try:
            yield ast.literal_eval(s)
        except Exception:
            yield s


def main(cmd, args=()):
    """
    Run a database command
    """
    if cmd in commands and len(args) != len(commands[cmd]):
        sys.exit('Wrong number of arguments, expected %s, got %s' % (
            commands[cmd], args))
    elif (cmd not in commands and not cmd.upper().startswith('SELECT') and
          config.multi_user and getpass.getuser() != 'openquake'):
        sys.exit('You have no permission to run %s' % cmd)
    res = logs.dbcmd(cmd, *convert(args))
    if hasattr(res, '_fields') and res.__class__.__name__ != 'Row':
        print(text_table(res))
    else:
        print(res)


main.cmd = 'db command'
main.args = dict(help='db command arguments', nargs='*')
