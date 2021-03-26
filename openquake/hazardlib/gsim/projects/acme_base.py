# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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

class CoeffsTableACME(CoeffsTable):

    def __getitem__(self, imt):
        """
        Return a dictionary of coefficients corresponding to ``imt``
        from this table (if there is a line for requested IMT in it),
        or the dictionary of interpolated coefficients, if ``imt`` is
        of type :class:`~openquake.hazardlib.imt.SA` and interpolation
        is possible.

        :raises KeyError:
            If ``imt`` is not available in the table and no interpolation
            can be done.
        """
        try:
            return self._coeffs[imt]
        except KeyError:
            pass
        if imt.name != 'SA':
            self._coeffs[imt] = c = self.non_sa_coeffs[imt]
            return c
        try:
            self._coeffs[imt] = c = self.sa_coeffs[imt]
            return c
        except KeyError:
            pass

        max_below = min_above = None
        for unscaled_imt in list(self.sa_coeffs):
            if unscaled_imt.damping != imt.damping:
                continue
            if unscaled_imt.period > imt.period:
                if min_above is None or unscaled_imt.period < min_above.period:
                    min_above = unscaled_imt
            elif unscaled_imt.period < imt.period:
                if max_below is None or unscaled_imt.period > max_below.period:
                    max_below = unscaled_imt
        if max_below is None or min_above is None:
            raise KeyError(imt)

        # ratio tends to 1 when target period tends to a minimum
        # known period above and to 0 if target period is close
        # to maximum period below.
        ratio = (((imt.period) - (max_below.period))
                 / ((min_above.period) - (max_below.period)))
        max_below = self.sa_coeffs[max_below]
        min_above = self.sa_coeffs[min_above]
        self._coeffs[imt] = c = {
            co: (min_above[co] - max_below[co]) * ratio + max_below[co]
            for co in max_below}
        return c


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
                                    quantile)
                }
    return CoeffsTableACME(sa_damping=5., table=coeffs)
