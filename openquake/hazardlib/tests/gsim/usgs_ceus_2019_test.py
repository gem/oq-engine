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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
"""
Test case for the Central and Eastern US (CEUS) models used in the 2019
National Seismic Hazard Map. Tests generated from test tables adopted in USGS
NSHMP software:
https://github.com/usgs/nshmp-haz/tree/master/src/gov/usgs/earthquake/nshmp/gmm/tables

An independent set of test tables to exercise the complete site amplification
and aleatory uncertainty models is provided from the US NSHMP implementation
courtesy of Eric Thompson (USGS)
"""
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
import openquake.hazardlib.gsim.usgs_ceus_2019 as ceus

# Standard Deviation Models Test Case

MAX_DISCREP = 0.01


class NGAEastUSGSCEUSUncertaintyEPRITestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSGMPE

    def test_std(self):
        self.check("usgs_ceus_2019/USGS_CEUS_EPRI_INTRA_EVENT_STDDEV.csv",
                   "usgs_ceus_2019/USGS_CEUS_EPRI_INTER_EVENT_STDDEV.csv",
                   "usgs_ceus_2019/USGS_CEUS_EPRI_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_table="nga_east_PEER_EX.hdf5",
                   sigma_model="EPRI")


class NGAEastUSGSCEUSUncertaintyPANELTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSGMPE

    def test_std(self):
        self.check("usgs_ceus_2019/USGS_CEUS_PANEL_INTRA_EVENT_STDDEV.csv",
                   "usgs_ceus_2019/USGS_CEUS_PANEL_INTER_EVENT_STDDEV.csv",
                   "usgs_ceus_2019/USGS_CEUS_PANEL_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_table="nga_east_PEER_EX.hdf5",
                   sigma_model="PANEL")


# Site Amplification Epistemic Uncertainty Test Cases
class NGAEastUSGSCEUSSiteAmpTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSGMPE

    def test_median(self):
        self.check("usgs_ceus_2019/NGAEAST_SITE_MEDIAN_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   gmpe_table="nga_east_PEER_EX.hdf5")


# USGS verification tests using independently generated test tables
# Verification Test Cases - Means and stddevs
def make_test(alias, key):
    def test_all(self):
        self.check(f"usgs_ceus_2019/{alias}_MEAN.csv",
                   f"usgs_ceus_2019/{alias}_TOTAL_STDDEV.csv",
                   max_discrep_percentage=0.15,
                   std_discrep_percentage=0.01,
                   gmpe_table=f"nga_east_{key}.hdf5",
                   epistemic_site=False)
    test_all.__name__ = 'test_all' + key
    return test_all


def add_tests(cls):
    for line in ceus.lines:
        if not line.startswith("NGAEastUSGSSammons"):
            continue
        alias, key = line.split()
        setattr(cls, 'test_all' + key, make_test(alias, key))
    return cls


@add_tests  # 34 tests
class NGAEastUSGSTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSGMPE
