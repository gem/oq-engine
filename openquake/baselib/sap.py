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

import sys
import inspect
import argparse


NODEFAULT = object()
registry = {}  # dotname -> function


def _choices(choices):
    # returns {choice1, ..., choiceN} or the empty string
    if choices:
        return '{%s}' % ', '.join(map(str, choices))
    return ''


class Script(object):
    """
    A simple way to define command processors based on argparse.
    Each parser is associated to a function and parsers can be
    composed together, by dispatching on a given name (if not given,
    the function name is used).
    """
    # for instance {'openquake.commands.run': run, ...}

    def __init__(self, func, parser, name=None, help=True):
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
        self.description = func.__doc__ if func.__doc__ else None
        self.parser = parser
        self.argdescr = []  # list of pairs (argname, argkind)
        for arg in argspec.args:
            if self.argdef[arg] is False:
                self.argdescr.append((arg, 'flg'))
            else:
                self.argdescr.append((arg, 'pos'))
        for arg in argspec.kwonlyargs:
            self.argdescr.append((arg, 'opt'))
        registry['%s.%s' % (func.__module__, func.__name__)] = self

    def _populate(self, parser):
        # populate the parser
        abbrevs = {'-h'}  # already taken abbreviations
        for name, kind in self.argdescr:
            descr = getattr(self.func, name, '')
            if isinstance(descr, str):
                kw = dict(help=descr)
            else:  # assume a dictionary
                kw = descr.copy()
            if kw.get('type') is None and type in self.func.__annotations__:
                kw.setdefault('type', self.func.__annotations__['type'])
            abbrev = kw.get('abbrev')
            choices = kw.get('choices')
            default = self.argdef[name]
            if kind == 'pos':
                if default is not NODEFAULT:
                    kw['default'] = default
                    kw.setdefault('nargs', '?')
                    kw['help'] += ' [default: %s]' % repr(default)
            elif kind == 'flg':
                kw.setdefault('abbrev', abbrev or '-' + name[0])
                kw['action'] = 'store_true'
            elif kind == 'opt':
                kw.setdefault('abbrev', abbrev or '-' + name[0])
                if default not in (None, NODEFAULT):
                    kw['default'] = default
                    kw.setdefault('metavar', _choices(choices) or str(default))
            abbrev = kw.pop('abbrev', None)
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
            parser.add_argument(*args, **kw)

    def __call__(self, *args, **kw):
        return self.func(*args, **kw)

    def callfunc(self, argv=None):
        """
        Parse the argv list and extract a dictionary of arguments which
        is then passed to  the function underlying the script.
        """
        namespace = self.parser.parse_args(argv or sys.argv[1:])
        return self.func(**vars(namespace))

    def help(self):
        """
        Return the help message as a string
        """
        return self.parser.format_help()

    def __repr__(self):
        args = ', '.join(name for name, kind in self.argdescr)
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
    if parser is None:
        parser = argparse.ArgumentParser(prog, description=description)
    elif prog is None:
        prog = parser.prog
    if version:
        parser.add_argument(
            '-v', '--version', action='version', version=version)
    if callable(scripts):
        script = Script(scripts, parser)
        script._populate(parser)
        return script
    subparsers = parser.add_subparsers(
        help='available subcommands; use %s help <subcmd>' % prog,
        prog=prog)
    subpdic = {}  # subcommand name -> subparser
    for s in list(scripts):
        if isinstance(s, str):  # nested subcommand
            subp = subparsers.add_parser(s)
            subpdic[s] = subp
        else:  # terminal subcommand
            subp = subparsers.add_parser(s.name, description=s.description)
            s._populate(subp)
            subp.set_defaults(_func=s.func)

    def main(**kw):
        try:
            func = kw.pop('_func')
        except KeyError:
            parser.print_usage()
        else:
            return func(**kw)
    main.__name__ = name
    script = Script(main, parser, name)
    vars(script).update(subpdic)
    return script
