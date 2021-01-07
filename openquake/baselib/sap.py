# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
Here is a minimal example of usage:

.. code-block:: python

    >>> from openquake.baselib import sap
    >>> def fun(input, inplace, output=None, out='/tmp'):
    ...     'Example'
    ...     for item in sorted(locals().items()):
    ...         print('%s = %s' % item)

    >>> s = sap.Script(fun)
    >>> s.arg('input', 'input file or archive')
    >>> s.flg('inplace', 'convert inplace')
    >>> s.arg('output', 'output archive')
    >>> s.opt('out', 'optional output file')

    >>> s.callfunc(['a'])
    inplace = False
    input = a
    out = /tmp
    output = None

    >>> s.callfunc(['a', 'b', '-i', '-o', 'OUT'])
    inplace = True
    input = a
    out = OUT
    output = b

Parsers can be composed too.
"""

import sys
import inspect
import argparse


NODEFAULT = object()
registry = {}  # dotname -> function


def get_parser(parser, description=None, help=True):
    """
    :param parser: :class:`argparse.ArgumentParser` instance or None
    :param description: string used to build a new parser if parser is None
    :param help: flag used to build a new parser if parser is None
    :returns: if parser is None the new parser; otherwise the `.parser`
              attribute (if set) or the parser itself (if not set)
    """
    if parser is None:
        return argparse.ArgumentParser(description=description, add_help=help)
    elif hasattr(parser, 'parser'):
        return parser.parser
    else:
        return parser


def _choices(choices):
    # returns {choice1, ..., choiceN} or the empty string
    if choices:
        return '{%s}' % ', '.join(map(str, choices))
    return ''


def _populate(parser, argdescr):
    # populate the parser
    abbrevs = {'-h'}  # already taken abbreviations
    for name, kw in argdescr.items():
        dic = kw.copy()
        abbrev = dic.pop('abbrev')
        longname = '--' + name.replace('_', '-')
        if abbrev and abbrev in abbrevs:
            # avoid conflicts with previously defined abbreviations
            args = longname,
        elif abbrev:
            # ok abbrev
            args = longname, abbrev
            abbrevs.add(abbrev)
        else:
            # no abbrev
            args = name,
        parser.add_argument(*args, **dic)


class Script(object):
    """
    A simple way to define command processors based on argparse.
    Each parser is associated to a function and parsers can be
    composed together, by dispatching on a given name (if not given,
    the function name is used).
    """
    # for instance {'openquake.commands.run': run, ...}

    def __init__(self, func, name=None, parser=None, help=True):
        self.func = func
        self.name = name or func.__name__
        # args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, anns
        argspec = inspect.getfullargspec(func)
        if argspec.varargs:
            raise TypeError('varargs in the signature of %s are not supported'
                            % func)
        defaults = argspec.defaults or ()
        nodefaults = len(argspec.args) - len(defaults)
        alldefaults = (NODEFAULT,) * nodefaults + defaults
        self.argdef = dict(zip(argspec.args, alldefaults))
        self.argdef.update(argspec.kwonlydefaults or {})
        self.description = descr = func.__doc__ if func.__doc__ else None
        self.parser = get_parser(parser, descr, help)
        self.argdescr = {}  # argname->argkw
        self._argno = 0  # used in the NameError check in the _add method
        self.checked = False  # used in the check_arguments method
        registry['%s.%s' % (func.__module__, func.__name__)] = self

    def _get_type(self, name, type):
        if type is None and name in self.func.__annotations__:
            return self.func.__annotations__[name]
        return type

    def arg(self, name, help, type=None, choices=None, metavar=None,
            nargs=None):
        """
        Describe a positional argument
        """
        kw = dict(help=help, abbrev=None, type=self._get_type(name, type),
                  choices=choices, metavar=metavar, nargs=nargs)
        default = self.argdef[name]
        if default is not NODEFAULT:
            kw['nargs'] = nargs or '?'
            kw['default'] = default
            kw['help'] = kw['help'] + ' [default: %s]' % repr(default)
        self.argdescr[name] = kw

    def opt(self, name, help, abbrev=None,
            type=None, choices=None, metavar=None, nargs=None):
        """
        Describe an option
        """
        kw = dict(help=help, abbrev=abbrev or '-' + name[0],
                  type=self._get_type(name, type),
                  choices=choices, metavar=metavar, nargs=nargs)
        default = self.argdef[name]
        if default not in (None, NODEFAULT):
            kw['default'] = default
            kw['metavar'] = metavar or _choices(choices) or str(default)
        self.argdescr[name] = kw

    def flg(self, name, help, abbrev=None):
        """
        Describe a flag
        """
        self.argdescr[name] = dict(help=help, abbrev=abbrev or '-' + name[0],
                                   action='store_true')

    def check_arguments(self):
        """
        Make sure all arguments have a specification
        """
        for name, default in self.argdef.items():
            if name not in self.argdescr and default is NODEFAULT:
                raise NameError('Missing argparse specification for %r' % name)

    def __call__(self, *args, **kw):
        return self.func(*args, **kw)

    def callfunc(self, argv=None):
        """
        Parse the argv list and extract a dictionary of arguments which
        is then passed to  the function underlying the script.
        """
        if not self.checked:
            self.check_arguments()
            self.checked = True
        namespace = self.parser.parse_args(argv or sys.argv[1:])
        return self.func(**vars(namespace))

    def help(self):
        """
        Return the help message as a string
        """
        return self.parser.format_help()

    def __repr__(self):
        args = ', '.join(self.argdescr)
        return '<%s %s(%s)>' % (self.__class__.__name__, self.name, args)


def script(scripts, name='main', description=None, prog=None,
           version=None, parser=None):
    """
    Collects together different scripts and builds a single
    script dispatching to the subparsers depending on
    the first argument, i.e. the name of the subparser to invoke.

    :param scripts: a list of script instances
    :param name: the name of the composed parser
    :param description: description of the composed parser
    :param prog: name of the script printed in the usage message
    :param version: version of the script printed with --version
    """
    assert len(scripts) >= 1, scripts
    if parser is None:
        parser = argparse.ArgumentParser(
            description=description, add_help=False)
    elif prog is None:
        prog = parser.prog
    if version:
        parser.add_argument(
            '--version', '-v', action='version', version=version)
    subparsers = parser.add_subparsers(
        help='available subcommands; use %s help <subcmd>' % prog,
        prog=prog)

    def gethelp(cmd=None):
        if cmd is None:
            print(parser.format_help())
            return
        subp = subparsers._name_parser_map.get(cmd)
        if subp is None:
            print('No help for unknown command %r' % cmd)
        else:
            print(subp.format_help())
    help_script = Script(gethelp, 'help', help=False)
    progname = '%s ' % prog if prog else ''
    help_script.arg('cmd', progname + 'subcommand')
    subpdic = {}  # subcommand name -> subparser
    for s in list(scripts) + [help_script]:
        if isinstance(s, str):  # nested subcommand
            subp = subparsers.add_parser(s)
            subpdic[s] = subp
        else:  # terminal subcommand
            subp = subparsers.add_parser(s.name, description=s.description)
            _populate(subp, s.argdescr)
            subp.set_defaults(_func=s.func)

    def main(**kw):
        try:
            func = kw.pop('_func')
        except KeyError:
            parser.print_usage()
        else:
            return func(**kw)
    main.__name__ = name
    script = Script(main, name, parser)
    _populate(parser, script.argdescr)
    vars(script).update(subpdic)
    return script
