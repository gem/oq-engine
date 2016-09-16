#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2016, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import ast
import shlex
import inspect
from decorator import getfullargspec
from openquake.baselib import sap
from openquake.engine import logs
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
        except:
            yield s


@sap.Script
def db(cmd):
    """
    Run a database command
    """
    cmds = shlex.split(cmd)
    if cmds[0] not in commands:
        okcmds = '\n'.join('%s(%s)' % (name, ', '.join(args))
                           for name, args in sorted(commands.items()))
        print('Invalid command "%s": choose one from\n%s' % (cmds[0], okcmds))
    elif len(cmds[1:]) != len(commands[cmds[0]]):
        print('Wrong number of arguments, expected %s, got %s' % (
            commands[cmds[0]], cmds[1:]))
    else:
        print(logs.dbcmd(*convert(cmds)))


db.arg('cmd', 'db command')
