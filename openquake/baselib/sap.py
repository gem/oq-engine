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
"""
``openquake.baselib.sap`` is a Simple Argument Parser based on argparse
which is extremely powerful. Its features are

1. zero boilerplate (no decorators)
2. supports arbitrarily nested subcommands with an easy sintax
3. automatically generates a simple parser from a Python module and
   a hierarchic parser from a Python package.

Here is a minimal example of usage:

.. code-block:: python

 >>> def convert_archive(input_, output=None, inplace=False, *, out='/tmp'):
 ...    "Example"
 ...    print(input_, output, inplace, out)
 >>> convert_archive.input_ = 'input file or archive'
 >>> convert_archive.inplace = 'convert inplace'
 >>> convert_archive.output = 'output archive'
 >>> convert_archive.out = 'output directory'
 >>> run(convert_archive, argv=['a.zip', 'b.zip'])
 a.zip b.zip False /tmp
 >>> run(convert_archive, argv=['a.zip', '-i', '-o', '/tmp/x'])
 a.zip None True /tmp/x
"""

import os
import inspect
import argparse
import importlib

NODEFAULT = object()


def _choices(choices):
    # returns {choice1, ..., choiceN} or the empty string
    if choices:
        return '{%s}' % ', '.join(map(str, choices))
    return ''


def _populate(parser, func):
    # populate the parser
    # args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, anns
    argspec = inspect.getfullargspec(func)
    if argspec.varargs:
        raise TypeError('varargs in the signature of %s are not supported'
                        % func)
    defaults = argspec.defaults or ()
    nodefaults = len(argspec.args) - len(defaults)
    alldefaults = (NODEFAULT,) * nodefaults + defaults
    argdef = dict(zip(argspec.args, alldefaults))
    argdef.update(argspec.kwonlydefaults or {})
    parser.description = func.__doc__
    parser.set_defaults(_func=func)
    parser.aliases = {}
    argdescr = []  # list of pairs (argname, argkind)
    for arg in argspec.args:
        if argdef[arg] is False:
            argdescr.append((arg, 'flg'))
        else:
            argdescr.append((arg, 'pos'))
    for arg in argspec.kwonlyargs:
        argdescr.append((arg, 'opt'))
    abbrevs = {'-h'}  # already taken abbreviations
    for name, kind in argdescr:
        if name.endswith('_'):
            # make it possible use bultins/keywords as argument names
            stripped = name.rstrip('_')
            parser.aliases[stripped] = name
        else:
            stripped = name
        descr = getattr(func, name, '')
        if isinstance(descr, str):
            kw = dict(help=descr)
        else:  # assume a dictionary
            kw = descr.copy()
        if (kind != 'flg' and kw.get('type') is None and
                name in func.__annotations__):
            kw.setdefault('type', func.__annotations__[name])
        abbrev = kw.get('abbrev')
        choices = kw.get('choices')
        default = argdef[name]
        if kind == 'pos':
            if default is not NODEFAULT:
                kw['default'] = default
                kw.setdefault('nargs', '?')
                if default is not None:
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
        longname = '--' + stripped.replace('_', '-')
        if abbrev and abbrev in abbrevs:
            # avoid conflicts with previously defined abbreviations
            args = longname,
        elif abbrev:
            if len(abbrev) > 2:  # no single-letter abbrev
                args = longname, abbrev
            else:  # single-letter abbrev
                args = abbrev, longname
            abbrevs.add(abbrev)
        else:
            # no abbrev
            args = stripped,
        parser.add_argument(*args, **kw)


def _rec_populate(parser, funcdict):
    subparsers = parser.add_subparsers(
        help='available subcommands; use %s <subcmd> --help' % parser.prog)
    for name, func in funcdict.items():
        subp = subparsers.add_parser(name, prog=parser.prog + ' ' + name)
        if isinstance(func, dict):  # nested subcommand
            _rec_populate(subp, func)
        else:  # terminal subcommand
            _populate(subp, func)


def pkg2dic(pkg):
    """
    :param pkg: a python module or package
    :returns: a dictionary name -> func_or_dic_of_funcs
    """
    if not hasattr(pkg, '__path__'):  # is a module, not a package
        return {pkg.__name__: pkg.main}
    dic = {}
    for path in pkg.__path__:
        for name in os.listdir(path):
            fname = os.path.join(path, name)
            dotname = pkg.__name__ + '.' + name
            if os.path.isdir(fname) and '__init__.py' in os.listdir(fname):
                subdic = pkg2dic(importlib.import_module(dotname))
                if subdic:
                    dic[name] = subdic
            elif name.endswith('.py') and name not in (
                    '__init__.py', '__main__.py'):
                mod = importlib.import_module(dotname[:-3])
                if hasattr(mod, 'main'):
                    dic[name[:-3]] = mod.main
    return dic


def parser(funcdict, **kw):
    """
    :param funcdict: a function or a nested dictionary of functions
    :param kw: keyword arguments passed to the underlying ArgumentParser
    :returns: the ArgumentParser instance
    """
    if isinstance(funcdict, dict):
        version = funcdict.pop('__version__', None)
    else:
        version = getattr(funcdict, '__version__', None)
    parser = argparse.ArgumentParser(**kw)
    if version:
        parser.add_argument(
            '-v', '--version', action='version', version=version)
    if inspect.ismodule(funcdict):  # passed a module or package
        funcdict = pkg2dic(funcdict)
    if callable(funcdict):
        _populate(parser, funcdict)
    else:
        _rec_populate(parser, funcdict)
    return parser


def _run(parser, argv=None):
    namespace = parser.parse_args(argv)
    try:
        func = namespace.__dict__.pop('_func')
    except KeyError:
        parser.print_usage()
        return
    if hasattr(parser, 'aliases'):
        # go back from stripped to unstripped names
        dic = {parser.aliases.get(name, name): value
               for name, value in vars(namespace).items()}
    else:
        dic = vars(namespace)
    return func(**dic)


def run(funcdict, argv=None, **parserkw):
    """
    :param funcdict: a function or a nested dictionary of functions
    :param argv: a list of command-line arguments (if None, use sys.argv[1:])
    :param parserkw: arguments accepted by argparse.ArgumentParser
    """
    return _run(parser(funcdict, **parserkw), argv)


def runline(line, **parserkw):
    """
    Run a command-line. Useful in the tests.
    """
    pkg, *args = line.split()
    return run(importlib.import_module(pkg), args, **parserkw)
