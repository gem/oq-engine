# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Test suite for NGA East GMPEs median value with pre-defined tables.

The median values are taken from Excel tables supplied as an electronic
appendix to:

PEER (2015) "NGA-East: Adjustments to Median Ground-Motion Models for Central
and Eastern North America", Pacific Earthquake Engineering Research Center,
Report Number 2015/08, University of California, Berkeley, August 2015
"""
import os
import openquake.hazardlib.gsim.nga_east as neb
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# A discrepancy of 0.1 % is tolerated
MAX_DISC = 0.1


def maketest(alias, key):
    def test(self):
        self.check(f"nga_east_median_tables/NGAEast_{key}_MEAN.csv",
                   max_discrep_percentage=MAX_DISC,
                   gmpe_table=os.path.join(neb.PATH, f"NGAEast_{key}.hdf5"))
        test.__name__ = f'test_mean_{alias}'
    return test


def build_tests(testcls):
    for line in neb.lines:
        alias, key = line.split()
        setattr(testcls, f'test_mean_{alias}', maketest(alias, key))


class NGAEastTestCase(BaseGSIMTestCase):
    GSIM_CLASS = neb.NGAEastGMPE


#class NGAEastTotalSigmaTestCase(BaseGSIMTestCase):
#    GSIM_CLASS = neb.NGAEastGMPETotalSigma


build_tests(NGAEastTestCase)
#build_tests(NGAEastTotalSigmaTestCase)
