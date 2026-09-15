# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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
Subclass-scan registries for the four FDHA model slots.

Mirrors :func:`openquake.hazardlib.scalerel._get_available_class`: model
classes are discovered by walking the slot package and filtering subclasses
of its abstract base, so adding a model needs no hand-maintained import list.
Keyed by class name, sorted.
"""
import os
import inspect
import importlib
from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup
from openquake.pfd.primary_surf_displ.base import (
    BasePrimarySurfDispl, BaseSecondarySurfDispl)
from openquake.pfd.secondary_surf_rup.base import BaseSecondarySurfRup

HERE = os.path.dirname(__file__)

SLOTS = {
    'primary_surf_rup': (BasePrimarySurfRup, 'primary_surf_rup'),
    'primary_surf_displ': (BasePrimarySurfDispl, 'primary_surf_displ'),
    'secondary_surf_rup': (BaseSecondarySurfRup, 'secondary_surf_rup'),
    'secondary_surf_displ': (BaseSecondarySurfDispl, 'secondary_surf_displ'),
}


def _iter_modules(pkgpath):
    """Yield ``(modname, module)`` for every module under ``pkgpath``."""
    for cwd, dirs, files in os.walk(pkgpath):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if not f.endswith('.py'):
                continue
            rel = os.path.relpath(os.path.join(cwd, f), HERE)
            modname, _ = os.path.splitext(rel)
            modname = 'openquake.pfd.' + modname.replace(os.sep, '.')
            if modname.endswith('.__init__'):
                modname = modname[:-len('.__init__')]
            yield modname


def _get_available_class(slot):
    """
    :param slot: one of ``SLOTS``
    :returns: dict class_name -> class, sorted by name
    """
    base, pkg = SLOTS[slot]
    pkgpath = os.path.join(HERE, pkg)
    classes = {}
    for modname in _iter_modules(pkgpath):
        try:
            mod = importlib.import_module(modname)
        except ImportError:
            continue
        for cls in vars(mod).values():
            if (inspect.isclass(cls) and issubclass(cls, base)
                    and cls is not base and not inspect.isabstract(cls)
                    and cls.__module__.startswith('openquake.pfd.' + pkg)):
                classes[cls.__name__] = cls
    return {k: classes[k] for k in sorted(classes)}


def get_available_primary_surf_rup():
    return _get_available_class('primary_surf_rup')


def get_available_primary_surf_displ():
    return _get_available_class('primary_surf_displ')


def get_available_secondary_surf_rup():
    return _get_available_class('secondary_surf_rup')


def get_available_secondary_surf_displ():
    return _get_available_class('secondary_surf_displ')


def get_available(slot):
    """
    :param slot: slot package name (see ``SLOTS``)
    :returns: dict class_name -> class
    """
    if slot not in SLOTS:
        raise KeyError('unknown FDHA model slot %r; expected one of %s'
                       % (slot, ', '.join(sorted(SLOTS))))
    return _get_available_class(slot)
