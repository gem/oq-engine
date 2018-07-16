# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

import unittest
import numpy as np
from openquake.hazardlib.contexts import (DistancesContext, RuptureContext,
                                          SitesContext)
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import const
from openquake.hazardlib.gsim import get_available_gsims
from openquake.hazardlib.gsim.wrapper import WrapperGMPE


GSIM_LIST = get_available_gsims()


class WrapperGMPETestCase(unittest.TestCase):
    """
    Tests the execution of the WrapperGMPE, a GMPE capable of being
    intantiated with a set of GMPE objects organised by IMT and calling the
    required GMPE when givena specific IMT
    """
    def test_wrapper_gmpe_instantiation_dict(self):
        """
        """
        test_dict = {"PGA": "BooreEtAl2014",
                     "PGV": "AkkarEtAlRjb2014",
                     "IA": "TravasarouEtAl2003",
                     "SA(1.0)": "BooreEtAl2014"}
        wrapper = WrapperGMPE(gmpes_by_imt=test_dict)
        for key, gmpe in test_dict.items():
            key_imt = from_string(key)
            self.assertTrue(key_imt in wrapper.gmpes)
            self.assertTrue(isinstance(wrapper.gmpes[key_imt],
                                       GSIM_LIST[gmpe]))

    def test_wrapper_gmpe_instantiation_str(self):
        test_str = "{PGA: BooreEtAl2014, PGV: AkkarEtAlRjb2014, "\
            "IA: TravasarouEtAl2003, SA(1.0): BooreEtAl2014}"
        wrapper = WrapperGMPE(gmpes_by_imt=test_str)
        test_dict = {"PGA": "BooreEtAl2014",
                     "PGV": "AkkarEtAlRjb2014",
                     "IA": "TravasarouEtAl2003",
                     "SA(1.0)": "BooreEtAl2014"}
        for key, gmpe in test_dict.items():
            key_imt = from_string(key)
            self.assertTrue(key_imt in wrapper.gmpes)
            self.assertTrue(isinstance(wrapper.gmpes[key_imt],
                                       GSIM_LIST[gmpe]))

    def _check_elements_in_sets(self, set1, set2):
        for x in set1:
            self.assertTrue(x in set2)

    def test_check_all_attrs_wrapper(self):
        test_dict = {"PGA": "BooreEtAl2014",
                     "PGV": "AkkarEtAlRjb2014",
                     "IA": "TravasarouEtAl2003",
                     "SA(1.0)": "BooreEtAl2014"}
        wrapper = WrapperGMPE(gmpes_by_imt=test_dict)
        for imt, gmpe in test_dict.items():
            gsim = GSIM_LIST[gmpe]()
            self._check_elements_in_sets(
                gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES,
                wrapper.DEFINED_FOR_INTENSITY_MEASURE_TYPES)
            self._check_elements_in_sets(
                gsim.REQUIRES_RUPTURE_PARAMETERS,
                wrapper.REQUIRES_RUPTURE_PARAMETERS)
            self._check_elements_in_sets(
                gsim.REQUIRES_SITES_PARAMETERS,
                wrapper.REQUIRES_SITES_PARAMETERS)
            self._check_elements_in_sets(
                gsim.REQUIRES_DISTANCES, wrapper.REQUIRES_DISTANCES)

    def test_raise_unsupported_imt_error(self):
        test_dict = {"PGA": "BooreEtAl2014",
                     "PGV": "AkkarEtAlRjb2014",
                     "IA": "BooreEtAl2014",
                     "SA(1.0)": "BooreEtAl2014"}
        with self.assertRaises(ValueError) as ve:
            WrapperGMPE(gmpes_by_imt=test_dict)
        self.assertEqual(str(ve.exception),
                         "IMT IA not supported by BooreEtAl2014")

    def _compare_gmpe_call(self, wrapper, gmpe, imt, rctx, dctx, sctx):
        mean_wr, [stddev_wr] = wrapper.get_mean_and_stddevs(
            sctx, rctx, dctx, imt, [const.StdDev.TOTAL])
        mean, [stddev] = gmpe.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                   [const.StdDev.TOTAL])
        np.testing.assert_array_almost_equal(mean, mean_wr)
        np.testing.assert_array_almost_equal(stddev, stddev_wr)

    def test_correct_execution(self):
        test_dict = {"PGA": "BooreEtAl2014",
                     "PGV": "AkkarEtAlRjb2014",
                     "IA": "TravasarouEtAl2003",
                     "SA(1.0)": "BooreEtAl2014"}
        wrapper = WrapperGMPE(gmpes_by_imt=test_dict)
        rctx = RuptureContext()
        rctx.mag = 6.5
        rctx.rake = -90.
        dctx = DistancesContext()
        dctx.rjb = np.array([5., 10.])
        dctx.rrup = np.array([5., 10.])
        sctx = SitesContext()
        sctx.vs30 = np.array([500., 700.])
        for imt, gmpe in test_dict.items():
            self._compare_gmpe_call(wrapper, GSIM_LIST[gmpe](),
                                    from_string(imt), rctx, dctx, sctx)

    def test_execution_missing_imt(self):
        test_dict = {"PGA": "BooreEtAl2014",
                     "PGV": "AkkarEtAlRjb2014",
                     "IA": "TravasarouEtAl2003",
                     "SA(1.0)": "BooreEtAl2014"}
        wrapper = WrapperGMPE(gmpes_by_imt=test_dict)
        rctx = RuptureContext()
        rctx.mag = 6.5
        rctx.rake = -90.
        dctx = DistancesContext()
        dctx.rjb = np.array([5., 10.])
        dctx.rrup = np.array([5., 10.])
        sctx = SitesContext()
        sctx.vs30 = np.array([500., 700.])
        with self.assertRaises(KeyError) as ke:
            wrapper.get_mean_and_stddevs(sctx, rctx, dctx,
                                         from_string('SA(0.5)'),
                                         [const.StdDev.TOTAL])
        # Don't know why but two matching strings not considered equal by
        # nosetests - stripping the excess inverted commas
        self.assertEqual(str(ke.exception).strip("'"),
                         "IMT SA(0.5) not defined for WrapperGMPE")
