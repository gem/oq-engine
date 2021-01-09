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

import os
import sys
import inspect
import argparse
import importlib

NODEFAULT = object()


def _choices(choices):
    # returns {choice1, ..., choiceN} or the empty string
    if choices:
        return '{%s}' % ', '.join(map(str, choices))
    return ''


class _Script(object):
    def __init__(self, func, parser, name=None):
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

    def _populate(self):
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
            self.parser.add_argument(*args, **kw)

    def __repr__(self):
        args = ', '.join(name for name, kind in self.argdescr)
        return '<%s %s(%s)>' % (self.__class__.__name__, self.name, args)


class Parser(argparse.ArgumentParser):
    """
    argparse.ArgumentParser with a .run method
    """
    def run(self, argv=None):
        """
        Parse the command-line and run the script
        """
        namespace = self.parse_args(argv or sys.argv[1:])
        try:
            func = namespace.__dict__.pop('_func')
        except KeyError:
            self.print_usage()
        else:
            return func(**vars(namespace))


def parser(funcdict, prog=None, description=None, version=None) -> Parser:
    """
    :param funcdict: a function or a nested dictionary of functions
    :param prog: the name of the associated command line application
    :param description: description of the application
    :param version: version of the application printed with --version
    :returns: a sap.Parser instance
    """
    parser = Parser(prog, description=description)
    if version:
        parser.add_argument(
            '-v', '--version', action='version', version=version)
    if callable(funcdict):
        _Script(funcdict, parser)._populate()
    elif isinstance(funcdict, str):  # passed a package name
        funcdict = find_main(funcdict)
    _rec_populate(parser, funcdict, prog)
    return parser


def _rec_populate(parser, funcdict, prog):
    subparsers = parser.add_subparsers(
        help='available subcommands; use %s <subcmd> --help' % prog, prog=prog)
    for name, func in funcdict.items():
        if isinstance(func, dict):  # nested subcommand
            _rec_populate(subparsers.add_parser(name), func, prog + ' ' + name)
        else:  # terminal subcommand
            subp = subparsers.add_parser(name, description=func.__doc__,
                                         prog=prog + ' ' + name)
            subp.set_defaults(_func=func)
            _Script(func, subp)._populate()


def find_main(pkgname):
    """
    :param pkgname: name of a packake (i.e. myapp.plot) with "main" functions
    :returns: a dictionary name -> func_or_subdic
    """
    pkg = importlib.import_module(pkgname)
    dic = {}
    for path in pkg.__path__:
        for name in os.listdir(path):
            fname = os.path.join(path, name)
            dotname = pkgname + '.' + name
            if os.path.isdir(fname) and '__init__.py' in os.listdir(fname):
                subdic = find_main(dotname)
                if subdic:
                    dic[name] = subdic
            elif name.endswith('.py') and name != '__init__.py':
                mod = importlib.import_module(dotname[:-3])
                main = name[:-3]
                if hasattr(mod, main):
                    dic[main] = getattr(mod, main)
    return dic
