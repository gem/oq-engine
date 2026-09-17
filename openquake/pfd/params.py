# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Validation helpers for FDHA model parameters.

Every parameter that can appear in an ``uncertaintyModel`` logic-tree block
is an explicit, stored, *validated* constructor argument of its model (see
docs/EngineIntegration.md §5.7). These helpers keep the validation and the
error messages uniform across the model families. All of them accept
``None`` transparently (``None`` means "not pinned by the logic-tree branch;
resolve at call time or from the rupture context").
"""

#: Global vocabulary for the ``style`` (faulting style) parameter.
STYLES = frozenset(["all", "normal", "reverse", "strike-slip"])


def check_choice(model, name, value, accepted, canon=str):
    """
    Validate an enumerated model parameter.

    :param model: model class name used in the error message
    :param name: parameter name used in the error message
    :param value: raw value (any type); ``None`` is returned unchanged
    :param accepted: iterable of accepted *canonical* values
    :param canon: canonicalisation callable applied before membership
        testing (e.g. ``str``, or ``lambda v: str(v).lower()``)
    :returns: the canonical value, or ``None``
    :raises ValueError: if the canonical value is not in ``accepted``
    """
    if value is None:
        return None
    cv = canon(value)
    if cv not in accepted:
        raise ValueError(
            f"{model}: invalid {name}={value!r}; "
            f"accepted values: {sorted(accepted)}")
    return cv


def check_style(model, style, accepted=STYLES):
    """
    Validate ``style`` against ``accepted`` (default: the global vocabulary),
    lower-casing it first. Returns ``None`` for ``None``.
    """
    return check_choice(model, "style", style, accepted,
                        canon=lambda v: str(v).lower())


def check_bool(model, name, value):
    """
    Coerce a boolean-ish parameter: ``True``/``False``, or the strings
    ``"true"``/``"false"`` (any case) that the lenient logic-tree parser
    produces for unquoted TOML-style booleans. ``None`` passes through.
    """
    if value is None or isinstance(value, bool):
        return value
    s = str(value).lower()
    if s == "true":
        return True
    if s == "false":
        return False
    raise ValueError(
        f"{model}: invalid {name}={value!r}; expected true or false")


def check_positive(model, name, value):
    """
    Coerce a strictly positive float parameter. ``None`` passes through.
    """
    if value is None:
        return None
    fv = float(value)
    if fv <= 0.0:
        raise ValueError(f"{model}: {name} must be positive; got {value!r}")
    return fv
