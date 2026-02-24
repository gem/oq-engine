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
Module :mod:`openquake.fdha.utils` provides shared utility functions
for fault displacement hazard analysis (FDHA) models.
"""

import numpy as np
from openquake.hazardlib.contexts import RuptureContext 
from openquake.hazardlib.gsim.utils import (
    get_fault_type_dummy_variables,
)


def rake_to_style(rake):
    """
    Map rake angle(s) to faulting-style string(s).

    Delegates to :func:`openquake.hazardlib.gsim.utils
    .get_fault_type_dummy_variables` for the rake-to-mechanism
    classification.  The string ``"undefined"`` (accepted by
    :data:`openquake.hazardlib.valid.rake_range`) is mapped to
    ``"all"``.

    :param rake:
        Rake angle(s) in degrees, in [-180, 180]. Scalar, array-like,
        or the string ``"undefined"``.
    :returns:
        One of ``"normal"``, ``"reverse"``, ``"strike_slip"``, or
        ``"all"``
    """
    if isinstance(rake, str):
        if rake.lower() == "undefined":
            return "all"
        raise ValueError("rake string must be 'undefined', got %r" % rake)

    rake = np.atleast_1d(np.asarray(rake, dtype=float))
    if np.any((rake < -180) | (rake > 180)):
        raise ValueError(
            "rake must be in [-180, 180], got %s" % rake
        )

    ctx = RuptureContext([('rake', rake)])
    ss, ns, rs = get_fault_type_dummy_variables(ctx)

    out = np.full(rake.shape, "all", dtype=object)
    out[ss == 1] = "strike_slip"
    out[ns == 1] = "normal"
    out[rs == 1] = "reverse"

    return out.item() if out.size == 1 else np.asarray(out, dtype=str)
