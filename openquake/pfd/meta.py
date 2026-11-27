# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen (OGS), GEM Foundation
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
Renamed PFD model classes.

The model classes follow the naming of the GSIMs in
:mod:`openquake.hazardlib.gsim`: ``<Surname><Year>`` for one author,
``<Surname1><Surname2><Year>`` for two and ``<FirstSurname>EtAl<Year>`` for
three or more, followed by the component (``PrimarySR``, ``PrimaryFD``,
``SecondarySR``, ``SecondaryFD``).

As for the GSIMs, a renamed class is kept for a transition period as a
subclass of the new class with ``superseded_by = <new class>``: it still
works, emits a :class:`openquake.baselib.general.DeprecationWarning` when
instantiated and is left out of the model listings
(``registry.get_available(slot, superseded=False)``). The former names will
be removed in a future version; inputs should use the new names only.
"""
import abc
import functools
import warnings

from openquake.baselib.general import DeprecationWarning


@functools.lru_cache()
def warn_superseded_by(cls):
    """Warn (once per class) when a superseded model class is used."""
    if cls.superseded_by:
        warnings.warn('%s is deprecated and will be removed in a future '
                      'version - use %s instead' % (
                          cls.__name__, cls.superseded_by.__name__),
                      DeprecationWarning)


class MetaPFDModel(abc.ABCMeta):
    """
    Metaclass of the PFD model base classes: an :class:`abc.ABCMeta` that
    gives every model class the attribute ``superseded_by`` (``None``
    unless the class is a deprecated name) and warns when a superseded
    class is instantiated.
    """
    superseded_by = None

    def __call__(cls, *args, **kwargs):
        warn_superseded_by(cls)
        return super().__call__(*args, **kwargs)


def canonical(cls):
    """
    :param cls: a PFD model class
    :returns: the class superseding ``cls``, or ``cls`` itself
    """
    return getattr(cls, 'superseded_by', None) or cls
