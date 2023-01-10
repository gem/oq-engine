# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

import itertools
from openquake.hazardlib.gsim import nga_east as ne
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Maximum discrepancy is increased to 2 % to account for misprints and
# rounding errors in the tables used for the target values
MAX_DISC = 2.0


def maketest(phi_model, phi_s2ss_model, sigma_quantile, csvname):
    # choosing DARRAGH_1CCSP, but anything would work
    def test(self):
        self.check(csvname, max_discrep_percentage=MAX_DISC,
                   gmpe_table="NGAEast_DARRAGH_1CCSP.hdf5",
                   phi_model=phi_model,
                   phi_s2ss_model=phi_s2ss_model,
                   sigma_quantile=sigma_quantile)
        test.__name__ = csvname
    return test


class NGAEastTotalSigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ne.NGAEastGMPETotalSigma


# add tests dynamically
phi_models = ["global", "cena_constant", "cena"]
phi_s2ss_models = ["cena", None]
quantiles = [.05, .50, .95]
SUFFIX = {.05: "LOW", .50: "CENTRAL", .95: "HIGH"}
for phi_model, phi_s2ss_model, quantile in itertools.product(
        phi_models, phi_s2ss_models, quantiles):
    # there are 3 x 2 x 3 = 18 tests
    prefix = phi_model.upper()
    infix = "ERGODIC" if phi_s2ss_model else "NON_ERGODIC"
    suffix = SUFFIX[quantile]
    csvname = f"nga_east_total_sigma_tables/{prefix}_{infix}_{suffix}.csv"
    args = (phi_model, phi_s2ss_model, quantile, csvname)
    setattr(NGAEastTotalSigmaTestCase, 'test_' + csvname, maketest(*args))
