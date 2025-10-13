# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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

from copy import deepcopy
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.nga_east import _at_percentile


def get_phi_ss_at_quantile_ACME(phi_model, quantile):
    """
    Returns the phi_ss values at the specified quantile as an instance of
    `class`:: openquake.hazardlib.gsim.base.CoeffsTable - applies to the
    magnitude-dependent cases
    """
    # Setup SA coeffs - the backward compatible Python 2.7 way
    coeffs = deepcopy(phi_model.sa_coeffs)
    coeffs.update(phi_model.non_sa_coeffs)
    for imt in coeffs:
        if quantile is None:
            coeffs[imt] = {"a": phi_model[imt]["mean_a"],
                           "b": phi_model[imt]["mean_b"]}
        else:
            coeffs[imt] = {
                "a": _at_percentile(phi_model[imt]["mean_a"],
                                    phi_model[imt]["var_a"],
                                    quantile),
                "b": _at_percentile(phi_model[imt]["mean_b"],
                                    phi_model[imt]["var_b"],
                                    quantile)}
    return CoeffsTable.fromdict(coeffs, logratio=False)
