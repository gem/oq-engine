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
import inspect
from decorator import getfullargspec
from openquake.baselib import sap
from openquake.calculators.views import rst_table
from openquake.commonlib import logs
from openquake.server import dbserver
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
def db(cmd, args=()):
    """
    Run a database command
    """
    if cmd not in commands:
        okcmds = '\n'.join(
            '%s %s' % (name, repr(' '.join(args)) if args else '')
            for name, args in sorted(commands.items()))
        print('Invalid command "%s": choose one from\n%s' % (cmd, okcmds))
    elif len(args) != len(commands[cmd]):
        print('Wrong number of arguments, expected %s, got %s' % (
            commands[cmd], args))
    else:
        dbserver.ensure_on()
        res = logs.dbcmd(cmd, *convert(args))
        if hasattr(res, '_fields') and res.__class__.__name__ != 'Row':
            print(rst_table(res))
        else:
            print(res)

db.arg('cmd', 'db command')
db.arg('args', 'db command arguments', nargs='*')
